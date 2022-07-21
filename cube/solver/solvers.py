from enum import Enum, unique

from cube.operator.cube_operator import Operator
from .CFOP.cfop import CFOP
from .solver import Solver
from .solver import BeginnerLBLReduce
from cube.solver.begginer.beginner_solver import BeginnerSolver
from .solver_name import SolverName
from .. import config
from ..app_exceptions import InternalSWError


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

        next = _ids[ (index + 1) % len(_ids)]

        return cls._create_solver(next, op)

    @classmethod
    def _create_solver(cls, id: SolverName, op: Operator):

        match id:

            case SolverName.LBL:
                return cls.beginner(op)

            case SolverName.CFOP:
                return cls.cfop(op)

            case _:
                raise InternalSWError("Unknown solver: {id}")



