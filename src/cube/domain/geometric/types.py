"""
Geometric type definitions for coordinate transformation functions.

All types are centralized here to avoid duplication and confusion.

Naming convention:
- "Unit" prefix = size-independent (accepts n_slices as parameter)
- No prefix = size-bound (n_slices baked in at creation)

Coordinate systems:
- Slice coordinates: (slice_index, slot) - position within a slice
- Face coordinates: (row, col) - position on a face center grid
"""
from __future__ import annotations

from typing import Callable

# Basic coordinate type
Point = tuple[int, int]

# =============================================================================
# SIZE-INDEPENDENT functions (Unit functions) - accept n_slices as parameter
# These have n_slices as FIRST parameter (consistent convention)
# =============================================================================

# Forward: slice coords -> face coords
# Signature: (n_slices, slice_index, slot) -> (row, col)
SliceToCenter = Callable[[int, int, int], Point]

# Reverse: face coords -> slice coords
# Signature: (n_slices, row, col) -> (slice_index, slot)
CenterToSlice = Callable[[int, int, int], Point]

# Edge index computation
# Signature: (n_slices, slice_index) -> edge_index
SliceToEntryEdge = Callable[[int, int], int]

# =============================================================================
# LEGACY: n_slices LAST (to be migrated to n_slices FIRST)
# =============================================================================

# Reverse with n_slices LAST - used by FaceWalkingInfoUnit._compute_reverse
# Signature: (row, col, n_slices) -> (slice_index, slot)
# TODO: Migrate to CenterToSlice (n_slices FIRST) and remove this
CenterToSliceLegacy = Callable[[int, int, int], Point]

# =============================================================================
# SIZE-BOUND functions - n_slices baked in at creation time
# =============================================================================

# Forward: slice coords -> face coords (size-bound)
# Signature: (slice_index, slot) -> (row, col)
PointComputer = Callable[[int, int], Point]

# Reverse: face coords -> slice coords (size-bound)
# Signature: (row, col) -> (slice_index, slot)
ReversePointComputer = Callable[[int, int], Point]
