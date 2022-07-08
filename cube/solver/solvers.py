from cube.operator.cube_operator import Operator
from .solver import Solver
from .solver import BeginnerLBLReduce
from cube.solver.begginer.beginner_solver import BeginnerSolver


class Solvers:

    @staticmethod
    def default(op: Operator) -> Solver:
        return Solvers.beginner(op)

    @staticmethod
    def beginner(op: Operator) -> BeginnerLBLReduce:
        return BeginnerSolver(op)


