from _solver.base_solver import ISolver
from _solver.common_op import CommonOp
from _solver.l1_corners import L1Corners
from _solver.l1_cross import L1Cross
from _solver.l2 import L2
from _solver.l3_cross import L3Cross
from cube import Cube
from cube_operator import Operator

_DEBUG = True


class Solver(ISolver):
    __slots__ = ["_op", "_cube",
                 "l1_cross",
                 "l1_corners",
                 "l2",
                 "l3_cross",
                 "common"]

    def __init__(self, op: Operator) -> None:
        super().__init__()
        self._cube = op.cube
        self._op = op

        self.common = CommonOp(self)
        self.l1_cross = L1Cross(self)
        self.l1_corners = L1Corners(self)
        self.l2 = L2(self)
        self.l3_cross = L3Cross(self)

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

        cross = self.l1_cross.is_cross()
        corners = self.l1_corners.is_corners()

        if cross and corners:
            s = "L1"
        elif cross:
            s = "L1-Cross"
        elif corners:
            s = "L1-Corners"
        else:
            s = "No-L1"

        if self.l2.solved():
            s += ", L2"
        else:
            s += ", No L2"

        if self.l3_cross.solved():
            s += ", L3-Cross"
        else:
            s += ", No L3-Cross"

        return s

    def solve(self):
        if self._cube.solved:
            return

        self.l1_cross.solve_l0_cross()
        self.l1_corners.solve()
        self.l2.solve()
        self.l3_cross.solve()

    def debug(self, *args):
        if _DEBUG:
            print("Solver:", *args)
