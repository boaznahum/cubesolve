from abc import ABC, abstractmethod
from enum import Enum


class SolveStep(Enum):
    ALL = "ALL"
    L1x = "L1x"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3x = "L3x"

    # CFOP
    F2L = "F2L"

    NxNCenters = "NxNCenters"
    NxNEdges = "NxNEdges"


class SolverResults:

    def __init__(self) -> None:
        super().__init__()
        self._was_corner_swap = False
        self._was_partial_edge_parity = False
        self._was_even_edge_parity = False

    @property
    def was_corner_swap(self):
        return self._was_corner_swap

    @property
    def was_even_edge_parity(self):
        return self._was_even_edge_parity

    @property
    def was_partial_edge_parity(self):
        return self._was_partial_edge_parity


class Solver(ABC):

    @abstractmethod
    def solve(self, debug: bool | None = None, animation: bool | None = True,
              what: SolveStep = SolveStep.ALL) -> SolverResults:
        pass

    @property
    @abstractmethod
    def is_solved(self):
        pass


class ReductionSolver(ABC):
    pass


class BeginnerLBLReduce(Solver, ReductionSolver, ABC):
    pass
