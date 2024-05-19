from abc import ABC, abstractmethod
from enum import Enum

from cube.operator.cube_operator import Operator
from cube.solver.solver_name import SolverName


class SolveStep(Enum):
    ALL = "ALL"
    L1x = "L1x"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3x = "L3x"

    # CFOP
    F2L = "F2L"
    OLL = L3x
    PLL = L3

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

    @property
    @abstractmethod
    def get_code(self) -> SolverName:
        pass

    @property
    def name(self) -> str:
        return str(self.get_code.value)

    @abstractmethod
    def solve(self, debug: bool | None = None, animation: bool | None = True,
              what: SolveStep = SolveStep.ALL) -> SolverResults:
        """
        :param debug:
        :param animation: not None force True/ False, you can create Application without animation,
                so you don't need to pass False to solver
        :param what:
        :return:
        """
        pass

    @property
    @abstractmethod
    def is_solved(self):
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """
        String describes the solver status - which parts are solved
        :return:
        """
        pass

    @property
    @abstractmethod
    def is_debug_config_mode(self) -> bool:
        pass

    @property
    @abstractmethod
    def op(self) -> Operator:
        pass



class ReductionSolver(ABC):
    pass


class BeginnerLBLReduce(Solver, ReductionSolver, ABC):
    pass
