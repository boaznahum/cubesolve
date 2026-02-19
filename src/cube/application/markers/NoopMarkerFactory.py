"""No-op marker factory for non-animation scenarios."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ._marker_creator_protocol import MarkerCreator
from .IMarkerFactory import IMarkerFactory

if TYPE_CHECKING:
    from ._marker_toolkit import MarkerToolkit


class _NoopMarkerCreator(MarkerCreator):
    """Lightweight marker that draws nothing. Singleton via _NOOP."""

    __slots__ = ()

    z_order: int = 0

    def get_z_order(self) -> int:
        return 0

    def draw(self, toolkit: "MarkerToolkit") -> None:
        pass

    def __hash__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _NoopMarkerCreator)


_NOOP = _NoopMarkerCreator()


class NoopMarkerFactory(IMarkerFactory):
    """No-op implementation of IMarkerFactory.

    Used when animation is disabled. Returns a shared _NoopMarkerCreator
    singleton — no validation, no CPU waste.
    """

    def c0(self) -> MarkerCreator:
        return _NOOP

    def c1(self) -> MarkerCreator:
        return _NOOP

    def c2(self) -> MarkerCreator:
        return _NOOP

    def at_risk(self) -> MarkerCreator:
        return _NOOP

    def origin(self) -> MarkerCreator:
        return _NOOP

    def on_x(self) -> MarkerCreator:
        return _NOOP

    def on_y(self) -> MarkerCreator:
        return _NOOP

    def ltr_origin(self) -> MarkerCreator:
        return _NOOP

    def ltr_arrow_x(self) -> MarkerCreator:
        return _NOOP

    def ltr_arrow_y(self) -> MarkerCreator:
        return _NOOP

    def create_ring(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 1.0,
        thickness: float = 0.5,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerCreator:
        return _NOOP

    def create_filled_circle(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerCreator:
        return _NOOP

    def create_cross(
        self,
        color: tuple[float, float, float],
    ) -> MarkerCreator:
        return _NOOP

    def checkmark(
        self,
        color: tuple[float, float, float] = (0.0, 0.8, 0.0),
    ) -> MarkerCreator:
        return _NOOP

    def char(
        self,
        character: str,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> MarkerCreator:
        return _NOOP

    def create_outlined_circle(
        self,
        fill_color: tuple[float, float, float],
        outline_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius_factor: float = 0.4,
        outline_width: float = 0.15,
        height_offset: float = 0.12,
        z_order: int = 0,
        min_radius: float = 0.0,
        min_outline_width: float = 0.0,
    ) -> MarkerCreator:
        return _NOOP
