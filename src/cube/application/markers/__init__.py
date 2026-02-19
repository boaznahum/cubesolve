"""Markers package - centralized marker management for cube visualization.

This package provides a unified system for adding visual markers to cube stickers.
All marker operations should go through MarkerManager.

Classes:
    IMarkerManager: Protocol defining the marker manager interface
    MarkerCreator: Protocol for marker objects (draw themselves via toolkit)
    MarkerFactory: Factory providing predefined markers (C0, C1, C2, ORIGIN, etc.)
    MarkerManager: Central manager implementing IMarkerManager

Usage:
    from cube.application.markers import MarkerManager, MarkerFactory, IMarkerManager

    # Get or create the marker manager (stored in cube's service provider)
    manager: IMarkerManager = cube.sp.marker_manager
    factory = cube.sp.marker_factory

    # Add a moveable marker (follows piece during rotation)
    manager.add_marker(part_edge, "c1", factory.c1(), moveable=True)

    # Add a fixed position marker
    manager.add_marker(part_edge, "c2", factory.c2(), moveable=False)

    # Get all markers for rendering (deduplicated, sorted by z_order)
    markers = manager.get_markers(part_edge)

    # Remove a marker by name
    manager.remove_marker(part_edge, "c1")

    # Remove from multiple parts
    manager.remove_all("c1", [edge1, edge2, edge3])
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge

from ._marker_config import color_255_to_float, color_float_to_255
from ._marker_creator_protocol import MarkerCreator
from ._marker_toolkit import MarkerToolkit
from ._outlined_circle_marker import OutlinedCircleMarker
from .IMarkerFactory import IMarkerFactory
from .MarkerFactory import MarkerFactory
from .NoopMarkerFactory import NoopMarkerFactory
from .IMarkerManager import IMarkerManager
from .MarkerManager import MarkerManager
from .NoopMarkerManager import NoopMarkerManager

def get_markers_from_part_edge(part_edge: "PartEdge") -> list[MarkerCreator]:
    """Convenience function to read all markers from a PartEdge.

    This function reads markers from both attribute dictionaries (fixed_attributes,
    moveable_attributes). Visually identical configs are deduplicated
    (keeping highest z_order), then sorted by z_order for proper layering.

    Can be used by renderers without needing a MarkerManager instance.

    Args:
        part_edge: The sticker to get markers from

    Returns:
        List of unique MarkerCreator objects, sorted by z_order.
    """
    all_markers: list[MarkerCreator] = []
    key = "markers"

    for attrs in [part_edge.fixed_attributes, part_edge.moveable_attributes]:
        markers_dict: dict[str, MarkerCreator] | None = attrs.get(key)
        if markers_dict:
            all_markers.extend(markers_dict.values())

    # Deduplicate: keep highest z_order for each unique config
    # All marker creators are frozen dataclasses — hashable
    unique: dict[Any, Any] = {}
    for marker in all_markers:
        if marker not in unique or marker.z_order > unique[marker].z_order:
            unique[marker] = marker

    # Sort by z_order (lowest first, so highest draws on top)
    result: list[MarkerCreator] = list(unique.values())
    result.sort(key=lambda m: m.z_order)
    return result


__all__ = [
    "IMarkerFactory",
    "IMarkerManager",
    "MarkerCreator",
    "MarkerToolkit",
    "MarkerFactory",
    "MarkerManager",
    "NoopMarkerFactory",
    "NoopMarkerManager",
    "OutlinedCircleMarker",
    "color_255_to_float",
    "color_float_to_255",
    "get_markers_from_part_edge",
]
