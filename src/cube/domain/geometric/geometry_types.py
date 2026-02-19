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

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple, Protocol

if TYPE_CHECKING:
    from cube.domain.model.Edge import Edge
    from cube.domain.model.PartSlice import EdgeWing

class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()


# Basic coordinate types using NamedTuple for clarity
class Point(NamedTuple):
    """A 2D coordinate point, used for (row, col) or (slice_index, slot)."""
    row: int
    col: int


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
