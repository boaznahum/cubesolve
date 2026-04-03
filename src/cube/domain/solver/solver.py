from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING

from cube.domain.solver.ParityFix import ParityFix as ParityFix  # re-export
from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg

from cube.domain.solver.common.SolverStatistics import SolverStatistics





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


class ParityType(Enum):
    """Types of parity that can occur in even-layered cubes."""
    EvenEdge = ("Even Edge(OLL)", "Even Edge")
    CornerSwap = ("Corner(PLL)", "Corner Swap")
    PartialEdge = ("Partial Edge", "Partial Edge")

    _display_name: str
    _short_name: str

    def __new__(cls, display_name: str, short_name: str) -> "ParityType":
        obj = object.__new__(cls)
        obj._value_ = display_name
        obj._display_name = display_name
        obj._short_name = short_name
        return obj

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def short_name(self) -> str:
        return self._short_name


class SolverResults:

    def __init__(self) -> None:
        super().__init__()
        self._parities: list[tuple[ParityType, ParityFix]] = []

    # -------------------------------------------------------------------------
    # Accumulation methods
    # -------------------------------------------------------------------------

    def add_parity(self, parity_type: ParityType, fix: ParityFix | None) -> None:
        """Record a parity fix. Skips None."""
        if fix is not None:
            self._parities.append((parity_type, fix))

    def add_corner_swap(self, fix: ParityFix | None) -> None:
        self.add_parity(ParityType.CornerSwap, fix)

    def add_even_edge_parity(self, fix: ParityFix | None) -> None:
        self.add_parity(ParityType.EvenEdge, fix)

    def add_partial_edge_parity(self, fix: ParityFix | None) -> None:
        self.add_parity(ParityType.PartialEdge, fix)

    def merge(self, other: "SolverResults") -> None:
        """Accumulate parity info from a child SolverResults into this one."""
        self._parities.extend(other._parities)

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    @property
    def parities(self) -> list[tuple[ParityType, ParityFix]]:
        """All recorded parity events in order."""
        return list(self._parities)

    def fixes_for(self, parity_type: ParityType) -> list[ParityFix]:
        """All fixes recorded for a given parity type."""
        return [fix for pt, fix in self._parities if pt == parity_type]

    @property
    def was_corner_swap(self) -> ParityFix | None:
        fixes = self.fixes_for(ParityType.CornerSwap)
        return fixes[-1] if fixes else None

    @property
    def was_even_edge_parity(self) -> ParityFix | None:
        fixes = self.fixes_for(ParityType.EvenEdge)
        return fixes[-1] if fixes else None

    @property
    def was_partial_edge_parity(self) -> ParityFix | None:
        fixes = self.fixes_for(ParityType.PartialEdge)
        return fixes[-1] if fixes else None

    @property
    def has_parity(self) -> bool:
        """Check if any parity was detected."""
        return bool(self._parities)

    def parity_summary(self) -> str:
        """Return a summary of detected parities."""
        parts: list[str] = []
        for parity_type in (ParityType.EvenEdge, ParityType.CornerSwap, ParityType.PartialEdge):
            fixes = self.fixes_for(parity_type)
            if not fixes:
                continue
            suffix = " [Advanced]" if fixes[-1].advanced else " [non-Advanced]"
            count = f" (×{len(fixes)})" if len(fixes) > 1 else ""
            parts.append(parity_type.display_name + suffix + count)
        if parts:
            return "Parity: " + ", ".join(parts)
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

    def get_block_statistics(self) -> SolverStatistics:
        """Return block solving statistics. Override in subclasses that track stats."""
        return SolverStatistics()

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
