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

        Optimized: all rotation math is inlined to avoid per-point function
        call overhead. The original block corners are recovered via direct
        formulas and iteration applies the forward rotation inline.

        Args:
            start: First corner of the block (may be rotated)
            end: Second corner of the block (may be rotated)
            n_slices: Face size (e.g., 7 for a 7x7 face)

        Yields:
            Points in order that preserves original relative positions
        """
        from cube.domain.geometric.geometry_types import Point

        r1, c1 = start
        r2, c2 = end
        nm1 = n_slices - 1

        # Detect n_rotations from corner orientation and iterate with
        # inlined rotation formulas. The original (pre-rotation) block is
        # always normalized, so we can iterate without min/max.
        #
        # Rotation formulas (CW):
        #   0: (r, c) -> (r, c)
        #   1: (r, c) -> (nm1-c, r)
        #   2: (r, c) -> (nm1-r, nm1-c)
        #   3: (r, c) -> (c, nm1-r)
        #
        # Reverse rotation formulas (to recover original corners):
        #   reverse of 1 = 3 CW: (r, c) -> (c, nm1-r)
        #   reverse of 2 = 2 CW: (r, c) -> (nm1-r, nm1-c)
        #   reverse of 3 = 1 CW: (r, c) -> (nm1-c, r)

        if r1 <= r2 and c1 <= c2:
            # n_rot == 0: no rotation, iterate directly
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    yield Point(r, c)

        elif r1 > r2 and c1 <= c2:
            # n_rot == 1: reverse corners via 3 CW, then apply 1 CW per point
            # original corners: (c1, nm1-r1) to (c2, nm1-r2) — already normalized
            for r in range(c1, c2 + 1):
                for c in range(nm1 - r1, nm1 - r2 + 1):
                    yield Point(nm1 - c, r)

        elif r1 > r2 and c1 > c2:
            # n_rot == 2: reverse corners via 2 CW, then apply 2 CW per point
            # original corners: (nm1-r1, nm1-c1) to (nm1-r2, nm1-c2) — already normalized
            for r in range(nm1 - r1, nm1 - r2 + 1):
                for c in range(nm1 - c1, nm1 - c2 + 1):
                    yield Point(nm1 - r, nm1 - c)

        else:
            # n_rot == 3 (r1 < r2 and c1 > c2): reverse corners via 1 CW, then apply 3 CW per point
            # original corners: (nm1-c1, r1) to (nm1-c2, r2) — already normalized
            for r in range(nm1 - c1, nm1 - c2 + 1):
                for c in range(r1, r2 + 1):
                    yield Point(c, nm1 - r)

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
        # After 90° CW: start.row > end.row, start.col <= end.col
        # (includes c1 == c2 for single-column blocks rotated to single-row)
        if r1 > r2 and c1 <= c2:
            return 1
        # After 270° CW: start.row <= end.row, start.col > end.col
        # (includes r1 == r2 for single-row blocks rotated to single-column)
        if r1 <= r2 and c1 > c2:
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