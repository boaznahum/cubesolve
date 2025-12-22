"""Annotation type enumeration."""

from enum import Enum, unique


@unique
class AnnWhat(Enum):
    """
    Annotation tracking mode for solver visualization.

    If color is given, find its actual location and track it where it goes.
    If part is given, find its actual location and track it where it goes.
    """
    Moved = 1
    FixedPosition = 2
    Both = 3  # Applicable only for Part
