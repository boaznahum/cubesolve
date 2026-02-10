from cube.domain.model import Face, CenterSlice, Color

# Visual marker key for rendering tracker dots on center slices.
# This is ONLY for on-screen display (marker_manager) — NOT used for solver logic.
# Solver logic uses moveable_attributes with _TRACKER_KEY_PREFIX instead.
_TRACKER_VISUAL_MARKER = "tracker_ct"


def tracer_visual_key(tracer_key: str) -> str:
    return _TRACKER_VISUAL_MARKER + tracer_key

def _find_markable_center_slice(face: Face, color: Color) -> CenterSlice:
    """Find a center slice on the given face to mark.

    Prefers a slice matching our target color if available,
    otherwise uses the first available center slice.

    Args:
        face: The Face to find a center slice on.

    Returns:
        A CenterSlice suitable for marking.
    """
    # Prefer a slice matching our target color
    for s in face.center.all_slices:
        if s.color == color:
            return s
    # Fallback to first available slice
    return next(iter(face.center.all_slices))

def find_and_track_slice(face: Face, key: str, color: Color) -> None:

        center_slice = _find_markable_center_slice(face, color)

        # 4. Mark it with our color (reuse existing key)
        edge = center_slice.edge
        edge.moveable_attributes[key] = color

        # 5. Re-add visual marker on the new edge
        cube = face.cube
        if cube.config.face_tracker.annotate:
            cube.sp.marker_manager.add_marker(edge, tracer_visual_key(key), cube.sp.marker_factory.center_tracker(), moveable=True)
