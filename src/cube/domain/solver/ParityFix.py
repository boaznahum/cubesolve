"""Parity fix result enum."""

from enum import Enum, auto


class ParityFix(Enum):
    NonPreserving = auto()  # basic — disrupts edges/pairing
    Preserving = auto()     # advanced — preserves edges/pairing
