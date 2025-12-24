"""Big cube (NxN) solver utilities.

This package contains shared utilities for NxN cube solving:
- Center solving components (NxNCenters)
- Edge pairing components (NxNEdges)
- Corner parity fix (NxNCorners)
- Face tracking for even cubes (FaceTrackerHolder)

Private implementation details (prefixed with _):
- _NxNCentersFaceTracker - Face tracking implementation

These are used by:
- reducers/beginner/BeginnerReducer
- direct/cage/CageNxNSolver

Layer: 2 (common)
Can import: protocols/ (Layer 1), common/ utilities
Cannot import: solver implementations (Layer 3)
"""

from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNCorners import NxNCorners
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

__all__ = [
    "FacesTrackerHolder",
    "NxNCenters",
    "NxNCorners",
    "NxNEdges",
]
