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

    def detect_edge_parity(self) -> bool | None:
        """
        Detect if cube has edge parity (OLL parity) without side effects.

        This method should:
        1. Enter query mode (save state, no animation)
        2. Solve L1 and L2 to reach L3
        3. Count oriented edges on top face
        4. Rollback to original state
        5. Return result

        Returns:
            True: Edge parity detected (1 or 3 oriented edges)
            False: No edge parity (0, 2, or 4 oriented edges)
            None: This solver cannot detect parity (e.g., Kociemba)

        Note: Used by orchestrator to fix parity before calling solve_3x3()
        on solvers that can't handle parity (like Kociemba).
        """
        ...

    def detect_corner_parity(self) -> bool | None:
        """
        Detect if cube has corner parity (PLL parity) without side effects.

        This method should:
        1. Enter query mode (save state, no animation)
        2. Solve L1, L2, and orient L3 edges (OLL)
        3. Count corners in correct position
        4. Rollback to original state
        5. Return result

        Returns:
            True: Corner parity detected (exactly 2 corners in position)
            False: No corner parity (0, 1, or 4 corners in position)
            None: This solver cannot detect parity (e.g., Kociemba)

        Note: Corner parity can only be checked AFTER fixing edge parity.
        """
        ...
