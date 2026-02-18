from cube.domain.model import Face, CenterSlice, Color

# Visual marker key for rendering tracker dots on center slices.
# This is ONLY for on-screen display (marker_manager) — NOT used for solver logic.
# Solver logic uses moveable_attributes with _TRACKER_KEY_PREFIX instead.
_TRACKER_VISUAL_MARKER = "tracker_ct"
_TRACKER_OUTLINE_SUFFIX = "_ol"

# Map Color enum to RGB float tuples for marker rendering.
# These match the standard Rubik's cube color scheme.
_COLOR_TO_RGB: dict[Color, tuple[float, float, float]] = {
    Color.WHITE:  (1.0, 1.0, 1.0),
    Color.YELLOW: (1.0, 0.84, 0.0),
    Color.GREEN:  (0.0, 0.61, 0.28),
    Color.BLUE:   (0.0, 0.27, 0.68),
    Color.RED:    (0.72, 0.07, 0.20),
    Color.ORANGE: (1.0, 0.35, 0.0),
}


def tracer_visual_key(tracer_key: str) -> str:
    return _TRACKER_VISUAL_MARKER + tracer_key

def tracer_outline_key(tracer_key: str) -> str:
    return _TRACKER_VISUAL_MARKER + tracer_key + _TRACKER_OUTLINE_SUFFIX

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

        # 5. Re-add visual markers on the new edge:
        #    - Black outline ring (lower z_order, drawn first)
        #    - Face-colored filled circle (higher z_order, drawn on top)
        cube = face.cube
        if cube.config.face_tracker.annotate:
            mm = cube.sp.marker_manager
            mf = cube.sp.marker_factory
            face_rgb = _COLOR_TO_RGB.get(color, (1.0, 0.0, 1.0))  # fallback magenta

            # Black outline ring - slightly larger, drawn underneath
            outline = mf.create_ring(
                color=(0.0, 0.0, 0.0),
                radius_factor=0.5,
                thickness=0.35,
                height_offset=0.11,
            )
            mm.add_marker(edge, tracer_outline_key(key), outline, moveable=True)

            # Face-colored filled circle - on top
            dot = mf.create_filled_circle(
                color=face_rgb,
                radius_factor=0.4,
                height_offset=0.12,
            )
            mm.add_marker(edge, tracer_visual_key(key), dot, moveable=True)
