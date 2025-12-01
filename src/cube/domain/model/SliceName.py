"""Slice name enumeration."""

from enum import Enum, unique


@unique
class SliceName(Enum):
    S = "S"  # Middle over F
    M = "M"  # Middle over R
    E = "E"  # Middle over D
