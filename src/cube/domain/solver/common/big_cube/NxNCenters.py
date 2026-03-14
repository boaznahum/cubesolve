from collections.abc import Iterable, Iterator, Sequence, Set
from contextlib import AbstractContextManager, nullcontext
from enum import Enum, unique
from typing import Tuple

from cube.domain.exceptions import InternalSWError
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
        self._logger.set_level(NxNCenters.D_LEVEL)

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

        with self.ann.annotate(h1=f"Centers for {target_tracker.color.name}"):
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

        #self._faces = faces

        self._asserts_is_boy(faces)

        #    self._trackers._debug_print_track_slices("After creating all faces")

            # now each face has at least one color, so

        while True:
            if not self._do_faces(holder, faces):
                break
            self._asserts_is_boy(faces)

        self._asserts_is_boy(faces)

        assert self._is_solved()

    def _do_faces(self, tracker_holder: "FacesTrackerHolder", faces: Sequence[FaceTracker]) -> bool:
        # while True:
        self.debug( "_do_faces:", *faces, level=3)
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

    def _do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker, faces: Iterable[FaceTracker]) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug( f"Face is already done {face_loc.face}", level=1)
            return False

        color = face_loc.color

        sources: Set[Face] = OrderedSet(self.cube.faces) - {face_loc.face}

        if all(not self._has_color_on_face(f, color) for f in sources):
            self.debug( f"For face {face_loc.face}, No color {color} available on  {sources}", level=1)
            return False

        self.debug( f"Need to work on {face_loc.face}", level=1)

        work_done = self.__do_center(tracker_holder, face_loc, faces)

        self.debug( f"After working on {face_loc.face} {work_done=}, "
                           f"solved={self._is_face_solved(face_loc.face, face_loc.color)}", level=1)

        return work_done

    def __do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker, faces: Iterable[FaceTracker]) -> bool:
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
            self.debug(f"Face is already done {face}", level=1)
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}", level=1)

        with self.ann.annotate(h2=f"{face_loc.color.long} face"):
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
        1. Complete slice swaps (UP/DOWN/BACK — M-axis faces)
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

        # Complete slice swaps — BlockBySliceSwapHelper supports ALL face pairs
        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            if self._do_complete_slices(tracker_holder, color, face, source_face):
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
                                            rc, rc,
                                            _SearchBlockMode.CompleteBlock, faces):
                    after_fixed_color = center.get_center_slice(rc).color
                    if after_fixed_color != color:
                        raise InternalSWError(f"Slice was not fixed {rc}, " +
                                              f"required={color}, " +
                                              f"actual={after_fixed_color}")
                    self.debug(f"Fixed slice {rc}", level=3)
                    work_done = True

        return work_done

    def _do_complete_slices(self, tracker_holder: "FacesTrackerHolder", color: Color,
                            face: Face, source_face: Face) -> bool:
        """Find and execute the best complete slice swaps between target and source faces.

        For each target slice block, uses BSH dry_run to find the natural source,
        then grades all 4 rotations of the source face to find the best content.
        Picks the globally best swap, executes it, and repeats until no swap
        with grade > 1 exists.
        """
        nn: int = self.cube.n_slices

        # Get source face's target color
        source_color: Color = self._get_face_color(tracker_holder, source_face)

        # Generate all full-slice blocks (skip middle on odd cubes)
        all_slices: list[Block] = self._generate_all_slice_blocks(nn)

        # Precompute natural source for each target slice (geometry doesn't change)
        target_natural_pairs: list[tuple[Block, Block]] = []
        for ts in all_slices:
            combos = self._bsh.get_all_combinations(
                source_face, face, ts,
                undo_target_setup=self._preserve_cage,
                undo_source_setup=self._preserve_cage,
            )
            if combos:
                natural: Block = combos[0].natural_source.main
                target_natural_pairs.append((ts, natural))

        work_done: bool = False
        max_iterations: int = nn * nn
        iterations: int = 0

        while True:
            # Find the best swap across all target slices × 4 source rotations
            best_grade: int = 1  # minimum threshold (ignore grade <= 1)
            best_target: Block | None = None
            best_source: Block | None = None

            for ts, natural in target_natural_pairs:
                for rot in range(4):
                    ss: Block = natural.rotate_clockwise(nn, (-rot) % 4)
                    grade: int = self._compute_swap_grade(
                        face, ts, color,
                        source_face, ss, source_color,
                    )
                    if grade > best_grade:
                        best_grade = grade
                        best_target = ts
                        best_source = ss

            if best_target is None:
                return work_done

            # Execute the best swap
            with self.ann.annotate(h2=", Swap complete slice"):
                with tracker_holder.preserve_physical_faces():
                    self._bsh.execute_swap(
                        source_face=source_face,
                        target_face=face,
                        target_block=best_target,
                        source_block=best_source,
                        undo_target_setup=self._preserve_cage,
                        undo_source_setup=self._preserve_cage,
                    )

            # Track slice swap statistics
            self._slice_stats.get_topic(self.SLICE_SWAP_KEY).add_swap(
                grade=best_grade, nn=nn,
            )

            work_done = True
            iterations += 1
            assert iterations <= max_iterations, (
                f"Bug: too many slice swap iterations ({iterations}) for nn={nn}"
            )

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
            target_color, target_face, target_block.start, target_block.end, ignore_if_back=True
        )
        source_ok_before: int = self._count_colors_on_block(
            source_color, source_face, source_block.start, source_block.end, ignore_if_back=True
        )

        # After swap: target gets source content, source gets target content
        target_ok_after: int = self._count_colors_on_block(
            target_color, source_face, source_block.start, source_block.end, ignore_if_back=True
        )
        source_ok_after: int = self._count_colors_on_block(
            source_color, target_face, target_block.start, target_block.end, ignore_if_back=True
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

    @staticmethod
    def _get_face_color(tracker_holder: "FacesTrackerHolder", face: Face) -> Color:
        """Get the target color for a face from the tracker holder."""
        for ft in tracker_holder:
            if ft.face is face:
                return ft.color
        raise InternalSWError(f"No tracker for face {face.name}")

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
            self.debug(f"  No unsolved blocks found for {color} on {face.name}", level=2)
            return False

        # Log found blocks
        large_blocks = [(b.size, b) for _, b in big_blocks if b.size > 1]
        self.debug(f"  Found {len(big_blocks)} unsolved blocks on {face.name}, "
                   f"{len(large_blocks)} larger than 1x1", level=1)

        for _, big_block in big_blocks:
            block_size = big_block.size
            block_dims = big_block.dim

            # Pass target-face coordinates directly — _block_commutator uses
            # dry_run internally to find natural source coordinates and checks
            # if source has matching colors
            if self._block_commutator(tracker_holder, color,
                                        face,
                                        source_face,
                                        big_block[0], big_block[1],
                                        _SearchBlockMode.ExactMatch, faces):
                self.debug(f"    ✓ Block {block_dims[0]}x{block_dims[1]} ({block_size} pieces) "
                           f"from {source_face.name} to {face.name}", level=1)
                work_done = True

        return work_done

    @staticmethod
    def _is_face_solved(face: Face, color: Color) -> bool:

        x = face.center.is3x3
        slice__color = face.center.get_center_slice((0, 0)).color

        return x and slice__color == color

    def _get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        inv = self.cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def _block_commutator(self,
                            tracker_holder: "FacesTrackerHolder",
                            required_color: Color,
                            face: Face, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
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
        :param rc1: one corner of block, center slices indexes [0..n)
        :param rc2: other corner of block, center slices indexes [0..n)
        :param mode: to search complete block or with colors more than mine
        :return: False if block not found (or no work need to be done)
        """
        cube: Cube = face.cube
        assert face is cube.front

        # fix: use block methods, simplify

        # normalize block
        r1: int = rc1[0]
        c1: int = rc1[1]

        r2: int = rc2[0]
        c2: int = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        rc1 = Point(r1, c1)
        rc2 = Point(r2, c2)
        normalized_block = Block(rc1, rc2)

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
    def _count_colors_on_block(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                               ignore_if_back=False) -> int:

        """
        Count number of centerpieces on center that match color
        :param source_face: front up or back
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        cube = source_face.cube
        fix_back_coords = not ignore_if_back and source_face is cube.back

        if fix_back_coords:
            # Fix:
            # claude: we can fix it !!!, itis easy !!!
            # lets understand all the callers and why it works today !!!

            # the logic here is hard code of the logic in slice rotate
            # it will be broken if cube layout is changed
            # here we assume we work on F, and UP has same coord system as F, and
            # back is mirrored in both direction
            # claude: but now we know using geometry classes to translate
            inv = cube.inv
            rc1 = (inv(rc1[0]), inv(rc1[1]))
            rc2 = (inv(rc2[0]), inv(rc2[1]))

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1

        if c1 > c2:
            c1, c2 = c2, c1

        _count = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                center_slice = source_face.center.get_center_slice((r, c))
                if color == center_slice.color:
                    _count += 1

        return _count

    @staticmethod
    def _2d_range(rc1: Point, rc2: Point) -> Iterator[Point]:

        """
        Iterator over 2d block columns advanced faster
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1

        if c1 > c2:
            c1, c2 = c2, c1

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield Point(r, c)

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

        for rc in self._2d_range(block.start, block.end):
            if center.get_center_slice(rc).color != required_color:
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
        n_ok = self._count_colors_on_block(required_color, target_face, target_block.start, target_block.end)

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
