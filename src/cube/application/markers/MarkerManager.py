"""Marker manager - central authority for adding and retrieving markers."""
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Hashable, Any

from .IMarkerManager import IMarkerManager
from ._marker_creator_protocol import MarkerCreator

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge


# Key used to store markers in fixed_attributes/moveable_attributes
_MARKER_KEY: str = "markers"


class MarkerManager(IMarkerManager):
    """Central manager for marker operations on cube stickers.

    This is the ONLY class that should add or retrieve markers from PartEdges.
    All other code (AnnotationManager, Face init, renderers) must use this manager.

    Storage Model:
        Markers are stored as dict[name, config] under the "markers" key.
        Names are provided by callers when adding markers. The same config
        instance can be stored under different names.

    Rendering Deduplication:
        When get_markers() is called, visually identical configs are deduplicated
        (keeping highest z_order), then sorted by z_order for proper layering.

    Markers can be stored in two modes:
    - Moveable (moveable_attributes): Marker follows the sticker color during rotations
    - Fixed (fixed_attributes): Marker stays at the physical position

    Usage:
        manager = MarkerManager()

        # Add a moveable marker (follows piece during rotation)
        manager.add_marker(part_edge, "c1", MarkerFactory.c1(), moveable=True)

        # Add a fixed marker (stays at position)
        manager.add_marker(part_edge, "c2", MarkerFactory.c2(), moveable=False)

        # Get all markers for rendering (deduplicated, sorted)
        markers = manager.get_markers(part_edge)

        # Remove a marker by name
        manager.remove_marker(part_edge, "c1")

        # Remove a marker from multiple parts
        manager.remove_all("c1", [edge1, edge2, edge3])
    """

    def __init__(self) -> None:
        """Initialize the marker manager."""
        # Could add caching or other state here if needed
        pass

    def add_marker(
        self,
        part_edge: PartEdge,
        name: str,
        marker: MarkerCreator,
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
        if moveable:
            attrs = part_edge.moveable_attributes
        else:
            attrs = part_edge.fixed_attributes

        self._add_to_dict(attrs, name, marker)

    def add_fixed_marker(
        self,
        part_edge: PartEdge,
        name: str,
        marker: MarkerCreator,
    ) -> None:
        """Add a marker fixed to a position (stored in fixed_attributes).

        This is equivalent to add_marker(moveable=False) but with a clearer name
        for structural markers like origin/on_x/on_y that are set during
        Face initialization and should never change.

        Args:
            part_edge: The sticker to mark
            name: Unique name for this marker
            marker: The marker configuration
        """
        self._add_to_dict(part_edge.fixed_attributes, name, marker)

    def remove_marker(
        self,
        part_edge: PartEdge,
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

        Note:
            BUG: Silently fails if wrong type (e.g. PartSlice) is passed instead
            of PartEdge - no exception, just returns False. Consider adding
            runtime isinstance check.
        """
        removed = False

        if moveable is True or moveable is None:
            if self._remove_from_dict(part_edge.moveable_attributes, name):
                removed = True

        if moveable is False or moveable is None:
            if self._remove_from_dict(part_edge.fixed_attributes, name):
                removed = True

        return removed

    def remove_all(
        self,
        name: str,
        parts: Iterable[PartEdge],
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

        Note:
            BUG: Silently fails if wrong type (e.g. PartSlice) is passed instead
            of PartEdge - no exception, just returns 0. Consider adding
            runtime isinstance check.
        """
        count = 0
        for part in parts:
            if self.remove_marker(part, name, moveable):
                count += 1
        return count

    def get_markers(self, part_edge: PartEdge) -> list[MarkerCreator]:
        """Get all markers for a PartEdge, deduplicated and sorted.

        Retrieves markers from both attribute dictionaries. Visually
        identical configs are deduplicated (keeping highest z_order), then
        sorted by z_order (lowest first, so highest draws on top).

        Args:
            part_edge: The sticker to get markers from

        Returns:
            List of unique MarkerCreator objects, sorted by z_order.
        """
        all_markers: list[MarkerCreator] = []

        # Collect from both attribute dicts
        all_markers.extend(self._get_from_dict(part_edge.fixed_attributes))
        all_markers.extend(self._get_from_dict(part_edge.moveable_attributes))

        # Deduplicate: keep highest z_order for each unique config
        # MarkerCreator is frozen/hashable, so can use as dict key
        unique: dict[MarkerCreator, MarkerCreator] = {}
        for marker in all_markers:
            if marker not in unique or marker.get_z_order() > unique[marker].get_z_order():
                unique[marker] = marker

        # Sort by z_order (lowest first, so highest draws on top)
        result = list(unique.values())
        result.sort(key=lambda m: m.get_z_order())
        return result

    def get_markers_raw(self, part_edge: PartEdge) -> dict[str, MarkerCreator]:
        """Get all markers with their names (no deduplication).

        Useful for debugging or when you need to know marker names.

        Args:
            part_edge: The sticker to get markers from

        Returns:
            Dict of name -> MarkerCreator, merged from all attribute dicts.
        """
        result: dict[str, MarkerCreator] = {}

        for attrs in [part_edge.fixed_attributes, part_edge.moveable_attributes]:
            markers_dict: dict[str, MarkerCreator] | None = attrs.get(_MARKER_KEY)
            if markers_dict:
                result.update(markers_dict)

        return result

    def get_moveable_markers(self, part_edge: PartEdge) -> list[MarkerCreator]:
        """Get only moveable markers (from moveable_attributes)."""
        return self._get_from_dict(part_edge.moveable_attributes)

    def get_fixed_markers(self, part_edge: PartEdge) -> list[MarkerCreator]:
        """Get only fixed markers (from fixed_attributes)."""
        return self._get_from_dict(part_edge.fixed_attributes)

    def has_markers(self, part_edge: PartEdge) -> bool:
        """Check if a PartEdge has any markers."""
        return (
            bool(self._get_from_dict(part_edge.fixed_attributes))
            or bool(self._get_from_dict(part_edge.moveable_attributes))
        )

    def has_marker(self, part_edge: PartEdge, name: str) -> bool:
        """Check if a PartEdge has a marker with the given name."""
        for attrs in [part_edge.fixed_attributes, part_edge.moveable_attributes]:
            markers_dict: dict[str, MarkerCreator] | None = attrs.get(_MARKER_KEY)
            if markers_dict and name in markers_dict:
                return True
        return False

    def clear_markers(
        self,
        part_edge: PartEdge,
        moveable: bool | None = None,
    ) -> None:
        """Remove all markers from a PartEdge.

        Args:
            part_edge: The sticker to clear
            moveable: If True, clear only moveable_attributes. If False, clear only
                     fixed_attributes. If None, clear all.
        """
        if moveable is True or moveable is None:
            part_edge.moveable_attributes.pop(_MARKER_KEY, None)

        if moveable is False or moveable is None:
            part_edge.fixed_attributes.pop(_MARKER_KEY, None)

    # ================================================================
    # Internal Helper Methods
    # ================================================================

    @staticmethod
    def _add_to_dict(attrs: dict[Hashable, Any], name: str, marker: MarkerCreator) -> None:
        """Add a marker to an attributes dictionary."""
        markers: dict[str, MarkerCreator] | None = attrs.get(_MARKER_KEY)
        if markers is None:
            attrs[_MARKER_KEY] = {name: marker}
        else:
            markers[name] = marker  # Replace if exists

    @staticmethod
    def _remove_from_dict(attrs: dict[Hashable, Any], name: str) -> bool:
        """Remove a marker from an attributes dictionary by name."""
        markers: dict[str, MarkerCreator] | None = attrs.get(_MARKER_KEY)
        if markers is None:
            return False

        if name in markers:
            del markers[name]
            # Clean up empty dict
            if not markers:
                attrs.pop(_MARKER_KEY, None)
            return True
        return False

    @staticmethod
    def _get_from_dict(attrs: dict[Hashable, Any]) -> list[MarkerCreator]:
        """Get marker values from an attributes dictionary."""
        markers: dict[str, MarkerCreator] | None = attrs.get(_MARKER_KEY)
        return list(markers.values()) if markers else []
