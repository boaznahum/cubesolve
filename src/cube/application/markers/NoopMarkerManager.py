"""No-op marker manager for non-animation scenarios."""
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .IMarkerManager import IMarkerManager

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge
    from ._marker_creator_protocol import MarkerCreator


class NoopMarkerManager(IMarkerManager):
    """No-op implementation of IMarkerManager.

    Used when animation is disabled (no backend or non-animation backends).
    All operations are silent no-ops, avoiding CPU waste on marker bookkeeping.
    """

    def add_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        marker: "MarkerCreator",
        moveable: bool = True,
    ) -> None:
        pass

    def add_fixed_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        marker: "MarkerCreator",
    ) -> None:
        pass

    def remove_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        moveable: bool | None = None,
    ) -> bool:
        return False

    def remove_all(
        self,
        name: str,
        parts: Iterable["PartEdge"],
        moveable: bool | None = None,
    ) -> int:
        return 0

    def get_markers(self, part_edge: "PartEdge") -> list["MarkerCreator"]:
        return []

    def has_markers(self, part_edge: "PartEdge") -> bool:
        return False

    def has_marker(self, part_edge: "PartEdge", name: str) -> bool:
        return False

    def clear_markers(
        self,
        part_edge: "PartEdge",
        moveable: bool | None = None,
    ) -> None:
        pass
