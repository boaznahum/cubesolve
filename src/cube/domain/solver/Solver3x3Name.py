"""Names for pure 3x3 solvers (sub-components used by orchestrators)."""

from __future__ import annotations

from enum import Enum, unique


@unique
class Solver3x3Name(Enum):
    """Available 3x3 solver implementations.

    These are pure 3x3 solvers used as sub-components by NxN orchestrators
    and by Cage for shadow cube solving. They are NOT user-visible solvers.
    """
    BEGINNER = "beginner"
    CFOP = "cfop"
    KOCIEMBA = "kociemba"
