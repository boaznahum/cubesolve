"""Marker manager - central authority for adding and retrieving markers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Hashable, Any

from .IMarkerManager import IMarkerManager
from ._marker_config import MarkerConfig

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge


# Key used to store markers in attributes/c_attributes/f_attributes
_MARKER_KEY: str = "markers"


class MarkerManager(IMarkerManager):
    """Central manager for marker operations on cube stickers.

    This is the ONLY class that should add or retrieve markers from PartEdges.
    All other code (AnnotationManager, Face init, renderers) must use this manager.

    Marker Uniqueness:
        Markers use full dataclass equality (all fields must match).
        - add_marker: Skips only if exact same marker exists (all fields equal)
        - remove_marker: Removes by exact match (all fields must match)
        This allows multiple markers of same type (name) with different properties
        (e.g., two "CHAR" markers with different characters on same cell).

    Markers can be stored in two modes:
    - Moveable (c_attributes): Marker follows the sticker color during rotations
    - Fixed (attributes or f_attributes): Marker stays at the physical position

    Usage:
        manager = MarkerManager()

        # Add a moveable marker (follows piece during rotation)
        manager.add_marker(part_edge, MarkerFactory.c1(), moveable=True)

        # Add a fixed marker (stays at position)
        manager.add_marker(part_edge, MarkerFactory.c2(), moveable=False)

        # Get all markers for rendering
        markers = manager.get_markers(part_edge)

        # Remove a specific marker (exact match required)
        manager.remove_marker(part_edge, MarkerFactory.c1())

        # Remove all markers of a type by name
        manager.remove_markers_by_name(part_edge, "C1")
    """

    def __init__(self) -> None:
        """Initialize the marker manager."""
        # Could add caching or other state here if needed
        pass

    def add_marker(
        self,
        part_edge: PartEdge,
        marker: MarkerConfig,
        moveable: bool = True,
        remove_same_name: bool = False,
    ) -> None:
        """Add a marker to a PartEdge.

        Duplicate prevention uses full dataclass equality (ALL fields including name).
        Two markers with identical visual properties but different names are considered
        different and will both be added.

        Args:
            part_edge: The sticker to mark
            marker: The marker configuration
            moveable: If True, marker moves with the sticker color during rotations
                     (stored in c_attributes). If False, marker stays at physical
                     position (stored in f_attributes).
            remove_same_name: If True, removes all existing markers with the same
                     name before adding the new marker. Useful for updating markers
                     that should replace previous values (e.g., index indicators).
        """
        if remove_same_name:
            self.remove_markers_by_name(part_edge, marker.name, moveable=moveable)

        if moveable:
            attrs = part_edge.c_attributes
        else:
            attrs = part_edge.f_attributes

        self._add_to_dict(attrs, marker)

    def add_fixed_marker(
        self,
        part_edge: PartEdge,
        marker: MarkerConfig,
    ) -> None:
        """Add a marker fixed to a position (uses attributes, not f_attributes).

        This is for structural markers like origin/on_x/on_y that are set during
        Face initialization and should never change.

        Args:
            part_edge: The sticker to mark
            marker: The marker configuration
        """
        self._add_to_dict(part_edge.attributes, marker)

    def remove_marker(
        self,
        part_edge: PartEdge,
        marker: MarkerConfig,
        moveable: bool | None = None,
    ) -> bool:
        """Remove a marker from a PartEdge.

        Args:
            part_edge: The sticker to unmark
            marker: The marker configuration to remove
            moveable: If True, remove from c_attributes. If False, remove from
                     f_attributes. If None, try both.

        Returns:
            True if marker was found and removed, False otherwise.
        """
        removed = False

        if moveable is True or moveable is None:
            if self._remove_from_dict(part_edge.c_attributes, marker):
                removed = True

        if moveable is False or moveable is None:
            if self._remove_from_dict(part_edge.f_attributes, marker):
                removed = True

        # Also check attributes for fixed structural markers
        if moveable is None:
            if self._remove_from_dict(part_edge.attributes, marker):
                removed = True

        return removed

    def remove_markers_by_name(
        self,
        part_edge: PartEdge,
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
        count = 0

        if moveable is True or moveable is None:
            count += self._remove_by_name_from_dict(part_edge.c_attributes, name)

        if moveable is False or moveable is None:
            count += self._remove_by_name_from_dict(part_edge.f_attributes, name)

        # Also check attributes for fixed structural markers
        if moveable is None:
            count += self._remove_by_name_from_dict(part_edge.attributes, name)

        return count

    def get_markers(self, part_edge: PartEdge) -> list[MarkerConfig]:
        """Get all markers for a PartEdge.

        Retrieves markers from all three attribute dictionaries and returns
        them sorted by z_order (lowest first, so highest draws on top).

        Args:
            part_edge: The sticker to get markers from

        Returns:
            List of MarkerConfig objects, sorted by z_order.
        """
        markers: list[MarkerConfig] = []

        # Collect from all three attribute dicts
        markers.extend(self._get_from_dict(part_edge.attributes))
        markers.extend(self._get_from_dict(part_edge.c_attributes))
        markers.extend(self._get_from_dict(part_edge.f_attributes))

        # Sort by z_order so lower values are drawn first (higher on top)
        markers.sort(key=lambda m: m.z_order)

        return markers

    def get_moveable_markers(self, part_edge: PartEdge) -> list[MarkerConfig]:
        """Get only moveable markers (from c_attributes)."""
        return self._get_from_dict(part_edge.c_attributes)

    def get_fixed_markers(self, part_edge: PartEdge) -> list[MarkerConfig]:
        """Get only fixed markers (from f_attributes and attributes)."""
        markers: list[MarkerConfig] = []
        markers.extend(self._get_from_dict(part_edge.attributes))
        markers.extend(self._get_from_dict(part_edge.f_attributes))
        return markers

    def has_markers(self, part_edge: PartEdge) -> bool:
        """Check if a PartEdge has any markers."""
        return (
            bool(self._get_from_dict(part_edge.attributes))
            or bool(self._get_from_dict(part_edge.c_attributes))
            or bool(self._get_from_dict(part_edge.f_attributes))
        )

    def clear_markers(
        self,
        part_edge: PartEdge,
        moveable: bool | None = None,
    ) -> None:
        """Remove all markers from a PartEdge.

        Args:
            part_edge: The sticker to clear
            moveable: If True, clear only c_attributes. If False, clear only
                     f_attributes. If None, clear all.
        """
        if moveable is True or moveable is None:
            part_edge.c_attributes.pop(_MARKER_KEY, None)

        if moveable is False or moveable is None:
            part_edge.f_attributes.pop(_MARKER_KEY, None)

        # Also clear attributes for fixed structural markers
        if moveable is None:
            part_edge.attributes.pop(_MARKER_KEY, None)

    # ================================================================
    # Internal Helper Methods
    # ================================================================

    @staticmethod
    def _add_to_dict(attrs: dict[Hashable, Any], marker: MarkerConfig) -> None:
        """Add a marker to an attributes dictionary."""
        markers: list[MarkerConfig] | None = attrs.get(_MARKER_KEY)
        if markers is None:
            attrs[_MARKER_KEY] = [marker]
        else:
            # Avoid duplicates using full dataclass equality (all fields)
            # This allows same type (name) with different properties
            if marker not in markers:
                markers.append(marker)

    @staticmethod
    def _remove_from_dict(attrs: dict[Hashable, Any], marker: MarkerConfig) -> bool:
        """Remove a marker from an attributes dictionary by full equality."""
        markers: list[MarkerConfig] | None = attrs.get(_MARKER_KEY)
        if markers is None:
            return False

        # Find and remove by full dataclass equality (all fields must match)
        try:
            markers.remove(marker)
            # Clean up empty list
            if not markers:
                attrs.pop(_MARKER_KEY, None)
            return True
        except ValueError:
            return False

    @staticmethod
    def _remove_by_name_from_dict(attrs: dict[Hashable, Any], name: str) -> int:
        """Remove all markers with given name from an attributes dictionary."""
        markers: list[MarkerConfig] | None = attrs.get(_MARKER_KEY)
        if markers is None:
            return 0

        # Find all markers with matching name and remove them
        original_len = len(markers)
        attrs[_MARKER_KEY] = [m for m in markers if m.name != name]
        new_markers = attrs[_MARKER_KEY]

        # Clean up empty list
        if not new_markers:
            attrs.pop(_MARKER_KEY, None)

        return original_len - len(new_markers) if new_markers else original_len

    @staticmethod
    def _get_from_dict(attrs: dict[Hashable, Any]) -> list[MarkerConfig]:
        """Get markers from an attributes dictionary."""
        markers: list[MarkerConfig] | None = attrs.get(_MARKER_KEY)
        return list(markers) if markers else []
