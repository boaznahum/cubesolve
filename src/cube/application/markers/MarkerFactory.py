"""Factory for predefined markers with singleton caching."""
from __future__ import annotations

from typing import Any

from .IMarkerFactory import IMarkerFactory
from ._marker_config import color_255_to_float
from ._marker_creator_protocol import MarkerCreator
from ._marker_creators import (
    ArrowMarker,
    BoldCrossMarker,
    CharacterMarker,
    CheckmarkMarker,
    CrossMarker,
    FilledCircleMarker,
    RingMarker,
)
from ._outlined_circle_marker import OutlinedCircleMarker


class MarkerFactory(IMarkerFactory):
    """Factory providing predefined markers.

    Implements IMarkerFactory protocol.

    This factory provides all standard markers used in the application:
    - Animation markers: C0, C1, C2
    - Coordinate markers: ORIGIN, ON_X, ON_Y
    - Debug/sample markers

    All factory methods use caching (singleton pattern) - calling the same method
    with the same arguments returns the same instance every time.
    The cache is maintained at the class level, shared across all instances.

    Developers can also create custom markers using create_* methods.
    """

    # Class-level cache for singleton instances
    _cache: dict[tuple[str, ...], Any] = {}

    # ============================================================
    # Animation Markers (used by solver/animation system)
    # ============================================================

    def c0(self) -> MarkerCreator:
        """C0 marker - tracker anchor indicator."""
        key = ("c0",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = RingMarker(
                radius_factor=1.0,
                thickness=0.8,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def c1(self) -> MarkerCreator:
        """C1 marker - moved piece indicator."""
        key = ("c1",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = FilledCircleMarker(
                radius_factor=0.6,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def c2(self) -> MarkerCreator:
        """C2 marker - destination slot indicator."""
        key = ("c2",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = RingMarker(
                radius_factor=1.0,
                thickness=0.3,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def at_risk(self) -> MarkerCreator:
        """At-risk marker - bold red X for pieces that may be destroyed."""
        key = ("at_risk",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = BoldCrossMarker(
                color=(1.0, 0.2, 0.2),
                radius_factor=0.85,
                thickness=1.0,
                height_offset=0.15,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Coordinate Markers (used by Face initialization)
    # ============================================================

    def origin(self) -> MarkerCreator:
        """Origin marker - black X cross at [0,0] reference point."""
        key = ("origin",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CrossMarker(color=(0.0, 0.0, 0.0))
        return MarkerFactory._cache[key]

    def on_x(self) -> MarkerCreator:
        """On-X marker - blueviolet X cross for X-axis direction."""
        key = ("on_x",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CrossMarker(color=(0.54, 0.17, 0.89))
        return MarkerFactory._cache[key]

    def on_y(self) -> MarkerCreator:
        """On-Y marker - deepskyblue X cross for Y-axis direction."""
        key = ("on_y",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CrossMarker(color=(0.0, 0.75, 1.0))
        return MarkerFactory._cache[key]

    # ============================================================
    # LTR Coordinate System Markers
    # ============================================================

    def ltr_origin(self) -> MarkerCreator:
        """LTR origin marker - filled black circle at coordinate origin."""
        key = ("ltr_origin",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = FilledCircleMarker(
                color=(0.0, 0.0, 0.0),
                radius_factor=0.4,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def ltr_arrow_x(self) -> MarkerCreator:
        """LTR X-axis arrow - red arrow pointing right."""
        key = ("ltr_arrow_x",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = ArrowMarker(
                color=(1.0, 0.0, 0.0),
                direction=0.0,
                radius_factor=0.8,
                thickness=1.0,
            )
        return MarkerFactory._cache[key]

    def ltr_arrow_y(self) -> MarkerCreator:
        """LTR Y-axis arrow - blue arrow pointing up."""
        key = ("ltr_arrow_y",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = ArrowMarker(
                color=(0.0, 0.0, 1.0),
                direction=90.0,
                radius_factor=0.8,
                thickness=1.0,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Legacy Markers (with fixed colors from config)
    # ============================================================

    def c0_legacy(self) -> MarkerCreator:
        """C0 marker with legacy fixed color (mediumvioletred)."""
        key = ("c0_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = RingMarker(
                color=color_255_to_float((199, 21, 133)),
                radius_factor=1.0,
                thickness=0.8,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def c1_legacy(self) -> MarkerCreator:
        """C1 marker with legacy fixed color (mediumvioletred)."""
        key = ("c1_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = FilledCircleMarker(
                color=color_255_to_float((199, 21, 133)),
                radius_factor=0.6,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def c2_legacy(self) -> MarkerCreator:
        """C2 marker with legacy fixed color (darkgreen)."""
        key = ("c2_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = RingMarker(
                color=color_255_to_float((0, 100, 0)),
                radius_factor=1.0,
                thickness=0.3,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Custom Marker Creation
    # ============================================================

    def create_ring(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 1.0,
        thickness: float = 0.5,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerCreator:
        """Create a custom ring marker."""
        key = ("create_ring", str(color), str(radius_factor), str(thickness), str(height_offset), str(use_complementary_color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = RingMarker(
                color=color,
                radius_factor=radius_factor,
                thickness=thickness,
                height_offset=height_offset,
                use_complementary_color=use_complementary_color,
            )
        return MarkerFactory._cache[key]

    def create_filled_circle(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerCreator:
        """Create a custom filled circle marker."""
        key = ("create_filled_circle", str(color), str(radius_factor), str(height_offset), str(use_complementary_color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = FilledCircleMarker(
                color=color,
                radius_factor=radius_factor,
                height_offset=height_offset,
                use_complementary_color=use_complementary_color,
            )
        return MarkerFactory._cache[key]

    def create_cross(
        self,
        color: tuple[float, float, float],
    ) -> MarkerCreator:
        """Create a custom cross marker."""
        key = ("create_cross", str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CrossMarker(color=color)
        return MarkerFactory._cache[key]

    # ============================================================
    # Special Shape Markers
    # ============================================================

    def checkmark(
        self,
        color: tuple[float, float, float] = (0.0, 0.8, 0.0),
    ) -> MarkerCreator:
        """Create a checkmark marker. Cached by color."""
        key = ("checkmark", str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CheckmarkMarker(
                color=color,
                radius_factor=0.85,
                thickness=1.0,
                height_offset=0.08,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Character Markers
    # ============================================================

    def char(
        self,
        character: str,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> MarkerCreator:
        """Create a character marker. Cached by (character, color)."""
        key = ("char", character, str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = CharacterMarker(
                character=character,
                color=color,
                radius_factor=0.8,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Outlined Circle Markers
    # ============================================================

    def create_outlined_circle(
        self,
        fill_color: tuple[float, float, float],
        outline_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius_factor: float = 0.4,
        outline_width: float = 0.15,
        height_offset: float = 0.12,
        z_order: int = 0,
    ) -> MarkerCreator:
        """Create an outlined circle marker (filled circle with outline ring)."""
        key = (
            "outlined_circle",
            str(fill_color),
            str(outline_color),
            str(radius_factor),
            str(outline_width),
            str(height_offset),
            str(z_order),
        )
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = OutlinedCircleMarker(
                fill_color=fill_color,
                outline_color=outline_color,
                radius_factor=radius_factor,
                outline_width=outline_width,
                height_offset=height_offset,
                z_order=z_order,
            )
        return MarkerFactory._cache[key]


