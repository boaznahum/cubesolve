"""Solvers3x3 factory - creates pure 3x3 solver instances."""

from __future__ import annotations

from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol


class Solvers3x3:
    """
    Factory for pure 3x3 cube solvers.

    These solvers handle only 3x3 cubes (or reduced NxN cubes that
    look like 3x3). For NxN support, use the main Solvers factory
    which returns orchestrators that combine reducers with 3x3 solvers.

    Usage:
        solver_3x3 = Solvers3x3.beginner(op)
        solver_3x3 = Solvers3x3.cfop(op)
        solver_3x3 = Solvers3x3.kociemba(op)  # Only for actual 3x3 cubes
    """

    @staticmethod
    def beginner(op: OperatorProtocol) -> Solver3x3Protocol:
        """
        Get beginner layer-by-layer 3x3 solver.

        Uses the beginner method:
        L1 Cross -> L1 Corners -> L2 -> L3 Cross -> L3 Corners

        Args:
            op: Operator for cube manipulation

        Returns:
            BeginnerSolver3x3 instance
        """
        from cube.domain.solver._3x3.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
        return BeginnerSolver3x3(op)

    @staticmethod
    def cfop(op: OperatorProtocol) -> Solver3x3Protocol:
        """
        Get CFOP (Fridrich) 3x3 solver.

        Uses the CFOP method:
        Cross -> F2L -> OLL -> PLL

        Args:
            op: Operator for cube manipulation

        Returns:
            CFOP3x3 instance
        """
        from cube.domain.solver._3x3.cfop.CFOP3x3 import CFOP3x3
        return CFOP3x3(op)

    @staticmethod
    def kociemba(op: OperatorProtocol) -> Solver3x3Protocol:
        """
        Get Kociemba near-optimal 3x3 solver.

        Uses Kociemba's two-phase algorithm for near-optimal solutions
        (18-22 moves).

        Args:
            op: Operator for cube manipulation

        Returns:
            Kociemba3x3 instance
        """
        from cube.domain.solver._3x3.kociemba.Kociemba3x3 import Kociemba3x3
        return Kociemba3x3(op)

    @classmethod
    def by_name(cls, name: str, op: OperatorProtocol) -> Solver3x3Protocol:
        """
        Get a 3x3 solver by its name.

        Args:
            name: Solver name - "beginner", "cfop", or "kociemba"
            op: Operator for cube manipulation

        Returns:
            Solver3x3Protocol instance

        Raises:
            ValueError: If name is not recognized
        """
        match name:
            case "beginner":
                return cls.beginner(op)
            case "cfop":
                return cls.cfop(op)
            case "kociemba":
                return cls.kociemba(op)
            case _:
                raise ValueError(f"Unknown 3x3 solver: {name}. "
                                 f"Options: beginner, cfop, kociemba")
