"""Solver factory - creates solver instances using orchestrator pattern."""

from cube.domain.exceptions import InternalSWError
from cube.domain.solver.protocols import OperatorProtocol

from .solver import Solver
from .SolverName import SolverName


class Solvers:
    """
    Factory for creating solver instances.

    All solvers use the orchestrator pattern:
    - LBL, CFOP, KOCIEMBA return NxNSolverOrchestrator instances
      that compose a Reducer + 3x3Solver

    This design allows:
    - Any reducer to work with any 3x3 solver
    - Easy swapping of reducers without changing solvers
    - Centralized parity handling in orchestrator
    - Consistent behavior across all solver types
    """

    @classmethod
    def default(cls, op: OperatorProtocol) -> Solver:
        """Get the default solver based on config setting."""
        solver_name = SolverName.lookup(op.app_state.config.default_solver)
        return cls.by_name(solver_name, op)

    @staticmethod
    def beginner(op: OperatorProtocol) -> Solver:
        """
        Get beginner layer-by-layer solver with NxN support.

        For 3x3: Uses BeginnerSolver3x3 via orchestrator
        For NxN: Uses BeginnerReducer + BeginnerSolver3x3

        Uses basic (M-slice) edge parity algorithm.
        """
        from .NxNSolverOrchestrator import NxNSolverOrchestrator
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3

        parent_logger = op.cube.sp.logger
        solver_3x3 = Solvers3x3.beginner(op, parent_logger)
        reducer = Reducers.beginner(op, advanced_edge_parity=False)

        return NxNSolverOrchestrator(
            op, parent_logger, reducer, solver_3x3, SolverName.LBL
        )

    @staticmethod
    def cfop(op: OperatorProtocol) -> Solver:
        """
        Get CFOP (Fridrich) solver with NxN support.

        For 3x3: Uses CFOP3x3 via orchestrator
        For NxN: Uses BeginnerReducer + CFOP3x3

        Uses advanced (R/L-slice) edge parity algorithm.
        """
        from .NxNSolverOrchestrator import NxNSolverOrchestrator
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3

        parent_logger = op.cube.sp.logger
        solver_3x3 = Solvers3x3.cfop(op, parent_logger)
        reducer = Reducers.beginner(op, advanced_edge_parity=True)

        return NxNSolverOrchestrator(
            op, parent_logger, reducer, solver_3x3, SolverName.CFOP
        )

    @staticmethod
    def kociemba(op: OperatorProtocol) -> Solver:
        """
        Get Kociemba near-optimal solver with NxN support.

        For 3x3: Uses Kociemba algorithm (18-22 moves)
        For NxN: Uses BeginnerReducer + Kociemba3x3

        Uses advanced (R/L-slice) edge parity algorithm.
        """
        from .NxNSolverOrchestrator import NxNSolverOrchestrator
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3

        parent_logger = op.cube.sp.logger
        solver_3x3 = Solvers3x3.kociemba(op, parent_logger)
        reducer = Reducers.beginner(op, advanced_edge_parity=True)

        return NxNSolverOrchestrator(
            op, parent_logger, reducer, solver_3x3, SolverName.KOCIEMBA
        )

    @staticmethod
    def cage(op: OperatorProtocol) -> Solver:
        """
        Get Cage method solver (odd cubes only).

        Solves in this order:
        - Phase 1a: Edges (reuses NxNEdges)
        - Phase 1b: Corners (uses 3x3 solver from cfg.CAGE_3X3_SOLVER)
        - Phase 2: Centers (TODO - commutators)

        NOTE: Only supports ODD cubes (5x5, 7x7) where face center
        defines the face color. Even cubes not yet supported.
        """
        from .direct.cage.CageNxNSolver import CageNxNSolver

        parent_logger = op.cube.sp.logger
        return CageNxNSolver(op, parent_logger)

    @staticmethod
    def reducer(op: OperatorProtocol) -> Solver:
        """
        Get Reducer solver for NxN cubes.

        Reduces the cube to a 3x3 equivalent by solving centers and
        pairing edges, then solves using a 3x3 method.
        """
        from .direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver

        parent_logger = op.cube.sp.logger
        return LayerByLayerNxNSolver(op, parent_logger)

    @classmethod
    def next_solver(cls, current: SolverName, op: OperatorProtocol) -> Solver:
        """Get the next solver in rotation (skips unimplemented solvers)."""
        all_solvers = [*SolverName]
        index = all_solvers.index(current)

        # Find next implemented solver
        for _ in range(len(all_solvers)):
            index = (index + 1) % len(all_solvers)
            candidate = all_solvers[index]
            if candidate.meta.implemented:
                return cls.by_name(candidate, op)

        # All solvers are unimplemented (shouldn't happen)
        raise InternalSWError("No implemented solvers available")

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
                return cls.cage(op)

            case SolverName.REDUCER:
                return cls.reducer(op)

            case _:
                raise InternalSWError(f"Unknown solver: {solver_id}")
