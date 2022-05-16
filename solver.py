import viewer
from _solver.base_solver import ISolver
from _solver.common_op import CommonOp
from _solver.l1_corners import L1Corners
from _solver.l1_cross import L1Cross
from _solver.l2 import L2
from _solver.l3_corners import L3Corners
from _solver.l3_cross import L3Cross
from algs import Algs
from cube import Cube
from cube_operator import Operator


class Solver(ISolver):
    __slots__ = ["_op", "_cube", "_debug",
                 "l1_cross",
                 "l1_corners",
                 "l2",
                 "l3_cross",
                 "l3_corners",
                 "common"]

    def __init__(self, op: Operator) -> None:
        super().__init__()
        self._cube = op.cube
        self._op: Operator = op

        self.common = CommonOp(self)
        self.l1_cross = L1Cross(self)
        self.l1_corners = L1Corners(self)
        self.l2 = L2(self)
        self.l3_cross = L3Cross(self)
        self.l3_corners = L3Corners(self)

        self._debug = True

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
    def is_solved(self):
        return self._cube.solved

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

        if self.l3_cross.solved() and self.l3_corners.solved():
            s += ", L3"
        elif self.l3_cross.solved():
            s += ", L3-Cross"
        elif self.l3_corners.solved():
            s += ", L3-Corners"
        else:
            s += ", No L3"

        return s

    def solve(self, debug=True, animation=True):
        with self._op.suspended_animation(not animation):
            return self._solve(debug)

    def _solve(self, debug=True):
        if self._cube.solved:
            return

        _d = self.debug
        try:
            self._debug = debug
            self.l1_cross.solve_l0_cross()
            self.l1_corners.solve()
            self.l2.solve()
            self.l3_cross.solve()
            self.l3_corners.solve()
        finally:
            self._debug = _d

    def debug(self, *args):
        if self._debug:
            print("Solver:", *args)

    def solution(self):
        if self.is_solved:
            return Algs.alg(None)

        n = len(self.op.history)
        solution_algs = []

        with self._op.suspended_animation():
            self.solve(debug=False, animation=False)
            while n < len(self.op.history):
                step = self.op.undo(animation=False)
                # s=str(step)
                if step:
                    solution_algs.insert(0, step)

            return Algs.alg(None, *solution_algs)
