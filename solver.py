from _solver.base_solver import ISolver
from _solver.common_op import CommonOp
from _solver.l0_corners import L0Corners
from _solver.l0_cross import L0Cross
from cube import Cube
from cube_operator import Operator

_DEBUG = True


class Solver(ISolver):
    __slots__ = ["_op", "_cube", "l0_cross", "common"]

    def __init__(self, op: Operator) -> None:
        super().__init__()
        self._cube = op.cube
        self._op = op

        self.common = CommonOp(self)
        self.l0_cross = L0Cross(self)
        self.l0_corners = L0Corners(self)

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def op(self) -> Operator:
        return self._op

    @property
    def cmn(self) -> CommonOp:
        return self.common

    @property
    def status(self):

        if self._cube.solved:
            return "Solved"

        cross= self.l0_cross.is_cross()
        corners = self.l0_corners.is_corners()

        if cross and corners:
            s = "L0"
        elif cross:
            s = "L0-Cross"
        elif corners:
            s = "L0-Corners"
        else:
            s = "No-L0"

        s += ", Unknown"

        return s

    def solve(self):
        if self._cube.solved:
            return

        self.l0_cross.solve_l0_cross()
        self.l0_corners.solve()

    def debug(self, *args):
        if _DEBUG:
            print("Solver:", *args)
