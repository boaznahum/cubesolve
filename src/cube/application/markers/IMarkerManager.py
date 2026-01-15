"""Marker manager protocol."""
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge
    from ._marker_config import MarkerConfig


@runtime_checkable
class IMarkerManager(Protocol):
    """Protocol for marker manager operations.

    This protocol defines the interface for adding/removing/retrieving
    markers on cube stickers. All code should depend on this protocol,
    not the concrete implementation.

    Storage Model:
        Markers are stored as dict[name, config]. Names are provided by callers.
        The same config instance can be stored under different names.

    Rendering Deduplication:
        get_markers() deduplicates visually identical configs and sorts by z_order.
    """

    def add_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        marker: "MarkerConfig",
        moveable: bool = True,
    ) -> None:
        """Add a marker to a PartEdge.

        If a marker with the same name already exists, it is replaced.

        Args:
            part_edge: The sticker to mark
            name: Unique name for this marker on this PartEdge
            marker: The marker configuration
            moveable: If True, marker moves with the sticker color during rotations
                     (stored in moveable_attributes). If False, marker stays at physical
                     position (stored in fixed_attributes).
        """
        ...

    def add_fixed_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        marker: "MarkerConfig",
    ) -> None:
        """Add a marker fixed to a position (structural markers).

        This is for structural markers like origin/on_x/on_y that are set during
        Face initialization and should never change.

        Args:
            part_edge: The sticker to mark
            name: Unique name for this marker
            marker: The marker configuration
        """
        ...

    def remove_marker(
        self,
        part_edge: "PartEdge",
        name: str,
        moveable: bool | None = None,
    ) -> bool:
        """Remove a marker from a PartEdge by name.

        Args:
            part_edge: The sticker to unmark
            name: The name of the marker to remove
            moveable: If True, remove from moveable_attributes. If False, remove from
                     fixed_attributes. If None, try both.

        Returns:
            True if marker was found and removed, False otherwise.
        """
        ...

    def remove_all(
        self,
        name: str,
        parts: Iterable["PartEdge"],
        moveable: bool | None = None,
    ) -> int:
        """Remove marker with given name from all provided parts.

        Args:
            name: The name of the marker to remove
            parts: Iterable of PartEdges to check
            moveable: If True, remove from moveable_attributes. If False, remove from
                     fixed_attributes. If None, remove from all.

        Returns:
            Number of parts where the marker was removed.
        """
        ...

    def get_markers(self, part_edge: "PartEdge") -> list["MarkerConfig"]:
        """Get all markers for a PartEdge, deduplicated and sorted.

        Retrieves markers from both attribute dictionaries. Visually
        identical configs are deduplicated (keeping highest z_order), then
        sorted by z_order (lowest first, so highest draws on top).

        Args:
            part_edge: The sticker to get markers from

        Returns:
            List of unique MarkerConfig objects, sorted by z_order.
        """
        ...

    def has_markers(self, part_edge: "PartEdge") -> bool:
        """Check if a PartEdge has any markers."""
        ...

    def has_marker(self, part_edge: "PartEdge", name: str) -> bool:
        """Check if a PartEdge has a marker with the given name."""
        ...

    def clear_markers(
        self,
        part_edge: "PartEdge",
        moveable: bool | None = None,
    ) -> None:
        """Remove all markers from a PartEdge.

        Args:
            part_edge: The sticker to clear
            moveable: If True, clear only moveable_attributes. If False, clear only
                     fixed_attributes. If None, clear all.
        """
        ...
