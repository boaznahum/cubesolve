"""Slice name enumeration."""

from enum import Enum, unique


@unique
class SliceName(Enum):
    """
        See: https://alg.cubing.net/?alg=m and https://ruwix.com/the-rubiks-cube/notation/advanced/
    """
    S = "S"  # Standing - middle between F and B, rotates like F
    M = "M"  # Middle - middle between L and R, rotates like L (standard notation)
    E = "E"  # Equator - middle between U and D, rotates like D
