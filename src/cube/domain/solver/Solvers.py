from cube.domain.solver.protocols import OperatorProtocol
from .solver import Solver
from .SolverName import SolverName
from cube.domain.exceptions import InternalSWError


class Solvers:
    """
    Factory for creating solver instances.

    All solvers use the orchestrator pattern:
    - beginner() and cfop() return NxNSolverOrchestrator instances
      that compose a Reducer + 3x3Solver
    - cage() returns a direct NxN solver (no reducer)

    This design allows:
    - Any reducer to work with any 3x3 solver
    - Easy swapping of reducers without changing solvers
    - Centralized parity handling in orchestrator
    - Consistent behavior across all solver types

    The default() method reads from DEFAULT_SOLVER config setting.
    """

    @classmethod
    def default(cls, op: OperatorProtocol) -> Solver:
        """
        Get the default solver based on config setting.

        The solver name is read from DEFAULT_SOLVER in _config.py.
        Supports case-insensitive matching and unambiguous prefix matching.

        See SolverName.lookup() for matching rules.
        """
        from cube.application import _config as cfg

        solver_name = SolverName.lookup(cfg.DEFAULT_SOLVER)
        return cls.by_name(solver_name, op)

    @staticmethod
    def beginner(op: OperatorProtocol) -> Solver:
        """
        Get beginner layer-by-layer solver with NxN support.

        For 3x3: Uses BeginnerSolver3x3 via orchestrator
        For NxN: Uses BeginnerReducer + BeginnerSolver3x3

        Uses basic (M-slice) edge parity algorithm.
        """
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3
        from .NxNSolverOrchestrator import NxNSolverOrchestrator

        solver_3x3 = Solvers3x3.beginner(op)
        reducer = Reducers.beginner(op, advanced_edge_parity=False)

        return NxNSolverOrchestrator(
            op, reducer, solver_3x3, SolverName.LBL
        )

    @staticmethod
    def cfop(op: OperatorProtocol) -> Solver:
        """
        Get CFOP (Fridrich) solver with NxN support.

        For 3x3: Uses CFOP3x3 via orchestrator
        For NxN: Uses BeginnerReducer + CFOP3x3

        Uses advanced (R/L-slice) edge parity algorithm.
        """
        from .Reducers import Reducers
        from .Solvers3x3 import Solvers3x3
        from .NxNSolverOrchestrator import NxNSolverOrchestrator

        solver_3x3 = Solvers3x3.cfop(op)
        reducer = Reducers.beginner(op, advanced_edge_parity=True)

        return NxNSolverOrchestrator(
            op, reducer, solver_3x3, SolverName.CFOP
        )

    # @staticmethod
    # def kociemba(op: OperatorProtocol) -> Solver:
    #     """
    #     Get Kociemba near-optimal solver with NxN support.
    #
    #     For 3x3: Uses Kociemba algorithm (18-22 moves)
    #     For NxN: Uses BeginnerReducer + Kociemba3x3
    #
    #     Uses advanced (R/L-slice) edge parity algorithm.
    #     """
    #     from .Reducers import Reducers
    #     from .Solvers3x3 import Solvers3x3
    #     from .NxNSolverOrchestrator import NxNSolverOrchestrator
    #
    #     solver_3x3 = Solvers3x3.kociemba(op)
    #     reducer = Reducers.beginner(op, advanced_edge_parity=True)
    #
    #     return NxNSolverOrchestrator(
    #         op, reducer, solver_3x3, SolverName.KOCIEMBA
    #     )

    @staticmethod
    def cage(op: OperatorProtocol) -> Solver:
        """
        Get Cage Method direct NxN solver.

        Solves big cubes by building edges+corners first (the "cage"),
        then filling centers last using commutators.

        This approach is completely parity-free.
        Only works for cubes larger than 3x3.
        """
        from .direct.cage import CageNxNSolver

        return CageNxNSolver(op)

    @classmethod
    def next_solver(cls, current: SolverName, op: OperatorProtocol) -> Solver:
        """
        Get the next solver in rotation.

        Cycles through all available solvers in SolverName enum order.
        """
        _ids = [*SolverName]
        index = _ids.index(current)

        next_s = _ids[(index + 1) % len(_ids)]

        return cls.by_name(next_s, op)

    @classmethod
    def by_name(cls, solver_id: SolverName, op: OperatorProtocol) -> Solver:
        """
        Get a solver by its name.

        Args:
            solver_id: The solver name enum value
            op: Operator for cube manipulation

        Returns:
            Solver instance

        Raises:
            InternalSWError: If solver_id is unknown
        """
        match solver_id:

            case SolverName.LBL:
                return cls.beginner(op)

            case SolverName.CFOP:
                return cls.cfop(op)

            # case SolverName.KOCIEMBA:
            #     return cls.kociemba(op)

            case SolverName.CAGE:
                return cls.cage(op)

            case _:
                raise InternalSWError(f"Unknown solver: {solver_id}")



