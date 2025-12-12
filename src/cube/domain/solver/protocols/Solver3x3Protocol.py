"""Solver3x3 protocol - interface for pure 3x3 cube solving."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
    from cube.domain.solver.solver import SolverResults, SolveStep


class Solver3x3Protocol(Protocol):
    """
    Protocol for pure 3x3 cube solving.

    A 3x3 solver solves a cube that is already in 3x3 state
    (either a real 3x3 cube, or an NxN cube that has been reduced).

    Implementations should inherit from this protocol.

    Note: solve_3x3() may raise parity exceptions on even cubes:
    - EvenCubeEdgeParityException: Edge parity detected
    - EvenCubeCornerSwapException: Corner swap parity detected

    These exceptions should be caught by the orchestrator.
    """

    @property
    def op(self) -> "OperatorProtocol":
        """The operator for cube manipulation."""
        ...

    def solve_3x3(
        self,
        debug: bool = False,
        what: "SolveStep | None" = None
    ) -> "SolverResults":
        """
        Solve a 3x3 cube (or reduced NxN cube).

        Args:
            debug: Enable debug output
            what: Which step to solve (default: ALL)

        Returns:
            SolverResults with solve metadata

        Raises:
            EvenCubeEdgeParityException: If edge parity detected
            EvenCubeCornerSwapException: If corner swap parity detected
        """
        ...

    @property
    def is_solved(self) -> bool:
        """Check if cube is solved."""
        ...

    @property
    def status_3x3(self) -> str:
        """Human-readable 3x3 solving status."""
        ...
