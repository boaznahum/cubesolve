"""Marker shape enumeration."""
from __future__ import annotations

from enum import Enum, unique


@unique
class MarkerShape(Enum):
    """Defines the visual shape of a marker.

    Markers can be drawn as different geometric shapes on cube stickers.
    """

    # Ring/circle shapes (3D cylinders when rendered)
    RING = "ring"              # Hollow ring (like C0, C2)
    FILLED_CIRCLE = "filled"   # Filled circle/disk (like C1)

    # Line-based shapes
    CROSS = "cross"            # X shape through corners (like origin/on_x/on_y)

    # Future shapes can be added here
    # DOT = "dot"              # Small point
    # SQUARE = "square"        # Square outline
    # DIAMOND = "diamond"      # Diamond shape
