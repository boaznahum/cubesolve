"""Solver factory - creates solver instances."""

from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.beginner.BeginnerSolver import BeginnerSolver
from .CFOP.CFOP import CFOP
from .kociemba.KociembaSolver import KociembaSolver
from .solver import BeginnerLBLReduce
from .solver import Solver
from .SolverName import SolverName
from cube.domain.exceptions import InternalSWError


class Solvers:
    """
    Factory for creating solver instances.

    - LBL: Uses original BeginnerSolver (handles NxN internally)
    - CFOP: Uses original CFOP (3x3 only)
    - KOCIEMBA: Uses NxNSolverOrchestrator with Kociemba3x3 for NxN support
    """

    @classmethod
    def default(cls, op: OperatorProtocol) -> Solver:
        """Get the default solver based on config setting."""
        from cube.application import _config as cfg

        solver_name = SolverName.lookup(cfg.DEFAULT_SOLVER)
        return cls.by_name(solver_name, op)

    @staticmethod
    def beginner(op: OperatorProtocol) -> BeginnerLBLReduce:
        """
        Get beginner layer-by-layer solver with NxN support.

        Uses the original BeginnerSolver which handles both reduction
        and 3x3 solving internally with integrated parity handling.
        """
        return BeginnerSolver(op)

    @staticmethod
    def cfop(op: OperatorProtocol) -> Solver:
        """
        Get CFOP (Fridrich) solver.

        Currently only supports 3x3 cubes. For NxN, use beginner() instead.
        """
        return CFOP(op)

    @staticmethod
    def kociemba(op: OperatorProtocol) -> Solver:
        """
        Get Kociemba near-optimal solver with NxN support.

        For 3x3: Uses Kociemba algorithm (18-22 moves)
        For NxN: Uses BeginnerReducer + Kociemba3x3 via orchestrator
        """
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3
        from .NxNSolverOrchestrator import NxNSolverOrchestrator

        solver_3x3 = Solvers3x3.kociemba(op)
        reducer = Reducers.beginner(op, advanced_edge_parity=True)

        return NxNSolverOrchestrator(
            op, reducer, solver_3x3, SolverName.KOCIEMBA
        )

    @classmethod
    def next_solver(cls, current: SolverName, op: OperatorProtocol) -> Solver:
        """Get the next solver in rotation."""
        _ids = [*SolverName]
        index = _ids.index(current)

        next_s = _ids[(index + 1) % len(_ids)]

        return cls.by_name(next_s, op)

    @classmethod
    def by_name(cls, solver_id: SolverName, op: OperatorProtocol) -> Solver:
        """Get a solver by its name."""
        match solver_id:

            case SolverName.LBL:
                return cls.beginner(op)

            case SolverName.CFOP:
                return cls.cfop(op)

            case SolverName.KOCIEMBA:
                return cls.kociemba(op)

            case SolverName.CAGE:
                raise InternalSWError("CAGE solver not implemented yet")

            case _:
                raise InternalSWError(f"Unknown solver: {solver_id}")
