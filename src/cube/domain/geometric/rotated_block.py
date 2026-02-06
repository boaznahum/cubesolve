"""
RotatedBlock - Domain class for representing rotated blocks on cube faces.

For detailed documentation including coordinate system, rotation formulas,
and visual examples, see: RotatedBlock.md
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.domain.geometric.geometry_types import Block, Point
    from cube.domain.model.Face import Face
    from cube.domain.model.PartSlice import CenterSlice


@dataclass(frozen=True)
class RotatedBlock:
    """Represents a rotated block of cells on a cube face.

    RotatedBlock ALWAYS holds:
    1. The ORIGINAL corner positions (before normalization)
    2. The TOTAL number of 90° CW rotations from the original normalized state

    This design enables the `points` property to yield cells in an order that
    preserves the original relative cell positions - fixing the rotation bug
    where Block.cells iterator loses the cell-to-cell mapping.

    The class can detect the orientation of a block based on corner positions.
    See RotatedBlock.md section "Detecting Block Orientation" for the mathematical
    proof of how we determine n_rotations from corner relationships.

    Terminology:
        **"Original"** refers to the state BEFORE any rotation was applied.
        - Original block: The normalized block with start.row <= end.row
        - Original corners: The corner positions before rotation
        - Original orientation: Normalized state (0 rotations)

        The term "original" is used throughout methods to distinguish between:
        - The pre-rotation state (what we're tracking)
        - The post-rotation state (current corner positions)

    Attributes:
        start: First corner of the block (may be unnormalized after rotation).
            These are the ROTATED corner positions from the original block.
        end: Second corner of the block (may be unnormalized after rotation).
            These are the ROTATED corner positions from the original block.
        n_slices: Face size (e.g., 7 for a 7x7 face)
        n_rotations: Total number of 90° CW rotations from the original normalized
            state (0, 1, 2, or 3). Default is 0, but factory methods will
            auto-detect based on corner orientation.
    """

    start: Point
    end: Point
    n_slices: int
    n_rotations: int = field(default=0)

    @property
    def points(self) -> Iterator[Point]:
        """Yield points in the order that preserves original relative positions.

        Delegates to iterate_points() static method for the actual logic.

        Returns:
            Iterator of Points in order that preserves original relative positions
        """
        return RotatedBlock.iterate_points(self.start, self.end, self.n_slices)

    @staticmethod
    def iterate_points(start: Point, end: Point, n_slices: int) -> Iterator[Point]:
        """Iterate over points in order that preserves original relative positions.

        This is the CORE logic that both Block and RotatedBlock delegate to.
        It detects n_rotations from corner positions, then iterates over the
        original block's cells and transforms each by the rotation.

        Args:
            start: First corner of the block (may be rotated)
            end: Second corner of the block (may be rotated)
            n_slices: Face size (e.g., 7 for a 7x7 face)

        Yields:
            Points in order that preserves original relative positions
        """
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise
        from cube.domain.geometric.geometry_types import Block, Point

        # Step 1: Detect n_rotations from corner positions
        n_rot = RotatedBlock.detect_n_rotations(start, end)

        # Step 2: Get the original block by reverse-rotating the corners
        # This preserves the original block's corner order
        reverse_n_rot = (-n_rot) % 4
        orig_start = rotate_point_clockwise(start, n_slices, n_rotations=reverse_n_rot)
        orig_end = rotate_point_clockwise(end, n_slices, n_rotations=reverse_n_rot)

        # Step 3: Iterate over the original block's cells (preserves order)
        # and rotate each by n_rotations
        original_block = Block(orig_start, orig_end)
        for orig_point in original_block.cells:
            rotated_point = rotate_point_clockwise(
                orig_point, n_slices, n_rotations=n_rot
            )
            yield rotated_point

    @property
    def is_normalized(self) -> bool:
        """Check if the block is in normalized orientation.

        A normalized block has start.row <= end.row and start.col <= end.col.
        For rotated blocks, this will typically be False for 90°/270° rotations.

        Returns:
            True if the block corners are in normalized order, False otherwise
        """
        return self.start.row <= self.end.row and self.start.col <= self.end.col

    @property
    def cells(self) -> Iterator[Point]:
        """Alias for points property - yields in original relative order.

        This provides API compatibility with Block.cells, but preserves the
        original relative positions instead of using normalized row-by-row order.

        Returns:
            Iterator of Points in order that preserves original relative positions
        """
        return self.points

    def pieces(self, face: Face) -> Iterator[CenterSlice]:
        """Yield center slices from the face in original relative order.

        Iterates over the block's points (which preserve the original relative
        positions) and yields the corresponding center slices from the face.

        This is the primary method for accessing the actual cube pieces that
        belong to this rotated block, ensuring the pieces are returned in the
        same relative order as the original unrotated block.

        Args:
            face: The cube face to iterate over

        Yields:
            CenterSlice objects from the face at the block's point positions,
            in the order that preserves original relative positions

        Example:
            >>> from cube.domain.geometric.geometry_types import Block, Point
            >>> original = Block(Point(1, 2), Point(2, 4))
            >>> rotated = RotatedBlock.from_block(original, n_slices=7, n_rotations=1)
            >>> # Get pieces in original order: [1,2], [1,3], [1,4], [2,2], [2,3], [2,4]
            >>> for piece in rotated.pieces(face):
            ...     print(piece)
        """
        for point in self.points:
            yield face.center.get_center_slice((point.row, point.col))

    @property
    def normalize(self) -> Block:
        """Return a normalized Block from this RotatedBlock.

        Creates a regular Block with the corners normalized (start.row <= end.row
        and start.col <= end.col).

        Returns:
            A normalized Block with the same corner positions
        """
        from cube.domain.geometric.geometry_types import Block, Point
        r1, c1 = self.start.row, self.start.col
        r2, c2 = self.end.row, self.end.col
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1
        return Block(Point(r1, c1), Point(r2, c2))

    def rotate(self, n_rotations: int) -> RotatedBlock:
        """Return a new RotatedBlock with adjusted rotation count.

        Simply increments or decrements n_rotations by the given amount.

        Args:
            n_rotations: Number of additional 90° CW rotations (can be negative)

        Returns:
            A new RotatedBlock with updated n_rotations count
        """
        from cube.domain.geometric.geometry_utils import rotate_point_clockwise

        new_n_rotations = (self.n_rotations + n_rotations) % 4

        # Rotate the corner points
        new_start = rotate_point_clockwise(
            self.start,
            n_slices=self.n_slices,
            n_rotations=n_rotations
        )
        new_end = rotate_point_clockwise(
            self.end,
            n_slices=self.n_slices,
            n_rotations=n_rotations
        )

        return RotatedBlock(
            start=new_start,
            end=new_end,
            n_rotations=new_n_rotations,
            n_slices=self.n_slices
        )

    @staticmethod
    def detect_n_rotations(start: Point, end: Point) -> int:
        """Detect the number of rotations based on corner orientation.

        Analyzes the relationship between start and end points to determine
        how many 90° CW rotations have been applied.

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

        # Normalized: start.row <= end.row AND start.col <= end.col
        if r1 <= r2 and c1 <= c2:
            return 0
        # After 90° CW: start.row > end.row, start.col < end.col
        if r1 > r2 and c1 < c2:
            return 1
        # After 270° CW: start.row < end.row, start.col > end.col
        if r1 < r2 and c1 > c2:
            return 3
        # After 180°: both inverted (start.row > end.row AND start.col > end.col)
        # OR the alternative corner ordering for 180°
        return 2

    @staticmethod
    def from_points(start: Point, end: Point, n_slices: int, n_rotations: int = 0) -> RotatedBlock:
        """Create a RotatedBlock from two corner points.

        Auto-detects the orientation of the block and adds the detected
        rotation count to the provided n_rotations parameter.

        See RotatedBlock.md section "Detecting Block Orientation" for details.

        Args:
            start: First corner of the block
            end: Second corner of the block
            n_slices: Face size (e.g., 7 for a 7x7 face)
            n_rotations: Additional rotations to apply (default: 0).
                The detected orientation rotations are added to this value.

        Returns:
            A new RotatedBlock with computed n_rotations
        """
        detected = RotatedBlock.detect_n_rotations(start, end)
        total_n_rotations = (detected + n_rotations) % 4

        return RotatedBlock(
            start=start,
            end=end,
            n_slices=n_slices,
            n_rotations=total_n_rotations
        )

    @staticmethod
    def from_block(block: Block, n_slices: int, n_rotations: int = 0) -> RotatedBlock:
        """Create a RotatedBlock from a regular Block.

        Auto-detects the orientation of the block and adds the detected
        rotation count to the provided n_rotations parameter.

        See RotatedBlock.md section "Detecting Block Orientation" for details.

        Args:
            block: The Block to convert (uses its start and end points)
            n_slices: Face size (e.g., 7 for a 7x7 face)
            n_rotations: Additional rotations to apply (default: 0).
                The detected orientation rotations are added to this value.

        Returns:
            A new RotatedBlock with the block's corners and computed n_rotations
        """
        return RotatedBlock.from_points(
            start=block.start,
            end=block.end,
            n_slices=n_slices,
            n_rotations=n_rotations
        )