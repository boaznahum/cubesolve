"""Beginner 3x3 solver - pure layer-by-layer 3x3 cube solving."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver._3x3.shared.L1Cross import L1Cross
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger

from ._L1Corners import L1Corners
from ._L2 import L2
from ._L3Corners import L3Corners
from ._L3Cross import L3Cross


class BeginnerSolver3x3(BaseSolver, Solver3x3Protocol):
    """
    Pure 3x3 beginner layer-by-layer solver.

    Solves a 3x3 cube (or a reduced NxN cube) using the beginner
    layer-by-layer method:
    1. L1 Cross - White cross on bottom
    2. L1 Corners - White corners
    3. L2 - Middle layer edges
    4. L3 Cross - Yellow cross orientation
    5. L3 Corners - Yellow corners permutation

    Does NOT include NxN reduction - use with NxNSolverOrchestrator
    for larger cubes.

    Note: solve_3x3() may raise parity exceptions on even cubes:
    - EvenCubeEdgeParityException: From L3Cross
    - EvenCubeCornerSwapException: From L3Corners

    Inherits from Solver3x3Protocol to satisfy the project's convention.
    """

    __slots__ = ["l1_cross", "l1_corners", "l2", "l3_cross", "l3_corners"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: "ILogger",
    ) -> None:
        """
        Create a BeginnerSolver3x3.

        Args:
            op: Operator for cube manipulation
            parent_logger: Parent logger (cube.sp.logger for root, parent._logger for child)
        """
        super().__init__(op, parent_logger, logger_prefix="Beginner3x3")

        self.l1_cross = L1Cross(self)
        self.l1_corners = L1Corners(self)
        self.l2 = L2(self)
        self.l3_cross = L3Cross(self)
        self.l3_corners = L3Corners(self)

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return SolverName.LBL

    @property
    def can_detect_parity(self) -> bool:
        """BeginnerSolver3x3 detects parity via exceptions in L3Cross/L3Corners."""
        return True

    def solve_3x3(
        self,
        debug: bool = False,
        what: SolveStep | None = None
    ) -> SolverResults:
        """
        Solve 3x3 cube.

        Args:
            debug: Enable debug output
            what: Which step to solve (default: ALL)

        Returns:
            SolverResults with solve metadata

        Raises:
            EvenCubeEdgeParityException: If edge parity detected in L3
            EvenCubeCornerSwapException: If corner swap parity detected in L3
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        if what is None:
            what = SolveStep.ALL

        # Execute appropriate solve steps
        # Note: L3 steps may raise parity exceptions on even cubes
        match what:
            case SolveStep.L1x:
                self.l1_cross.solve()

            case SolveStep.L1:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)

            case SolveStep.L2:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()

            case SolveStep.L3x:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()
                self.l3_cross.solve()

            case SolveStep.ALL | SolveStep.L3:
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()
                self.l3_cross.solve()
                self.l3_corners.solve()

            case SolveStep.F2L:
                # F2L is CFOP terminology, but support it here too
                self.l1_cross.solve()
                self.l1_corners.solve(self.l1_cross)
                self.l2.solve()

        return sr

    @property
    def status_3x3(self) -> str:
        """Human-readable 3x3 solving status."""
        if self._cube.solved:
            return "Solved"

        cross = self.l1_cross.is_cross_rotate_and_check()
        corners = self.l1_corners.is_corners(self.l1_cross)

        if cross and corners:
            s = "L1"
        elif cross:
            s = "L1-Cross"
        elif corners:
            s = "L1-Corners"
        else:
            s = "No-L1"

        if self.l2.solved():
            s += ", L2"
        else:
            s += ", No L2"

        if self.l3_cross.solved() and self.l3_corners.solved():
            s += ", L3"
        elif self.l3_cross.solved():
            s += ", L3-Cross"
        elif self.l3_corners.solved():
            s += ", L3-Corners"
        else:
            s += ", No L3"

        return s

    # Required by Solver ABC - delegate to status_3x3
    @property
    def status(self) -> str:
        """Human-readable solver status."""
        return self.status_3x3

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve the cube. Called by AbstractSolver.solve().

        Animation and OpAborted are handled by the template method.

        Args:
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        return self.solve_3x3(self._is_debug_enabled, what)

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        BeginnerSolver3x3 uses layer-by-layer method with these steps:
        L1x (cross), L1 (complete), L2, L3x (cross), L3 (complete).
        """
        return [
            SolveStep.L1x,
            SolveStep.L1,
            SolveStep.L2,
            SolveStep.L3x,
            SolveStep.L3,
        ]
