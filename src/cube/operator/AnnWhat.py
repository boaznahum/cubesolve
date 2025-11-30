"""Annotation type enumeration."""

from enum import unique, Enum


@unique
class AnnWhat(Enum):
    """
    If color is given , find its actual location and track it where it goes
    If part is given find it actual location and track it where it goes
    """
    Moved = 1
    FixedPosition = 2
    Both = 3  # Applicable ony for Part
