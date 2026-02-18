"""Marker configuration dataclass."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .MarkerShape import MarkerShape

if TYPE_CHECKING:
    from ._marker_toolkit import MarkerToolkit


@dataclass(frozen=True)
class MarkerConfig:
    """Configuration for a single marker.

    Contains all information needed to draw a marker on a cube sticker.
    The renderer should not need to guess anything - all visual properties
    are specified here.

    Note: The marker name is NOT part of the config. Names are provided externally
    by callers when adding markers via MarkerManager. This allows the same config
    to be reused with different names (singleton pattern).

    Uniqueness Model:
        Markers are stored by name in MarkerManager. The same config instance
        can be stored under different names. When rendering, visually identical
        configs are deduplicated (keeping highest z_order).

    Attributes:
        shape: The geometric shape of the marker
        color: RGB color tuple (0.0-1.0 range). If None, use complementary color.
        radius_factor: Outer radius as fraction of cell size (0.0-1.0)
        thickness: Ring thickness relative to outer radius (1.0 = filled)
        height_offset: Height above cell surface (in model resolution units)
        use_complementary_color: If True, color is computed from face color
        z_order: Drawing order (higher = drawn on top). Default 0.
        direction: Arrow direction in degrees (0=right, 90=up, 180=left, 270=down).
                   Only used for ARROW shape. Uses face-local coordinates.
        character: Single character to display. Only used for CHARACTER shape.
    """

    shape: MarkerShape
    color: tuple[float, float, float] | None = None
    radius_factor: float = 1.0
    thickness: float = 1.0
    height_offset: float = 0.1
    use_complementary_color: bool = False
    z_order: int = 0
    direction: float = 0.0  # Arrow direction in degrees (0=right, 90=up)
    character: str = ""     # Character to display (for CHARACTER shape)

    def __post_init__(self) -> None:
        """Validate marker configuration."""
        if self.color is None and not self.use_complementary_color:
            raise ValueError(
                "MarkerConfig: must specify color or use_complementary_color"
            )
        if self.radius_factor <= 0 or self.radius_factor > 1.0:
            raise ValueError(
                f"MarkerConfig: radius_factor must be in (0, 1.0], got {self.radius_factor}"
            )
        if self.thickness <= 0 or self.thickness > 1.0:
            raise ValueError(
                f"MarkerConfig: thickness must be in (0, 1.0], got {self.thickness}"
            )

    def _resolve_color(self, toolkit: "MarkerToolkit") -> tuple[float, float, float]:
        """Resolve marker color, handling complementary color logic.

        Args:
            toolkit: The toolkit providing face_color and complementary_color.

        Returns:
            RGB color tuple (0.0-1.0).
        """
        if self.color is not None:
            return self.color
        if self.use_complementary_color:
            return toolkit.complementary_color
        return (1.0, 0.0, 1.0)  # Fallback magenta

    def draw(self, toolkit: "MarkerToolkit") -> None:
        """Draw this marker using toolkit primitives.

        Dispatches to the appropriate toolkit method based on self.shape.
        Implements the MarkerCreator protocol for backward compatibility.

        Args:
            toolkit: Backend-specific toolkit initialized with cell geometry.
        """
        color = self._resolve_color(toolkit)

        if self.shape == MarkerShape.CROSS:
            toolkit.draw_cross(color)

        elif self.shape == MarkerShape.ARROW:
            toolkit.draw_arrow(color, self.direction, self.radius_factor, self.thickness)

        elif self.shape == MarkerShape.CHARACTER:
            toolkit.draw_character(self.character, color, self.radius_factor)

        elif self.shape == MarkerShape.CHECKMARK:
            toolkit.draw_checkmark(color, self.radius_factor, self.thickness, self.height_offset)

        elif self.shape == MarkerShape.BOLD_CROSS:
            toolkit.draw_bold_cross(color, self.radius_factor, self.thickness, self.height_offset)

        elif self.shape == MarkerShape.FILLED_CIRCLE:
            toolkit.draw_filled_circle(self.radius_factor, color, self.height_offset)

        elif self.shape == MarkerShape.RING:
            inner_radius = self.radius_factor * (1.0 - self.thickness)
            toolkit.draw_ring(inner_radius, self.radius_factor, color, self.height_offset)


# Type alias for marker color (RGB 0-255 int or 0.0-1.0 float)
ColorRGB = tuple[float, float, float]
ColorRGB255 = tuple[int, int, int]


def color_255_to_float(color: ColorRGB255) -> ColorRGB:
    """Convert RGB color from 0-255 range to 0.0-1.0 range."""
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)


def color_float_to_255(color: ColorRGB) -> ColorRGB255:
    """Convert RGB color from 0.0-1.0 range to 0-255 range."""
    return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
