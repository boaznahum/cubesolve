"""Face Tracker Package - Tracks face→color mapping for even cubes.

This package provides the tracker system used by even cubes (4x4, 6x6) to
determine which color belongs on which face during solving.

PUBLIC API:
===========

    from cube.domain.solver.common.tracker import FacesTrackerHolder

    # For solving (holder-specific):
    with FacesTrackerHolder(solver) as holder:
        face_colors = holder.face_colors
        if holder.part_match_faces(edge):
            # edge is correctly positioned

    # For display (holder-agnostic static methods):
    color = FacesTrackerHolder.get_tracked_edge_color(part_edge)
    if color is not None:
        # Display indicator with this color

INTERNAL CLASSES:
=================
Do NOT import these directly - they are implementation details:
- FaceTracker, SimpleFaceTracker, MarkedFaceTracker (base classes)
- NxNCentersFaceTrackers (factory)
"""

from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder

__all__ = [
    "FacesTrackerHolder",
]
