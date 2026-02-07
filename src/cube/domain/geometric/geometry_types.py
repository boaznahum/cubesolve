"""
Geometric type definitions for coordinate transformation functions.

All types are centralized here to avoid duplication and confusion.

Naming convention:
- "Unit" suffix = size-independent (accepts n_slices as parameter)
- No suffix = size-bound (n_slices baked in at creation)

Coordinate systems:
- Slice coordinates: (slice_index, slot) - position within a slice
- Face coordinates: (row, col) - position on a face center grid

Using Protocol classes instead of Callable aliases for better readability:
- Parameter names are visible in IDE autocomplete/hints
- Self-documenting signatures
- Type checkers verify exact signatures
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple, Protocol, Tuple

if TYPE_CHECKING:
    from cube.domain.model.Edge import Edge
    from cube.domain.model.PartSlice import EdgeWing
    from cube.domain.model.Face import Face
    from cube.domain.model.PartSlice import CenterSlice
    from cube.domain.geometric.rotated_block import RotatedBlock


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()


# Basic coordinate types using NamedTuple for clarity
class Point(NamedTuple):
    """A 2D coordinate point, used for (row, col) or (slice_index, slot)."""
    row: int
    col: int


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
        # Late import to avoid circular dependency
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
        # Late import to avoid circular dependency
        from cube.domain.geometric import geometry_utils
        new_start = geometry_utils.rotate_point_clockwise(self.start, n_slices, n_rotations=n_rotations)
        new_end = geometry_utils.rotate_point_clockwise(self.end, n_slices, n_rotations=n_rotations)
        return Block(new_start, new_end)  # No normalization!

    @property
    def is_normalized(self) -> bool:
        """Check if the block is in normalized orientation.

        Delegates to RotatedBlock for consistency.

        Returns:
            True if the block is normalized, False otherwise
        """
        # Late import to avoid circular dependency
        from cube.domain.geometric.rotated_block import RotatedBlock
        return RotatedBlock.detect_n_rotations(self.start, self.end) == 0

    @property
    def n_rotations(self) -> int:
        """Detect and return the number of rotations from the kernel.

        Delegates to RotatedBlock.detect_n_rotations() for the actual logic.

        Returns:
            Detected n_rotations value (0, 1, 2, or 3)
        """
        # Late import to avoid circular dependency
        from cube.domain.geometric.rotated_block import RotatedBlock
        return RotatedBlock.detect_n_rotations(self.start, self.end)

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
        # Late import to avoid circular dependency
        from cube.domain.geometric.rotated_block import RotatedBlock
        from cube.domain.geometric import geometry_utils

        # Detect how many rotations from the kernel
        n_rot = RotatedBlock.detect_n_rotations(self.start, self.end)

        # Reverse-rotate the corners to recover the kernel
        # If we rotated 90° CW (n_rot=1), reverse by rotating 270° CW (n_rot=-1 or 3)
        reverse_n_rot = (-n_rot) % 4
        kernel_start = geometry_utils.rotate_point_clockwise(self.start, n_slices, n_rotations=reverse_n_rot)
        kernel_end = geometry_utils.rotate_point_clockwise(self.end, n_slices, n_rotations=reverse_n_rot)

        # The kernel is always normalized (by definition)
        return Block(kernel_start, kernel_end)

    def _detect_rotation_from(self, order_by: Block, n_slices: int) -> int:
        """Detect the rotation count from order_by to self.

        Tries all 4 rotations of order_by and returns the one that matches
        self (after normalization).

        Args:
            order_by: The reference block
            n_slices: Face size

        Returns:
            n_rot such that order_by.rotate_clockwise(n_slices, n_rot) == self.normalize

        Raises:
            ValueError: If self is not a rotation of order_by
        """
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise

        self_norm = self.normalize
        for n_rot in range(4):
            rotated_start = rotate_point_clockwise(order_by.start, n_slices, n_rot)
            rotated_end = rotate_point_clockwise(order_by.end, n_slices, n_rot)
            if Block._normalize(rotated_start, rotated_end) == self_norm:
                return n_rot

        raise ValueError(f"Block {self} is not a rotation of {order_by}")

    def points_by(self, n_slices: int, order_by: Block | None = None) -> Iterator[Point]:
        """Yield points of self in kernel order.

        The kernel is determined by order_by (normalized to its kernel form).
        All blocks that are rotations of the same kernel can be iterated with
        the same order_by, ensuring cell[i] from each block corresponds to
        the same kernel cell.

        Args:
            n_slices: Face size (e.g., 7 for a 7x7 face)
            order_by: The kernel that defines iteration order. Must be a rotation
                of self. Gets normalized if not already. Defaults to self
                (plain row-by-row iteration).

        Yields:
            Points of self in kernel order
        """
        if order_by is None or order_by is self:
            yield from self.cells
            return

        # Normalize order_by to its kernel
        order_by = order_by.normalize

        n_rot = self._detect_rotation_from(order_by, n_slices)

        if n_rot == 0:
            yield from self.cells
            return

        # Create an unnormalized block whose corners encode the rotation,
        # then use iterate_points (fused kernel-order iteration)
        rotated = order_by.rotate_preserve_original(n_slices, n_rot)
        from cube.domain.geometric.rotated_block import RotatedBlock
        yield from RotatedBlock.iterate_points(rotated.start, rotated.end, n_slices)

    def pieces_by(self, face: Face, order_by: Block | None = None) -> Iterator[CenterSlice]:
        """Yield center slices of self in kernel order.

        Same as points_by but yields CenterSlice objects from the face.

        Args:
            face: The cube face to iterate over
            order_by: The kernel that defines iteration order. Must be a rotation
                of self. Gets normalized if not already. Defaults to self
                (plain row-by-row iteration).

        Yields:
            CenterSlice objects from the face in kernel order
        """
        n_slices = face.cube.n_slices
        for point in self.points_by(n_slices, order_by):
            yield face.center.get_center_slice((point.row, point.col))

# =============================================================================
# SIZE-INDEPENDENT functions (Unit functions) - accept n_slices as parameter
# These have n_slices as FIRST parameter (consistent convention)
# =============================================================================

class SliceToCenter(Protocol):
    """Convert slice coords to face coords (size-independent)."""
    def __call__(self, n_slices: int, slice_index: int, slot: int) -> Point: ...


class CenterToSlice(Protocol):
    """Convert face coords to slice coords (size-independent)."""
    def __call__(self, n_slices: int, row: int, col: int) -> Point: ...


class SliceToEntryEdgeUnit(Protocol):
    """Compute entry edge index from slice index (size-independent)."""
    def __call__(self, n_slices: int, slice_index: int) -> int: ...


# =============================================================================
# SIZE-BOUND functions - n_slices baked in at creation time
# =============================================================================

class SliceToEntryEdge(Protocol):
    """Compute entry edge index from slice index (size-bound)."""
    def __call__(self, slice_index: int) -> int: ...


class PointComputer(Protocol):
    """Convert slice coords to face coords (size-bound)."""
    def __call__(self, slice_index: int, slot: int) -> Point: ...


class ReversePointComputer(Protocol):
    """Convert face coords to slice coords (size-bound)."""
    def __call__(self, row: int, col: int) -> Point: ...


# =============================================================================
# Dataclasses for complex return types
# =============================================================================

@dataclass(frozen=True)
class FaceOrthogonalEdgesInfo:
    """
    Information about a row/column on a face and its orthogonal edges.

    Returned by SizedCubeLayout.get_orthogonal_index_by_distance_from_face().

    This dataclass captures the relationship between a face's row/column and
    the edges that are orthogonal (perpendicular) to that row/column.

    Attributes:
        row_or_col: The row or column index in the face's LTR coordinate system.
            - Row index if base_face is above/below (shared edge is horizontal)
            - Column index if base_face is left/right (shared edge is vertical)

        edge_one: First orthogonal edge (perpendicular to the shared edge with base_face).
            - Left edge if base is top/bottom
            - Top edge if base is left/right

        edge_two: Second orthogonal edge (perpendicular to the shared edge with base_face).
            - Right edge if base is top/bottom
            - Bottom edge if base is left/right

        index_on_edge_one: Index in edge_one's internal coordinate system.
            Use edge_one.get_slice(index_on_edge_one) to access the slice.

        index_on_edge_two: Index in edge_two's internal coordinate system.
            Use edge_two.get_slice(index_on_edge_two) to access the slice.
    """
    row_or_col: int
    edge_one: "Edge"
    edge_two: "Edge"
    index_on_edge_one: int
    index_on_edge_two: int

    @property
    def wing_one(self) -> "EdgeWing":
        return self.edge_one.get_slice(self.index_on_edge_one)

    @property
    def wing_two(self) -> "EdgeWing":
        return self.edge_two.get_slice(self.index_on_edge_two)
