"""Markers package - centralized marker management for cube visualization.

This package provides a unified system for adding visual markers to cube stickers.
All marker operations should go through MarkerManager.

Classes:
    IMarkerManager: Protocol defining the marker manager interface
    MarkerConfig: Configuration dataclass for marker visual properties
    MarkerShape: Enum defining marker shapes (RING, FILLED_CIRCLE, CROSS)
    MarkerFactory: Factory providing predefined markers (C0, C1, C2, ORIGIN, etc.)
    MarkerManager: Central manager implementing IMarkerManager

Usage:
    from cube.application.markers import MarkerManager, MarkerFactory, IMarkerManager

    # Get or create the marker manager (stored in cube's service provider)
    manager: IMarkerManager = cube.sp.marker_manager

    # Add a moveable marker (follows piece during rotation)
    manager.add_marker(part_edge, MarkerFactory.c1(), moveable=True)

    # Add a fixed position marker
    manager.add_marker(part_edge, MarkerFactory.c2(), moveable=False)

    # Get all markers for rendering
    markers = manager.get_markers(part_edge)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.domain.model.PartEdge import PartEdge

from .MarkerShape import MarkerShape
from ._marker_config import MarkerConfig, color_255_to_float, color_float_to_255
from .IMarkerFactory import IMarkerFactory
from .MarkerFactory import MarkerFactory
from .IMarkerManager import IMarkerManager
from .MarkerManager import MarkerManager

def get_markers_from_part_edge(part_edge: "PartEdge") -> list[MarkerConfig]:
    """Convenience function to read all markers from a PartEdge.

    This function reads markers from all attribute dictionaries (attributes,
    c_attributes, f_attributes) and returns them sorted by z_order.

    Can be used by renderers without needing a MarkerManager instance.

    Args:
        part_edge: The sticker to get markers from

    Returns:
        List of MarkerConfig objects, sorted by z_order.
    """
    result: list[MarkerConfig] = []
    key = "markers"

    for attrs in [part_edge.attributes, part_edge.c_attributes, part_edge.f_attributes]:
        marker_list: list[MarkerConfig] | None = attrs.get(key)
        if marker_list:
            result.extend(marker_list)

    result.sort(key=lambda m: m.z_order)
    return result


__all__ = [
    "IMarkerFactory",
    "IMarkerManager",
    "MarkerShape",
    "MarkerConfig",
    "MarkerFactory",
    "MarkerManager",
    "color_255_to_float",
    "color_float_to_255",
    "get_markers_from_part_edge",
]
