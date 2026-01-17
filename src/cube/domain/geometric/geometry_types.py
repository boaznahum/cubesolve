from __future__ import annotations

from enum import Enum, auto
from typing import Callable


# =============================================================================
# SLICE INDEX COMPUTATION - Derived from geometry (Issue #55)
# =============================================================================
#
# The slice index computation is derived dynamically from geometry:
#   - does_slice_cut_rows_or_columns(): determines if we use row or col
#   - does_slice_of_face_start_with_face(): determines if direct or inverted
#
# Key insight:
#   - "cuts rows" = vertical slice → column coordinate identifies which slice
#   - "cuts columns" = horizontal slice → row coordinate identifies which slice
#


class SliceIndexComputerUnit:
    """Callable that computes 0-based slice index from (row, col, n_slices)."""

    def __init__(self, func: "Callable[[int, int, int], int]") -> None:
        self._func = func

    def __call__(self, row: int, col: int, n_slices: int) -> int:
        """Compute 0-based slice index for a coordinate on a face."""
        return self._func(row, col, n_slices)


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()

