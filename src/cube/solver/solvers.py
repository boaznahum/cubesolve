from cube.operator.cube_operator import Operator
from cube.solver.begginer.beginner_solver import BeginnerSolver
from .CFOP.cfop import CFOP
from .solver import BeginnerLBLReduce
from .solver import Solver
from .solver_name import SolverName
from .. import config
from cube.app.app_exceptions import InternalSWError


class Solvers:

    @staticmethod
    def default(op: Operator) -> Solver:
        if config.SOLVER_CFOP:
            return Solvers.cfop(op)
        else:
            return Solvers.beginner(op)

    @staticmethod
    def beginner(op: Operator) -> BeginnerLBLReduce:
        return BeginnerSolver(op)

    @staticmethod
    def cfop(op: Operator) -> Solver:
        return CFOP(op)

    @classmethod
    def next_solver(cls, current: SolverName, op: Operator):

        _ids = [ * SolverName ]
        index = _ids.index(current)

        next_s = _ids[ (index + 1) % len(_ids)]

        return cls.by_name(next_s, op)

    @classmethod
    def by_name(cls, solver_id: SolverName, op: Operator):

        match solver_id:

            case SolverName.LBL:
                return cls.beginner(op)

            case SolverName.CFOP:
                return cls.cfop(op)

            case _:
                raise InternalSWError("Unknown solver: {id}")



