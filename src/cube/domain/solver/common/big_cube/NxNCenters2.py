import sys
from collections.abc import Iterator
from enum import Enum, unique
from typing import Tuple, TypeAlias

from cube.domain import algs
from cube.domain.algs import Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import CenterSlice, Color
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.tracker._base import FaceTracker
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider

Point: TypeAlias = Tuple[int, int]


@unique
class _SearchBlockMode(Enum):
    CompleteBlock = 1
    BigThanSource = 2
    ExactMatch = 3  # required on source match source


class NxNCenters2(SolverElement):
    """
    Solves center pieces on NxN cubes (N > 3) using block commutators.

    This solver brings center pieces from source faces to target faces using
    single-piece or block commutators (3-cycle of center pieces).

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
    - In _block_communicator: source_face * n_rotate to align blocks

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
        play(source_face * n_rotate)  # Setup: align block
        play(commutator)              # Balanced, corners return
        # Setup is NOT undone - corners are permanently rotated

    With preserve_cage (cage method):
        play(source_face * n_rotate)  # Setup: align block
        play(commutator)              # Balanced, corners return
        play(source_face' * n_rotate) # UNDO: restore corners
    """

    def __init__(
            self,
            slv: SolverElementsProvider,
            preserve_cage: bool = False,
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
        """
        super().__init__(slv)

        self._preserve_cage = preserve_cage

    def debug(self, *args, level=3):
        if level <= NxNCenters2.D_LEVEL:
            super().debug("NxX Centers:", args)

    def solve_single_center_row_slice(
            self, face_tracker: FaceTracker, row_slice_index: int
    ) -> None:
        """
        Solve a single row of center pieces on a face.

        Uses block commutators to bring pieces from source faces.
        Properly handles cage preservation if preserve_cage=True.

        Args:
            face_tracker: Face to solve
            row_slice_index: Row index to solve
        """
        self._solve_single_center_row_slice(face_tracker, row_slice_index)

    def _solve_single_center_row_slice(self, target_face: FaceTracker, slice_row_index: int):

        source_faces = target_face.other_faces()

        for source_face in source_faces:
            self._solve_single_center_piece_from_source_face(target_face, source_face, slice_row_index)

    def _solve_single_center_piece_from_source_face(self, face: FaceTracker, source_face: FaceTracker,
                                                    slice_row_index: int) -> bool:
        """
        Solve center pieces from a specific source face.

        The target face is brought to front, source face to up or back,
        then block commutators are used to move pieces.

        :param face: target face tracker
        :param source_face: source face tracker
        :param slice_row_index: row index to solve
        :return: True if work was done
        """
        self.cmn.bring_face_front(face.face)

        if source_face is not face.opposite:
            self.cmn.bring_face_up_preserve_front(source_face.face)

        cube = self.cube

        assert face.face is cube.front
        assert source_face.face in [cube.up, cube.back]

        color = face.color

        if self.count_color_on_face(source_face.face, color) == 0:
            return False  # nothing can be done here

        work_done = False

        for rc in self._2d_center_row_slice_iter(slice_row_index):

            if self._block_communicator(color,
                                        face.face,
                                        source_face.face,
                                        rc, rc,
                                        _SearchBlockMode.CompleteBlock):

                after_fixed_color = face.face.center.get_center_slice(rc).color

                if after_fixed_color != color:
                    raise InternalSWError(f"Slice was not fixed {rc}, " +
                                          f"required={color}, " +
                                          f"actual={after_fixed_color}")

                self.debug(f"Fixed slice {rc}")

                work_done = True

        # now check is there slice on my target

        return work_done

    def _block_communicator(self,
                            required_color: Color,
                            face: Face, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                            mode: _SearchBlockMode) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        CAGE METHOD (preserve_cage=True):
        =================================
        The commutator itself is balanced, but the SOURCE ROTATION setup move
        (line: source_face * n_rotate) is NOT balanced. This permanently moves corners.
        With preserve_cage=True: We undo this rotation after the commutator.

        WHY THE COMMUTATOR IS BALANCED - VISUAL:
        ----------------------------------------
        The commutator cycles 3 positions:

           Source (UP)          Front (F)
           +-+-+-+              +-+-+-+
           | |A| |              | |C| |
           +-+-+-+              +-+-+-+
           | | | |              | | | |
           +-+-+-+              +-+-+-+
           | | | |              | |B| |
           +-+-+-+              +-+-+-+

        After [M', F, M', F', M, F, M, F']:
        - A (from UP) -> C position (on F)
        - C (from F)  -> B position (on F after rotation)
        - B (from F)  -> A position (on UP)

        The F rotations happen in pairs: F + F' and F + F' = 0 net rotation.
        So corners end up back where they started.

        BUT: If we first played source_face * n_rotate to align the block,
        that rotation is NOT undone by the commutator. We must undo it manually.

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

        # center indexes are in opposite direction of R
        #   index is from left to right, R is from right to left
        rotate_on_cell = self._get_slice_m_alg(rc1[1], rc2[1])
        rotate_on_second = self._get_slice_m_alg(rc1_f_rotated[1], rc2_f_rotated[1])

        if is_back:
            rotate_mul = 2
        else:
            rotate_mul = 1

        cum = [rotate_on_cell.prime * rotate_mul,
               on_front_rotate,
               rotate_on_second.prime * rotate_mul,
               on_front_rotate.prime,
               rotate_on_cell * rotate_mul,
               on_front_rotate,
               rotate_on_second * rotate_mul,
               on_front_rotate.prime]

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

        # =========================================================
        # CAGE METHOD: Undo source rotation to preserve paired edges
        # =========================================================
        # The commutator itself is balanced (F rotations cancel out).
        # But the source face rotation setup is NOT balanced - undo it.
        if self._preserve_cage and n_rotate:
            undo_alg = Algs.of_face(source_face.name).prime * n_rotate
            undo_alg = undo_alg.simplify()
            self.debug(f"  [CAGE] Undoing source rotation: {undo_alg}", level=1)
            self.op.play(undo_alg)

        return True

    def count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)

    @staticmethod
    def _count_colors_on_block(color: Color, source_face: Face, rc1: Tuple[int, int], rc2: Tuple[int, int],
                               ignore_if_back=False) -> int:
        """Count center pieces in block that match color."""
        cube = source_face.cube
        fix_back_coords = not ignore_if_back and source_face is cube.back

        if fix_back_coords:
            inv = cube.inv
            rc1 = (inv(rc1[0]), inv(rc1[1]))
            rc2 = (inv(rc2[0]), inv(rc2[1]))

        r1, c1 = rc1
        r2, c2 = rc2

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        _count = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if source_face.center.get_center_slice((r, c)).color == color:
                    _count += 1

        return _count

    @staticmethod
    def _1_d_intersect(range_1: Tuple[int, int], range_2: Tuple[int, int]) -> bool:
        """
        Check if two 1D ranges intersect.

                 x3--------------x4
           x1--------x2
        :param range_1:  x1, x2
        :param range_2:  x3, x4
        :return:  not ( x3  > x2 or x4 < x1 )
        """
        x1, x2 = range_1
        x3, x4 = range_2

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
        """Convert point coordinates for source face (handles back face mirroring)."""
        inv = self.cube.inv
        if is_back:
            return inv(rc[0]), inv(rc[1])
        else:
            return rc

    def _2d_range_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Iterator[Point]:
        """
        Iterator over 2d block, converting to source coordinates.

        :param rc1: one corner of block, front coords
        :param rc2: other corner of block, front coords
        """
        rc1 = self._point_on_source(is_back, rc1)
        rc2 = self._point_on_source(is_back, rc2)
        yield from self._2d_range(rc1, rc2)

    @staticmethod
    def _2d_range(rc1: Point, rc2: Point) -> Iterator[Point]:
        """Iterator over 2d block (columns advance faster)."""
        r1, c1 = rc1
        r2, c2 = rc2

        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield r, c

    def _2d_center_row_slice_iter(self, slice_index: int) -> Iterator[Point]:
        """Iterate over all columns in a specific row."""
        n = self.cube.n_slices
        for c in range(n):
            yield slice_index, c

    @staticmethod
    def _block_size(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> int:
        """Calculate number of pieces in a block."""
        return (abs(rc2[0] - rc1[0]) + 1) * (abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def _block_size2(rc1: Tuple[int, int], rc2: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate block dimensions (rows, cols)."""
        return (abs(rc2[0] - rc1[0]) + 1), (abs(rc2[1] - rc1[1]) + 1)

    def _is_block(self,
                  source_face: Face,
                  required_color: Color,
                  min_points: int | None,
                  rc1: Tuple[int, int], rc2: Tuple[int, int],
                  dont_convert_coordinates: bool = False) -> bool:
        """
        Check if a block contains enough pieces of required color.

        :param source_face: face to check
        :param required_color: color to match
        :param min_points: minimum matches required (None = all)
        :param rc1: one corner of block
        :param rc2: other corner of block
        :param dont_convert_coordinates: if True, don't adjust for back face
        :return: True if block has enough matching pieces
        """
        _max = self._block_size(rc1, rc2)

        if min_points is None:
            min_points = _max

        max_allowed_not_match = _max - min_points

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
        Search for matching block on source face.

        :param target_face: face to solve
        :param source_face: face to search on
        :param required_color: color to find
        :param mode: search mode (CompleteBlock, BigThanSource, ExactMatch)
        :param rc1: one corner of block
        :param rc2: other corner of block
        :return: Number of clockwise rotations needed, or None if not found
        """
        block_size = self._block_size(rc1, rc2)

        n_ok = self._count_colors_on_block(required_color, target_face, rc1, rc2)

        if n_ok == block_size:
            return None  # nothing to do

        if mode == _SearchBlockMode.CompleteBlock:
            min_required = block_size
        elif mode == _SearchBlockMode.BigThanSource:
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
                return (-n) % 4
            rc1 = cube.cqr.rotate_point_clockwise(rc1)
            rc2 = cube.cqr.rotate_point_clockwise(rc2)

        return None

    def rotate_point_clockwise(self, row: int, column: int, n: int = 1) -> Tuple[int, int]:
        return self.cube.cqr.rotate_point_clockwise((row, column), n)

    def rotate_point_counterclockwise(self, row: int, column: int, n: int = 1) -> Tuple[int, int]:
        return self.cube.cqr.rotate_point_counterclockwise((row, column), n)

    def _get_slice_m_alg(self, c1: int, c2: int) -> algs.Alg:
        """
        Get M slice algorithm for column range.

        :param c1: Center Slice index [0, n)
        :param c2: Center Slice index [0, n)
        :return: M slice algorithm for [c1, c2]
        """
        if c1 > c2:
            c1, c2 = c2, c1

        return Algs.M[c1 + 1:c2 + 1].prime

    D_LEVEL = 3
