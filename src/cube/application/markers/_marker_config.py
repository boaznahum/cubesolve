"""Marker configuration dataclass."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .MarkerShape import MarkerShape

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class MarkerConfig:
    """Configuration for a single marker.

    Contains all information needed to draw a marker on a cube sticker.
    The renderer should not need to guess anything - all visual properties
    are specified here.

    Uniqueness Model:
        Markers are identified by their `name` field, NOT by dataclass equality.
        - add_marker: Prevents duplicate names on same PartEdge (skips if name exists)
        - remove_marker: Removes by name match, not by full equality
        This allows creating new MarkerConfig instances with same name to remove/update.

    Attributes:
        name: Unique identifier for this marker type (e.g., "C0", "ORIGIN").
              Used for duplicate prevention and removal - NOT dataclass equality.
        shape: The geometric shape of the marker
        color: RGB color tuple (0.0-1.0 range). If None, use complementary color.
        radius_factor: Outer radius as fraction of cell size (0.0-1.0)
        thickness: Ring thickness relative to outer radius (1.0 = filled)
        height_offset: Height above cell surface (in model resolution units)
        use_complementary_color: If True, color is computed from face color
        z_order: Drawing order (higher = drawn on top). Default 0.
        direction: Arrow direction in degrees (0=right, 90=up, 180=left, 270=down).
                   Only used for ARROW shape. Uses face-local coordinates.
    """

    name: str
    shape: MarkerShape
    color: tuple[float, float, float] | None = None
    radius_factor: float = 1.0
    thickness: float = 1.0
    height_offset: float = 0.1
    use_complementary_color: bool = False
    z_order: int = 0
    direction: float = 0.0  # Arrow direction in degrees (0=right, 90=up)

    def __post_init__(self) -> None:
        """Validate marker configuration."""
        if self.color is None and not self.use_complementary_color:
            raise ValueError(
                f"Marker '{self.name}': must specify color or use_complementary_color"
            )
        if self.radius_factor <= 0 or self.radius_factor > 1.0:
            raise ValueError(
                f"Marker '{self.name}': radius_factor must be in (0, 1.0], got {self.radius_factor}"
            )
        if self.thickness <= 0 or self.thickness > 1.0:
            raise ValueError(
                f"Marker '{self.name}': thickness must be in (0, 1.0], got {self.thickness}"
            )

    def with_z_order(self, z_order: int) -> MarkerConfig:
        """Return a copy with a different z_order."""
        return MarkerConfig(
            name=self.name,
            shape=self.shape,
            color=self.color,
            radius_factor=self.radius_factor,
            thickness=self.thickness,
            height_offset=self.height_offset,
            use_complementary_color=self.use_complementary_color,
            z_order=z_order,
            direction=self.direction,
        )


# Type alias for marker color (RGB 0-255 int or 0.0-1.0 float)
ColorRGB = tuple[float, float, float]
ColorRGB255 = tuple[int, int, int]


def color_255_to_float(color: ColorRGB255) -> ColorRGB:
    """Convert RGB color from 0-255 range to 0.0-1.0 range."""
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)


def color_float_to_255(color: ColorRGB) -> ColorRGB255:
    """Convert RGB color from 0.0-1.0 range to 0-255 range."""
    return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
