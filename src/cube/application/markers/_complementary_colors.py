"""Shared complementary color table for marker rendering.

Maps cube face colors (RGB 0.0-1.0) to high-contrast marker colors.
Used by both the pyglet2 backend (VBO rendering) and the WebGL backend
(JSON serialization) to resolve ``use_complementary_color`` markers.
"""
from __future__ import annotations

ColorRGB = tuple[float, float, float]

# Complementary colors for each cube face color (RGB 0.0-1.0)
# These provide maximum contrast for visibility
_COMPLEMENTARY_COLORS: dict[ColorRGB, ColorRGB] = {
    # Red face -> Cyan marker
    (1.0, 0.0, 0.0): (0.0, 1.0, 1.0),
    # Green face -> Magenta marker
    (0.0, 1.0, 0.0): (1.0, 0.0, 1.0),
    # Blue face -> Yellow marker
    (0.0, 0.0, 1.0): (1.0, 1.0, 0.0),
    # Yellow face -> Blue/Purple marker
    (1.0, 1.0, 0.0): (0.4, 0.2, 1.0),
    # Orange face -> Cyan marker
    (1.0, 0.5, 0.0): (0.0, 1.0, 1.0),
    # White face -> Dark magenta marker
    (1.0, 1.0, 1.0): (0.6, 0.0, 0.6),
}

# Default marker color if face color not found (bright magenta)
DEFAULT_MARKER_COLOR: ColorRGB = (1.0, 0.0, 1.0)


def get_complementary_color(face_color: ColorRGB) -> ColorRGB:
    """Get a complementary marker color for maximum contrast.

    Rounds to 1 decimal place to handle floating-point imprecision,
    then looks up in the complementary color table.
    Falls back to bright magenta if the face color is not in the table.

    Args:
        face_color: RGB tuple (0.0-1.0) of the face color.

    Returns:
        RGB tuple for the marker color.
    """
    rounded = (round(face_color[0], 1), round(face_color[1], 1), round(face_color[2], 1))
    return _COMPLEMENTARY_COLORS.get(rounded, DEFAULT_MARKER_COLOR)
