"""Marker creator protocol - stored on PartEdge, knows how to draw itself.

MarkerCreator is the base protocol for all marker types. Each concrete
implementation holds its own visual data (colors, sizes, etc.) and knows
how to draw itself using abstract toolkit primitives.

Concrete implementations: RingMarker, FilledCircleMarker, CrossMarker,
ArrowMarker, CheckmarkMarker, BoldCrossMarker, CharacterMarker,
OutlinedCircleMarker.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ._marker_toolkit import MarkerToolkit


@runtime_checkable
class MarkerCreator(Protocol):
    """Stored on PartEdge. Knows its data + how to draw via toolkit."""

    z_order: int
    """Drawing order (higher = drawn on top). Default 0."""

    def draw(self, toolkit: "MarkerToolkit") -> None:
        """Draw this marker using the provided toolkit primitives.

        Args:
            toolkit: Backend-specific toolkit initialized with cell geometry.
        """
        ...
