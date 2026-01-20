"""Face Tracker Package - Tracks face→color mapping for even cubes.

This package provides the tracker system used by even cubes (4x4, 6x6) to
determine which color belongs on which face during solving.

PUBLIC API:
===========

    from cube.domain.tracker import FacesTrackerHolder

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

from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker.MarkedPartTracker import MarkedPartTracker, MultiPartTracker
from cube.domain.tracker.PartSliceTracker import MultiSliceTracker, PartSliceTracker
from cube.domain.tracker.Tracker import CornerTracker, EdgeTracker, PartTracker

__all__ = [
    # Face tracking (for even cubes)
    "FacesTrackerHolder",
    # Part tracking (marker-based, for big cubes)
    "MarkedPartTracker",
    "MultiPartTracker",
    # Slice tracking (marker-based)
    "MultiSliceTracker",
    "PartSliceTracker",
    # Color-based tracking (for 3x3 or post-reduction)
    "CornerTracker",
    "EdgeTracker",
    "PartTracker",
]
