"""Common utilities for LBL (Layer-By-Layer) NxN solver.

This module contains shared context managers and helper functions used
by multiple LBL solver components (NxNCenters2, _LBLSlices, etc.).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from cube.domain.model import CenterSlice
from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder

if TYPE_CHECKING:
    from cube.domain.solver.common.SolverElement import SolverElement
    from cube.domain.solver.common.tracker.trackers import FaceTracker

# Key used in moveable_attributes to track center slices during solving
CENTER_SLICE_TRACK_KEY = "xxxxxxx"


def position_l1(slv: SolverElement, l1_white_tracker: FaceTracker) -> None:
    """Position L1 (white face) down.

    Args:
        slv: Solver element providing access to cmn.bring_face_down
        l1_white_tracker: The Layer 1 face tracker to position down
    """
    slv.cmn.bring_face_down(l1_white_tracker.face)
    assert l1_white_tracker.face is slv.cube.down


def clear_center_slice(cs: CenterSlice) -> None:
    """Clear tracking marker from a single center slice.

    Args:
        cs: The center slice to clear
    """
    cs.moveable_attributes.pop(CENTER_SLICE_TRACK_KEY, None)


def clear_all_tracking(slv: SolverElement) -> None:
    """Clear all center slice tracking markers from the cube.

    Args:
        slv: Solver element providing access to cube.centers
    """
    for c in slv.cube.centers:
        for cc in c.all_slices:
            clear_center_slice(cc)


@contextmanager
def setup_l1(slv: SolverElement, l1_white_tracker: FaceTracker) -> Iterator[None]:
    """Setup L1 position and manage tracking lifecycle.

    Positions L1 (white face) down for solving. Tracking is accumulated
    during solving (via _track_row_slices) and cleared only here when
    all slices are done. This protects solved pieces from being destroyed.

    Args:
        slv: Solver element providing access to cube operations
        l1_white_tracker: The Layer 1 face tracker

    Yields:
        None - context manager for setup/cleanup lifecycle
    """
    position_l1(slv, l1_white_tracker)
    try:
        yield
    finally:
        clear_all_tracking(slv)


def _get_side_face_trackers(
        th: FacesTrackerHolder, l1_tracker: FaceTracker
) -> list[FaceTracker]:
    """Get trackers for side faces (not Layer 1 or its opposite).

    Args:
        th: FacesTrackerHolder with all 6 face trackers
        l1_tracker: The Layer 1 face tracker (to exclude with its opposite)

    Returns:
        List of 4 side face trackers
    """
    l1_opposite_face = l1_tracker.face.opposite
    return [t for t in th.trackers
            if t.face is not l1_tracker.face and t.face is not l1_opposite_face]