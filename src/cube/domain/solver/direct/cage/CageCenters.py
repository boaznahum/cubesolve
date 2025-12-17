"""
NxNCenters - Solves center pieces on NxN cubes (N > 3).

=============================================================================
OVERVIEW
=============================================================================

This solver brings center pieces from source faces to target faces using:
1. Complete slice swaps (swap entire row/column between faces)
2. Block commutators (3-cycle blocks of center pieces)
3. Single-piece commutators (3-cycle individual center pieces)

DESIGNED FOR: Reduction method (centers solved BEFORE edges)
WARNING: Breaks paired edges! NOT suitable for Cage method.

=============================================================================
WHY IT BREAKS THE CAGE (PAIRED EDGES)
=============================================================================

The core commutator in _block_communicator (lines ~790-797) uses SINGLE F rotations:

    [M', F, M', F', M, F, M, F']

Single F rotations move the ENTIRE front face, which:
- Separates the 3 wing slices of each front edge
- Even though the commutator "undoes" itself mathematically,
  the wing pieces end up scrambled

For reduction method: This is fine - centers are solved BEFORE edge pairing
For cage method: This breaks already-paired edges!

=============================================================================
ALGORITHM ANALYSIS - WHAT AFFECTS WHAT
=============================================================================

MOVE TYPES AND THEIR EFFECTS:
-----------------------------
| Move      | Centers | Edges (paired) | Corners |
|-----------|---------|----------------|---------|
| M, M'     | YES     | NO (inner only)| NO      |
| M2        | YES     | NO             | NO      |
| F, F'     | YES     | **BREAKS!**    | MOVES   |
| F2        | YES     | NO (symmetric) | MOVES   |
| U, U'     | YES     | **BREAKS!**    | MOVES   |
| U2        | YES     | NO (symmetric) | MOVES   |
| r (inner) | YES     | NO             | NO      |

KEY INSIGHT: Single face rotations (F, U, etc.) break edge pairing.
             Double rotations (F2, U2) and inner slices (M, r) are safe.

=============================================================================
CAGE-SAFE ALTERNATIVE NEEDED
=============================================================================

For cage method, need commutators using ONLY:
- Inner slice moves: M, E, S, r, l, u, d, f, b
- Double face rotations: F2, B2, U2, D2, R2, L2

Example cage-safe center commutator:
    [r U2 r', D2, r U2 r', D2']  - cycles 3 centers without affecting edges

=============================================================================
"""

import sys
from collections.abc import Iterator, Sequence, Iterable, Set
from enum import Enum, unique
from typing import Tuple, TypeAlias

from cube.domain import algs
from cube.domain.algs import Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName, Color, CenterSlice
from cube.domain.model.Cube import Cube
from cube.domain.model.cube_boy import CubeLayout, color2long
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.FaceTracker import FaceTracker
from cube.domain.solver.beginner.NxnCentersFaceTracker import NxNCentersFaceTrackers
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils.OrderedSet import OrderedSet


def use(_):
    pass


_status = None

Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]


@unique
class _SearchBlockMode(Enum):
    """
    Mode for searching matching blocks on source face.

    CompleteBlock: All pieces in block must match target color
    BigThanSource: Block has more matching pieces than current target
    ExactMatch: Block matches exactly (no partial matches allowed)
    """
    CompleteBlock = 1
    BigThanSource = 2
    ExactMatch = 3  # required on source match source


class _CompleteSlice:
    """
    Represents a complete row or column of center pieces.

    Used by _do_complete_slices to find and swap entire slices
    between faces, which is more efficient than moving pieces
    one at a time.

    Attributes:
        is_row: True if this is a horizontal slice, False if vertical
        index: Row/column index in the center grid [0, n_slices)
        n_matches: How many pieces in this slice match the target color
        contains_track_slice: True if slice contains a tracker piece (even cubes)
    """
    is_row: bool
    index: int  # of row/column
    n_matches: int  # number of pieces match color

    def __init__(self, is_row: bool, index: int, n_matches: int, contains_trackers) -> None:
        self.is_row = is_row
        self.index = index
        self.n_matches = n_matches
        self.contains_track_slice = contains_trackers


