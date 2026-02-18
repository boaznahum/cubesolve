"""Marker toolkit protocol - abstract drawing primitives for markers.

Each renderer backend implements this protocol to translate marker drawing
commands into backend-specific graphics calls (OpenGL display lists, VBOs, etc.).

The toolkit is created per-cell by the renderer, initialized with the cell's
geometry (corners, normal, size, face color). Marker creators call these methods
without knowing anything about the rendering backend.

Coordinate conventions:
    - radius/inner_radius/outer_radius: fraction of cell size (0.0-1.0),
      scaled internally by the toolkit (typically cell_size * 0.4 * factor)
    - height: fraction of cell size, scaled internally (typically cell_size * factor)
    - color: RGB tuple (0.0-1.0 range)
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

ColorRGB = tuple[float, float, float]


@runtime_checkable
class MarkerToolkit(Protocol):
    """Abstract drawing primitives for markers. Implemented per backend."""

    @property
    def face_color(self) -> ColorRGB:
        """RGB color of the cell's face (0.0-1.0 range).

        Marker creators can use this to compute complementary colors.
        """
        ...

    @property
    def complementary_color(self) -> ColorRGB:
        """Pre-computed complementary color for maximum contrast with face_color."""
        ...

    def draw_ring(
        self,
        inner_radius: float,
        outer_radius: float,
        color: ColorRGB,
        height: float,
    ) -> None:
        """Draw a 3D ring (hollow cylinder) above the cell surface.

        Args:
            inner_radius: Inner radius as fraction of cell size.
            outer_radius: Outer radius as fraction of cell size.
            color: RGB color (0.0-1.0).
            height: Height above surface as fraction of cell size.
        """
        ...

    def draw_filled_circle(
        self,
        radius: float,
        color: ColorRGB,
        height: float,
    ) -> None:
        """Draw a filled circle (solid disk) above the cell surface.

        Args:
            radius: Radius as fraction of cell size.
            color: RGB color (0.0-1.0).
            height: Height above surface as fraction of cell size.
        """
        ...

    def draw_cross(self, color: ColorRGB) -> None:
        """Draw an X cross through the cell corners.

        Args:
            color: RGB color (0.0-1.0).
        """
        ...

    def draw_arrow(
        self,
        color: ColorRGB,
        direction: float,
        radius_factor: float,
        thickness: float,
    ) -> None:
        """Draw a directional arrow marker.

        Args:
            color: RGB color (0.0-1.0).
            direction: Arrow direction in degrees (0=right, 90=up).
            radius_factor: Size factor (0.0-1.0).
            thickness: Stroke thickness factor.
        """
        ...

    def draw_checkmark(
        self,
        color: ColorRGB,
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        """Draw a checkmark (plus sign) marker.

        Args:
            color: RGB color (0.0-1.0).
            radius_factor: Size factor.
            thickness: Stroke thickness.
            height_offset: Height above surface.
        """
        ...

    def draw_bold_cross(
        self,
        color: ColorRGB,
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        """Draw a bold X cross marker (capsule strokes).

        Args:
            color: RGB color (0.0-1.0).
            radius_factor: Size factor.
            thickness: Stroke thickness.
            height_offset: Height above surface.
        """
        ...

    def draw_character(
        self,
        character: str,
        color: ColorRGB,
        radius_factor: float,
    ) -> None:
        """Draw a single character marker using line segments.

        Args:
            character: Single character to display.
            color: RGB color (0.0-1.0).
            radius_factor: Size factor.
        """
        ...
