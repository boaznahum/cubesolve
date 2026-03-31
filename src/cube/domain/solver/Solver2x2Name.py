"""Names for 2x2 solvers (sub-components used by orchestrators for delegation)."""

from __future__ import annotations

from enum import Enum, unique


@unique
class Solver2x2Name(Enum):
    """Available 2x2 solver implementations.

    These are 2x2 solvers used as delegates when a 3x3+ solver
    is asked to solve a 2x2 cube.
    """
    BEGINNER = "beginner"
    IDA = "ida"
