from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.beginner.BeginnerSolver import BeginnerSolver
from .CFOP.CFOP import CFOP
from .kociemba.KociembaSolver import KociembaSolver
from .solver import BeginnerLBLReduce
from .solver import Solver
from .SolverName import SolverName
from cube.domain.exceptions import InternalSWError


class Solvers:

    @staticmethod
    def default(op: OperatorProtocol) -> Solver:
        # Kociemba is the default - near-optimal solutions (18-22 moves)
        return Solvers.kociemba(op)

    @staticmethod
    def beginner(op: OperatorProtocol) -> BeginnerLBLReduce:
        return BeginnerSolver(op)

    @staticmethod
    def cfop(op: OperatorProtocol) -> Solver:
        return CFOP(op)

    @staticmethod
    def kociemba(op: OperatorProtocol) -> Solver:
        return KociembaSolver(op)

    @classmethod
    def next_solver(cls, current: SolverName, op: OperatorProtocol) -> Solver:

        _ids = [*SolverName]
        index = _ids.index(current)

        next_s = _ids[(index + 1) % len(_ids)]

        return cls.by_name(next_s, op)

    @classmethod
    def by_name(cls, solver_id: SolverName, op: OperatorProtocol) -> Solver:

        match solver_id:

            case SolverName.LBL:
                return cls.beginner(op)

            case SolverName.CFOP:
                return cls.cfop(op)

            case SolverName.KOCIEMBA:
                return cls.kociemba(op)

            case _:
                raise InternalSWError(f"Unknown solver: {solver_id}")



