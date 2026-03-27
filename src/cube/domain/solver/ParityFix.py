"""Parity fix result enum."""

from enum import Enum, auto


class ParityFix(Enum):
    NonAdvanced = auto()  # basic — disrupts edges/pairing
    Advanced = auto()     # advanced — preserves edges/pairing

    @staticmethod
    def of(advanced: bool) -> 'ParityFix':
        return ParityFix.Advanced if advanced else ParityFix.NonAdvanced

    @property
    def advanced(self) -> bool:
        return self == ParityFix.Advanced
