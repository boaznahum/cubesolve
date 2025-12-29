"""Big cube (NxN) solver utilities.

This package contains shared utilities for NxN cube solving:
- Center solving components (NxNCenters)
- Edge pairing components (NxNEdges)
- Corner parity fix (NxNCorners)
- Face tracking for even cubes (FacesTrackerHolder) - re-exported from tracker/

These are used by:
- reducers/beginner/BeginnerReducer
- direct/cage/CageNxNSolver

Layer: 2 (common)
Can import: protocols/ (Layer 1), common/ utilities
Cannot import: solver implementations (Layer 3)
"""

# Re-export FacesTrackerHolder from tracker package for backward compatibility
from cube.domain.solver.common.tracker import FacesTrackerHolder

from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNCorners import NxNCorners
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

__all__ = [
    "FacesTrackerHolder",
    "NxNCenters",
    "NxNCorners",
    "NxNEdges",
]
