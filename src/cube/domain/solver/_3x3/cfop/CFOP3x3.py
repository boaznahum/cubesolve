"""CFOP 3x3 solver - pure 3x3 CFOP (Fridrich) method."""

from __future__ import annotations

from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.solver import SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver._3x3.shared.L1Cross import L1Cross
from ._F2L import F2L
from ._OLL import OLL
from ._PLL import PLL


class CFOP3x3(BaseSolver, Solver3x3Protocol):
    """
    Pure 3x3 CFOP (Fridrich) method solver.

    Solves a 3x3 cube (or a reduced NxN cube) using the CFOP method:
    1. Cross - White cross on bottom
    2. F2L - First Two Layers (corners + edges together)
    3. OLL - Orientation of Last Layer
    4. PLL - Permutation of Last Layer

    Based on https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/

    Does NOT include NxN reduction - use with NxNSolverOrchestrator
    for larger cubes.

    Note: solve_3x3() may raise parity exceptions on even cubes:
    - EvenCubeEdgeParityException: From OLL
    - EvenCubeCornerSwapException: From PLL

    Inherits from Solver3x3Protocol to satisfy the project's convention.
    """

    __slots__ = ["l1_cross", "f2l", "oll", "pll"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a CFOP3x3 solver.

        Args:
            op: Operator for cube manipulation
        """
        super().__init__(op)

        self.l1_cross = L1Cross(self)
        self.f2l = F2L(self)
        self.oll = OLL(self)
        self.pll = PLL(self)

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return SolverName.CFOP

    @property
    def can_detect_parity(self) -> bool:
        """CFOP3x3 detects parity via exceptions in OLL/PLL."""
        return True

    def solve_3x3(
            self,
            debug: bool = False,
            what: SolveStep | None = None
    ) -> SolverResults:
        """
        Solve 3x3 cube using CFOP method.

        Args:
            debug: Enable debug output
            what: Which step to solve (default: ALL)

        Returns:
            SolverResults with solve metadata

        Raises:
            EvenCubeEdgeParityException: If edge parity detected
            EvenCubeCornerSwapException: If corner swap parity detected
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        if what is None:
            what = SolveStep.ALL

        # Execute appropriate solve steps
        match what:
            # CFOP knows only L1 cross, so L1x and L1 are the same
            case SolveStep.L1x | SolveStep.L1:
                self.l1_cross.solve()

            case SolveStep.F2L | SolveStep.L2:
                self.l1_cross.solve()
                self.f2l.solve()

            case SolveStep.OLL | SolveStep.L3x:
                self.l1_cross.solve()
                self.f2l.solve()
                self.oll.solve()

            case SolveStep.ALL | SolveStep.L3 | SolveStep.PLL:
                self.l1_cross.solve()
                self.f2l.solve()
                self.oll.solve()
                self.pll.solve()

        return sr

    def solve(
            self,
            debug: bool | None = None,
            animation: bool | None = True,
            what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """
        Solve the cube (Solver interface).

        This method exists for backward compatibility and direct usage.
        For NxN cubes, use NxNSolverOrchestrator instead.

        Args:
            debug: Enable debug output
            animation: Enable animation
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        if debug is None:
            debug = self._is_debug_enabled

        with self._op.with_animation(animation=animation):
            return self.solve_3x3(debug, what)

    @property
    def status_3x3(self) -> str:
        """Human-readable 3x3 solving status."""
        if self._cube.solved:
            return "Solved"

        s = ""

        def _add(x: str) -> None:
            nonlocal s
            if s:
                s += ","
            s += x

        cross = self.l1_cross.is_cross()
        f2f = self.f2l.solved()

        if cross and f2f:
            s = "F2L"
        else:
            if self.f2l.is_l1():
                _add("L1")
            elif cross:
                _add("L1 cross")

            if self.f2l.is_l2():
                _add("L2")

            if not s:
                s = "No F2L"

        if self.pll.is_solved:
            _add("L3")
        else:
            oll = self.oll.is_rotate_and_solved()
            pll = self.pll.is_rotate_and_solved()

            if oll or pll:
                if oll:
                    _add("OLL")
                if pll:
                    _add("PLL")
            else:
                _add("NO L3")

        return s

    # Required by Solver ABC - delegate to status_3x3
    @property
    def status(self) -> str:
        """Human-readable solver status."""
        return self.status_3x3
