from cube.application.markers import MarkerCreator
from cube.domain.model import Face, CenterSlice, Color

# Visual marker key for rendering tracker dots on center slices.
# This is ONLY for on-screen display (marker_manager) — NOT used for solver logic.
# Solver logic uses moveable_attributes with _TRACKER_KEY_PREFIX instead.
_TRACKER_VISUAL_MARKER = "tracker_ct"

_cached_visual_face_marker: dict[Color, MarkerCreator] = {}

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

def _find_markable_center_slice(face: Face, color: Color) -> CenterSlice:
    """Find a center slice on the given face to mark.

    Prefers a slice matching our target color if available,
    otherwise uses the first available center slice.

    Args:
        face: The Face to find a center slice on.

    Returns:
        A CenterSlice suitable for marking.
    """
    if True:
        n = face.n_slices
        return face.center.get_slice((n // 2, n // 2))
    else:
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

        # 5. Add visual marker: outlined circle showing face color with black outline
        cube = face.cube
        if cube.config.face_tracker.annotate:
            mm = cube.sp.marker_manager

            # Single outlined circle marker: face-colored fill + black outline
            global _cached_visual_face_marker

            marker = _cached_visual_face_marker.get(color, None)
            if marker is None:

                mf = cube.sp.marker_factory
                ti = cube.config.tracker_indicator
                face_rgb: tuple[float, float, float] = _COLOR_TO_RGB.get(color, (1.0, 0.0, 1.0))  # fallback magenta

                marker = mf.create_outlined_circle(
                    fill_color=face_rgb,
                    outline_color=ti.outline_color,
                    radius_factor=ti.radius_factor,
                    outline_width=ti.outline_width_factor,
                    height_offset=ti.height_offset,
                    min_radius=ti.min_radius,
                    min_outline_width=ti.min_outline_width,
                )
                _cached_visual_face_marker[color] = marker
            else:
                marker = _cached_visual_face_marker[color]

            mm.add_marker(edge, tracer_visual_key(key), marker, moveable=True)
