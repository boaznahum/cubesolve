"""Concrete MarkerCreator implementations — one class per shape.

Each class holds its visual data and knows how to draw itself
via toolkit primitives. No shape dispatch — pure OOP.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._marker_creator_protocol import MarkerCreator

if TYPE_CHECKING:
    from ._marker_toolkit import MarkerToolkit

ColorRGB = tuple[float, float, float]
ColorRGB255 = tuple[int, int, int]


def color_255_to_float(color: ColorRGB255) -> ColorRGB:
    """Convert RGB color from 0-255 range to 0.0-1.0 range."""
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)


def color_float_to_255(color: ColorRGB) -> ColorRGB255:
    """Convert RGB color from 0.0-1.0 range to 0-255 range."""
    return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))


def _resolve_color(
    color: ColorRGB | None,
    use_complementary: bool,
    toolkit: "MarkerToolkit",
) -> ColorRGB:
    """Resolve marker color at draw time."""
    if color is not None:
        return color
    if use_complementary:
        return toolkit.complementary_color
    return (1.0, 0.0, 1.0)  # Fallback magenta


@dataclass(frozen=True)
class RingMarker(MarkerCreator):
    """Ring (hollow circle) marker."""

    color: ColorRGB | None = None
    radius_factor: float = 1.0
    thickness: float = 0.5
    height_offset: float = 0.1
    use_complementary_color: bool = False
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        c = _resolve_color(self.color, self.use_complementary_color, toolkit)
        inner = self.radius_factor * (1.0 - self.thickness)
        toolkit.draw_ring(inner, self.radius_factor, c, self.height_offset)


@dataclass(frozen=True)
class FilledCircleMarker(MarkerCreator):
    """Filled circle (solid disk) marker."""

    color: ColorRGB | None = None
    radius_factor: float = 0.6
    height_offset: float = 0.1
    use_complementary_color: bool = False
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        c = _resolve_color(self.color, self.use_complementary_color, toolkit)
        toolkit.draw_filled_circle(self.radius_factor, c, self.height_offset)


@dataclass(frozen=True)
class CrossMarker(MarkerCreator):
    """X cross through cell corners."""

    color: ColorRGB = (0.0, 0.0, 0.0)
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        toolkit.draw_cross(self.color)


@dataclass(frozen=True)
class ArrowMarker(MarkerCreator):
    """Directional arrow marker."""

    color: ColorRGB = (0.0, 0.0, 0.0)
    direction: float = 0.0
    radius_factor: float = 0.8
    thickness: float = 1.0
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        toolkit.draw_arrow(self.color, self.direction, self.radius_factor, self.thickness)


@dataclass(frozen=True)
class CheckmarkMarker(MarkerCreator):
    """Checkmark (tick) marker."""

    color: ColorRGB = (0.0, 0.8, 0.0)
    radius_factor: float = 0.85
    thickness: float = 1.0
    height_offset: float = 0.08
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        toolkit.draw_checkmark(self.color, self.radius_factor, self.thickness, self.height_offset)


@dataclass(frozen=True)
class BoldCrossMarker(MarkerCreator):
    """Bold X cross marker (capsule strokes)."""

    color: ColorRGB = (1.0, 0.2, 0.2)
    radius_factor: float = 0.85
    thickness: float = 1.0
    height_offset: float = 0.15
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        toolkit.draw_bold_cross(self.color, self.radius_factor, self.thickness, self.height_offset)


@dataclass(frozen=True)
class CharacterMarker(MarkerCreator):
    """Single character drawn with line segments."""

    character: str = ""
    color: ColorRGB = (0.0, 0.0, 0.0)
    radius_factor: float = 0.8
    z_order: int = 0

    def get_z_order(self) -> int:
        return self.z_order

    def draw(self, toolkit: "MarkerToolkit") -> None:
        toolkit.draw_character(self.character, self.color, self.radius_factor)
