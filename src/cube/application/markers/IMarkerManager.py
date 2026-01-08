"""Marker manager protocol."""
from __future__ import annotations

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
    """

    def add_marker(
        self,
        part_edge: "PartEdge",
        marker: "MarkerConfig",
        moveable: bool,
    ) -> None:
        """Add a marker to a PartEdge.

        Args:
            part_edge: The sticker to mark
            marker: The marker configuration
            moveable: If True, marker moves with the sticker color during rotations
                     (stored in c_attributes). If False, marker stays at physical
                     position (stored in f_attributes).
        """
        ...

    def add_fixed_marker(
        self,
        part_edge: "PartEdge",
        marker: "MarkerConfig",
    ) -> None:
        """Add a marker fixed to a position (structural markers).

        This is for structural markers like origin/on_x/on_y that are set during
        Face initialization and should never change.

        Args:
            part_edge: The sticker to mark
            marker: The marker configuration
        """
        ...

    def remove_marker(
        self,
        part_edge: "PartEdge",
        marker: "MarkerConfig",
        moveable: bool | None = None,
    ) -> bool:
        """Remove a marker from a PartEdge (exact match required).

        Args:
            part_edge: The sticker to unmark
            marker: The marker configuration to remove (all fields must match)
            moveable: If True, remove from c_attributes. If False, remove from
                     f_attributes. If None, try both.

        Returns:
            True if marker was found and removed, False otherwise.
        """
        ...

    def remove_markers_by_name(
        self,
        part_edge: "PartEdge",
        name: str,
        moveable: bool | None = None,
    ) -> int:
        """Remove all markers with a given name from a PartEdge.

        Unlike remove_marker which requires exact match, this removes all markers
        that have the specified name regardless of other properties.

        Args:
            part_edge: The sticker to unmark
            name: The marker name/type to remove (e.g., "C1", "ORIGIN")
            moveable: If True, remove from c_attributes. If False, remove from
                     f_attributes. If None, remove from all.

        Returns:
            Number of markers removed.
        """
        ...

    def get_markers(self, part_edge: "PartEdge") -> list["MarkerConfig"]:
        """Get all markers for a PartEdge.

        Retrieves markers from all attribute dictionaries and returns
        them sorted by z_order (lowest first, so highest draws on top).

        Args:
            part_edge: The sticker to get markers from

        Returns:
            List of MarkerConfig objects, sorted by z_order.
        """
        ...

    def has_markers(self, part_edge: "PartEdge") -> bool:
        """Check if a PartEdge has any markers."""
        ...

    def clear_markers(
        self,
        part_edge: "PartEdge",
        moveable: bool | None = None,
    ) -> None:
        """Remove all markers from a PartEdge.

        Args:
            part_edge: The sticker to clear
            moveable: If True, clear only c_attributes. If False, clear only
                     f_attributes. If None, clear all.
        """
        ...
