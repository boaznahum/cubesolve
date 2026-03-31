"""Big cube (NxN) solver utilities.

This package contains shared utilities for NxN cube solving:
- Center solving components (NxNCenters)
- Edge pairing components (NxNEdges)
- Corner swap parity fix (CornerSwapParity)
- Face tracking for even cubes (FacesTrackerHolder) - re-exported from tracker/

These are used by:
- reducers/beginner/BeginnerReducer
- direct/cage/CageNxNSolver

Layer: 2 (common)
Can import: protocols/ (Layer 1), common/ utilities
Cannot import: solver implementations (Layer 3)
"""

# Re-export FacesTrackerHolder from tracker package for backward compatibility
from cube.domain.tracker import FacesTrackerHolder

from cube.domain.solver.common.big_cube.CornerSwapParity import CornerSwapParity
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

__all__ = [
    "CornerSwapParity",
    "FacesTrackerHolder",
    "NxNCenters",
    "NxNEdges",
]
