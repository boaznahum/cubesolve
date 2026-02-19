"""Outlined circle marker - filled circle with a contrasting outline ring.

Used by the face tracker to show tracked face color with a black outline
for visibility (especially when face color is white on white background).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._marker_creator_protocol import MarkerCreator

if TYPE_CHECKING:
    from ._marker_toolkit import MarkerToolkit

ColorRGB = tuple[float, float, float]

# The toolkit scales radius factors by cell_size * _TOOLKIT_BASE_SCALE.
# We need this to convert between absolute world units and factors.
_TOOLKIT_BASE_SCALE = 0.4


@dataclass(frozen=True)
class OutlinedCircleMarker(MarkerCreator):
    """Circle marker with fill color + outline color.

    Draws two layers:
    1. Outline ring (lower, slightly larger) in outline_color
    2. Filled circle (on top) in fill_color

    Implements MarkerCreator protocol.

    Attributes:
        fill_color: RGB color for the inner filled circle (0.0-1.0).
        outline_color: RGB color for the outer ring (0.0-1.0).
        radius_factor: Radius as fraction of cell size (0.0-1.0).
        outline_width: Outline width as fraction of radius (0.0-1.0).
        height_offset: Height above surface as fraction of cell size.
        z_order: Drawing order (higher = drawn on top).
        min_radius: Minimum absolute radius in world units (0 = no minimum).
        min_outline_width: Minimum absolute outline width in world units (0 = no minimum).
    """

    fill_color: ColorRGB
    outline_color: ColorRGB
    radius_factor: float = 0.4
    outline_width: float = 0.15
    height_offset: float = 0.12
    z_order: int = 0
    min_radius: float = 0.0
    min_outline_width: float = 0.0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        """Draw outlined circle: outline ring underneath, filled circle on top.

        When min_radius or min_outline_width are set, the effective factors
        are boosted so the actual rendered size meets the minimum. This ensures
        visibility on big cubes where cells are tiny.
        """
        inner_r = self.radius_factor

        # Boost radius factor if actual size would be below minimum
        if self.min_radius > 0:
            base_r = toolkit.cell_size * _TOOLKIT_BASE_SCALE
            if base_r > 0:
                min_factor = self.min_radius / base_r
                inner_r = max(inner_r, min_factor)

        outline_r = inner_r * self.outline_width

        # Boost outline if actual size would be below minimum
        if self.min_outline_width > 0:
            base_r = toolkit.cell_size * _TOOLKIT_BASE_SCALE
            if base_r > 0:
                min_outline_factor = self.min_outline_width / base_r
                outline_r = max(outline_r, min_outline_factor)

        outer_r = inner_r + outline_r
        # Outline ring (drawn first = underneath)
        toolkit.draw_ring(inner_r, outer_r, self.outline_color, self.height_offset)
        # Filled circle (drawn second = on top)
        toolkit.draw_filled_circle(inner_r, self.fill_color, self.height_offset)
