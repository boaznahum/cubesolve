from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING

from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg

from cube.domain.solver.common.CenterBlockStatistics import CenterBlockStatistics





class SmallStepSolveState(Enum):

    WAS_SOLVED=auto(),
    SOLVED=auto(),

    NOT_SOLVED=auto(),

    @property
    def is_solved(self) -> bool:
        return (self is SmallStepSolveState.SOLVED or
                        self is SmallStepSolveState.WAS_SOLVED)


class SolveStep(Enum):
    """Solve steps with short code and description for UI display.

    Each member is defined as: NAME = (value, short_code, description)
    """
    _short_code: str
    _description: str

    # value, short_code, description
    ALL = ("ALL", "Solve", "Solve Complete Cube")
    L1x = ("L1x", "L1x", "Layer 1 Cross")
    L1 = ("L1", "L1", "Layer 1 Complete")
    L2 = ("L2", "L2", "Layer 2")
    L3x = ("L3x", "L3x", "Layer 3 Cross")
    L3 = ("L3", "L3", "Layer 3 Complete")

    # CFOP-specific steps
    F2L = ("F2L", "F2L", "First Two Layers")
    OLL = ("OLL", "OLL", "Orientation Last Layer")
    PLL = ("PLL", "PLL", "Permutation Last Layer")

    # NxN reduction steps
    NxNCenters = ("NxNCenters", "Ctr", "NxN Centers")
    NxNEdges = ("NxNEdges", "Edg", "NxN Edges")

    # Cage method step
    Cage = ("Cage", "Cage", "Cage (Edges + Corners)")

    # Reducer method steps (layer-by-layer for big cubes)
    LBL_L1_Ctr = ("LBL_L1_Ctr", "L1Ctr", "Layer 1 Centers")
    LBL_L1_EDGES = ("LBL_L1_Edges", "L1Edg", "Layer 1 Edges")
    LBL_L1 = ("LBL_L1", "L1", "Layer 1 Complete")
    LBL_L2_SLICES = ("LBL_SLICES_CTR", "L2", "Middle Slices Centers")
    LBL_L3_CENTER = ("LBL_L3_CENTER", "L3Ctr", "Layer 3 Centers")
    LBL_L3_EDGES = ("LBL_L3_EDGES", "L3Ed", "Layer 3 Edges")
    LBL_L3_CROSS = ("LBL_L3_CROSS", "L3x", "Layer 3 Cross")

    def __new__(cls, value: str, short_code: str, description: str) -> "SolveStep":
        obj = object.__new__(cls)
        obj._value_ = value
        obj._short_code = short_code
        obj._description = description
        return obj

    @property
    def short_code(self) -> str:
        """Short code for button label (e.g., 'L1x', 'F2L')."""
        return self._short_code

    @property
    def description(self) -> str:
        """Long description for tooltip (e.g., 'Layer 1 Cross')."""
        return self._description


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

    Implements SolverElementsProvider to allow solver elements (SolverHelper subclasses)
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
        """Solve the cube.

        AbstractSolver provides a @final template method implementation that:
        1. Handles animation flag via with_animation()
        2. Catches OpAborted for clean user abort handling
        3. Manages debug flag

        Subclasses should NOT override this method. Instead, implement _solve_impl().

        Args:
            debug: Enable debug output (None = use config)
            animation: Enable animation (None = use current, True/False = force)
            what: Which step to solve

        Returns:
            SolverResults with parity information
        """
        pass

    @abstractmethod
    def solution(self) -> Alg:
        """Compute the full solution without modifying the cube.

        Solves the cube with animation OFF, records all moves, then undoes
        them so the cube returns to its original state. Returns the solution
        as an Alg that can be replayed with op.play().
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

    @abstractmethod
    def diagnostic(self) -> None:
        """Print diagnostic information about current solver state.

        Called by diagnostics button in GUI. Default implementations do nothing.
        Solvers that have detailed state (like LayerByLayerNxNSolver) can override
        to print tracker holder state, layer progress, etc.

        Output goes to stdout/stderr for debugging.
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

    def get_block_statistics(self) -> CenterBlockStatistics:
        """Return block solving statistics. Override in subclasses that track stats."""
        return CenterBlockStatistics()

    @abstractmethod
    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Steps should be returned in the order they should appear in UI.
        Does NOT include SolveStep.ALL (implied for all solvers).
        """
        pass


class ReductionSolver(ABC):
    pass


class BeginnerLBLReduce(Solver, ReductionSolver, ABC):
    pass
