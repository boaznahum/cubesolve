"""Runtime-checkable protocol for objects that expose a ``color`` property."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cube.domain.model.Color import Color


@runtime_checkable
class Colorable(Protocol):
    """Any object that has a read-only ``color`` property returning a :class:`Color`."""

    @property
    def color(self) -> Color: ...
