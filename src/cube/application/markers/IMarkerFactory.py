"""Marker factory protocol."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ._marker_config import MarkerConfig


@runtime_checkable
class IMarkerFactory(Protocol):
    """Protocol for marker factory operations.

    Defines the interface for creating predefined and custom markers.
    All code should depend on this protocol, not the concrete implementation.
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
    # Custom Marker Creation
    # ============================================================

    def create_ring(
        self,
        name: str,
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
        name: str,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom filled circle marker."""
        ...

    def create_cross(
        self,
        name: str,
        color: tuple[float, float, float],
    ) -> MarkerConfig:
        """Create a custom cross marker."""
        ...
