"""Marker factory protocol."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ._marker_config import MarkerConfig
from ._outlined_circle_marker import OutlinedCircleMarker


@runtime_checkable
class IMarkerFactory(Protocol):
    """Protocol for marker factory operations.

    Defines the interface for creating predefined and custom markers.
    All code should depend on this protocol, not the concrete implementation.

    All factory methods should use caching (singleton pattern) - calling the same
    method with the same arguments returns the same MarkerConfig instance every time.
    """

    # ============================================================
    # Animation Markers
    # ============================================================

    def c0(self) -> MarkerConfig:
        """C0 marker - tracker anchor indicator."""
        ...

    def c1(self) -> MarkerConfig:
        """C1 marker - moved piece indicator."""
        ...

    def c2(self) -> MarkerConfig:
        """C2 marker - destination slot indicator."""
        ...

    def at_risk(self) -> MarkerConfig:
        """At-risk marker - bold red X for pieces that may be destroyed."""
        ...

    # ============================================================
    # Coordinate Markers
    # ============================================================

    def origin(self) -> MarkerConfig:
        """Origin marker - face coordinate origin."""
        ...

    def on_x(self) -> MarkerConfig:
        """On-X marker - X-axis direction indicator."""
        ...

    def on_y(self) -> MarkerConfig:
        """On-Y marker - Y-axis direction indicator."""
        ...

    # ============================================================
    # LTR Coordinate System Markers
    # ============================================================

    def ltr_origin(self) -> MarkerConfig:
        """LTR origin marker - filled circle at coordinate origin."""
        ...

    def ltr_arrow_x(self) -> MarkerConfig:
        """LTR X-axis arrow - red arrow pointing right."""
        ...

    def ltr_arrow_y(self) -> MarkerConfig:
        """LTR Y-axis arrow - blue arrow pointing up."""
        ...

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
    ) -> MarkerConfig:
        """Create a custom ring marker."""
        ...

    def create_filled_circle(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom filled circle marker."""
        ...

    def create_cross(
        self,
        color: tuple[float, float, float],
    ) -> MarkerConfig:
        """Create a custom cross marker."""
        ...

    def checkmark(
        self,
        color: tuple[float, float, float] = (0.0, 0.8, 0.0),
    ) -> MarkerConfig:
        """Create a thick green checkmark (✓) marker."""
        ...

    def char(
        self,
        character: str,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> MarkerConfig:
        """Create a character marker.

        Multiple characters with different values can be placed on same cell.
        """
        ...

    # ============================================================
    # Outlined Circle Markers (MarkerCreator-based)
    # ============================================================

    def create_outlined_circle(
        self,
        fill_color: tuple[float, float, float],
        outline_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius_factor: float = 0.4,
        outline_width: float = 0.15,
        height_offset: float = 0.12,
        z_order: int = 0,
    ) -> OutlinedCircleMarker:
        """Create an outlined circle marker (filled circle with outline ring).

        Used by face tracker to show tracked face color with visible outline.
        """
        ...
