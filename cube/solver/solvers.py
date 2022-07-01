from cube.operator.cube_operator import Operator
from .abstract_solver import Solver
from .abstract_solver import BeginnerLBLReduce
from .imp.begginer.beginner_solver import BeginnerSolver


class Solvers:

    @staticmethod
    def default(op: Operator) -> Solver:
        return Solvers.beginner(op)

    @staticmethod
    def beginner(op: Operator) -> BeginnerLBLReduce:
        return BeginnerSolver(op)


