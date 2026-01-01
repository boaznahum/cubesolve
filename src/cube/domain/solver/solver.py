from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.domain.solver.SolverName import SolverName


# Metadata for each SolveStep: (short_code, description)
_SOLVE_STEP_META: dict[str, tuple[str, str]] = {
    "ALL": ("Solve", "Solve Complete Cube"),
    "L1x": ("L1x", "Layer 1 Cross"),
    "L1": ("L1", "Layer 1 Complete"),
    "L2": ("L2", "Layer 2"),
    "L3x": ("L3x", "Layer 3 Cross"),
    "L3": ("L3", "Layer 3 Complete"),
    "F2L": ("F2L", "First Two Layers"),
    "OLL": ("OLL", "Orientation Last Layer"),
    "PLL": ("PLL", "Permutation Last Layer"),
    "NxNCenters": ("Ctr", "NxN Centers"),
    "NxNEdges": ("Edg", "NxN Edges"),
    "Cage": ("Cage", "Cage (Edges + Corners)"),
    # LBL-Big method steps
    "LBL_L1_Ctr": ("L1Ctr", "Layer 1 Centers"),
    "LBL_L1_Edg": ("L1Edg", "Layer 1 Edges"),
    "LBL_L1": ("L1", "Layer 1 Complete"),
    "LBL_SLICES_CTR": ("SlCtr", "Middle Slices Centers"),
    # Slice 0 granular steps (4 faces per slice)
    "LBL_S0F1": ("S0F1", "Slice 0 Face 1"),
    "LBL_S0F2": ("S0F2", "Slice 0 Faces 1-2"),
    "LBL_S0F3": ("S0F3", "Slice 0 Faces 1-3"),
    "LBL_S0F4": ("S0F4", "Slice 0 Complete"),
}


class SolveStep(Enum):
    """Solve steps with short code and description for UI display."""
    ALL = "ALL"
    L1x = "L1x"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3x = "L3x"

    # CFOP-specific steps
    F2L = "F2L"
    OLL = "OLL"
    PLL = "PLL"

    # NxN reduction steps
    NxNCenters = "NxNCenters"
    NxNEdges = "NxNEdges"

    # Cage method step
    Cage = "Cage"

    # LBL-Big method steps (layer-by-layer for big cubes)
    LBL_L1_Ctr = "LBL_L1_Ctr"  # Layer 1 centers only
    LBL_L1_Edg = "LBL_L1_Edg"  # Layer 1 edges only
    LBL_L1 = "LBL_L1"          # Layer 1 complete (centers + edges + corners)
    LBL_SLICES_CTR = "LBL_SLICES_CTR"  # Middle slices centers only (for debugging)
    # Slice 0 granular steps (4 faces per slice)
    LBL_S0F1 = "LBL_S0F1"      # Slice 0, first face center row
    LBL_S0F2 = "LBL_S0F2"      # Slice 0, faces 1-2
    LBL_S0F3 = "LBL_S0F3"      # Slice 0, faces 1-3
    LBL_S0F4 = "LBL_S0F4"      # Slice 0 complete (all 4 faces)

    @property
    def short_code(self) -> str:
        """Short code for button label (e.g., 'L1x', 'F2L')."""
        return _SOLVE_STEP_META.get(self.value, (self.value, ""))[0]

    @property
    def description(self) -> str:
        """Long description for tooltip (e.g., 'Layer 1 Cross')."""
        return _SOLVE_STEP_META.get(self.value, ("", self.value))[1]


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
