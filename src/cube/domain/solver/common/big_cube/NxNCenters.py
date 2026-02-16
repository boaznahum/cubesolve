from collections.abc import Iterable, Iterator, Sequence, Set
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from enum import Enum, unique
from typing import Tuple

from cube.domain import algs
from cube.domain.algs import Algs, SeqAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.block import Block
from cube.domain.geometric.cube_boy import color2long
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.geometric.geometry_types import Point
from cube.domain.model import CenterSlice, Color, FaceName
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.CenterBlockStatistics import CenterBlockStatistics
from cube.domain.solver.common.SolverHelper import SolverHelper
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


@dataclass
class _CompleteSlice:
    is_row: bool
    index: int  # of row/column
    n_matches: int  # number of pieces match color


class NxNCenters(SolverHelper):
    """
    Solves center pieces on NxN cubes (N > 3).

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
                      * _OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS

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
            # _swap_entire_face_odd_cube also uses moves that break the cage.
            self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False
            self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False
        else:
            self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = cfg.optimize_big_cube_centers_search_complete_slices
            self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = cfg.optimize_odd_cube_centers_switch_centers

        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO = cfg.optimize_big_cube_centers_search_complete_slices_only_target_zero
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = cfg.optimize_big_cube_centers_search_blocks

        # Use CommutatorHelper for block search operations
        self._comm_helper = CommutatorHelper(slv)

    def _is_solved(self):
        return all((f.center.is3x3 for f in self.cube.faces)) and self.cube.is_boy

    @staticmethod
    def is_cube_solved(cube: Cube):
        return all((f.center.is3x3 for f in cube.faces)) and cube.is_boy

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and it is a boy
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
                if not self._do_faces(holder, [target_tracker], False, False):
                    break
                self._asserts_is_boy(all_faces)

            self._asserts_is_boy(all_faces)

            # Final pass with back face too
            self._do_faces(holder, [target_tracker], False, True)

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

        # SPECIAL_CASE_1
        # A rare case here, when use_back_too is false and complete slice is enabled
        # We have two slices, that have no source other on of the other and on back(but back is not is used)
        # These sources are on the same slice S
        # Face RED finds two colors on S
        # Face Orange finds two colors S
        # what happens is that RED takes slice from ORANGE
        # then ORANGE take from RED, infinite loop
        # It is very rare:
        #   there should be empty target slice in the target face (see config)
        #   this slice is swapped, and not filled by other step(becuase it's sources are on back)
        # To overcome it we swap only if number sources is > n//2
        while True:
            if not self._do_faces(holder, faces, False, False):
                break
            self._asserts_is_boy(faces)

        self._asserts_is_boy(faces)

        self._do_faces(holder, faces, False, True)

        self._asserts_is_boy(faces)

        assert self._is_solved()

    def _do_faces(self, tracker_holder: "FacesTrackerHolder", faces: Sequence[FaceTracker], minimal_bring_one_color, use_back_too: bool) -> bool:
        # while True:
        self.debug( "_do_faces:", *faces, level=3)
        work_done = False
        for f in faces:
            # we must trace faces, because they are moved by algorith
            # we need to locate the face by original_color, b ut on odd cube, the color is of the center
            if self._do_center(tracker_holder, f, minimal_bring_one_color, use_back_too, faces):
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
    def _asserts_is_boy(self, faces: Iterable[FaceTracker]):

        CubeLayout.sanity_cost_assert_match_cube_layout(self.cube,
                                                        lambda: {f.face.name: f.color for f in faces} )

    def _do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker, minimal_bring_one_color, use_back_too: bool, faces: Iterable[FaceTracker]) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug( f"Face is already done {face_loc.face}", level=1)
            return False

        color = face_loc.color

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug( f"{face_loc.face} already has at least one {color}", level=3)
            return False

        sources:Set[Face] = OrderedSet(self.cube.faces) - {face_loc.face}
        if not use_back_too:
            sources -= {face_loc.face.opposite}

        if all(not self._has_color_on_face(f, color) for f in sources):
            self.debug( f"For face {face_loc.face}, No color {color} available on  {sources}", level=1)
            return False

        self.debug( f"Need to work on {face_loc.face}", level=1)

        work_done = self.__do_center(tracker_holder, face_loc, minimal_bring_one_color, use_back_too, faces)

        self.debug( f"After working on {face_loc.face} {work_done=}, "
                           f"solved={self._is_face_solved(face_loc.face, face_loc.color)}", level=1)

        return work_done

    def __do_center(self, tracker_holder: "FacesTrackerHolder", face_loc: FaceTracker, minimal_bring_one_color: bool, use_back_too: bool, faces: Iterable[FaceTracker]) -> bool:
        """
        Process one face - bring correct colored pieces from adjacent faces.

        CAGE METHOD (preserve_cage=True):
        =================================
        Tracks all _bring_face_up_preserve_front rotations and undoes them before return.

        WHY THIS MATTERS - VISUAL EXAMPLE:
        -----------------------------------
        Initial cube orientation (looking at front):

            ┌───┐
            │ U │  <- UP face (source)
        ┌───┼───┼───┐
        │ L │ F │ R │  <- FRONT face (target), LEFT, RIGHT
        └───┼───┼───┘
            │ D │  <- DOWN face
            └───┘

        The algorithm loops through L, D, R faces, bringing each to UP:
        - Iteration 1: Process UP (already up)
        - Iteration 2: B'[1:n] -> brings LEFT to UP
        - Iteration 3: B'[1:n] -> brings DOWN to UP
        - Iteration 4: B'[1:n] -> brings RIGHT to UP (now done)

        After 3 B'[1:n] rotations, cube is rotated 270° around front axis.
        This BREAKS paired edges and moves corners.

        With preserve_cage=True: We undo these rotations before returning.
        setup_alg = B'[1:n] + B'[1:n] + B'[1:n] = B'[1:n] * 3
        undo = setup_alg.prime = B[1:n] * 3

        :return: if any work was done
        """
        face: Face = face_loc.face
        color: Color = face_loc.color

        if self._is_face_solved(face, color):
            self.debug( f"Face is already done {face}", level=1)
            return False

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug( f"{face_loc.face} already has at least one {color}", level=3)
            return False

        cmn = self.cmn

        self.debug( f"Working on face {face}", level=1)

        with self.ann.annotate(h2=f"{color2long(face_loc.color).value} face"):
            cube = self.cube

            # we loop bringing all adjusted faces up
            cmn.bring_face_front(face_loc.face)
            # from here face is no longer valid

            work_done = False

            if any(self._has_color_on_face(f, color) for f in cube.front.adjusted_faces()):
                # =========================================================
                # CAGE METHOD: Track setup rotations for undo
                # =========================================================
                setup_alg: SeqAlg = Algs.NOOP

                for _ in range(3):  # 3 faces: L, D, R brought to UP
                    # don't use face - it was moved !!!
                    if self._do_center_from_face(tracker_holder, cube.front, minimal_bring_one_color, color, cube.up, faces):
                        work_done = True
                        if minimal_bring_one_color:
                            if self._preserve_cage:
                                self.op.play(setup_alg.prime)  # UNDO before return!
                            return work_done

                    if self._is_face_solved(face_loc.face, color):
                        if self._preserve_cage:
                            self.op.play(setup_alg.prime)  # UNDO before return!
                        return work_done

                    # Rotate to bring next adjacent face to UP
                    # Track the algorithm so we can undo
                    setup_alg = setup_alg + self._bring_face_up_preserve_front(cube.left)

                # on the last face (4th iteration)
                # don't use face - it was moved !!!
                if self._do_center_from_face(tracker_holder, cube.front, minimal_bring_one_color, color, cube.up, faces):
                    work_done = True
                    if minimal_bring_one_color:
                        if self._preserve_cage:
                            self.op.play(setup_alg.prime)  # UNDO before return!
                        return work_done

                if self._is_face_solved(face_loc.face, color):
                    if self._preserve_cage:
                        self.op.play(setup_alg.prime)  # UNDO before return!
                    return work_done

                # =========================================================
                # CAGE METHOD: Undo all setup rotations
                # =========================================================
                if self._preserve_cage:
                    self.op.play(setup_alg.prime)

            if use_back_too:
                # now from back
                # don't use face - it was moved !!!
                if self._do_center_from_face(tracker_holder, cube.front, minimal_bring_one_color, color, cube.back, faces):
                    work_done = True

            return work_done

    def _do_center_from_face(self, tracker_holder: "FacesTrackerHolder", face: Face, minimal_bring_one_color, color: Color, source_face: Face, faces: Iterable[FaceTracker]) -> bool:

        """
        The sources are on source_face !!! source face is in its location up /back
        The target face is on front !!!
        :param face:
        :param color:
        :param source_face:
        :return:
        """

        cube = self.cube

        assert face is cube.front
        assert source_face in [cube.up, cube.back]

        if self.count_color_on_face(source_face, color) == 0:
            return False  # nothing can be done here

        work_done = False

        center = face.center

        n = cube.n_slices

        if n % 2 and self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS:

            ok_on_this = self.count_color_on_face(face, color)

            on_source = self.count_color_on_face(source_face, color)

            if on_source - ok_on_this > 2:  # swap two faces is about two commutators
                self._swap_entire_face_odd_cube(tracker_holder, color, face, source_face, faces)
                work_done = True

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            if self._do_complete_slices(tracker_holder, color, face, source_face):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS:
            # should move minimal_bring_one_color into _do_blocks, because ein case of back, it can do too much
            if self._do_blocks(tracker_holder, color, face, source_face, faces):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        else:

            # the above also did a 1 size block
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

                    self.debug( f"Fixed slice {rc}", level=3)

                    work_done = True
                    if minimal_bring_one_color:
                        return work_done

        if not work_done:
            self.debug( f"Internal error, no work was done on face {face} required color {color}, "
                               f"but source face  {source_face} contains {self.count_color_on_face(source_face, color)}", level=3)
            for rc in self._comm_helper._2d_center_iter():
                if center.get_center_slice(rc).color != color:
                    print(f"Missing: {rc}  {[*self._get_four_center_points(rc[0], rc[1])]}")
            for rc in self._comm_helper._2d_center_iter():
                if source_face.center.get_center_slice(rc).color == color:
                    print(f"Found on {source_face}: {rc}  {source_face.center.get_center_slice(rc)}")

            raise InternalSWError("See error in log")

        return work_done

    def _do_complete_slices(self, tracker_holder: "FacesTrackerHolder", color, face, source_face) -> bool:

        work_done = False

        # do while work is done
        while True:
            if not self._do_one_complete_slice(tracker_holder, color, face, source_face):
                return work_done

            work_done = True

    def _do_one_complete_slice(self, tracker_holder: "FacesTrackerHolder",  color, target_face: Face, source_face: Face) -> bool:

        with tracker_holder.preserve_physical_faces():
            return self._do_one_complete_slice_imp(color, target_face, source_face)

    def _do_one_complete_slice_imp(self, color, target_face: Face, source_face: Face) -> bool:

        source_slices: Sequence[_CompleteSlice] = self._search_slices_on_face(source_face, color, None, True)

        if not source_slices:
            return False

        odd_mid_slice: int | None = None
        n_slices = self.cube.n_slices
        if n_slices % 2:
            odd_mid_slice = n_slices // 2

        # cache already searched source_slices on the target face
        slices_on_target_face: dict[int, Sequence[_CompleteSlice]] = {}

        for source_slice in source_slices:

            index = source_slice.index

            if index == odd_mid_slice:
                continue  # skip this one

            # if source_slice.contains_track_slice:
            #     continue  # we can't move it happens in even cube

            target_slices = slices_on_target_face.get(index)

            if target_slices is None:
                target_slices = self._search_slices_on_face(target_face, color, index, False)
                assert len(target_slices) == 4  # we search vertical and horizontal x  index, inv(index)
                slices_on_target_face[index] = target_slices

            min_target_slice = target_slices[0]

            if (
                    (min_target_slice.n_matches == 0 or
                     not self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO) and
                      source_slice.n_matches > 0 / 2.0  # SEE SPECIAL_CASE_1 above
            ) and source_slice.n_matches > min_target_slice.n_matches:
                # ok now swap

                # before = self._count_color_on_face(face, color)

                # self._debug_print_track_slices()
                # print("before", end="")
                # self._print_faces()
                # before = [ (f.face, f.color) for f in self._faces]

                # _tf: FaceLoc = next(_f for _f in self._faces if _f.face is target_face)
                # _sf: FaceLoc = next(_f for _f in self._faces if _f.face is source_face)
                # print(f"@@@ to {color} {_tf} from {_sf} n={source_slice.n_matches}")

                with self.ann.annotate(h2=", Swap complete slice"):
                    self._swap_slice(min_target_slice, target_face, source_slice, source_face)

                    # print("after", end="")
                    # self._print_faces()
                    # _after = [ (f.face, f.color) for f in self._faces]
                    # if _before != _after:
                    #     print("xxxx")
                    #     raise InternalSWError()

                    # self._debug_print_track_slices()
                    # self._asserts_is_boy(self._faces)

                    # after = self._count_color_on_face(face, color)

                    # print(before, after, color)

                    return True

        return False

    def _swap_slice(self, target_slice: _CompleteSlice,
                    target_face: Face,
                    source_slice: _CompleteSlice, source_face: Face):
        """
        Swap a complete slice (row or column) between target and source faces.

        CAGE METHOD (preserve_cage=True):
        =================================
        Undoes setup moves (F' and source rotation) after the swap.

        WHY THIS MATTERS - VISUAL EXAMPLE:
        -----------------------------------
        To swap slices, we need them aligned as COLUMNS.
        If target is a ROW, we first play F' to rotate it to a column.

        Before F':              After F':
        ┌─┬─┬─┐                ┌─┬─┬─┐
        │ │█│ │ <- row         │ │ │ │
        ├─┼─┼─┤                ├─┼─┼─┤
        │ │█│ │                │█│█│█│ <- now column
        ├─┼─┼─┤                ├─┼─┼─┤
        │ │█│ │                │ │ │ │
        └─┴─┴─┘                └─┴─┴─┘

        The F' move BREAKS paired edges (rotates front wings).
        With preserve_cage=True: We undo F' after the swap.

        Similarly, source rotation (U * n_rotate) aligns source with target.
        This also needs to be undone for cage method.
        """
        cube = self.cube
        n_slices = cube.n_slices

        target_index: int

        # Track if we did F' setup (for cage undo)
        did_f_prime_setup = False

        # slice must be vertical
        op = self.op
        if target_slice.is_row:
            target_slice_block_1 = cube.cqr.rotate_point_counterclockwise((target_slice.index, 0))
            target_index = target_slice_block_1[1]
            op.play(Algs.F.prime)
            did_f_prime_setup = True  # Track for cage undo
        else:
            # column
            target_index = target_slice.index

        # now we must bring source slice into position (0,  target_index^)

        nm1 = cube.n_slices - 1
        source_index = source_slice.index
        if source_slice.is_row:
            s1 = Point(source_index, 0)
            s2 = Point(source_index, nm1)
        else:
            s1 = Point(0, source_index)
            s2 = Point(nm1, source_index)

        # now we need to bring source slice such that one of its endpoints is (0,  target_index^)
        required_on_target = Point(0, cube.inv(target_index))

        def is_column(p1: Point, p2: Point):

            return (p1[0] == 0 and p2[0] == n_slices - 1) or (p2[0] == 0 and p1[0] == n_slices - 1)

        source_is_back = source_face is cube.back
        n_rotate: int | None = None
        for i in range(4):

            if is_column(s1, s2):
                s1_on_target = self._point_on_target(source_is_back, s1)
                s2_on_target = self._point_on_target(source_is_back, s2)

                if s1_on_target == required_on_target or s2_on_target == required_on_target:
                    n_rotate = i
                    break

            s1 = Point(*cube.cqr.rotate_point_clockwise(s1))
            s2 = Point(*cube.cqr.rotate_point_clockwise(s2))

        assert n_rotate is not None

        # now rotate source face accordingly:
        rotate_source_alg = Algs.of_face(source_face.name)
        op.play(rotate_source_alg * n_rotate)

        mul = 2 if source_is_back else 1
        # do the swap:
        slice_source_alg: algs.Alg = self._get_slice_m_alg(target_index, target_index)

        def ann_source() -> Iterator[CenterSlice]:
            for rc in self._2d_range(s1, s2):
                yield source_face.center.get_center_slice(rc)

        def ann_target() -> Iterator[CenterSlice]:

            for rc in self._2d_range(Point(0, target_index), Point(nm1, target_index)):
                yield target_face.center.get_center_slice(rc)

        with self.ann.annotate((ann_source(), AnnWhat.Moved), (ann_target(), AnnWhat.FixedPosition)):
            op.play(slice_source_alg * mul +
                  rotate_source_alg * 2 +  # this replaces source slice with target
                  slice_source_alg.prime * mul
                  )

        # =========================================================
        # CAGE METHOD: Undo setup moves to preserve paired edges
        # =========================================================
        if self._preserve_cage:
            if n_rotate:
                self.debug( f"  [CAGE] Undoing source rotation: {rotate_source_alg.prime * n_rotate}", level=1)
                op.play(rotate_source_alg.prime * n_rotate)

            if did_f_prime_setup:
                self.debug( "  [CAGE] Undoing F' setup: F", level=1)
                op.play(Algs.F)

    def _do_blocks(self, tracker_holder: "FacesTrackerHolder", color, face, source_face, faces: Iterable[FaceTracker]):

        work_done = False

        cube = self.cube

        big_blocks = self._comm_helper.search_big_block(source_face, color)

        if not big_blocks:
            self.debug(f"  No blocks found for {color} on {source_face.name}", level=2)
            return False

        # Log found blocks
        block_sizes = [(b.size, b) for _, b in big_blocks]
        large_blocks = [(s, b) for s, b in block_sizes if s > 1]
        self.debug(f"  Found {len(big_blocks)} blocks on {source_face.name}, "
                   f"{len(large_blocks)} larger than 1x1", level=1)

        # because we do exact match, there is no risk that that new blocks will be constructed,
        # so we try all

        for _, big_block in big_blocks:
            rc1 = big_block[0]
            rc2 = big_block[1]
            block_size = big_block.size
            block_dims = big_block.dim

            rc1_on_target = self._point_on_source(source_face is cube.back, rc1)
            rc2_on_target = self._point_on_source(source_face is cube.back, rc2)

            for rotation in range(4):
                if self._block_commutator(tracker_holder, color,
                                            face,
                                            source_face,
                                            rc1_on_target, rc2_on_target,
                                            # actually we want big-than, but for this we need to find best match
                                            # it still doesn't work, we need another mode, Source and Target Match
                                            # but for this we need to search source only
                                            _SearchBlockMode.ExactMatch, faces):
                    # Log successful block commutator
                    self.debug(f"    ✓ Block {block_dims[0]}x{block_dims[1]} ({block_size} pieces) "
                               f"from {source_face.name}{rc1}->{rc2} to {face.name} "
                               f"(rotation={rotation})", level=1)
                    work_done = True
                    break

                rc1_on_target = cube.cqr.rotate_point_clockwise(rc1_on_target)
                rc2_on_target = cube.cqr.rotate_point_clockwise(rc2_on_target)

        return work_done

    @staticmethod
    def _is_face_solved(face: Face, color: Color) -> bool:

        x = face.center.is3x3
        slice__color = face.center.get_center_slice((0, 0)).color

        return x and slice__color == color

    def _bring_face_up_preserve_front(self, face) -> algs.Alg:
        """
        Bring an adjacent face to the UP position while preserving front.

        Returns the algorithm played so caller can undo with alg.prime if needed.
        For cage method: __do_center tracks these and undoes them at the end.

        Args:
            face: The face to bring to UP position (must be L, D, or R)

        Returns:
            The algorithm that was played (Algs.NOOP if face was already UP)
        """
        if face.name == FaceName.U:
            return Algs.NOOP  # Already UP, no rotation needed

        if face.name == FaceName.B or face.name == FaceName.F:
            raise InternalSWError(f"{face.name} is not supported, can't bring them to up preserving front")

        self.debug( f"Need to bring {face} to up", level=3)

        # rotate back with all slices clockwise
        rotate = Algs.B[1:self.cube.n_slices + 1]

        alg_to_play: algs.Alg
        match face.name:

            case FaceName.L:
                alg_to_play = rotate.prime

            case FaceName.D:
                alg_to_play = rotate.prime * 2

            case FaceName.R:
                alg_to_play = rotate

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

        self.op.play(alg_to_play)
        return alg_to_play

    def _get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        inv = self.cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def _swap_entire_face_odd_cube(self, tracker_holder: "FacesTrackerHolder", required_color: Color, face: Face, source: Face, faces: Iterable[FaceTracker]):

        cube = self.cube
        nn = cube.n_slices

        assert nn % 2, "Cube must be odd"

        assert face is cube.front
        assert source is cube.up or source is cube.back

        op = self.op

        mid = nn // 2
        mid_pls_1 = 1 + nn // 2  # == 3 on 5

        end = nn

        rotate_mul = 1
        if source is cube.back:
            rotate_mul = 2

        # TODO [#12]: MM algorithm broken - needs fix before odd cube face swap can work
        raise InternalSWError("Need to fix MM")

        swap_faces = [Algs.MM()[1:mid_pls_1 - 1].prime * rotate_mul, Algs.F.prime * 2,
                      Algs.MM()[1:mid_pls_1 - 1] * rotate_mul,
                      Algs.MM()[mid_pls_1 + 1:end].prime * rotate_mul,
                      Algs.F * 2 + Algs.MM()[mid_pls_1 + 1:end] * rotate_mul
                      ]
        op.op(Algs.seq_alg(None, *swap_faces))

        # commutator 1, upper block about center
        self._block_commutator(tracker_holder, required_color, face, source,
                                 (mid + 1, mid), (nn - 1, mid),
                                 _SearchBlockMode.BigThanSource, faces)

        # commutator 2, lower block below center
        self._block_commutator(tracker_holder, required_color, face, source,
                                 (0, mid), (mid - 1, mid),
                                 _SearchBlockMode.BigThanSource, faces)

        # commutator 3, left to center
        self._block_commutator(tracker_holder, required_color, face, source,
                                 (mid, 0), (mid, mid - 1),
                                 _SearchBlockMode.BigThanSource, faces)

        # commutator 4, right ot center
        self._block_commutator(tracker_holder, required_color, face, source,
                                 (mid, mid + 1), (mid, nn - 1),
                                 _SearchBlockMode.BigThanSource, faces)

    def _block_commutator(self,
                            tracker_holder: "FacesTrackerHolder",
                            required_color: Color,
                            face: Face, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                            mode: _SearchBlockMode, faces: Iterable[FaceTracker]) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        Delegates to CommutatorHelper.execute_commutator() which handles:
        - The 3-cycle algorithm: [M', F, M', F', M, F, M, F']
        - Animation annotations including s2 (at-risk) marker
        - Cage preservation (preserve_state parameter)

        :param face: Target face (must be front)
        :param source_face: Source face (must be up or back)
        :param rc1: one corner of block, center slices indexes [0..n)
        :param rc2: other corner of block, center slices indexes [0..n)
        :param mode: to search complete block or with colors more than mine
        :return: False if block not found (or no work need to be done)
        """
        cube: Cube = face.cube
        assert face is cube.front
        assert source_face is cube.up or source_face is cube.back

        is_back = source_face is cube.back

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

        # in case of odd and (mid, mid), search will fail, nothing to do
        # if we change the order, then block validation below will fail,
        # so we need to check for case odd (mid, mid) somewhere else
        # now search block
        n_rotate = self._search_block(face, source_face, required_color, mode, normalized_block)

        if n_rotate is None:
            return False

        # Compute source block: rotate the target block position by -n_rotate
        # to find where the source block is BEFORE the source face setup rotation
        cqr = cube.cqr
        _on_src1_1 = self._point_on_source(is_back, rc1)
        _on_src1_2 = self._point_on_source(is_back, rc2)
        # Apply inverse rotation to get original source position
        source_rc1 = Point(*cqr.rotate_point_clockwise(_on_src1_1, -n_rotate))
        source_rc2 = Point(*cqr.rotate_point_clockwise(_on_src1_2, -n_rotate))

        # Use CommutatorHelper to execute the commutator
        # This handles the algorithm, annotations (including s2), and cage preservation
        self._asserts_is_boy(tracker_holder)
        with tracker_holder.preserve_physical_faces():
            self._execute_commutator(source_face, face, rc1, rc2, source_rc1, source_rc2)
        self._asserts_is_boy(tracker_holder)

        return True

    def _preserve_trackers(self) -> AbstractContextManager[object]:
        """Return context manager that preserves tracker markers, or no-op.

        When tracker_holder is set (even cubes), returns
        preserve_physical_faces() to restore MarkedFaceTracker markers
        after commutators move center pieces between faces.
        Otherwise returns nullcontext() (no-op).
        """
        th = self._tracker_holder
        if th is not None:
            return th.preserve_physical_faces()
        return nullcontext()

    def _execute_commutator(self, source_face: Face, target_face: Face,
                            rc1: Point, rc2: Point,
                            source_rc1: Point, source_rc2: Point) -> None:
        """Execute a commutator, wrapping with preserve_physical_faces if needed."""
        with self._preserve_trackers():
            self._comm_helper.execute_commutator(
                source_face=source_face,
                target_face=target_face,
                target_block=Block(rc1, rc2),
                source_block=Block(source_rc1, source_rc2),
                preserve_state=self._preserve_cage,
                dry_run=False
            )

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

    def _search_slices_on_face(self, face, color, index: int | None, search_max: bool) -> list[_CompleteSlice]:

        """

        :param face:
        :param color:
        :param index: if not None then return only (index, 0) (index^, 0), (0, index), (0, index^)
        :param search_max:
        :return:
        """

        cube = self.cube
        inv = cube.inv
        n_slices = cube.n_slices
        nm1 = n_slices - 1

        rows: Iterable[int]
        columns: Iterable[int]
        if index is not None:
            rows = [index, inv(index)]
            columns = [index, inv(index)]
        else:
            rows = range(n_slices)
            columns = rows

        _slices = []
        for r in rows:

            n = self._count_colors_on_block(color, face, (r, 0), (r, nm1), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by commutator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(True, r, n)
                _slices.append(_slice)

        for c in columns:

            n = self._count_colors_on_block(color, face, (0, c), (nm1, c), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by commutator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(False, c, n)
                _slices.append(_slice)

        _slices = sorted(_slices, key=lambda s: s.n_matches, reverse=search_max)

        return _slices

    def _point_on_source(self, is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if is_back:
            return Point(inv(rc[0]), inv(rc[1]))
        else:
            # on up
            return Point(*rc)

    def _point_on_target(self, source_is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if source_is_back:
            return Point(inv(rc[0]), inv(rc[1]))
        else:
            # on up
            return Point(*rc)

    def _2d_range_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Iterator[Point]:

        """
        Iterator over 2d block columns advanced faster
        Convert block to source coordinates
        :param rc1: one corner of block, front coords, center slice indexes
        :param rc2: other corner of block, front coords, center slice indexes
        :return:
        """

        rc1 = self._point_on_source(is_back, rc1)
        rc2 = self._point_on_source(is_back, rc2)

        yield from self._2d_range(rc1, rc2)

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
                  block: Block,
                  dont_convert_coordinates: bool = False) -> bool:

        """

        :param source_face:
        :param required_color:
        :param min_points: If None that all block , min = block size
        :param block: Block to check
        :param dont_convert_coordinates if True then don't convert coordinates according to source face
        :return:
        """

        # Number of points in block
        _max = block.size

        if min_points is None:
            min_points = _max

        max_allowed_not_match = _max - min_points  # 0 in cas emin is max

        center = source_face.center
        miss_count = 0

        if dont_convert_coordinates:
            _range = self._2d_range(block.start, block.end)
        else:
            _range = self._2d_range_on_source(source_face is source_face.cube.back, block.start, block.end)

        for rc in _range:

            if center.get_center_slice(rc).color != required_color:

                miss_count += 1
                if miss_count > max_allowed_not_match:
                    return False

        return True

    def _search_block(self,
                      target_face: Face,
                      source_face: Face,
                      required_color: Color,
                      mode: _SearchBlockMode,
                      block: Block) -> int | None:

        """
        Search block according to mode, if target is already satisfied, then return not found
        :param source_face:
        :param required_color:
        :param mode:
        :param block: Block to search for
        :return: How many source clockwise rotate in order to match the block to source
        """

        n_ok = self._count_colors_on_block(required_color, target_face, block.start, block.end)

        if n_ok == block.size:
            return None  # nothing to do

        if mode == _SearchBlockMode.CompleteBlock:
            min_required = block.size
        elif mode == _SearchBlockMode.BigThanSource:
            # The number of commutators before > after
            # before = size - n_ok
            # after  = n_ok  - because the need somehow to get back
            # size-n_ok > n_ok
            min_required = n_ok + 1
        elif mode == _SearchBlockMode.ExactMatch:
            if n_ok:
                return None
            min_required = block.size

        else:
            raise InternalSWError

        n_slices = self.cube.n_slices
        rotated_block = block

        for n in range(4):
            if self._is_block(source_face, required_color, min_required, rotated_block):
                # we rotate n to find the block, so client need to rotate -n
                return (-n) % 4
            rotated_block = rotated_block.rotate_clockwise(n_slices)

        return None

    def _get_slice_m_alg(self, c1, c2):

        """

        :param c1: Center Slice index [0, n)
        :param c2: Center Slice index [0, n)
        :return: m slice in range suitable for [c1, c2]
        """

        #   index is from left to right, L is from left to right,
        # so we don't need to invert

        if c1 > c2:
            c1, c2 = c2, c1

        return Algs.M[c1 + 1:c2 + 1].prime

    def reset_block_statistics(self) -> None:
        """Reset block solving statistics."""
        self._comm_helper.reset_block_statistics()

    def get_block_statistics(self) -> CenterBlockStatistics:
        """Get accumulated block solving statistics."""
        return self._comm_helper.get_block_statistics()

    D_LEVEL = 3
