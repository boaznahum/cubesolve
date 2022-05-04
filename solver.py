from _solver.base_solver import ISolver
from _solver.l0 import L0
from cube import Cube
from cube_operator import Operator

_DEBUG = True


class Solver(ISolver):
    __slots__ = ["_op", "_cube", "l0"]

    def __init__(self, op: Operator) -> None:
        super().__init__()
        self._cube = op.cube
        self._op = op
        self.l0 = L0(self)

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def op(self) -> Operator:
        return self._op

    @property
    def status(self):

        if self._cube.solved:
            return "Solved"

        if not self.l0.is_l0_cross():
            return "No L0-Cross"

        s = "L0-Cross"

        s += ", Unknown"

        return s

    def solve(self):
        if self._cube.solved:
            return

        if not self.l0.is_l0_cross():
            self.l0.solve_l0_cross()
            self.l0.is_l0_cross()

    def debug(self, *args):
        if _DEBUG:
            print("Solver:", *args)
