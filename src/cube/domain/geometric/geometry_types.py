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

# Type for slice index computation function
# Takes (row, col, n_slices) and returns 0-based slice index
SliceIndexComputerUnit = Callable[[int, int, int], int]



# Takes (row, col) and returns 0-based slice index
# claude document  this type, it actually pass n_slices to SliceIndexComputerUnit
SliceIndexComputer = Callable[[int, int, int], int]


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()

