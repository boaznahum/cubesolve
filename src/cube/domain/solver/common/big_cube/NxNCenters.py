from collections.abc import Iterable, Iterator, Sequence, Set
from enum import Enum, unique

from cube.utils.logging import CubeLogger

from cube.domain.exceptions import InternalSWError
from cube.domain.model.PartSlice import CenterSlice
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.geometric.block import Block
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.geometric.geometry_types import Point
from cube.domain.model import Color
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverStatistics import SliceSwapTopic, SolverStatistics, TopicKey
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.commutator.BlockBySliceSwapHelper import BlockBySliceSwapHelper
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper
from cube.domain.solver.protocols import SolverElementsProvider
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker._face_trackers import FaceTracker
from cube.utils.OrderedSet import OrderedSet


@unique
class _SearchBlockMode(Enum):
    CompleteBlock = 1
    BigThanSource = 2
    ExactMatch = 3  # required on source match source



class NxNCenters(SolverHelper):
    """
    Solves center pieces on NxN cubes (N > 3).

    Statistics keys:
        SLICE_SWAP_KEY: Tracks complete slice swap grades and piece counts.

    This solver brings center pieces from source faces to target faces using:
    1. Complete slice swaps (swap entire row/column between faces)
    2. Block commutators (3-cycle blocks of center pieces)
    3. Single-piece commutators (3-cycle individual center pieces)

    MODES OF OPERATION:
    ===================

    preserve_cage=False (default): REDUCTION METHOD
    ------------------------------------------------
    Centers are solved BEFORE edges are paired.
    Setup moves (face rotations for alignment) are NOT undone.
    This is more efficient but BREAKS paired edges.
    Use this when: Centers are solved first, edges paired after.

    preserve_cage=True: CAGE METHOD
    --------------------------------
    Centers are solved AFTER edges and corners.
    Setup moves ARE undone to preserve the "cage" (paired edges + solved corners).
    This is slightly less efficient but preserves the 3x3 solution.
    Use this when: Edges and corners are solved first, then centers.

    WHY SETUP MOVES BREAK THE CAGE:
    ===============================

    The commutator algorithm itself is BALANCED:
        [M', F, M', F', M, F, M, F']
    This has 2 F rotations and 2 F' rotations, so corners return to position.

    However, SETUP MOVES are used to align pieces before the commutator:
    - In _swap_slice: F' to convert row alignment to column
    - In _swap_slice: source_face * n_rotate to align columns
    - In _block_commutator: source_face * n_rotate to align blocks
    - In __do_center: B[1:n] rotations to bring faces up

    These setup moves are NOT balanced - they permanently move corners.
    When preserve_cage=True, we track these moves and UNDO them after.

    ALGORITHM ANALYSIS - WHAT AFFECTS WHAT:
    =======================================

    | Move      | Centers | Edges (paired) | Corners |
    |-----------|---------|----------------|---------|
    | M, M'     | YES     | NO (inner)     | NO      |
    | M2        | YES     | NO             | NO      |
    | F, F'     | YES     | **BREAKS!**    | MOVES   |
    | F2        | YES     | NO (symmetric) | MOVES   |
    | U, U'     | YES     | **BREAKS!**    | MOVES   |
    | B[1:n]    | YES     | **BREAKS!**    | MOVES   |

    EXAMPLE - What preserve_cage=True does:
    =======================================

    Without preserve_cage (reduction method):
        play(F')           # Setup: convert row to column
        play(commutator)   # Balanced, corners return
        # F' is NOT undone - corners are permanently rotated

    With preserve_cage (cage method):
        play(F')           # Setup: convert row to column
        play(commutator)   # Balanced, corners return
        play(F)            # UNDO: restore corners to original position
    """

    SLICE_SWAP_KEY: TopicKey[SliceSwapTopic] = TopicKey("SliceSwap", SliceSwapTopic)

    def __init__(
        self,
        slv: SolverElementsProvider,
        preserve_cage: bool = False,
        tracker_holder: FacesTrackerHolder | None = None,
    ) -> None:
        """
        Initialize the center solver.

        Args:
            slv: Solver elements provider (cube, operator, etc.)

            preserve_cage: Controls whether setup moves are undone.

                False (default): REDUCTION METHOD
                    - Centers solved BEFORE edges
                    - Setup moves are NOT undone (more efficient)
                    - BREAKS paired edges - don't use if edges are already paired!

                True: CAGE METHOD
                    - Centers solved AFTER edges and corners
                    - Setup moves ARE undone (preserves 3x3 solution)
                    - Disables certain optimizations that break the cage:
                      * _OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES

            tracker_holder: Optional FacesTrackerHolder. When provided,
                each commutator execution is wrapped with
                preserve_physical_faces() to restore tracker markers
                to their correct physical faces. Required for even cubes
                where face 5/6 use MarkedFaceTracker.
        """
        super().__init__(slv, "NxNCenters")
        self._logger.set_cube_level(NxNCenters.D_LEVEL)

        self._preserve_cage = preserve_cage
        self._tracker_holder: FacesTrackerHolder | None = tracker_holder

        cfg = self.cube.config
        self._sanity_check_is_a_boy = cfg.solver_sanity_check_is_a_boy

        if preserve_cage:
            # CAGE METHOD: Disable optimizations that break the cage!
            # _do_complete_slices uses U2/B2 which permanently moves corners.
            self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False
        else:
            self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = cfg.optimize_big_cube_centers_search_complete_slices

        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO = cfg.optimize_big_cube_centers_search_complete_slices_only_target_zero
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = cfg.optimize_big_cube_centers_search_blocks

        # Use CommutatorHelper for block search operations
        self._comm_helper = CommutatorHelper(slv)
        # Use BlockBySliceSwapHelper for complete slice swaps
        self._bsh = BlockBySliceSwapHelper(slv)

        # Track complete slice swap statistics
        self._slice_stats: SolverStatistics = SolverStatistics()
        self._slice_stats.get_topic(self.SLICE_SWAP_KEY)  # register

    def _is_solved(self):
        return all((f.center.is3x3 for f in self.cube.faces)) and self.cube.match_original_scheme

    @staticmethod
    def is_cube_solved(cube: Cube):
        return all((f.center.is3x3 for f in cube.faces)) and cube.match_original_scheme

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and matches original scheme
        """

        return self._is_solved()

    def solve(self, holder: FacesTrackerHolder) -> None:
        """
        Solve all centers using the provided face tracker holder.

        The holder provides face trackers that map faces to target colors.
        Cleanup of tracker slices is handled by the holder's context manager,
        NOT by this method.

        Args:
            holder: FaceTrackerHolder containing trackers for each face.
                    The caller is responsible for cleanup via context manager.
        """
        if self._is_solved():
            return  # avoid rotating cube

        with self.ann.annotate(h1="Big cube centers"):
            self._solve(holder)

    def solve_single_face(self, holder: FacesTrackerHolder, target_tracker: FaceTracker) -> None:
        """
        Solve centers for a single target face only.

        Used by layer-by-layer solver to solve one face at a time.

        Args:
            holder: FaceTrackerHolder containing trackers for all faces
                    (needed to know face colors and for source pieces).
            target_tracker: FaceTracker for the target face (tracks by color).
        """

        target_face = target_tracker.face
        if self._is_face_solved(target_face, target_tracker.color):
            return

        with self.ann.annotate(h1=lambda: f"Centers for {target_tracker.color.name}"):
            # Get all trackers for sanity checking
            all_faces: list[FaceTracker] = list(holder)

            # Solve only the target face
            while True:
                if not self._do_faces(holder, [target_tracker]):
                    break
                self._asserts_is_boy(all_faces)

            self._asserts_is_boy(all_faces)

            self._asserts_is_boy(all_faces)

    def _solve(self, holder: FacesTrackerHolder) -> None:
        """
        Main solving algorithm - uses provided face trackers to solve all centers.

        FACE TRACKERS (provided by holder):
        ===================================
        - Odd cubes: Face color = fixed center piece color (simple)
        - Even cubes: Face color determined by majority color counting

        The holder is created by the caller at solve-time (not at construction),
        ensuring the cube state is correct when trackers are initialized.

        PERFORMANCE NOTE:
        =================
        Because the holder is created at solve-time rather than during face-by-face
        solving, even cube trackers use majority color counting on the initial state.
        This may be slightly less accurate than tracking colors as faces are solved,
        but simplifies the code and ownership model significantly.
        """
        faces: list[FaceTracker] = list(holder)

        self._asserts_is_boy(faces)

        # Phase 1: Exhaust all cheap full-slice swaps globally before commutators.
        # Iterates by color (stable) not face (unstable). Only brings to front
        # when a swap actually exists, avoiding unnecessary cube rotations.
        self._do_slice_swaps_phase(holder, faces)

        # Phase 2: Full solve — slices + commutator blocks
        while True:
            if not self._do_faces(holder, faces):
                break
            self._asserts_is_boy(faces)

        self._asserts_is_boy(faces)

        assert self._is_solved()

    def _do_slice_swaps_phase(self, holder: FacesTrackerHolder, faces: list[FaceTracker]) -> None:
        """Phase 1: Exhaust all full-slice swaps globally before commutators.

        Iterates by color (stable) instead of face (unstable after rotations).
        For each unsolved target face, finds the best swap across ALL source
        faces, brings to front only when work exists, and repeats.
        """
        if not self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            return

        while True:
            any_work: bool = False

            for target_tracker in faces:
                target_color: Color = target_tracker.color
                target_face: Face = target_tracker.face

                if self._is_face_solved(target_face, target_color):
                    continue

                # Dry-run: find best swap across all source faces (no cube rotation)
                if not self._find_best_slice_swap(target_face, target_color,
                                                  faces,
                                                  find_any=True):
                    continue

                # Work exists — bring to front and execute
                self.cmn.bring_face_front(target_face)
                # After rotation, re-resolve faces from trackers
                target_face = target_tracker.face

                with self.ann.annotate(h2=lambda: f"{target_color.long} face"):
                    if self._do_complete_slices(holder, target_color,
                                                target_face, faces):
                        any_work = True

                self._asserts_is_boy(faces)

            if not any_work:
                return

    def _find_best_slice_swap(
        self,
        target_face: Face, target_color: Color,
        faces: Iterable[FaceTracker],
        find_any: bool = False,
    ) -> tuple[Face, Color, Block, Block, int] | None:
        """Find the best slice swap across all source faces.

        Searches all source faces × all target slices × 4 rotations for the
        swap with the highest grade.

        Args:
            target_face: Face where content should arrive
            target_color: Target color for that face
            faces: All face trackers (target face is excluded automatically)
            find_any: If True, return first swap with grade > 1 (fast check)

        Returns:
            (source_face, source_color, target_block, source_block, grade)
            or None if no swap with grade > 1 exists.
        """
        nn: int = self.cube.n_slices
        all_slices: list[Block] = self._generate_all_slice_blocks(nn)

        best_grade: int = 1
        best: tuple[Face, Color, Block, Block, int] | None = None

        for source_tracker in faces:
            if source_tracker.face is target_face:
                continue
            source_face = source_tracker.face
            source_color = source_tracker.color

            if self.count_color_on_face(source_face, target_color) == 0:
                continue

            for ts in all_slices:
                combos = self._bsh.get_all_combinations(
                    source_face, target_face, ts,
                    undo_target_setup=self._preserve_cage,
                    undo_source_setup=self._preserve_cage,
                )
                if not combos:
                    continue
                natural: Block = combos[0].natural_source.main
                for rot in range(4):
                    ss: Block = natural.rotate_clockwise(nn, (-rot) % 4)
                    grade: int = self._compute_swap_grade(
                        target_face, ts, target_color,
                        source_face, ss, source_color,
                    )
                    if grade > best_grade:
                        best_grade = grade
                        best = (source_face, source_color, ts, ss, grade)
                        if find_any:
                            return best

        return best

    def _do_faces(self, tracker_holder: "FacesTrackerHolder", faces: Sequence[FaceTracker]) -> bool:
        self._logger.log_lazy(CubeLogger.cube_level(3), "_do_faces:", *faces)
        work_done = False
        for f in faces:
            # we must trace faces, because they are moved by algorith
            # we need to locate the face by original_color, b ut on odd cube, the color is of the center
            if self._do_center(tracker_holder, f, faces):
                work_done = True
                self._asserts_is_boy(tracker_holder)
            # if NxNCenters.work_on_b or not work_done:
            #     break

        return work_done

    # def _print_faces(self):
    #
    #     for f in self._faces:
    #         print(f.face, f.color, " ", end="")
    #     print()

    # noinspection PyUnreachableCode,PyUnusedLocal
    def _asserts_is_boy(self, faces: Iterable[FaceTracker]) -> None:

        CubeLayout.sanity_cost_assert_matches_scheme(self.cube,
                                                     lambda: {f.face.name: f.color for f in faces})

    def _do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker,
                   faces: Iterable[FaceTracker]) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"Face is already done {face_loc.face}")
            return False

        color = face_loc.color

        sources: Set[Face] = OrderedSet(self.cube.faces) - {face_loc.face}

        if all(not self._has_color_on_face(f, color) for f in sources):
            self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"For face {face_loc.face}, No color {color} available on  {sources}")
            return False

        self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"Need to work on {face_loc.face}")

        work_done = self.__do_center(tracker_holder, face_loc, faces)

        self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"After working on {face_loc.face} {work_done=}, "
                           f"solved={self._is_face_solved(face_loc.face, face_loc.color)}")

        return work_done

    def __do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker,
                    faces: Iterable[FaceTracker]) -> bool:
        """
        Process one face - bring correct colored pieces from ALL source faces.

        Iterates all source faces directly — no B[1:n] rotations needed.
        CommutatorHelper supports all 30 face pairs. BACK is not special.

        For each source: complete slices + blocks + 1x1 commutators.
        Skip sources with no matching colors (zero-cost).

        :return: if any work was done
        """
        face: Face = face_loc.face
        color: Color = face_loc.color

        if self._is_face_solved(face, color):
            self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"Face is already done {face}")
            return False

        cmn = self.cmn

        self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"Working on face {face}")

        with self.ann.annotate(h2=lambda: f"{face_loc.color.long} face"):
            cube = self.cube

            cmn.bring_face_front(face_loc.face)
            # from here face is no longer valid

            work_done = False

            # All source faces — BACK is not special
            source_faces: list[Face] = [*cube.front.adjusted_faces(), cube.back]

            for source_face in source_faces:
                if self.count_color_on_face(source_face, color) == 0:
                    continue  # Zero-cost skip

                if self._do_center_from_face_direct(tracker_holder, cube.front,
                                                     color,
                                                     source_face, faces):
                    work_done = True

                if self._is_face_solved(face_loc.face, color):
                    return work_done

            return work_done

    def _do_center_from_face_direct(self, tracker_holder: "FacesTrackerHolder", face: Face,
                                     color: Color,
                                     source_face: Face, faces: Iterable[FaceTracker]) -> bool:
        """
        Bring correct colored pieces from source_face to target face.

        Works with ANY source face. Does everything for that source:
        1. Complete slice swaps (all source faces — finds global best)
        2. Block commutators (all faces)
        3. 1x1 commutators fallback (all faces)

        :param face: Target face (must be front)
        :param color: Required color
        :param source_face: Source face (any face except front)
        :return: True if any work was done
        """
        cube = self.cube
        assert face is cube.front

        if self.count_color_on_face(source_face, color) == 0:
            return False  # nothing can be done here

        work_done = False
        center = face.center

        # Complete slice swaps — searches ALL source faces for global best
        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            if self._do_complete_slices(tracker_holder, color, face, faces):
                work_done = True

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS:
            if self._do_blocks(tracker_holder, color, face, source_face, faces):
                work_done = True
        else:
            # Fallback: 1x1 commutators for each center position
            for rc in self._comm_helper._2d_center_iter():
                if self._block_commutator(tracker_holder, color,
                                            face,
                                            source_face,
                                            Block.of(rc, rc),
                                            _SearchBlockMode.CompleteBlock, faces):
                    after_fixed_color = center.get_center_slice(rc).color
                    if after_fixed_color != color:
                        raise InternalSWError(f"Slice was not fixed {rc}, " +
                                              f"required={color}, " +
                                              f"actual={after_fixed_color}")
                    self._logger.log_lazy(CubeLogger.cube_level(3), lambda: f"Fixed slice {rc}")
                    work_done = True

        return work_done

    def _do_complete_slices(self, tracker_holder: "FacesTrackerHolder", color: Color,
                            face: Face, faces: Iterable[FaceTracker]) -> bool:
        """Find and execute the best complete slice swaps for a target face.

        Searches ALL source faces for the best swap, executes it, and repeats
        until no swap with grade > 1 exists.
        """
        work_done: bool = False

        while True:
            result = self._find_best_slice_swap(
                face, color, faces
            )
            if result is None:
                return work_done

            source_face, source_color, target_block, source_block, best_grade = result

            # Capture for annotation closures
            _bt, _bs = target_block, source_block
            _tf, _sf = face, source_face
            _tc, _sc = color, source_color

            def _ann_moved() -> Iterator["CenterSlice"]:
                for pt in _bs.cells:
                    cs = _sf.center.get_center_slice(pt)
                    if cs.color == _tc:
                        yield cs
                for pt in _bt.cells:
                    cs = _tf.center.get_center_slice(pt)
                    if cs.color == _sc:
                        yield cs

            def _ann_fixed() -> Iterator["CenterSlice"]:
                for pt in _bt.cells:
                    yield _tf.center.get_center_slice(pt)
                for pt in _bs.cells:
                    cs = _sf.center.get_center_slice(pt)
                    if cs.color == _sc:
                        yield cs

            with self.ann.annotate(
                    (_ann_moved, AnnWhat.Moved),
                    (_ann_fixed, AnnWhat.FixedPosition),
                    h2=lambda: f", Swap slice grade:{best_grade}",
            ):
                with tracker_holder.preserve_physical_faces():
                    self._bsh.execute_swap(
                        source_face=source_face,
                        target_face=face,
                        target_block=target_block,
                        source_block=source_block,
                        undo_target_setup=self._preserve_cage,
                        undo_source_setup=self._preserve_cage,
                    )

            self._slice_stats.get_topic(self.SLICE_SWAP_KEY).add_swap(
                grade=best_grade, nn=self.cube.n_slices,
            )
            work_done = True

    def _compute_swap_grade(
        self,
        target_face: Face, target_block: Block, target_color: Color,
        source_face: Face, source_block: Block, source_color: Color,
    ) -> int:
        """Compute the grade (net improvement) of swapping two slice blocks.

        Grade = solved_after - solved_before, where solved = pieces matching
        their face's target color.
        """
        # Before swap
        target_ok_before: int = self._count_colors_on_block(
            target_color, target_face, target_block
        )
        source_ok_before: int = self._count_colors_on_block(
            source_color, source_face, source_block
        )

        # After swap: target gets source content, source gets target content
        target_ok_after: int = self._count_colors_on_block(
            target_color, source_face, source_block
        )
        source_ok_after: int = self._count_colors_on_block(
            source_color, target_face, target_block
        )

        return (target_ok_after + source_ok_after) - (target_ok_before + source_ok_before)

    @staticmethod
    def _generate_all_slice_blocks(nn: int) -> list[Block]:
        """Generate all full-slice blocks (columns and rows).

        Returns nn columns + nn rows, skipping the middle slice on odd cubes.
        """
        blocks: list[Block] = []
        nm1: int = nn - 1
        mid: int | None = nn // 2 if nn % 2 else None

        for c in range(nn):
            if c == mid:
                continue
            blocks.append(Block(Point(0, c), Point(nm1, c)))  # column c

        for r in range(nn):
            if r == mid:
                continue
            blocks.append(Block(Point(r, 0), Point(r, nm1)))  # row r

        return blocks


    def _do_blocks(self, tracker_holder: "FacesTrackerHolder", color: Color, face: Face, source_face: Face, faces: Iterable[FaceTracker]) -> bool:
        """
        Search for unsolved blocks on target face and bring matching colors from source.

        Searches the TARGET face for blocks of wrong color (unsolved), then uses
        _block_commutator with dry_run to check if the source has matching colors
        and execute the commutator.

        Works with ANY source face (not restricted to UP/BACK).
        """
        work_done = False

        # Search for unsolved blocks on the TARGET face
        def unsolved_cell_predicate(f: Face, pt: Point) -> bool:
            """Cell is unsolved — wrong color."""
            return f.center.get_center_slice(pt).color != color

        big_blocks = self._comm_helper.search_big_block(
            face, color, cell_predicate=unsolved_cell_predicate
        )

        if not big_blocks:
            self._logger.log_lazy(CubeLogger.cube_level(2), lambda: f"  No unsolved blocks found for {color} on {face.name}")
            return False

        # Log found blocks
        large_blocks = [(b.size, b) for _, b in big_blocks if b.size > 1]
        self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"  Found {len(big_blocks)} unsolved blocks on {face.name}, "
                   f"{len(large_blocks)} larger than 1x1")

        for _, big_block in big_blocks:
            block_size = big_block.size
            block_dims = big_block.dim

            # Pass target-face coordinates directly — _block_commutator uses
            # dry_run internally to find natural source coordinates and checks
            # if source has matching colors
            if self._block_commutator(tracker_holder, color,
                                        face,
                                        source_face,
                                        big_block,
                                        _SearchBlockMode.ExactMatch, faces):
                self._logger.log_lazy(CubeLogger.cube_level(1), lambda: f"    ✓ Block {block_dims[0]}x{block_dims[1]} ({block_size} pieces) "
                           f"from {source_face.name} to {face.name}")
                work_done = True

        return work_done

    @staticmethod
    def _is_face_solved(face: Face, color: Color) -> bool:

        x = face.center.is3x3
        slice__color = face.center.get_center_slice((0, 0)).color

        return x and slice__color == color

    def _get_four_center_points(self, r: int, c: int) -> Iterator[Point]:
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise
        n_slices = self.cube.n_slices
        pt = Point(r, c)
        for rot in range(4):
            yield rotate_point_clockwise(pt, n_slices, rot)

    def _block_commutator(self,
                            tracker_holder: "FacesTrackerHolder",
                            required_color: Color,
                            face: Face, source_face: Face, target_block: Block,
                            mode: _SearchBlockMode, faces: Iterable[FaceTracker]) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        Uses CommutatorHelper dry_run to get natural source coordinates,
        then searches with 4 rotations. Supports ALL source face pairs
        (not just UP/BACK).

        Delegates to CommutatorHelper.execute_commutator() which handles:
        - The 3-cycle algorithm: [M', F, M', F', M, F, M, F']
        - Animation annotations including s2 (at-risk) marker
        - Cage preservation (preserve_state parameter)

        :param face: Target face (must be front)
        :param source_face: Source face (any face except front)
        :param target_block: Block on target face (in target face coordinates)
        :param mode: to search complete block or with colors more than mine
        :return: False if block not found (or no work need to be done)
        """
        cube: Cube = face.cube
        assert face is cube.front

        normalized_block = target_block.normalize

        # Use dry_run to get natural source coordinates — works for ALL source faces
        dry_result = self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=face,
            target_block=normalized_block,
            dry_run=True
        )
        natural_source_block = dry_result.natural_source_block

        # Search for required color on source face at natural source coordinates
        # with 4 rotations (like _LBLNxNCenters._source_block_has_color_with_rotation)
        n_rotate = self._search_block_via_dry_run(
            face, source_face, required_color, mode, normalized_block, natural_source_block
        )

        if n_rotate is None:
            return False

        # Compute actual source block by rotating natural source block by -n_rotate
        n_slices = cube.n_slices
        source_block = natural_source_block
        for _ in range((-n_rotate) % 4):
            source_block = source_block.rotate_clockwise(n_slices)

        # Use CommutatorHelper to execute the commutator
        # This handles the algorithm, annotations (including s2), and cage preservation
        self._asserts_is_boy(tracker_holder)
        with tracker_holder.preserve_physical_faces():
            self._comm_helper.execute_commutator(
                source_face=source_face,
                target_face=face,
                target_block=normalized_block,
                source_block=source_block,
                preserve_state=self._preserve_cage,
                dry_run=False,
                _cached_secret=dry_result
            )
        self._asserts_is_boy(tracker_holder)

        return True

    @staticmethod
    def count_missing(face: Face, color: Color) -> int:
        n = 0

        for s in face.center.all_slices:
            if s.color != color:
                n += 1
        return n

    def count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)

    @staticmethod
    def _has_color_on_face(face: Face, color: Color) -> int:
        for s in face.center.all_slices:
            if s.color == color:
                return True
        return False

    @staticmethod
    def _count_colors_on_block(color: Color, source_face: Face, block: Block) -> int:
        """Count number of centerpieces on block that match color.

        Block coordinates must be in source_face's coordinate space.

        :param color: Color to match
        :param source_face: Face to check
        :param block: Block defining the region (in source face coordinates)
        :return: Number of matching center pieces
        """
        _count = 0
        for pt in block.cells:
            if source_face.center.get_center_slice(pt).color == color:
                _count += 1
        return _count

    def _is_block(self,
                  source_face: Face,
                  required_color: Color,
                  min_points: int | None,
                  block: Block) -> bool:
        """
        Check if block on source face has at least min_points matching required_color.

        Block coordinates are in source face space (no coordinate conversion needed).

        :param source_face: Face to check
        :param required_color: Color to match
        :param min_points: Minimum matching points (None = all must match)
        :param block: Block to check (coordinates in source face space)
        :return: True if enough points match
        """
        _max = block.size

        if min_points is None:
            min_points = _max

        max_allowed_not_match = _max - min_points

        center = source_face.center
        miss_count = 0

        for pt in block.cells:
            if center.get_center_slice(pt).color != required_color:
                miss_count += 1
                if miss_count > max_allowed_not_match:
                    return False

        return True

    def _search_block_via_dry_run(self,
                                  target_face: Face,
                                  source_face: Face,
                                  required_color: Color,
                                  mode: _SearchBlockMode,
                                  target_block: Block,
                                  natural_source_block: Block) -> int | None:
        """
        Search for required color on source face using natural source coordinates from dry_run.

        Uses CommutatorHelper's natural source block instead of manual _point_on_source mapping.
        Searches with 4 rotations of the natural source block on the source face.

        :param target_face: Target face
        :param source_face: Source face (any face — not restricted to UP/BACK)
        :param required_color: Color to search for
        :param mode: Search mode (CompleteBlock, BigThanSource, ExactMatch)
        :param target_block: Block on target face
        :param natural_source_block: Natural source block from dry_run
        :return: Number of clockwise rotations to apply to source face to align, or None
        """
        n_ok = self._count_colors_on_block(required_color, target_face, target_block)

        if n_ok == target_block.size:
            return None  # nothing to do

        if mode == _SearchBlockMode.CompleteBlock:
            min_required = target_block.size
        elif mode == _SearchBlockMode.BigThanSource:
            min_required = n_ok + 1
        elif mode == _SearchBlockMode.ExactMatch:
            if n_ok:
                return None
            min_required = target_block.size
        else:
            raise InternalSWError

        n_slices = self.cube.n_slices
        rotated_block = natural_source_block

        for n in range(4):
            # Check directly on source face — block coords are already in source face space
            if self._is_block(source_face, required_color, min_required, rotated_block):
                return (-n) % 4
            rotated_block = rotated_block.rotate_clockwise(n_slices)

        return None

    def reset_block_statistics(self) -> None:
        """Reset block solving statistics."""
        self._comm_helper.reset_block_statistics()
        self._slice_stats.reset()
        self._slice_stats.get_topic(self.SLICE_SWAP_KEY)  # register

    def get_block_statistics(self) -> SolverStatistics:
        """Get accumulated block solving statistics (commutators + slice swaps)."""
        stats: SolverStatistics = SolverStatistics()
        stats.accumulate(self._comm_helper.get_block_statistics())
        stats.accumulate(self._slice_stats)
        return stats

    D_LEVEL = 3
