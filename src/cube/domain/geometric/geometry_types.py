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

from enum import Enum, auto
from typing import NamedTuple, Protocol


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()


# Basic coordinate types using NamedTuple for clarity
class Point(NamedTuple):
    """A 2D coordinate point, used for (row, col) or (slice_index, slot)."""
    row: int
    col: int


class Block(NamedTuple):
    """A rectangle defined by two corner points.

    Note: The start and end points may not be in normalized order (i.e., start
    may not be top-left and end may not be bottom-right). Consumers should
    normalize the coordinates when needed for specific operations.
    """
    start: Point
    end: Point


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