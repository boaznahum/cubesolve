"""Abstract base class for all 2x2 cube solvers.

Both IDA* and Beginner 2x2 solvers extend this class. It serves as
a marker type so AbstractSolver.solve() can detect when it's already
running a 2x2 solver (to avoid infinite delegation loops).
"""

from abc import ABC

from cube.domain.solver.common.BaseSolver import BaseSolver


class Solver2x2Base(BaseSolver, ABC):
    """Base class for all 2x2 cube solvers.

    Subclasses: Solver2x2IDA, Solver2x2Beginner.
    """

    @property
    def _is_2x2_solver(self) -> bool:
        return True
