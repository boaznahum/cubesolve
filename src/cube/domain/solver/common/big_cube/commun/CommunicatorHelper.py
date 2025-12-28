"""
Communicator Helper for NxN Big Cubes.

Provides the block commutator algorithm for any source/target face pair.
Unlike NxNCenters which only supports Front as target and Up/Back as source,
this helper supports all 30 face pair combinations.

Coordinate system: Bottom-Up, Left-to-Right (BULR/LTR)
- (0,0) is at bottom-left
- Y increases upward (ltr_y)
- X increases rightward (ltr_x)
"""
import sys
from dataclasses import dataclass
from typing import Tuple, TypeAlias

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.algs import Algs, Alg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.model import FaceName, Cube
from cube.domain.model.Face import Face
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult, SliceAlgorithmResult
from cube.domain.model.SliceName import SliceName
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.big_cube.commun._supported_faces import _get_supported_pairs
from cube.domain.solver.protocols import SolverElementsProvider

Point: TypeAlias = Tuple[int, int]  # row , column
Block: TypeAlias = Tuple[Point, Point]


@dataclass(frozen=True)
class _InternalCommData:
    source_coordinate: Point  # point on the source from where communicator will bring the data, before source setup alg
    trans_data: FaceTranslationResult


class CommunicatorHelper(SolverElement):
    """
    Helper for the block commutator algorithm on NxN cubes.

    Supports any source/target face pair (30 combinations).
    Executes the commutator WITHOUT first positioning faces.
    Optionally preserves cube state (cage preservation).

    PUBLIC API USES LTR COORDINATES:
    ================================
    All public methods accept LTR (Left-to-Right) coordinates:
    - (0, 0) is at bottom-left corner
    - Y (first value) increases upward
    - X (second value) increases rightward

    The helper handles all coordinate translations internally.
    Clients should NOT use index coordinates directly.

    Key methods:
    - do_communicator(): Execute commutator with LTR block coordinates
    - get_expected_source_ltr(): Map target LTR to source LTR
    - rotate_ltr_on_face(): Rotate LTR on a face (physical rotation)
    - ltr_to_index() / index_to_ltr(): Coordinate translation
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver)

    @property
    def n_slices(self) -> int:
        return self.cube.n_slices

    # =========================================================================
    # Coordinate Translation: LTR <-> Index
    # =========================================================================

    def ltr_to_index(self, face: Face, ltr_y: int, ltr_x: int) -> Point:
        """
        Translate LTR coordinates to center index coordinates.

        Args:
            face: The face to translate for
            ltr_y: Y in LTR system (0 = bottom, increases upward)
            ltr_x: X in LTR system (0 = left, increases rightward)

        Returns:
            (idx_row, idx_col) for use with face.center.get_center_slice()
        """
        idx_row = face.edge_left.get_slice_index_from_ltr_index(face, ltr_y)
        idx_col = face.edge_bottom.get_slice_index_from_ltr_index(face, ltr_x)
        return idx_row, idx_col

    def index_to_ltr(self, face: Face, idx_row: int, idx_col: int) -> Point:
        """
        Translate center index coordinates to LTR coordinates.

        Args:
            face: The face to translate for
            idx_row: Row index from get_center_slice()
            idx_col: Column index from get_center_slice()

        Returns:
            (ltr_y, ltr_x) in LTR system
        """
        ltr_y = face.edge_left.get_ltr_index_from_slice_index(face, idx_row)
        ltr_x = face.edge_bottom.get_ltr_index_from_slice_index(face, idx_col)
        return ltr_y, ltr_x

    def ltr_block_to_index(self, face: Face, ltr_block: Block) -> Block:
        """Translate an LTR block to index coordinates."""
        p1 = self.ltr_to_index(face, ltr_block[0][0], ltr_block[0][1])
        p2 = self.ltr_to_index(face, ltr_block[1][0], ltr_block[1][1])
        return p1, p2

    def get_expected_source_ltr(
            self, source: Face, target: Face, target_ltr: Point
    ) -> Point:
        """

        For debug only, it is done by the communicator

        Get the expected source LTR position for a given target LTR.

        Before the commincator do the source setup algorithm

        This is where the source piece should be (before rotation) to move
        to the target position.

        Args:
            source: Source face
            target: Target face
            target_ltr: Target position in LTR

        Returns:
            Expected source position in LTR on source face
        """

        data = self._do_communicator(source, target, (target_ltr, target_ltr))

        return data.source_coordinate

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _normalize_block(block: Block) -> Block:
        """Normalize block so r1 <= r2 and c1 <= c2."""

        #claude documnet this it is critical

        rc1: Point = block[0]
        rc2 = block[1]

        r1, c1 = block[0]
        r2, c2 = block[0]
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1
        return (r1, c1), (r2, c2)

    @staticmethod
    def _1d_intersect(range_1: tuple[int, int], range_2: tuple[int, int]) -> bool:
        """Check if two 1D ranges intersect."""
        x1, x2 = range_1
        x3, x4 = range_2
        if x1 > x2:
            x1, x2 = x2, x1
        if x3 > x4:
            x3, x4 = x4, x3
        return not (x3 > x2 or x4 < x1)

    def _is_inner_position(self, r: int, c: int) -> bool:
        """
        Check if (r, c) is in the inner 2x2 center of an even cube.

        On even cubes, inner 2x2 positions have adjacent M slices that share
        edge wings. These positions need special M slice ordering.

        - 4x4 (n_slices=2): ALL positions are inner (0,0) to (1,1)
        - 6x6 (n_slices=4): inner is (1,1) to (2,2)
        - 8x8 (n_slices=6): inner is (2,2) to (3,3)
        """
        n = self.n_slices
        if n % 2 != 0:
            return False  # Only even cubes have inner 2x2 issues
        # Inner 2x2 is at [n//2 - 1, n//2] for each dimension
        inner_min = n // 2 - 1
        inner_max = n // 2
        return inner_min <= r <= inner_max and inner_min <= c <= inner_max

    def _get_slice_alg(self, base_slice_alg: SliceAlg,
                       target_block):

        """

        :param target_block_begin_column: Center Slice index [0, n)
        :param target_block_end_column: Center Slice index [0, n)
        :return: m slice in range suitable for [c1, c2]
        """

        #   index is from left to right, L is from left to right,
        # so we don't need to invert

        match base_slice_alg.slice_name:

            case SliceName.M:
                return self._get_slice_m_alg(target_block[0][1], target_block[1][1])

            case SliceName.S:
                return self._get_slice_s_alg(target_block[0][0], target_block[1][0])

            case SliceName.E:
                return self._get_slice_e_alg(target_block[0][0], target_block[1][0])

            case _:
                raise InternalSWError(f"Unknown slice name {base_slice_alg.slice_name}")

    def _get_slice_m_alg(self, c1: int, c2: int):
        """
        Get M slice algorithm for column range.

        Returns M' (prime) for use in commutator pattern. The algorithm uses
        m.prime and m directly, where m = M':
        [m', F, m', F', m, F, m, F'] = [M, F, M, F', M', F, M', F']

        This matches NxNCenters._get_slice_m_alg() behavior.

        Args:
            c1: Center slice index [0, n)
            c2: Center slice index [0, n)

        Returns:
            M' slice algorithm for the range
        """
        if c1 > c2:
            c1, c2 = c2, c1
        # M[n:n] notation works for a single slice at position n
        return Algs.M[c1 + 1:c2 + 1]

    def _get_slice_e_alg(self, r1: int, r2: int):
        """
        Get E slice algorithm for row range.

        Returns E' (prime) for use in commutator pattern. The algorithm uses
        e.prime and e directly, where e = E':
        [e', F, e2', F', e, F, e2, F'] = [E, F, E, F', E', F, E', F']

        This matches the pattern used by _get_slice_m_alg for M slices.

        Args:
            r1: Center slice index [0, n)
            r2: Center slice index [0, n)

        Returns:
            E' slice algorithm for the range
        """
        if r1 > r2:
            r1, r2 = r2, r1
        # E[n:n] notation works for single slice at position n
        return Algs.E[r1 + 1:r2 + 1]

    def _get_slice_s_alg(self, r1: int, r2: int):
        """
        Get S slice algorithm for row range.

        Returns S' (prime) for use in commutator pattern when Right is target.
        The algorithm uses s.prime and s directly, where s = S':
        [s', R, s2', R', s, R, s2, R'] = [S, R, S, R', S', R, S', R']

        S slice follows F direction: U→R→D→L (clockwise looking at F).
        S' direction: U→L→D→R (counter-clockwise looking at F).

        For Right target with Up source: S' brings U→R (since S' moves U→L not U→R)
        Wait, need to verify the direction...

        Actually S (positive) moves: U→R (pieces on U face move to R face)
        So for Up→Right, we need S, not S'.
        But to match the pattern of other methods, we return S' and let the caller
        use .prime to get S.

        Args:
            r1: Center slice index [0, n)
            r2: Center slice index [0, n)

        Returns:
            S' slice algorithm for the range
        """
        if r1 > r2:
            r1, r2 = r2, r1
        # S[n:n] notation works for single slice at position n
        return Algs.S[r1 + 1:r2 + 1]

    def _find_rotation_idx(self, actual_source_idx: Point, expected_source_idx: Point) -> int:
        """
        Find how many clockwise rotations of source face align actual to expected.

        After rotating source face by n_rotate clockwise, the piece at actual_source_idx
        will move to expected_source_idx.

        Args:
            actual_source_idx: Where the piece actually is (index coords)
            expected_source_idx: Where commutator expects it (index coords)

        Returns:
            Number of clockwise rotations (0-3)

        Raises:
            ValueError: If positions cannot be mapped by rotation
        """
        cqr = self.cube.cqr
        for n in range(4):
            # After n clockwise rotations, actual moves to rotated
            rotated = cqr.rotate_point_clockwise(actual_source_idx, n)
            if rotated == expected_source_idx:
                return n
        raise ValueError(
            f"Cannot align {actual_source_idx} to {expected_source_idx} by rotation"
        )

    # =========================================================================
    # Supported Pairs
    # =========================================================================

    def get_supported_pairs(self) -> list[tuple[FaceName, FaceName]]:
        """
        Return list of (source, target) face pairs that are currently supported.

        These are the combinations that do_communicator() can handle.
        Other combinations will raise NotImplementedError.

        Returns:
            List of (source_face, target_face) tuples
        """
        return _get_supported_pairs()

    def is_supported(self, source: Face, target: Face) -> bool:
        """
        Check if a source/target face pair is currently supported.

        Args:
            source: Source face
            target: Target face

        Returns:
            True if this combination is implemented, False otherwise
        """
        for src, tgt in self.get_supported_pairs():
            if source.name is src and target.name is tgt:
                return True
        return False

    def _do_communicator(
            self,
            source_face: Face,
            target_face: Face,
            target_block: Block
    ) -> _InternalCommData:
        """
        Execute a block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source_face: Source face (where pieces come from)
            target_face: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1))
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            True if the communicator was executed, False if not needed

        Raises:
            ValueError: If source and target are the same, face
            ValueError: If blocks cannot be mapped with 0-3 rotations
        """
        if source_face is target_face:
            raise ValueError("Source and target must be different faces")

        # currently we support  only blockof size 1
        assert target_block[0] == target_block[1]

        # Check if this pair is supported
        if not self.is_supported(source_face, target_face):
            raise NotImplementedError(
                f"Face pair ({source_face}, {target_face}) not yet implemented"
            )

        cube = self.cube

        # Convert LTR to index coordinates
        # claude see a new document, face is always ltt, no need to convert
        # target_idx_block = self.ltr_block_to_index(target, target_block)

        # now we assume block of size 1
        target_point_begin: Point = target_block[0]

        # try a new algorithm
        translation_result: FaceTranslationResult = Face2FaceTranslator.translate(target_face, source_face,
                                                                                  target_point_begin)

        new_expected_source_1_point = translation_result.source_coord

        return _InternalCommData(translation_result.source_coord, translation_result)

    def _compute_rotate_on_target(self, cube: Cube,
                                  face_name: FaceName,
                                  slice_name: SliceName, target_block: Block) -> Tuple[int, Block]:

        """

        :param cube:
        :param target_block:
        :param slice_name: the slice thet is used to do th epeuce move from source to target
        :return: [n times to roate, targte blcok after rotate]
        """

        def exc(point: Point) -> int:
            # extract column
            return point[1]

        def exr(point: Point) -> int:
            # extract row
            return point[0]

        # claude what is the Mathematica of this ???
        if slice_name == SliceName.M:
            ex = exc  # slice cut the row so we check column

        elif slice_name == SliceName.E:
            ex = exr  # slice cut the column so we check row

        elif slice_name == SliceName.S:

            if face_name == FaceName.R:
                # slice cut the rows so we take columns like in M
                ex = exc
            else:
                ex = exr

        else:
            assert False

        target_point_begin = target_block[0]
        target_point_end = target_block[1]

        cqr = cube.cqr
        target_begin_rotated_cw = cqr.rotate_point_clockwise(target_point_begin)
        target_end_rotated_cw = cqr.rotate_point_clockwise(target_point_end)

        if self._1d_intersect((ex(target_point_begin), ex(target_point_end)),
                              (ex(target_begin_rotated_cw), ex(target_end_rotated_cw))):

            on_front_rotate = -1
            target_begin_rotated_ccw = cqr.rotate_point_counterclockwise(target_point_begin)
            target_end_rotated_ccw = cqr.rotate_point_counterclockwise(target_point_end)

            target_block_after_rotate = (target_begin_rotated_ccw, target_end_rotated_ccw)

            if self._1d_intersect((ex(target_point_begin), ex(target_point_end)),
                                  (ex(target_begin_rotated_ccw), ex(target_begin_rotated_ccw))):
                print("Intersection still exists after rotation", file=sys.stderr)
                raise InternalSWError(f"Intersection still exists after rotation "

                                      f"target={target_block}"
                                      f"r={(target_point_begin[1], target_point_end[1])} "
                                      f"rcw{(target_begin_rotated_cw[1], target_end_rotated_cw[1])} "
                                      f"{(target_end_rotated_ccw[1], target_end_rotated_ccw[1])} ")
        else:
            # clockwise is OK
            target_block_after_rotate = (target_begin_rotated_cw, target_end_rotated_cw)
            on_front_rotate = 1

        return on_front_rotate, target_block_after_rotate

    def do_communicator(
            self,
            source_face: Face,
            target_face: Face,
            target_block: Block,
            source_block: Block | None = None,
            preserve_state: bool = True
    ) -> Alg:
        """
        Execute a block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source_face: Source face (where pieces come from)
            target_face: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1))
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            True if the communicator was executed, False if not needed

        Raises:
            ValueError: If source and target are the same, face
            ValueError: If blocks cannot be mapped with 0-3 rotations
        """
        if source_face is target_face:
            raise ValueError("Source and target must be different faces")

        source_block_was_none = source_block is None
        if source_block_was_none:
            source_block = target_block

        # currently we support  only blockof size 1
        assert source_block[0] == source_block[1]
        assert target_block[0] == target_block[1]

        # Check if this pair is supported
        if not self.is_supported(source_face, target_face):
            raise NotImplementedError(
                f"Face pair ({source_face}, {target_face}) not yet implemented"
            )

        cube = self.cube

        # Convert LTR to index coordinates
        # claude see a new document, face is always ltt, no need to convert
        # target_idx_block = self.ltr_block_to_index(target, target_block)

        source_block_normalized = self._normalize_block(source_block)
        target_block_normalized = self._normalize_block(target_block)

        # now we assume a block of size 1
        source_1_point: Point = source_block[0]
        target_point_begin: Point = target_block[0]
        target_point_end: Point = target_block[1]

        internal_data = self._do_communicator(source_face, target_face, target_block)

        # Find rotation to align the actual source to the expected source
        expected_source_1_point: Point = internal_data.source_coordinate

        source_setup_n_rotate = self._find_rotation_idx(source_1_point, expected_source_1_point)

        source_setup_alg = Algs.of_face(
            source_face.name) * source_setup_n_rotate if source_setup_n_rotate else Algs.NOOP

        # E, S, M
        slice_alg_data: SliceAlgorithmResult = internal_data.trans_data.slice_algorithms[0]
        slice_base_alg: SliceAlg = slice_alg_data.whole_slice_alg

        on_front_rotate_n, target_block_after_rotate = \
            self._compute_rotate_on_target(cube, target_face.name, slice_base_alg.slice_name, target_block)

        on_front_rotate: Alg = Algs.of_face(target_face.name) * on_front_rotate_n

        # build the communicator

        # we want to slice on the target
        inner_slice_alg: Alg = self._get_slice_alg(slice_base_alg, target_block) * slice_alg_data.n
        second_inner_slice_alg: Alg = self._get_slice_alg(slice_base_alg, target_block_after_rotate) * slice_alg_data.n

        # 4x4 U -> F, 0,0
        # M[2] F' M[1] F M[2]' F ' M[1]'
        cum = Algs.seq_alg(None,
                           inner_slice_alg,  # M[2]
                           on_front_rotate,  # F'
                           second_inner_slice_alg,  # M[1]
                           on_front_rotate.prime,  # F
                           inner_slice_alg.prime,  # M[2]
                           on_front_rotate,  # F'
                           second_inner_slice_alg.prime,  # M[1]'
                           on_front_rotate.prime  # F
                           )

        if source_setup_n_rotate:
            self.op.play(source_setup_alg)
        self.op.play(cum)

        # =========================================================
        # CAGE METHOD: Undo source rotation to preserve paired edges
        # =========================================================
        # The commutator itself is balanced (F rotations cancel out).
        # But the source face rotation setup is NOT balanced - undo it.
        if preserve_state and source_setup_n_rotate:
            self.op.play(source_setup_alg.prime)

        return (source_setup_alg + cum + source_setup_alg.prime).simplify()

    def _build_front_target_commutator(
            self,
            source: Face,
            rc1: Point,
            rc2: Point,
            r1: int,
            r2: int,
            c1: int,
            c2: int
    ) -> list:
        """Build commutator for Front as target face."""
        cube = self.cube

        # Detect source type for algorithm selection
        is_left = source is cube.left
        is_right = source is cube.right
        uses_e_slice = is_left or is_right

        if uses_e_slice:
            # E-based algorithm for Left/Right sources
            # E slice operates on rows, so check row intersection

            rc1_f_cw = cube.cqr.rotate_point_clockwise(rc1)
            rc2_f_cw = cube.cqr.rotate_point_clockwise(rc2)

            if self._1d_intersect((r1, r2), (rc1_f_cw[0], rc2_f_cw[0])):
                # Clockwise causes row intersection, use counter-clockwise
                on_front_rotate = Algs.F.prime
                rc1_f_rotated = cube.cqr.rotate_point_counterclockwise(rc1)
                rc2_f_rotated = cube.cqr.rotate_point_counterclockwise(rc2)
            else:
                on_front_rotate = Algs.F
                rc1_f_rotated = rc1_f_cw
                rc2_f_rotated = rc2_f_cw

            # Get E slice algorithms for the rows
            rotate_on_cell = self._get_slice_e_alg(r1, r2)
            rotate_on_second = self._get_slice_e_alg(rc1_f_rotated[0], rc2_f_rotated[0])

            if is_left:
                # Left: E brings L→F
                # Algorithm structure mirrors Up→Front but with E instead of M
                return [
                    rotate_on_cell.prime,  # E
                    on_front_rotate,
                    rotate_on_second.prime,  # E
                    on_front_rotate.prime,
                    rotate_on_cell,  # E'
                    on_front_rotate,
                    rotate_on_second,  # E'
                    on_front_rotate.prime
                ]
            else:
                # Right: E' brings R→F (swap E and E')
                return [
                    rotate_on_cell,  # E'
                    on_front_rotate,
                    rotate_on_second,  # E'
                    on_front_rotate.prime,
                    rotate_on_cell.prime,  # E
                    on_front_rotate,
                    rotate_on_second.prime,  # E
                    on_front_rotate.prime
                ]
        else:
            # M-based algorithm for Up/Down/Back sources

            # Determine F rotation direction to avoid column intersection
            # After rotating F, the block moves. Columns must not intersect.
            rc1_f_cw = cube.cqr.rotate_point_clockwise(rc1)
            rc2_f_cw = cube.cqr.rotate_point_clockwise(rc2)
            rc1_f_ccw = cube.cqr.rotate_point_counterclockwise(rc1)
            rc2_f_ccw = cube.cqr.rotate_point_counterclockwise(rc2)

            cw_intersect = self._1d_intersect((c1, c2), (rc1_f_cw[1], rc2_f_cw[1]))
            ccw_intersect = self._1d_intersect((c1, c2), (rc1_f_ccw[1], rc2_f_ccw[1]))

            # Choose F direction based on no column intersection
            if not cw_intersect:
                on_front_rotate = Algs.F
                rotated_col = rc1_f_cw[1]
            elif not ccw_intersect:
                on_front_rotate = Algs.F.prime
                rotated_col = rc1_f_ccw[1]
            else:
                # BOTH directions cause intersection - inner position on even cube
                # Choose F direction based on M slice ordering rule:
                # - F': inner slice first (when c1 is inner, i.e., c1 < rotated_col)
                # - F: outer slice first (when c1 is outer, i.e., c1 > rotated_col)
                # This prevents M slices from "crossing over" each other
                if rc1_f_ccw[1] > c1:
                    # With F', rotated_col > c1, so c1 is inner (closer to center)
                    # F' gives us inner-first ordering naturally
                    on_front_rotate = Algs.F.prime
                    rotated_col = rc1_f_ccw[1]
                else:
                    # With F, rotated_col < c1, so c1 is outer
                    # F gives us outer-first ordering naturally
                    on_front_rotate = Algs.F
                    rotated_col = rc1_f_cw[1]

            # Get M slice algorithms matching NxNCenters behavior
            rotate_on_cell = self._get_slice_m_alg(c1, c2)
            rotate_on_second = self._get_slice_m_alg(rotated_col, rotated_col)

            # M slice handling based on source face
            is_down = source is cube.down
            is_back = source is cube.back

            if is_back:
                # Back: double M moves (180°)
                rotate_mul = 2
                return [
                    rotate_on_cell.prime * rotate_mul,
                    on_front_rotate,
                    rotate_on_second.prime * rotate_mul,
                    on_front_rotate.prime,
                    rotate_on_cell * rotate_mul,
                    on_front_rotate,
                    rotate_on_second * rotate_mul,
                    on_front_rotate.prime
                ]
            elif is_down:
                # Down: M (not M') brings Down→Front
                return [
                    rotate_on_cell,  # M (instead of M')
                    on_front_rotate,
                    rotate_on_second,  # M (instead of M')
                    on_front_rotate.prime,
                    rotate_on_cell.prime,  # M' (instead of M)
                    on_front_rotate,
                    rotate_on_second.prime,  # M' (instead of M)
                    on_front_rotate.prime
                ]
            else:
                # Up: standard algorithm
                return [
                    rotate_on_cell.prime,
                    on_front_rotate,
                    rotate_on_second.prime,
                    on_front_rotate.prime,
                    rotate_on_cell,
                    on_front_rotate,
                    rotate_on_second,
                    on_front_rotate.prime
                ]

    def _build_right_target_commutator(
            self,
            source: Face,
            rc1: Point,
            rc2: Point,
            r1: int,
            r2: int,
            c1: int,
            c2: int
    ) -> list:
        """
        Build commutator for Right as target face.

        For Right target:
        - Up/Down sources: use S slices and R rotation
        - Front/Back/Left sources: use E slices and R rotation
        """
        cube = self.cube

        # For Right target, we use R rotation instead of F
        # S slice moves pieces between Up/Right/Down/Left (like M for Front target)
        # E slice moves pieces between Front/Right/Back/Left (like E for Front target)

        is_up = source is cube.up
        is_down = source is cube.down
        is_front = source is cube.front
        is_back = source is cube.back
        is_left = source is cube.left

        uses_s_slice = is_up or is_down

        if uses_s_slice:
            # S-based algorithm for Up/Down sources
            # S slice operates on rows (from Right face perspective), check row intersection

            rc1_r_cw = cube.cqr.rotate_point_clockwise(rc1)
            rc2_r_cw = cube.cqr.rotate_point_clockwise(rc2)
            rc1_r_ccw = cube.cqr.rotate_point_counterclockwise(rc1)
            rc2_r_ccw = cube.cqr.rotate_point_counterclockwise(rc2)

            # For S slice, we check row intersection (S operates on rows)
            cw_intersect = self._1d_intersect((r1, r2), (rc1_r_cw[0], rc2_r_cw[0]))
            ccw_intersect = self._1d_intersect((r1, r2), (rc1_r_ccw[0], rc2_r_ccw[0]))

            if not cw_intersect:
                on_right_rotate = Algs.R
                rotated_row = rc1_r_cw[0]
            elif not ccw_intersect:
                on_right_rotate = Algs.R.prime
                rotated_row = rc1_r_ccw[0]
            else:
                raise ValueError(
                    f"Position ({r1},{c1}) cannot be handled: both R and R' cause "
                    f"row intersection. This is a limitation of the commutator "
                    f"algorithm for inner positions on even cubes."
                )

            # Get S slice algorithms for the rows
            rotate_on_cell = self._get_slice_s_alg(r1, r2)
            rotate_on_second = self._get_slice_s_alg(rotated_row, rotated_row)

            if is_up:
                # Up→Right: S brings U→R
                # Algorithm: [s', R, s2', R', s, R, s2, R']
                # where s = S' from _get_slice_s_alg, so s' = S
                return [
                    rotate_on_cell.prime,  # S
                    on_right_rotate,
                    rotate_on_second.prime,  # S
                    on_right_rotate.prime,
                    rotate_on_cell,  # S'
                    on_right_rotate,
                    rotate_on_second,  # S'
                    on_right_rotate.prime
                ]
            else:
                # Down→Right: S' brings D→R (invert primes like Down→Front)
                return [
                    rotate_on_cell,  # S' (instead of S)
                    on_right_rotate,
                    rotate_on_second,  # S' (instead of S)
                    on_right_rotate.prime,
                    rotate_on_cell.prime,  # S (instead of S')
                    on_right_rotate,
                    rotate_on_second.prime,  # S (instead of S')
                    on_right_rotate.prime
                ]
        else:
            # E-based algorithm for Front/Back/Left sources
            # E slice operates on columns (from Right face perspective)

            rc1_r_cw = cube.cqr.rotate_point_clockwise(rc1)
            rc2_r_cw = cube.cqr.rotate_point_clockwise(rc2)
            rc1_r_ccw = cube.cqr.rotate_point_counterclockwise(rc1)
            rc2_r_ccw = cube.cqr.rotate_point_counterclockwise(rc2)

            # For E slice affecting Right, we check column intersection
            cw_intersect = self._1d_intersect((c1, c2), (rc1_r_cw[1], rc2_r_cw[1]))
            ccw_intersect = self._1d_intersect((c1, c2), (rc1_r_ccw[1], rc2_r_ccw[1]))

            if not cw_intersect:
                on_right_rotate = Algs.R
                rotated_col = rc1_r_cw[1]
            elif not ccw_intersect:
                on_right_rotate = Algs.R.prime
                rotated_col = rc1_r_ccw[1]
            else:
                raise ValueError(
                    f"Position ({r1},{c1}) cannot be handled: both R and R' cause "
                    f"column intersection. This is a limitation of the commutator "
                    f"algorithm for inner positions on even cubes."
                )

            # Get E slice algorithms for the columns
            # Note: E slice for Right target uses column, unlike E for Front target which uses row
            rotate_on_cell = self._get_slice_e_alg(c1, c2)
            rotate_on_second = self._get_slice_e_alg(rotated_col, rotated_col)

            if is_front:
                # Front→Right: E' brings F→R
                # Use inverted primes (like Right→Front)
                return [
                    rotate_on_cell,  # E'
                    on_right_rotate,
                    rotate_on_second,  # E'
                    on_right_rotate.prime,
                    rotate_on_cell.prime,  # E
                    on_right_rotate,
                    rotate_on_second.prime,  # E
                    on_right_rotate.prime
                ]
            elif is_back:
                # Back→Right: E brings B→R
                return [
                    rotate_on_cell.prime,  # E
                    on_right_rotate,
                    rotate_on_second.prime,  # E
                    on_right_rotate.prime,
                    rotate_on_cell,  # E'
                    on_right_rotate,
                    rotate_on_second,  # E'
                    on_right_rotate.prime
                ]
            else:
                # Left→Right: E2 brings L→R (180°)
                rotate_mul = 2
                return [
                    rotate_on_cell.prime * rotate_mul,
                    on_right_rotate,
                    rotate_on_second.prime * rotate_mul,
                    on_right_rotate.prime,
                    rotate_on_cell * rotate_mul,
                    on_right_rotate,
                    rotate_on_second * rotate_mul,
                    on_right_rotate.prime
                ]
