"""View marker utilities - Re-export from domain for backward compatibility."""

# VMarker has moved to domain layer.
# This re-export maintains backward compatibility.
from cube.domain.model.VMarker import (
    VMarker,
    viewer_add_view_marker,
    viewer_remove_view_marker,
    viewer_get_markers,
)

__all__ = ['VMarker', 'viewer_add_view_marker', 'viewer_remove_view_marker', 'viewer_get_markers']
