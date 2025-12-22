from abc import ABC, abstractmethod
from enum import Enum

from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.domain.solver.SolverName import SolverName


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
    def was_corner_swap(self) -> bool:
        return self._was_corner_swap

    @property
    def was_even_edge_parity(self) -> bool:
        return self._was_even_edge_parity

    @property
    def was_partial_edge_parity(self) -> bool:
        return self._was_partial_edge_parity

    @property
    def has_parity(self) -> bool:
        """Check if any parity was detected."""
        return (self._was_corner_swap or
                self._was_even_edge_parity or
                self._was_partial_edge_parity)

    def parity_summary(self) -> str:
        """Return a summary of detected parities."""
        parities: list[str] = []
        if self._was_even_edge_parity:
            parities.append("Edge(OLL)")
        if self._was_corner_swap:
            parities.append("Corner(PLL)")
        if self._was_partial_edge_parity:
            parities.append("PartialEdge")
        if parities:
            return "Parity: " + ", ".join(parities)
        return "Parity: None"


class Solver(SolverElementsProvider, ABC):
    """
    Base solver interface.

    Implements SolverElementsProvider to allow solver elements (SolverElement subclasses)
    to work with any Solver implementation. See SOLVER_ARCHITECTURE.md for class hierarchy.
    """

    @property
    @abstractmethod
    def get_code(self) -> SolverName:
        pass

    @property
    def name(self) -> str:
        return self.get_code.display_name

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
    def is_solved(self) -> bool:
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
    def op(self) -> OperatorProtocol:
        pass


class ReductionSolver(ABC):
    pass


class BeginnerLBLReduce(Solver, ReductionSolver, ABC):
    pass
