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
        Markers use full dataclass equality (frozen=True, so hashable).
        - add_marker: Skips only if exact same marker exists (all fields equal)
        - remove_marker: Removes by exact match (all fields must match)
        - remove_markers_by_name: Removes all markers with given name
        This allows multiple markers of same type (name) with different properties
        (e.g., two "CHAR" markers with different characters on same cell).

    Attributes:
        name: Type identifier for this marker (e.g., "C0", "ORIGIN", "CHAR").
              Multiple markers with same name but different properties are allowed.
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

    name: str
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
            character=self.character,
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
