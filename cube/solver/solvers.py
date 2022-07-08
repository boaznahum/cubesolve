from cube.operator.cube_operator import Operator
from .CFOP.cfop import CFOP
from .solver import Solver
from .solver import BeginnerLBLReduce
from cube.solver.begginer.beginner_solver import BeginnerSolver
from .. import config


class Solvers:

    @staticmethod
    def default(op: Operator) -> Solver:
        if config.CFOP:
            return Solvers.cfop(op)
        else:
            return Solvers.beginner(op)

    @staticmethod
    def beginner(op: Operator) -> BeginnerLBLReduce:
        return BeginnerSolver(op)

    @staticmethod
    def cfop(op: Operator) -> Solver:
        return CFOP(op)


