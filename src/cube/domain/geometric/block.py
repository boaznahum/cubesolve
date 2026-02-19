"""
Block - A rectangle on a cube face with kernel-based rotation ordering.

Terminology:
    **Kernel**: The normalized block from which all rotated variants are
    generated. A kernel always has start.row <= end.row AND
    start.col <= end.col. Every rotated block has exactly one kernel.

    **Rotation encoding**: An unnormalized block encodes its rotation state
    in the relationship between start and end corners. This allows
    iterate_points() to recover the kernel and iterate in kernel order.

    **Kernel ordering**: The kernel defines a natural row-by-row cell ordering
    (index 0, 1, 2...). When a block is rotated, cells move to new positions
    but retain their kernel index. points_by() maps this kernel ordering
    onto any rotated block.

For visual examples, see: RotatedBlock.md
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

from cube.domain.geometric.geometry_types import Point

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.PartSlice import CenterSlice


@dataclass(frozen=True)
class Block:
    """A rectangle defined by two corner points.

    A normalized block (kernel) has start.row <= end.row AND start.col <= end.col.
    An unnormalized block encodes rotation state in its corner ordering —
    the relationship between start and end reveals how many 90° CW rotations
    have been applied from the kernel.

    Attributes:
        start: First corner of the block
        end: Second corner of the block
    """
    start: Point
    end: Point

    def __getitem__(self, index: int) -> Point:
        """Support tuple-style indexing for backward compatibility.

        Block[0] returns start, Block[1] returns end.

        Args:
            index: 0 for start, 1 for end

        Returns:
            The Point at the specified index
        """
        if index == 0:
            return self.start
        elif index == 1:
            return self.end
        else:
            raise IndexError("Block index out of range (use 0 or 1)")



    @staticmethod
    def of(start: Point | Tuple[int, int], end: Point | Tuple[int, int])-> Block:

        if not isinstance(start, Point):
            start = Point(*start)

        if not isinstance(end, Point):
            end = Point(*end)

        return Block(start=start, end=end)

    @property
    def cells(self) -> Iterator[Point]:
        """Iterate over the kernel (normalized block) in row-by-row order.

        See #normalize
        """

        r1, c1 = self.start
        r2, c2 = self.end

        _c1 = min(c1, c2)
        _c2 = max(c1, c2)

        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(_c1, _c2 + 1):
                yield Point(r, c)

    @property
    def normalize(self) -> Block:
        """Return the kernel — normalized block with min values first.

        A block is defined by two corner points: (r1, c1) and (r2, c2).
        The kernel has r1 <= r2 and c1 <= c2.

        This is critical for commutator algorithms because:
        1. M-slice selection depends on column ordering
        2. Block iteration assumes kernel coordinates
        3. Intersection checks require consistent ordering

        Returns:
            Kernel block with r1 <= r2 and c1 <= c2
        """
        r1, c1 = self.start
        r2, c2 = self.end
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1
        return Block(Point(r1, c1), Point(r2, c2))

    @staticmethod
    def _normalize(start:Point, end: Point)-> Block:

        r1, c1 = start
        r2, c2 = end
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1
        return Block(Point(r1, c1), Point(r2, c2))

    @property
    def size(self) -> int:
        """Number of cells in the block."""
        r1, c1 = self.start
        r2, c2 = self.end
        return (abs(r2 - r1) + 1) * (abs(c2 - c1) + 1)

    @property
    def as_point(self) -> Point:
        """Return the block as a single Point, asserting it is a 1x1 block.

        Use this when you expect a block to be a single cell and want to
        get its coordinate as a Point. Raises AssertionError if block
        contains more than one cell.

        Returns:
            The single Point in this block

        Raises:
            AssertionError: If block is not a 1x1 block
        """
        assert self.size == 1, f"Block {self} is not a point (size={self.size})"
        return self.start

    @property
    def dim(self) -> tuple[int, int]:
        """
        Calculate the dimensions of a block (rows, cols).

        Returns:
            Tuple of (num_rows, num_cols)
        """
        rc1 = self.start
        rc2 = self.end
        return (abs(rc2[0] - rc1[0]) + 1), (abs(rc2[1] - rc1[1]) + 1)


    def rotate_clockwise(self, n_slices: int, n_rotations: int = 1) -> Block:
        """Return a new normalized Block rotated clockwise by n rotations.

        Note: This normalizes the result (returns a kernel), losing the rotation
        encoding. Use rotate_preserve_original() to preserve kernel-order iteration.
        """
        from cube.domain.geometric import geometry_utils
        new_start = geometry_utils.rotate_point_clockwise(self.start, n_slices, n_rotations=n_rotations)
        new_end = geometry_utils.rotate_point_clockwise(self.end, n_slices, n_rotations=n_rotations)
        return Block._normalize(new_start, new_end)

    def rotate_preserve_original(self, n_slices: int, n_rotations: int = 1) -> Block:
        """Return a rotated Block WITHOUT normalizing — preserves rotation encoding.

        Unlike rotate_clockwise() which returns a kernel, this method returns
        an unnormalized Block whose corner ordering encodes the rotation.
        This enables iterate_points() to recover the kernel and iterate
        in kernel order.

        See RotatedBlock.md section "Detecting Block Orientation" for details.

        Args:
            n_slices: Face size (e.g., 7 for a 7x7 face)
            n_rotations: Number of 90° CW rotations (default: 1)

        Returns:
            An unnormalized Block with rotated corners (start may be > end)
        """
        from cube.domain.geometric import geometry_utils
        new_start = geometry_utils.rotate_point_clockwise(self.start, n_slices, n_rotations=n_rotations)
        new_end = geometry_utils.rotate_point_clockwise(self.end, n_slices, n_rotations=n_rotations)
        return Block(new_start, new_end)  # No normalization!

    @staticmethod
    def detect_n_rotations(start: Point, end: Point) -> int:
        """Detect the number of rotations from the kernel based on corner orientation.

        Analyzes the relationship between start and end points to determine
        how many 90° CW rotations have been applied from the kernel.

        See RotatedBlock.md section "Detecting Block Orientation" for the
        mathematical proof behind this detection logic.

        Args:
            start: First corner of the block
            end: Second corner of the block

        Returns:
            Detected n_rotations value (0, 1, 2, or 3)
        """
        r1, c1 = start.row, start.col
        r2, c2 = end.row, end.col

        # Kernel: start.row <= end.row AND start.col <= end.col
        if r1 <= r2 and c1 <= c2:
            return 0
        # 90° CW from kernel: r1 > r2, c1 <= c2
        # (c1 == c2 occurs for single-column kernels rotated to single-row)
        if r1 > r2 and c1 <= c2:
            return 1
        # 270° CW from kernel: r1 <= r2, c1 > c2
        # (r1 == r2 occurs for single-row kernels rotated to single-column)
        if r1 <= r2 and c1 > c2:
            return 3
        # 180° from kernel: r1 > r2 AND c1 > c2
        return 2

    @staticmethod
    def iterate_points(start: Point, end: Point, n_slices: int) -> Iterator[Point]:
        """Iterate over points in kernel order, yielding rotated positions.

        This is the CORE iteration logic. It detects n_rotations from corner
        positions, recovers the kernel corners, and iterates in kernel order
        — all fused into one loop per rotation case with no per-point
        function calls.

        The kernel corners are recovered via reverse rotation (baked into
        range bounds), and the forward rotation is applied in the yield
        expression.

        Args:
            start: First corner of the block (may be rotated from kernel)
            end: Second corner of the block (may be rotated from kernel)
            n_slices: Face size (e.g., 7 for a 7x7 face)

        Yields:
            Points in kernel order at rotated positions
        """
        r1, c1 = start
        r2, c2 = end
        nm1 = n_slices - 1

        # Detect n_rotations from corner orientation and iterate with
        # inlined rotation formulas. The kernel is always normalized,
        # so we can iterate without min/max.
        #
        # Rotation formulas (CW):
        #   0: (r, c) -> (r, c)
        #   1: (r, c) -> (nm1-c, r)
        #   2: (r, c) -> (nm1-r, nm1-c)
        #   3: (r, c) -> (c, nm1-r)
        #
        # Reverse rotation formulas (to recover kernel corners):
        #   reverse of 1 = 3 CW: (r, c) -> (c, nm1-r)
        #   reverse of 2 = 2 CW: (r, c) -> (nm1-r, nm1-c)
        #   reverse of 3 = 1 CW: (r, c) -> (nm1-c, r)

        if r1 <= r2 and c1 <= c2:
            # n_rot == 0: kernel — iterate directly
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    yield Point(r, c)

        elif r1 > r2 and c1 <= c2:
            # n_rot == 1: kernel corners via 3 CW, yield via 1 CW
            # kernel: (c1, nm1-r1) to (c2, nm1-r2)
            for r in range(c1, c2 + 1):
                for c in range(nm1 - r1, nm1 - r2 + 1):
                    yield Point(nm1 - c, r)

        elif r1 > r2 and c1 > c2:
            # n_rot == 2: kernel corners via 2 CW, yield via 2 CW
            # kernel: (nm1-r1, nm1-c1) to (nm1-r2, nm1-c2)
            for r in range(nm1 - r1, nm1 - r2 + 1):
                for c in range(nm1 - c1, nm1 - c2 + 1):
                    yield Point(nm1 - r, nm1 - c)

        else:
            # n_rot == 3 (r1 <= r2, c1 > c2): kernel corners via 1 CW, yield via 3 CW
            # kernel: (nm1-c1, r1) to (nm1-c2, r2)
            for r in range(nm1 - c1, nm1 - c2 + 1):
                for c in range(r1, r2 + 1):
                    yield Point(c, nm1 - r)

    @property
    def is_normalized(self) -> bool:
        """Check if the block is in normalized (kernel) orientation.

        Returns:
            True if the block is normalized, False otherwise
        """
        return Block.detect_n_rotations(self.start, self.end) == 0

    @property
    def n_rotations(self) -> int:
        """Detect and return the number of rotations from the kernel.

        Returns:
            Detected n_rotations value (0, 1, 2, or 3)
        """
        return Block.detect_n_rotations(self.start, self.end)

    def detect_original(self, n_slices: int) -> Block:
        """Recover the kernel from a rotated block.

        Analyzes the corner positions to determine how many rotations have
        been applied from the kernel, then reverse-rotates the corners to
        recover it.

        Args:
            n_slices: Face size (e.g., 7 for a 7x7 face)

        Returns:
            The kernel Block (normalized, n_rotations=0)
        """
        from cube.domain.geometric import geometry_utils

        # Detect how many rotations from the kernel
        n_rot = Block.detect_n_rotations(self.start, self.end)

        # Reverse-rotate the corners to recover the kernel
        # If we rotated 90° CW (n_rot=1), reverse by rotating 270° CW (n_rot=-1 or 3)
        reverse_n_rot = (-n_rot) % 4
        kernel_start = geometry_utils.rotate_point_clockwise(self.start, n_slices, n_rotations=reverse_n_rot)
        kernel_end = geometry_utils.rotate_point_clockwise(self.end, n_slices, n_rotations=reverse_n_rot)

        # The kernel is always normalized (by definition)
        return Block(kernel_start, kernel_end)

    def same_kernel(self, other: Block, n_slices: int) -> Block | None:
        """Return the shared kernel if self and other are rotations of the same kernel.

        Two blocks share a kernel if one can be obtained from the other by
        0, 1, 2, or 3 clockwise 90° rotations on an n_slices × n_slices face.

        Args:
            other: The other block to compare with
            n_slices: Face size (e.g., 7 for a 7x7 face)

        Returns:
            The shared kernel Block if they are rotations of each other, None otherwise
        """
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise

        self_norm = self.normalize
        other_norm = other.normalize
        for n_rot in range(4):
            rotated_start = rotate_point_clockwise(other_norm.start, n_slices, n_rot)
            rotated_end = rotate_point_clockwise(other_norm.end, n_slices, n_rot)
            if Block._normalize(rotated_start, rotated_end) == self_norm:
                return self_norm
        return None

    def _detect_rotation_from(self, order_by: Block, n_slices: int) -> int:
        """Detect the rotation count from order_by's kernel to self's kernel.

        Normalizes both self and order_by to their kernels, then finds which
        rotation of order_by's kernel matches self's kernel.

        Args:
            order_by: The reference block (normalized to kernel internally)
            n_slices: Face size

        Returns:
            n_rot such that order_by.kernel.rotate_clockwise(n_slices, n_rot) == self.kernel

        Raises:
            ValueError: If self and order_by don't share a kernel
        """
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise

        self_norm = self.normalize
        order_by_norm = order_by.normalize
        for n_rot in range(4):
            rotated_start = rotate_point_clockwise(order_by_norm.start, n_slices, n_rot)
            rotated_end = rotate_point_clockwise(order_by_norm.end, n_slices, n_rot)
            if Block._normalize(rotated_start, rotated_end) == self_norm:
                return n_rot

        raise ValueError(f"Block {self} is not a rotation of {order_by}")

    def points_by(self, n_slices: int, order_by: Block | None = None) -> Iterator[Point]:
        """Yield points of self in kernel order defined by order_by.

        **The ordering concept:**

        A kernel (normalized block) has a natural row-by-row ordering.
        For example, kernel Block([1,2], [2,4]) on a 7x7 face defines::

            index 0 → (1,2)  cell 12
            index 1 → (1,3)  cell 13
            index 2 → (1,4)  cell 14
            index 3 → (2,2)  cell 22
            index 4 → (2,3)  cell 23
            index 5 → (2,4)  cell 24

        When the face rotates 90° CW, the cells move to new positions, but
        each cell retains its kernel index. Cell 12 (index 0) moves to (4,1),
        cell 13 (index 1) moves to (3,1), etc.

        points_by(n, order_by) maps the kernel ordering onto self: the i-th
        yielded point is the position where kernel cell[i] ended up in self's
        block after rotation.

        **Why this matters — shared ordering guarantee:**

        If blocks A and B share the same kernel, then::

            A.points_by(n, order_by=K)[i]  →  position of kernel cell[i] in A
            B.points_by(n, order_by=K)[i]  →  position of kernel cell[i] in B

        The same kernel cell[i] is at index i in both. Any block passed as
        order_by is normalized to its kernel internally, so passing A, B, or K
        directly as order_by all produce the same ordering — they share the
        same kernel implicitly.

        **Example — commutator 3-cycle with aligned iteration:**

        Given blocks s1, t, s2 that are rotations of the same kernel on a
        7x7 face. Kernel is Block([1,2], [2,4])::

            # All three blocks share the kernel:
            assert s1.same_kernel(t, n) is not None

            s1_cells = list(s1.points_by(n, order_by=t))
            t_cells  = list(t.points_by(n, order_by=t))
            s2_cells = list(s2.points_by(n, order_by=t))

            # s1_cells[0], t_cells[0], s2_cells[0] all correspond to
            # kernel cell 12 (index 0) — at their respective rotated positions.
            # s1_cells[1], t_cells[1], s2_cells[1] → kernel cell 13 (index 1).
            # etc.

            # This enables correct marker comparison: markers placed at
            # s1_cells[i] should appear at t_cells[i] after the commutator.

        Args:
            n_slices: Face size (e.g., 7 for a 7x7 face)
            order_by: Block that defines the iteration order (normalized to its
                kernel internally). Must share a kernel with self. Defaults to
                None (plain row-by-row iteration of self).

        Yields:
            Points of self in kernel order

        Raises:
            ValueError: If self and order_by don't share a kernel
        """
        if order_by is None or order_by is self:
            yield from self.cells
            return

        n_rot = self._detect_rotation_from(order_by, n_slices)

        if n_rot == 0:
            yield from self.cells
            return

        # Create an unnormalized block whose corners encode the rotation,
        # then use iterate_points (fused kernel-order iteration)
        kernel = order_by.normalize
        rotated = kernel.rotate_preserve_original(n_slices, n_rot)
        yield from Block.iterate_points(rotated.start, rotated.end, n_slices)

    def pieces_by(self, face: Face, order_by: Block | None = None) -> Iterator[CenterSlice]:
        """Yield center slices of self in kernel order defined by order_by.

        Same as points_by but yields CenterSlice objects instead of Points.
        See points_by for the full explanation of the ordering concept.

        Args:
            face: The cube face to iterate over
            order_by: Block that defines the iteration order (normalized to its
                kernel). Must share a kernel with self. Defaults to None
                (plain row-by-row iteration of self).

        Yields:
            CenterSlice objects from the face in kernel order

        Raises:
            ValueError: If self and order_by don't share a kernel
        """
        n_slices = face.cube.n_slices
        for point in self.points_by(n_slices, order_by):
            yield face.center.get_center_slice((point.row, point.col))
