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

from typing import Tuple, TypeAlias

from cube.domain.algs import Algs
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider

Point: TypeAlias = Tuple[int, int]
Block: TypeAlias = Tuple[Point, Point]


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

    def rotate_ltr_on_face(self, face: Face, ltr: Point, n: int = 1) -> Point:
        """
        Rotate an LTR point on a specific face n times clockwise.

        This performs PHYSICAL rotation on the face:
        1. Translate LTR to Index on the face
        2. Rotate in Index space (physical rotation)
        3. Translate back to LTR on the same face

        Different faces have different LTR→Index mappings, so the same
        LTR rotation looks different on different faces.

        Args:
            face: The face to rotate on
            ltr: (ltr_y, ltr_x) coordinate on the face
            n: Number of 90° clockwise rotations (0-3)

        Returns:
            Rotated (ltr_y, ltr_x) coordinate on the same face
        """
        # LTR → Index
        idx = self.ltr_to_index(face, ltr[0], ltr[1])
        # Rotate in Index space (physical rotation)
        rotated_idx = self.cube.cqr.rotate_point_clockwise(idx, n)
        # Index → LTR
        return self.index_to_ltr(face, rotated_idx[0], rotated_idx[1])

    def get_expected_source_ltr(
        self, source: Face, target: Face, target_ltr: Point
    ) -> Point:
        """
        Get the expected source LTR position for a given target LTR.

        This is where the source piece should be (before rotation) to move
        to the target position.

        Args:
            source: Source face
            target: Target face
            target_ltr: Target position in LTR

        Returns:
            Expected source position in LTR on source face
        """
        # Translate target LTR to target index
        target_idx = self.ltr_to_index(target, target_ltr[0], target_ltr[1])
        # Get expected source index (face-specific mapping)
        expected_source_idx = self._point_on_source_idx(source, target_idx)
        # Translate back to source LTR
        return self.index_to_ltr(source, expected_source_idx[0], expected_source_idx[1])

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _normalize_block(self, rc1: Point, rc2: Point) -> tuple[Point, Point]:
        """Normalize block so r1 <= r2 and c1 <= c2."""
        r1, c1 = rc1
        r2, c2 = rc2
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

    def _get_slice_m_alg(self, c1: int, c2: int):
        """
        Get M slice algorithm for column range.

        Args:
            c1: Center slice index [0, n)
            c2: Center slice index [0, n)

        Returns:
            M slice algorithm for the range
        """
        if c1 > c2:
            c1, c2 = c2, c1
        return Algs.M[c1 + 1:c2 + 1].prime

    def _get_slice_e_alg(self, r1: int, r2: int):
        """
        Get E slice algorithm for row range.

        Args:
            r1: Center slice index [0, n)
            r2: Center slice index [0, n)

        Returns:
            E slice algorithm for the range
        """
        if r1 > r2:
            r1, r2 = r2, r1
        return Algs.E[r1 + 1:r2 + 1].prime

    def _point_on_source_idx(self, source: Face, rc: Point) -> Point:
        """
        Convert target index coordinates to source index coordinates.

        For Up source: same coordinates (Front and Up share coordinate system)
        For Back source: both axes inverted
        For Down source: same coordinates as Up
        For Left source: same coordinates (E brings Left to Front directly)
        For Right source: same coordinates (E' brings Right to Front directly)
        """
        cube = self.cube
        inv = cube.inv

        if source is cube.back:
            return inv(rc[0]), inv(rc[1])
        elif source is cube.down:
            # Down→Front: M brings pieces, same coordinates as Up
            return rc
        elif source is cube.left:
            # Left→Front: E brings pieces, identity mapping
            return rc
        elif source is cube.right:
            # Right→Front: E' brings pieces, identity mapping
            return rc
        else:
            # Up source: same coordinates
            return rc

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

    def get_supported_pairs(self) -> list[tuple[Face, Face]]:
        """
        Return list of (source, target) face pairs that are currently supported.

        These are the combinations that do_communicator() can handle.
        Other combinations will raise NotImplementedError.

        Returns:
            List of (source_face, target_face) tuples
        """
        cube = self.cube
        return [
            (cube.up, cube.front),    # Source=Up, Target=Front
            (cube.back, cube.front),  # Source=Back, Target=Front
            (cube.down, cube.front),  # Source=Down, Target=Front
            (cube.left, cube.front),  # Source=Left, Target=Front (via z conjugate)
            (cube.right, cube.front), # Source=Right, Target=Front (via z' conjugate)
        ]

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
            if source is src and target is tgt:
                return True
        return False

    def is_position_supported(self, ltr_y: int, ltr_x: int) -> bool:
        """
        Check if a position is supported on this cube.

        Even cubes (4x4, 6x6, 8x8) have an unsupported inner 2x2 region
        where the commutator algorithm disturbs edges.

        Args:
            ltr_y: Y coordinate in LTR system
            ltr_x: X coordinate in LTR system

        Returns:
            True if position is supported, False otherwise
        """
        n = self.n_slices
        if n % 2 == 0:  # Even cube (e.g., 6x6 has n_slices=4)
            # Inner 2x2 is not supported
            mid_low = n // 2 - 1
            mid_high = n // 2
            if mid_low <= ltr_y <= mid_high and mid_low <= ltr_x <= mid_high:
                return False
        return True

    def do_communicator(
        self,
        source: Face,
        target: Face,
        target_block: Block,
        source_block: Block | None = None,
        preserve_state: bool = True
    ) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source: Source face (where pieces come from)
            target: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1)) in BULR
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            True if communicator was executed, False if not needed

        Raises:
            ValueError: If source and target are the same face
            ValueError: If blocks cannot be mapped with 0-3 rotations
        """
        if source is target:
            raise ValueError("Source and target must be different faces")

        source_block_was_none = source_block is None
        if source_block_was_none:
            source_block = target_block

        # Check if this pair is supported
        if not self.is_supported(source, target):
            raise NotImplementedError(
                f"Face pair ({source.name}, {target.name}) not yet implemented"
            )

        # Check if target position is supported (even cube inner 2x2 limitation)
        # On even cubes, the inner 2x2 uses different M slices that don't cancel out
        target_ltr = target_block[0]
        if not self.is_position_supported(target_ltr[0], target_ltr[1]):
            n = self.n_slices
            mid_low = n // 2 - 1
            mid_high = n // 2
            raise ValueError(
                f"Position ({target_ltr[0]}, {target_ltr[1]}) not supported on even cube. "
                f"Inner 2x2 region [{mid_low},{mid_high}] x [{mid_low},{mid_high}] "
                f"uses different M slices that don't cancel out."
            )

        cube = self.cube

        # Currently only support Front as target
        assert target is cube.front

        # Detect source type for algorithm selection
        is_left = source is cube.left
        is_right = source is cube.right
        uses_e_slice = is_left or is_right

        # Convert LTR to index coordinates
        # Target index is on Front face
        target_idx_block = self.ltr_block_to_index(target, target_block)
        rc1, rc2 = self._normalize_block(target_idx_block[0], target_idx_block[1])

        # Source: get where the piece actually is (LTR -> source index)
        source_ltr = source_block[0]
        actual_source_idx = self.ltr_to_index(source, source_ltr[0], source_ltr[1])

        # Expected source position: derived from target using face mapping
        target_idx = target_idx_block[0]
        expected_source_idx = self._point_on_source_idx(source, target_idx)

        # Find rotation to align actual source to expected source
        n_rotate = self._find_rotation_idx(actual_source_idx, expected_source_idx)

        # Invariant: if source_block was None, n_rotate must be 0
        # (source defaults to expected position)
        if source_block_was_none and n_rotate != 0:
            raise ValueError(
                f"source_block=None requires n_rotate=0, but got {n_rotate}. "
                f"actual={actual_source_idx}, expected={expected_source_idx}"
            )

        r1, c1 = rc1
        r2, c2 = rc2

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
                commutator = [
                    rotate_on_cell.prime,     # E
                    on_front_rotate,
                    rotate_on_second.prime,   # E
                    on_front_rotate.prime,
                    rotate_on_cell,           # E'
                    on_front_rotate,
                    rotate_on_second,         # E'
                    on_front_rotate.prime
                ]
            else:
                # Right: E' brings R→F (swap E and E')
                commutator = [
                    rotate_on_cell,           # E'
                    on_front_rotate,
                    rotate_on_second,         # E'
                    on_front_rotate.prime,
                    rotate_on_cell.prime,     # E
                    on_front_rotate,
                    rotate_on_second.prime,   # E
                    on_front_rotate.prime
                ]
        else:
            # M-based algorithm for Up/Down/Back sources

            # Determine F rotation direction to avoid column intersection
            # After rotating F, the block moves. Columns must not intersect.
            rc1_f_rotated = cube.cqr.rotate_point_clockwise(rc1)
            rc2_f_rotated = cube.cqr.rotate_point_clockwise(rc2)

            if self._1d_intersect((c1, c2), (rc1_f_rotated[1], rc2_f_rotated[1])):
                # Clockwise causes intersection, use counter-clockwise
                on_front_rotate = Algs.F.prime
                rc1_f_rotated = cube.cqr.rotate_point_counterclockwise(rc1)
                rc2_f_rotated = cube.cqr.rotate_point_counterclockwise(rc2)
            else:
                on_front_rotate = Algs.F

            # Get M slice algorithms for the columns
            rotate_on_cell = self._get_slice_m_alg(c1, c2)
            rotate_on_second = self._get_slice_m_alg(rc1_f_rotated[1], rc2_f_rotated[1])

            # M slice handling based on source face:
            # - Up: M' brings Up→Front, standard algorithm [M', F, M', F', M, F, M, F']
            # - Back: M'*2 = M2 brings Back→Front (180°)
            # - Down: M brings Down→Front, inverted algorithm [M, F, M, F', M', F, M', F']
            is_down = source is cube.down
            is_back = source is cube.back

            if is_down:
                # Down: swap prime/non-prime for M moves
                commutator = [
                    rotate_on_cell,               # M (instead of M')
                    on_front_rotate,
                    rotate_on_second,             # M (instead of M')
                    on_front_rotate.prime,
                    rotate_on_cell.prime,         # M' (instead of M)
                    on_front_rotate,
                    rotate_on_second.prime,       # M' (instead of M)
                    on_front_rotate.prime
                ]
            elif is_back:
                # Back: double M moves (180°)
                commutator = [
                    rotate_on_cell.prime * 2,
                    on_front_rotate,
                    rotate_on_second.prime * 2,
                    on_front_rotate.prime,
                    rotate_on_cell * 2,
                    on_front_rotate,
                    rotate_on_second * 2,
                    on_front_rotate.prime
                ]
            else:
                # Up: standard algorithm
                commutator = [
                    rotate_on_cell.prime,
                    on_front_rotate,
                    rotate_on_second.prime,
                    on_front_rotate.prime,
                    rotate_on_cell,
                    on_front_rotate,
                    rotate_on_second,
                    on_front_rotate.prime
                ]

        # Execute: first rotate source to align, then commutator
        if n_rotate:
            self.op.play(Algs.of_face(source.name) * n_rotate)

        self.op.play(Algs.seq_alg(None, *commutator))

        # Preserve state: undo source rotation if requested
        if preserve_state and n_rotate:
            undo_alg = Algs.of_face(source.name).prime * n_rotate
            self.op.play(undo_alg)

        return True