class CageCenters(SolverElement):
    """
    Solves center pieces for CAGE METHOD - preserves paired edges!

    This is a modified version of NxNCenters that UNDOES setup moves
    to preserve the cage (paired edges and solved corners).

    ALGORITHM OVERVIEW:
    ===================

    1. For each face, bring pieces of the correct color from other faces
    2. Use three strategies (in order of efficiency):
       a. Swap complete slices (entire rows/columns)
       b. Move blocks of matching pieces
       c. Move individual pieces via commutators

    KEY DIFFERENCE FROM NxNCenters:
    ===============================

    NxNCenters has setup moves that are NOT undone:
    - _swap_slice line 710: F' to convert row to column
    - _swap_slice line 752: source_face * n_rotate to align
    - _block_communicator line 1169: source_face * n_rotate to align

    CageCenters UNDOES these setup moves after each algorithm,
    preserving the cage.

    The commutator itself is BALANCED (2 F + 2 F' = 0), so it
    naturally preserves edge pairing. Only the setup moves break it.

    FOR ODD CUBES ONLY:
    ===================

    - Face color is determined by fixed center piece
    - Even cubes not yet supported (need FaceTracker)
    """
    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv)

        self._faces: Sequence[FaceTracker] = []

        self._trackers = NxNCentersFaceTrackers(slv)

        cfg = self.cube.config
        self._sanity_check_is_a_boy = cfg.solver_sanity_check_is_a_boy
        # =====================================================================
        # CAGE METHOD: DISABLE SLICE SWAPS AND FACE SWAPS!
        # =====================================================================
        # _do_complete_slices uses U2/B2 which permanently moves corners.
        # _swap_entire_face_odd_cube also uses moves that break the cage.
        # For cage method, we MUST preserve corners, so disable these.
        # We'll rely on commutators only, which have balanced F rotations.
        # =====================================================================
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False  # DISABLED for cage!
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO = cfg.optimize_big_cube_centers_search_complete_slices_only_target_zero
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS = cfg.optimize_big_cube_centers_search_blocks
        self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False  # DISABLED for cage!

    def debug(self, *args, level=3):
        if level <= CageCenters.D_LEVEL:
            super().debug("NxX Centers:", args)

    def _is_solved(self):
        return all((f.center.is3x3 for f in self.cube.faces)) and self.cube.is_boy

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and it is a boy
        """

        return self._is_solved()

    def solve(self):
        """
        Solve all center pieces.

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        This method preserves paired edges and solved corners.
        All internal methods either:
        - Use balanced commutators (F rotations cancel out)
        - Undo their setup moves before returning
        """
        if self._is_solved():
            return  # avoid rotating cube

        with self.ann.annotate(h1="Big cube centers"):
            try:
                self._solve()
            finally:
                self._trackers._debug_print_track_slices("After solving")
                self._trackers._remove_all_track_slices()
                self._trackers._debug_print_track_slices("After removal")

    def _solve(self) -> None:
        """
        Main solving algorithm - iterates over faces and brings correct colors.

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        Delegates to __do_center which preserves 3x3 solution.

        ALGORITHM FLOW:
        ===============

        1. CREATE FACE TRACKERS
           - Odd cubes: Face color = center piece color (fixed)
           - Even cubes: Must establish color mapping (complex logic)

        2. SOLVE WITHOUT BACK FACE (while loop)
           - Iterate faces, bringing colors from adjacent faces (U, D, L, R)
           - Back face is excluded to avoid moving pieces we just placed
           - Repeat until no more work can be done from adjacent faces

        3. SOLVE WITH BACK FACE (final pass)
           - Now include back face as source
           - Picks up any remaining pieces

        CUBE STATE CHANGES:
        ===================

        During solving, the cube is rotated to bring each target face to FRONT.
        This simplifies the algorithm - always work with front face as target.

        Moves used:
        - Cube rotations (x, y, z) - to position faces
        - M slice moves - to move center columns
        - F rotations - to set up commutators (but undone to preserve 3x3)
        """
        cube = self.cube

        faces: list[FaceTracker]

        if cube.n_slices % 2:
            # =================================================================
            # ODD CUBE (5x5, 7x7, etc.)
            # =================================================================
            # Face color is determined by the fixed center piece.
            # No need for complex color mapping.
            # =================================================================

            # do without back as long as there is work to do
            faces = [FaceTracker.track_odd(f) for f in cube.faces]

        else:

            f1: FaceTracker = self._trackers.track_no_1()

            f2 = f1.track_opposite()

            # because we find f1 by max colors, then it is clear that it has at least one of such a color
            # and opposite doesn't need color for tracing
            # self._do_faces([f1, f2], True, True)

            # now colors of f1/f2 can't be on 4 that left, so we can choose any one
            f3 = self._trackers._track_no_3([f1, f2])
            f4 = f3.track_opposite()

            # f3 contains at least one color that is not in f1, f2, so no need to bring at leas one
            # but there is a question if such f3 always exists
            self._do_faces([f3, f4], True, True)

            f5, f6 = self._trackers._track_two_last([f1, f2, f3, f4])

            # so we don't need this also, otherwise _track_two_last should crash
            self._do_faces([f5], True, True)
            self._asserts_is_boy([f1, f2, f3, f4, f5, f6])

            FaceTracker.remove_face_track_slices(f5.face)

            f5 = FaceTracker.search_color_and_track(f5.face, f5.color)
            f6 = f5.track_opposite()

            faces = [f1, f2, f3, f4, f5, f6]
            self._faces = faces

            self._asserts_is_boy(faces)

            self._trackers._debug_print_track_slices("After creating all faces")

            # self._faces = faces

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
            if not self._do_faces(faces, False, False):
                break
            self._asserts_is_boy(faces)

        self._asserts_is_boy(faces)

        self._do_faces(faces, False, True)

        self._asserts_is_boy(faces)

        assert self._is_solved()

    def _do_faces(self, faces: Sequence[FaceTracker], minimal_bring_one_color, use_back_too: bool) -> bool:
        # while True:
        self.debug("_do_faces:", *faces)
        work_done = False
        for f in faces:
            # we must trace faces, because they are moved by algorith
            # we need to locate the face by original_color, b ut on odd cube, the color is of the center
            if self._do_center(f, minimal_bring_one_color, use_back_too):
                work_done = True
                if len(faces) == 6:
                    self._asserts_is_boy(faces)
            # if NxNCenters.work_on_b or not work_done:
            #     break

        return work_done

    def _print_faces(self):

        for f in self._faces:
            print(f.face, f.color, " ", end="")
        print()

    # noinspection PyUnreachableCode,PyUnusedLocal
    def _asserts_is_boy(self, faces: Iterable[FaceTracker]):

        if not self._sanity_check_is_a_boy:
            return

        layout = {f.face.name: f.color for f in faces}

        cl: CubeLayout = CubeLayout(False, layout, self.cube.sp)

        is_boy = cl.same(self.cube.original_layout)

        if not is_boy:
            print(cl, file=sys.stderr)
            print(file=sys.stderr)

        assert is_boy

    def _do_center(self, face_loc: FaceTracker, minimal_bring_one_color, use_back_too: bool) -> bool:

        if self._is_face_solved(face_loc.face, face_loc.color):
            self.debug(f"Face is already done {face_loc.face}",
                       level=1)
            return False

        color = face_loc.color

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug(f"{face_loc.face} already has at least one {color}")
            return False

        sources:Set[Face] = OrderedSet(self.cube.faces) - {face_loc.face}
        if not use_back_too:
            sources -= {face_loc.face.opposite}

        if all(not self._has_color_on_face(f, color) for f in sources):
            self.debug(f"For face {face_loc.face}, No color {color} available on  {sources}",
                       level=1)
            return False

        self.debug(f"Need to work on {face_loc.face}",
                   level=1)

        work_done = self.__do_center(face_loc, minimal_bring_one_color, use_back_too)

        self.debug(f"After working on {face_loc.face} {work_done=}, "
                   f"solved={self._is_face_solved(face_loc.face, face_loc.color)}",
                   level=1)

        return work_done

    def __do_center(self, face_loc: FaceTracker, minimal_bring_one_color: bool, use_back_too: bool) -> bool:
        """
        Process one face - bring correct colored pieces from adjacent faces.

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        - Tracks all _bring_face_up_preserve_front rotations in setup_alg
        - Plays setup_alg.prime before every return to undo rotations
        - Delegates to _do_center_from_face which also preserves 3x3

        :return: if any work was done
        """

        face: Face = face_loc.face
        color: Color = face_loc.color

        if self._is_face_solved(face, color):
            self.debug(f"Face is already done {face}",
                       level=1)
            return False

        if minimal_bring_one_color and self._has_color_on_face(face_loc.face, color):
            self.debug(f"{face_loc.face} already has at least one {color}")
            return False

        cmn = self.cmn

        self.debug(f"Working on face {face}",
                   level=1)

        with self.ann.annotate(h2=f"{color2long(face_loc.color).value} face"):
            cube = self.cube

            # we loop bringing all adjusted faces up
            cmn.bring_face_front(face_loc.face)
            assert cube.front.color == color
            # from here face is no longer valid
            # so

            work_done = False

            if any(self._has_color_on_face(f, color) for f in cube.front.adjusted_faces()):
                # =============================================================
                # CAGE METHOD: SETUP ROTATION TRACKING AND UNDO
                # =============================================================
                #
                # PROBLEM:
                # --------
                # We need to cycle through adjacent faces (L, D, R) as source
                # faces. To do this, _bring_face_up_preserve_front rotates the
                # cube using B[1:n+1] (wide back rotation). These rotations
                # MOVE CORNERS and if not undone, break the solved cage.
                #
                # SOLUTION:
                # ---------
                # 1. Track all rotations in setup_alg (starts as NOOP)
                # 2. Each _bring_face_up_preserve_front returns the alg it played
                # 3. Accumulate: setup_alg = setup_alg + returned_alg
                # 4. Before ANY return, play setup_alg.prime to undo all rotations
                #
                # EXAMPLE:
                # --------
                # If we do: B'[1:n] then B'[1:n] then B'[1:n] (3 rotations)
                # setup_alg becomes: B'[1:n] + B'[1:n] + B'[1:n]
                # setup_alg.prime is: B[1:n] + B[1:n] + B[1:n] (undoes all)
                #
                # WHY THIS PRESERVES THE CAGE:
                # ----------------------------
                # - Corners return to original positions (rotations undone)
                # - Edges return to original positions (rotations undone)
                # - Only centers are changed (by the commutators)
                # =============================================================
                setup_alg = Algs.NOOP

                for _ in range(3):  # Process 3 adjacent faces: L, D, R
                    # don't use face - it was moved !!!
                    if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.up):
                        work_done = True
                        if minimal_bring_one_color:
                            self.op.play(setup_alg.prime)  # UNDO before return!
                            return work_done

                    if self._is_face_solved(face_loc.face, color):
                        self.op.play(setup_alg.prime)  # UNDO before return!
                        return work_done

                    # Rotate to bring next adjacent face to UP position
                    # _bring_face_up_preserve_front returns the alg it played
                    setup_alg = setup_alg + self._bring_face_up_preserve_front(cube.left)

                # Process the last (4th) adjacent face
                if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.up):
                    work_done = True
                    if minimal_bring_one_color:
                        self.op.play(setup_alg.prime)  # UNDO before return!
                        return work_done

                if self._is_face_solved(face_loc.face, color):
                    self.op.play(setup_alg.prime)  # UNDO before return!
                    return work_done

                # =============================================================
                # UNDO ALL SETUP ROTATIONS - RESTORE CAGE!
                # =============================================================
                # This is the normal exit path. Play the inverse of all
                # accumulated rotations to restore corners/edges.
                # =============================================================
                self.op.play(setup_alg.prime)

            if use_back_too:
                # now from back
                # don't use face - it was moved !!!
                if self._do_center_from_face(cube.front, minimal_bring_one_color, color, cube.back):
                    work_done = True

            return work_done

    def _do_center_from_face(self, face: Face, minimal_bring_one_color, color: Color, source_face: Face) -> bool:
        """
        Bring center pieces of `color` from source_face to target face (front).

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        - _do_complete_slices: DISABLED (uses U2/B2 which breaks corners)
        - _do_blocks: Calls _block_communicator which preserves 3x3
        - Single piece loop: Calls _block_communicator which preserves 3x3

        The sources are on source_face (UP or BACK position).
        The target face is on FRONT.

        :param face: Target face (must be cube.front)
        :param minimal_bring_one_color: Stop after bringing one piece
        :param color: The color to bring
        :param source_face: Where to get pieces from (cube.up or cube.back)
        :return: True if any work was done
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

            if on_source - ok_on_this > 2:  # swap two faces is about two communicators
                self._swap_entire_face_odd_cube(color, face, source_face)
                work_done = True

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES:
            if self._do_complete_slices(color, face, source_face):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        if self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_BLOCKS:
            # should move minimal_bring_one_color into _do_blocks, because ein case of back, it can do too much
            if self._do_blocks(color, face, source_face):
                work_done = True
                if minimal_bring_one_color:
                    return work_done

        else:

            # the above also did a 1 size block
            for rc in self._2d_center_iter():

                if self._block_communicator(color,
                                            face,
                                            source_face,
                                            rc, rc,
                                            _SearchBlockMode.CompleteBlock):

                    after_fixed_color = center.get_center_slice(rc).color

                    if after_fixed_color != color:
                        raise InternalSWError(f"Slice was not fixed {rc}, " +
                                              f"required={color}, " +
                                              f"actual={after_fixed_color}")

                    self.debug(f"Fixed slice {rc}")

                    work_done = True
                    if minimal_bring_one_color:
                        return work_done

        if not work_done:
            self.debug(f"Internal error, no work was done on face {face} required color {color}, "
                       f"but source face  {source_face} contains {self.count_color_on_face(source_face, color)}")
            for rc in self._2d_center_iter():
                if center.get_center_slice(rc).color != color:
                    print(f"Missing: {rc}  {[*self._get_four_center_points(rc[0], rc[1])]}")
            for rc in self._2d_center_iter():
                if source_face.center.get_center_slice(rc).color == color:
                    print(f"Found on {source_face}: {rc}  {source_face.center.get_center_slice(rc)}")

            raise InternalSWError("See error in log")

        return work_done

    def _do_complete_slices(self, color, face, source_face) -> bool:
        """
        Swap complete slices (rows/columns) between faces.

        PRESERVES 3x3 SOLUTION: NO - DISABLED FOR CAGE METHOD!
        =======================================================
        This method calls _swap_slice which uses U2/B2 that breaks corners.
        It is DISABLED for CageCenters via:
            _OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False
        """
        work_done = False

        # do while work is done
        while True:
            if not self._do_one_complete_slice(color, face, source_face):
                return work_done

            work_done = True

    def _do_one_complete_slice(self, color, target_face: Face, source_face: Face) -> bool:

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

            if source_slice.contains_track_slice:
                continue  # we can't move it happens in even cube

            target_slices = slices_on_target_face.get(index)

            if target_slices is None:
                target_slices = self._search_slices_on_face(target_face, color, index, False)
                assert len(target_slices) == 4  # we search vertical and horizontal x  index, inv(index)
                slices_on_target_face[index] = target_slices

            min_target_slice = target_slices[0]

            if not min_target_slice.contains_track_slice:

                if (
                        (min_target_slice.n_matches == 0 or
                         not self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES_ONLY_TARGET_ZERO) and
                          source_slice.n_matches > 0 / 2.0  # SEE SPECIAL_CASE_1 above
                ) and source_slice.n_matches > min_target_slice.n_matches:
                    # ok now swap

                    # before = self.count_color_on_face(face, color)

                    # self._debug_print_track_slices()
                    # print("before", end="")
                    # self._print_faces()
                    # before = [ (f.face, f.color) for f in self._faces]

                    # _tf: FaceLoc = next(_f for _f in self._faces if _f.face is target_face)
                    # _sf: FaceLoc = next(_f for _f in self._faces if _f.face is source_face)
                    # print(f"@@@ to {color} {_tf} from {_sf} n={source_slice.n_matches}")

                    with self.ann.annotate(h2=f", Swap complete slice"):
                        self._swap_slice(min_target_slice, target_face, source_slice, source_face)

                    # print("after", end="")
                    # self._print_faces()
                    # _after = [ (f.face, f.color) for f in self._faces]
                    # if _before != _after:
                    #     print("xxxx")
                    #     raise InternalSWError()

                    # self._debug_print_track_slices()
                    # self._asserts_is_boy(self._faces)

                    # after = self.count_color_on_face(face, color)

                    # print(before, after, color)

                    return True

        return False

    def _swap_slice(self, target_slice: _CompleteSlice,
                    target_face: Face,
                    source_slice: _CompleteSlice, source_face: Face):
        """
        Swap a complete slice (row or column) between target and source faces.

        PRESERVES 3x3 SOLUTION: NO - DISABLED FOR CAGE METHOD!
        =======================================================
        This method is called by _do_complete_slices, which is DISABLED
        for CageCenters (_OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES=False).

        The swap algorithm uses U2 or B2 which PERMANENTLY moves corners:
            M' + U2 + M  (or M' + B2 + M)
        The U2/B2 cannot be undone without breaking the swap itself.

        For cage method, we use only _block_communicator which has
        balanced F rotations that preserve corners.

        ALGORITHM:
        ==========

        1. NORMALIZE TARGET TO VERTICAL
           - If target is a row, rotate F' to make it a column
           - ⚠️ THIS F' BREAKS PAIRED EDGES!

        2. ROTATE SOURCE TO ALIGN
           - Rotate source face so its slice aligns with target column

        3. EXECUTE SWAP
           - M slice move brings source slice to target position
           - Source face rotation swaps the slices
           - M' slice move completes the swap

        CUBE STATE CHANGES:
        ===================

        Before: Target face has slice with wrong colors
                Source face has slice with correct colors

        Step 1 (if target is row):
            F' rotation - ⚠️ UNPAIRS FRONT EDGES
            Front face rotated 90° counterclockwise
            All front edge wings separated from their pairs

        Step 2: Source face rotation (U or B)
            Rotates source to align slices
            If source is U: affects top edges
            If source is B: affects back edges

        Step 3: The swap algorithm
            M[target_col]' * mul  - Move target column up/back
            Source_face * 2       - Swap slices (F2 equivalent - SAFE)
            M[target_col] * mul   - Move column back

        After: Target slice has correct colors
               Source slice has target's old colors
               ⚠️ Edges are UNPAIRED if F' was used in step 1!

        WHY THIS BREAKS THE CAGE:
        =========================

        Line: op.play(Algs.F.prime)

        This single F' rotation is a setup move to convert a horizontal
        target slice to vertical. It rotates the entire front face,
        which separates the 3 wing pieces of each front edge.

        The algorithm does NOT undo this F' - it's a permanent change
        to the front face orientation, breaking edge pairing.
        """
        cube = self.cube
        n_slices = cube.n_slices

        target_index: int
        did_f_prime_setup = False  # Track if we need to undo F'

        # slice must be vertical
        op = self.op
        if target_slice.is_row:
            # =====================================================================
            # SETUP MOVE: F' to convert row to column
            # =====================================================================
            # Will be UNDONE at end to preserve cage
            # =====================================================================
            target_slice_block_1 = cube.cqr.rotate_point_counterclockwise((target_slice.index, 0))
            target_index = target_slice_block_1[1]
            op.play(Algs.F.prime)
            did_f_prime_setup = True  # Remember to undo
        else:
            # column
            target_index = target_slice.index

        # now we must bring source slice into position (0,  target_index^)

        nm1 = cube.n_slices - 1
        source_index = source_slice.index
        if source_slice.is_row:
            s1 = (source_index, 0)
            s2 = (source_index, nm1)
        else:
            s1 = (0, source_index)
            s2 = (nm1, source_index)

        # now we need to bring source slice such that one of its endpoints is (0,  target_index^)
        required_on_target = (0, cube.inv(target_index))

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

            s1 = cube.cqr.rotate_point_clockwise(s1)
            s2 = cube.cqr.rotate_point_clockwise(s2)

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

            for rc in self._2d_range((0, target_index), (nm1, target_index)):
                yield target_face.center.get_center_slice(rc)

        with self.ann.annotate((ann_source(), AnnWhat.Moved), (ann_target(), AnnWhat.FixedPosition)):
            op.play(slice_source_alg * mul +
                  rotate_source_alg * 2 +  # this replaces source slice with target
                  slice_source_alg.prime * mul
                  )

        # =====================================================================
        # UNDO SETUP MOVES - PRESERVE CAGE!
        # =====================================================================
        # Undo the setup moves in reverse order to restore edge pairing
        # =====================================================================

        # Undo source face rotation (line 754)
        if n_rotate:
            self.debug(f"  [CAGE] Undoing source rotation: {rotate_source_alg.prime * n_rotate}", level=1)
            op.play(rotate_source_alg.prime * n_rotate)

        # Undo F' setup (line 711)
        if did_f_prime_setup:
            self.debug("  [CAGE] Undoing F' setup: F", level=1)
            op.play(Algs.F)

    def _do_blocks(self, color, face, source_face):
        """
        Move blocks of matching pieces using commutators.

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        Calls _block_communicator which has balanced F rotations
        and undoes its source face setup rotation.
        """
        work_done = False

        cube = self.cube

        big_blocks = self._search_big_block(source_face, color)

        if not big_blocks:
            return False

        # because we do exact match, there is no risk that that new blocks will be constructed,
        # so we try all

        for _, big_block in big_blocks:
            # print(f"@@@@@@@@@@@ Found big block: {big_block}")

            rc1 = big_block[0]
            rc2 = big_block[1]

            rc1_on_target = self._point_on_source(source_face is cube.back, rc1)
            rc2_on_target = self._point_on_source(source_face is cube.back, rc2)

            for _ in range(4):
                if self._block_communicator(color,
                                            face,
                                            source_face,
                                            rc1_on_target, rc2_on_target,
                                            # actually we want big-than, but for this we need to find best match
                                            # it still doesn't work, we need another mode, Source and Target Match
                                            # but for this we need to search source only
                                            _SearchBlockMode.ExactMatch):
                    # this is much far then true, we need to search new block
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

        PRESERVES 3x3 SOLUTION: NO (by itself) / YES (when caller undoes)
        =================================================================
        This method MOVES corners and edges via wide B rotation.
        It returns the algorithm played so caller can undo with alg.prime.
        Caller (__do_center) accumulates all algs and undoes them at the end.

        CAGE METHOD: Returns the algorithm played so caller can UNDO it!

        =================================================================
        WHY THIS METHOD EXISTS:
        =================================================================
        To solve centers, we need to bring pieces from adjacent faces
        (L, D, R) to the front. The algorithm works with source on UP,
        so we rotate the cube to bring each adjacent face to UP.

        =================================================================
        HOW IT WORKS:
        =================================================================
        Uses B[1:n+1] - a WIDE back rotation that moves:
        - All back slices (entire back "slab" of the cube)
        - This rotates L, D, R, U faces around the front face

        Visual (looking from front):

            U                    L
            |                    |
        L --+-- R   -->      D --+-- U   (after B'[1:n])
            |                    |
            D                    R

        =================================================================
        ALGORITHM FOR EACH FACE:
        =================================================================
        - L (Left)  -> UP: B'[1:n]     (counterclockwise)
        - D (Down)  -> UP: B'[1:n] * 2 (180 degrees)
        - R (Right) -> UP: B[1:n]      (clockwise)
        - U (Up)    -> UP: no rotation needed (return NOOP)

        =================================================================
        WHY RETURN THE ALG (CAGE METHOD):
        =================================================================
        These rotations MOVE CORNERS AND EDGES. For cage method, we must
        UNDO them after processing each face. By returning the alg played,
        the caller can accumulate all rotations and undo with alg.prime.

        Example:
        - Play B'[1:n] to bring L to UP
        - ... process centers ...
        - Undo with (B'[1:n]).prime = B[1:n]

        Returns:
            The algorithm played (to undo with alg.prime)
            Returns Algs.NOOP if face was already UP (no rotation needed)
        """
        if face.name == FaceName.U:
            return Algs.NOOP  # Already UP, no rotation needed

        if face.name == FaceName.B or face.name == FaceName.F:
            raise InternalSWError(f"{face.name} is not supported, can't bring them to up preserving front")

        self.debug(f"Need to bring {face} to up")

        # B[1:n+1] = wide back rotation (all slices except front face)
        rotate = Algs.B[1:self.cube.n_slices + 1]

        alg_to_play: algs.Alg
        match face.name:

            case FaceName.L:
                # L -> UP requires counterclockwise rotation (looking from back)
                alg_to_play = rotate.prime

            case FaceName.D:
                # D -> UP requires 180 degree rotation
                alg_to_play = rotate.prime * 2

            case FaceName.R:
                # R -> UP requires clockwise rotation (looking from back)
                alg_to_play = rotate

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

        self.op.play(alg_to_play)
        return alg_to_play

    def _find_matching_slice(self, f: Face, r: int, c: int, required_color: Color) -> CenterSlice | None:

        for i in self._get_four_center_points(r, c):

            cs = f.center.get_center_slice(i)

            if cs.color == required_color:
                return cs

        return None

    def _get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        inv = self.cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def rotate_point_clockwise(self, row: int, column: int, n=1) -> Tuple[int, int]:

        return self.cube.cqr.rotate_point_clockwise((row, column), n)

    def rotate_point_counterclockwise(self, row: int, column: int, n=1) -> Tuple[int, int]:
        return self.cube.cqr.rotate_point_counterclockwise((row, column), n)

    def _swap_entire_face_odd_cube(self, required_color: Color, face: Face, source: Face):

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

        # on odd cube
        # todo: replace with self._get_slice_m_alg()
        raise InternalSWError("Need to fix MM")

        swap_faces = [Algs.MM()[1:mid_pls_1 - 1].prime * rotate_mul, Algs.F.prime * 2,
                      Algs.MM()[1:mid_pls_1 - 1] * rotate_mul,
                      Algs.MM()[mid_pls_1 + 1:end].prime * rotate_mul,
                      Algs.F * 2 + Algs.MM()[mid_pls_1 + 1:end] * rotate_mul
                      ]
        op.op(Algs.seq_alg(None, *swap_faces))

        # communicator 1, upper block about center
        self._block_communicator(required_color, face, source,
                                 (mid + 1, mid), (nn - 1, mid),
                                 _SearchBlockMode.BigThanSource)

        # communicator 2, lower block below center
        self._block_communicator(required_color, face, source,
                                 (0, mid), (mid - 1, mid),
                                 _SearchBlockMode.BigThanSource)

        # communicator 3, left to center
        self._block_communicator(required_color, face, source,
                                 (mid, 0), (mid, mid - 1),
                                 _SearchBlockMode.BigThanSource)

        # communicator 4, right ot center
        self._block_communicator(required_color, face, source,
                                 (mid, mid + 1), (mid, nn - 1),
                                 _SearchBlockMode.BigThanSource)

    def _block_communicator(self,
                            required_color: Color,
                            face: Face, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                            mode: _SearchBlockMode) -> bool:
        """
        Execute a commutator to 3-cycle a block of center pieces.

        PRESERVES 3x3 SOLUTION: YES
        ===========================
        - The commutator itself is BALANCED: 2×F + 2×F' = net 0 rotation
        - Corners return to original positions after the 8 moves
        - Source face setup rotation (n_rotate) is UNDONE at the end

        This is the CORE ALGORITHM for moving center pieces.

        PARAMETERS:
        ===========
        face: Target face (must be cube.front)
        source_face: Source face (must be cube.up or cube.back)
        rc1, rc2: Corners of the block to move (center slice indices [0..n))
        mode: How to search for matching block on source face

        RETURNS:
        ========
        False if no matching block found or no work needed
        True if commutator was executed

        THE COMMUTATOR ALGORITHM:
        =========================

        This executes an 8-move commutator sequence:

            cum = [
                M[c1:c2]' * mul,      # Step 1: Move target column(s) toward source
                F (or F'),            # Step 2: Rotate front face ⚠️ BREAKS EDGES!
                M[c1':c2']' * mul,    # Step 3: Move buffer column(s) toward source
                F' (or F),            # Step 4: Undo front rotation
                M[c1:c2] * mul,       # Step 5: Move target column(s) back
                F (or F'),            # Step 6: Rotate front face ⚠️ BREAKS EDGES!
                M[c1':c2'] * mul,     # Step 7: Move buffer column(s) back
                F' (or F)             # Step 8: Undo front rotation
            ]

        Where:
        - M[c1:c2] = M slice(s) covering columns c1 to c2
        - mul = 1 for source=UP, 2 for source=BACK
        - (c1', c2') = rotated position of (c1, c2) after F rotation

        VISUAL EXPLANATION (single piece case):
        =======================================

        Initial state (front face view):
                        UP
                    [S . .]      S = source piece (correct color)
                    [. . .]
                    [. . .]
            LEFT                    RIGHT
                    [. T .]      T = target position (wrong color)
                    [. . .]
                    [. . B]      B = buffer position
                        DOWN

        After commutator:
        - Source piece S moves to Target position T
        - Target piece T moves to Buffer position B
        - Buffer piece B moves to Source position S

        CUBE STATE CHANGES - STEP BY STEP:
        ==================================

        Step 1: M' (or M'2 for back)
            - Inner column slides UP (or UP twice)
            - Target piece T moves to UP face
            - Source piece S stays on UP face
            - Centers affected, edges/corners UNCHANGED

        Step 2: F (or F') ⚠️ CAGE-BREAKING!
            - ENTIRE front face rotates 90°
            - Target piece T (now on UP) rotates with front column
            - ⚠️ All 4 front edge wings SEPARATE from their pairs!
            - Front corners move (affects corner positions)

        Step 3: M' (or M'2 for back)
            - Different column slides UP
            - Buffer piece B moves to UP face
            - Centers affected, edges/corners UNCHANGED

        Step 4: F' (or F)
            - Undo the F rotation
            - ⚠️ Edges still broken - different wings return!

        Step 5-8: Repeat pattern to complete 3-cycle
            - More F rotations continue to scramble edge wings

        AFTER COMMUTATOR:
        - Centers: 3 pieces cycled as intended ✓
        - Corners: Returned to original positions ✓
        - Edges: ⚠️ WINGS SCRAMBLED! Pairs broken!

        WHY THIS BREAKS THE CAGE:
        =========================

        The F rotations (steps 2, 4, 6, 8) move ALL stickers on the front face.

        In a 5x5 cube, the front face has:
        - 4 corners (returned correctly)
        - 4 edges, each with 3 wing pieces (SCRAMBLED!)
        - 9 center pieces (cycled as intended)

        When F rotates, all 3 wings of each front edge move together.
        But the M slice moves only affect the MIDDLE wing.
        So after the commutator:
        - Middle wings: cycled with centers
        - Outer wings: just rotated and returned
        - Result: The 3 wings of each edge are no longer adjacent!

        CAGE-SAFE ALTERNATIVE:
        ======================

        To preserve edges, replace F with F2:
            [M', F2, M', F2, M, F2, M, F2]

        But F2 doesn't create a 3-cycle - it creates a 2-swap.
        Need different algorithm for cage method.
        """
        cube: Cube = face.cube
        assert face is cube.front
        assert source_face is cube.up or source_face is cube.back

        is_back = source_face is cube.back

        # normalize block
        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        rc1 = (r1, c1)
        rc2 = (r2, c2)

        # in case of odd nd (mid, mid), search will fail, nothing to do
        # if we change the order, then block validation below will fail,
        #  so we need to check for case odd (mid, mid) somewhere else
        # now search block
        n_rotate = self._search_block(face, source_face, required_color, mode, rc1, rc2)

        if n_rotate is None:
            return False

        on_front_rotate: algs.Alg

        # assume we rotate F clockwise
        rc1_f_rotated = self.rotate_point_clockwise(r1, c1)
        rc2_f_rotated = self.rotate_point_clockwise(r2, c2)

        # the columns ranges must not intersect
        if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
            on_front_rotate = Algs.F.prime
            rc1_f_rotated = self.rotate_point_counterclockwise(r1, c1)
            rc2_f_rotated = self.rotate_point_counterclockwise(r2, c2)

            if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
                print("Intersection still exists after rotation", file=sys.stderr)
            assert not self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1]))
        else:
            # clockwise is OK
            on_front_rotate = Algs.F

        # =====================================================================
        # BUILD THE COMMUTATOR SEQUENCE
        # =====================================================================
        #
        # center indexes are in opposite direction of R
        #   index is from left to right, R is from right to left
        #
        # rotate_on_cell: M slice for target column(s)
        # rotate_on_second: M slice for buffer column(s) after F rotation
        # =====================================================================
        rotate_on_cell = self._get_slice_m_alg(rc1[1], rc2[1])
        rotate_on_second = self._get_slice_m_alg(rc1_f_rotated[1], rc2_f_rotated[1])

        # For back face, need double rotation (180°) to reach it
        if is_back:
            rotate_mul = 2
        else:
            rotate_mul = 1

        # =====================================================================
        # THE 8-MOVE COMMUTATOR - THIS IS WHERE EDGES GET BROKEN!
        # =====================================================================
        #
        # Pattern: [A, B] where A = M slice, B = F rotation
        # Expanded: A B A' B' (but we use 2 different A's)
        #
        # This 3-cycles centers:
        #   target_pos → buffer_pos → source_pos → target_pos
        #
        # ⚠️ THE F ROTATIONS (on_front_rotate) BREAK PAIRED EDGES!
        # =====================================================================
        cum = [
            rotate_on_cell.prime * rotate_mul,   # Step 1: M' - move target col to source face (SAFE)
            on_front_rotate,                      # Step 2: F  - rotate front ⚠️ BREAKS EDGES!
            rotate_on_second.prime * rotate_mul, # Step 3: M' - move buffer col to source face (SAFE)
            on_front_rotate.prime,               # Step 4: F' - undo front rotation ⚠️ EDGES SCRAMBLED
            rotate_on_cell * rotate_mul,         # Step 5: M  - return target col (SAFE)
            on_front_rotate,                      # Step 6: F  - rotate front again ⚠️ BREAKS EDGES!
            rotate_on_second * rotate_mul,       # Step 7: M  - return buffer col (SAFE)
            on_front_rotate.prime                # Step 8: F' - final undo ⚠️ EDGES STILL SCRAMBLED
        ]
        # =====================================================================
        # After this commutator:
        # - Centers: 3-cycled correctly ✓
        # - Corners: back in original positions ✓
        # - Edges: ⚠️ WING PIECES SCRAMBLED - PAIRS BROKEN!
        # =====================================================================

        def _ann_target():

            for rc in self._2d_range_on_source(False, rc1, rc2):
                yield face.center.get_center_slice(rc)

        def _ann_source():
            _on_src1_1 = self._point_on_source(is_back, rc1)
            _on_src1_2 = self._point_on_source(is_back, rc2)
            # why - ? because we didn't yet rotate it
            _on_src1_1 = cube.cqr.rotate_point_clockwise(_on_src1_1, -n_rotate)
            _on_src1_2 = cube.cqr.rotate_point_clockwise(_on_src1_2, -n_rotate)
            for rc in self._2d_range(_on_src1_1, _on_src1_2):
                yield source_face.center.get_center_slice(rc)

        def _h2():
            size_ = self._block_size2(rc1, rc2)
            return f", {size_[0]}x{size_[1]} communicator"

        with self.ann.annotate((_ann_source, AnnWhat.Moved),
                               (_ann_target, AnnWhat.FixedPosition),
                               h2=_h2
                               ):
            if n_rotate:
                self.op.play(Algs.of_face(source_face.name) * n_rotate)
            self.op.play(Algs.seq_alg(None, *cum))

        # =====================================================================
        # UNDO SETUP MOVE - PRESERVE CAGE!
        # =====================================================================
        # The commutator itself is balanced (F and F' cancel out).
        # But the source face rotation setup is NOT undone - fix it here.
        # =====================================================================
        if n_rotate:
            undo_alg = Algs.of_face(source_face.name).prime * n_rotate
            self.debug(f"  [CAGE] Undoing source rotation: {undo_alg}", level=1)
            self.op.play(undo_alg)

        return True

    def _is_valid_and_block_for_search(self, face: Face, color: Color, rc1: Point, rc2: Point):

        is_valid_block = self._is_valid_block(rc1, rc2)

        if not is_valid_block:
            return False

        is_block = self._is_block(face, color, None, rc1, rc2, dont_convert_coordinates=True)

        return is_block

    def _search_big_block(self, face: Face, color: Color) -> Sequence[Tuple[int, Block]] | None:

        """
        Rerun all possible blocks, 1 size too, sorted from big to small
        :param face:
        :param color:
        :return:
        """

        center = face.center

        res: list[Tuple[int, Block]] = []

        n = self.cube.n_slices

        for rc in self._2d_center_iter():

            if center.get_center_slice(rc).color == color:

                # collect also 1 size blocks
                res.append((1, (rc, rc)))

                # now try to extend it over r
                r_max = None
                for r in range(rc[0] + 1, n):

                    if not self._is_valid_and_block_for_search(face, color, rc, (r, rc[1])):
                        break
                    else:
                        r_max = r

                if not r_max:
                    r_max = rc[0]

                # now try to extend it over c
                c_max = None
                for c in range(rc[1] + 1, n):
                    if not self._is_valid_and_block_for_search(face, color, rc, (r_max, c)):
                        break
                    else:
                        c_max = c

                if not c_max:
                    c_max = rc[1]

                size = self._block_size(rc, (r_max, c_max))

                # if size > 1:
                res.append((size, (rc, (r_max, c_max))))

        res = sorted(res, key=lambda s: s[0], reverse=True)
        return res

    def _is_valid_block(self, rc1: Point, rc2: Point):

        r1 = rc1[0]
        c1 = rc1[1]

        r2 = rc2[0]
        c2 = rc2[1]

        rc1_f_rotated = self.rotate_point_clockwise(r1, c1)
        rc2_f_rotated = self.rotate_point_clockwise(r2, c2)

        # the columns ranges must not intersect
        if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
            rc1_f_rotated = self.rotate_point_counterclockwise(r1, c1)
            rc2_f_rotated = self.rotate_point_counterclockwise(r2, c2)

            if self._1_d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
                return False

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

        n, _ = CageCenters._count_colors_on_block_and_tracker(color, source_face, rc1, rc2, ignore_if_back)

        return n

    @staticmethod
    def _count_colors_on_block_and_tracker(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                                           ignore_if_back=False) -> Tuple[int, int]:

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
        _trackers = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                center_slice = source_face.center.get_center_slice((r, c))
                if color == center_slice.color:
                    _count += 1
                if not _trackers and FaceTracker.is_track_slice(center_slice):
                    _trackers += 1

        return _count, _trackers

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

            n, t = self._count_colors_on_block_and_tracker(color, face, (r, 0), (r, nm1), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by communicator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(True, r, n, t > 0)
                _slices.append(_slice)

        for c in columns:

            n, t = self._count_colors_on_block_and_tracker(color, face, (0, c), (nm1, c), ignore_if_back=True)

            if n > 1 or not search_max:  # one is not interesting, will be handled by communicator
                # if we search for minimum than we want zero too
                _slice = _CompleteSlice(False, c, n, t > 0)
                _slices.append(_slice)

        _slices = sorted(_slices, key=lambda s: s.n_matches, reverse=search_max)

        return _slices

    @staticmethod
    def _1_d_intersect(range_1: Tuple[int, int], range_2: Tuple[int, int]):

        """
                 x3--------------x4
           x1--------x2
        :param range_1:  x1, x2
        :param range_2:  x3, x4
        :return:  not ( x3  > x2 or x4 < x1 )
        """

        x1 = range_1[0]
        x2 = range_1[1]
        x3 = range_2[0]
        x4 = range_2[1]

        # after rotation points swap coordinates
        if x1 > x2:
            x1, x2 = x2, x1

        if x3 > x4:
            x3, x4 = x4, x3

        if x3 > x2:
            return False

        if x4 < x1:
            return False

        return True

    def _point_on_source(self, is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if is_back:
            return inv(rc[0]), inv(rc[1])
        else:
            # on up
            return rc

    def _point_on_target(self, source_is_back: bool, rc: Tuple[int, int]) -> Point:

        inv = self.cube.inv

        # the logic here is hard code of the logic in slice rotate
        # it will be broken if cube layout is changed
        # here we assume we work on F, and UP has same coord system as F, and
        # back is mirrored in both direction
        if source_is_back:
            return inv(rc[0]), inv(rc[1])
        else:
            # on up
            return rc

    def _block_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Block:

        return self._point_on_source(is_back, rc1), self._point_on_source(is_back, rc2)

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
                yield r, c

    def _2d_center_iter(self) -> Iterator[Point]:

        """
        Walk on all points in center of size n_slices
        """

        n = self.cube.n_slices

        for r in range(n):
            for c in range(n):
                yield r, c

    @staticmethod
    def _block_size(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> int:
        return (abs(rc2[0] - rc1[0]) + 1) * (abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def _block_size2(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> Tuple[int, int]:
        return (abs(rc2[0] - rc1[0]) + 1), (abs(rc2[1] - rc1[1]) + 1)

    def _is_block(self,
                  source_face: Face,
                  required_color: Color,
                  min_points: int | None,
                  rc1: Tuple[int, int], rc2: Tuple[int, int],
                  dont_convert_coordinates: bool = False) -> bool:

        """

        :param source_face:
        :param required_color:
        :param min_points: If None that all block , min = block size
        :param rc1:
        :param rc2:
        :param dont_convert_coordinates if True then don't convert coordinates according to source face
        :return:
        """

        # Number of points in block
        _max = self._block_size(rc1, rc2)

        if min_points is None:
            min_points = _max

        max_allowed_not_match = _max - min_points  # 0 in cas emin is max

        center = source_face.center
        miss_count = 0

        if dont_convert_coordinates:
            _range = self._2d_range(rc1, rc2)
        else:
            _range = self._2d_range_on_source(source_face is source_face.cube.back, rc1, rc2)

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
                      rc1: Tuple[int, int], rc2: Tuple[int, int]) -> int | None:

        """
        Search block according to mode, if target is already satisfied, then return not found
        :param source_face:
        :param required_color:
        :param mode:
        :param rc1:
        :param rc2:
        :return: How many source clockwise rotate in order to match the block to source
        """

        block_size = self._block_size(rc1, rc2)

        n_ok = self._count_colors_on_block(required_color, target_face, rc1, rc2)

        if n_ok == block_size:
            return None  # nothing to do

        if mode == _SearchBlockMode.CompleteBlock:
            min_required = block_size
        elif mode == _SearchBlockMode.BigThanSource:
            # The number of communicators before > after
            # before = size - n_ok
            # after  = n_ok  - because the need somehow to get back
            # size-n_ok > n_ok
            min_required = n_ok + 1
        elif mode == _SearchBlockMode.ExactMatch:
            if n_ok:
                return None
            min_required = block_size

        else:
            raise InternalSWError

        cube = self.cube

        for n in range(4):
            if self._is_block(source_face, required_color, min_required, rc1, rc2):
                # we rotate n to find the block, so client need to rotate -n
                return (-n) % 4
            rc1 = cube.cqr.rotate_point_clockwise(rc1)
            rc2 = cube.cqr.rotate_point_clockwise(rc2)

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

    D_LEVEL = 3
