"""Single-Step mode codes for debugging specific solver points.

Each SSCode represents a specific point in the solver code where
single-step mode can be triggered for debugging/inspection.

Usage in solver code:
    self._op.enter_single_step_mode(SSCode.NxN_CORNER_PARITY_FIX)

Enable/disable in _config.py:
    SS_CODES = {
        SSCode.NxN_CORNER_PARITY_FIX: True,
        SSCode.NxN_EDGE_PARITY_FIX: False,
    }
"""

from __future__ import annotations

from enum import Enum, auto


class SSCode(Enum):
    """Single-step mode trigger codes.

    Each code identifies a specific point in solver code where
    single-step mode can be enabled for debugging.
    """

    # NxN Orchestrator parity handling
    NxN_CORNER_PARITY_FIX = auto()
    """Pause before fixing corner parity in NxN solver."""

    NxN_EDGE_PARITY_FIX = auto()
    """Pause before fixing edge parity in NxN solver."""

    # Reducer phases
    REDUCER_CENTERS_DONE = auto()
    """Pause after centers are solved."""

    REDUCER_EDGES_DONE = auto()
    """Pause after edges are paired."""

    # 3x3 solver phases
    L1_CROSS_DONE = auto()
    """Pause after L1 cross is solved."""

    L1_CORNERS_DONE = auto()
    """Pause after L1 corners are solved."""

    L2_DONE = auto()
    """Pause after L2 is solved."""

    L3_CROSS_DONE = auto()
    """Pause after L3 cross is solved."""

    L3_CORNERS_DONE = auto()
    """Pause after L3 corners are solved."""

    # Cage solver phases
    CAGE_CENTERS_START = auto()
    """Pause before solving centers in cage method."""

    CAGE_CENTERS_DONE = auto()
    """Pause after solving centers in cage method."""

    # CFOP F2L phases
    F2L_WIDE_MOVE = auto()
    """Pause before executing a wide move (d, u, r, l, f, b) in F2L."""
