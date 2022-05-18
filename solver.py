from enum import Enum, unique

import viewer
from _solver.base_solver import ISolver
from _solver.common_op import CommonOp
from _solver.l1_corners import L1Corners
from _solver.l1_cross import L1Cross
from _solver.l2 import L2
from _solver.l3_corners import L3Corners
from _solver.l3_cross import L3Cross
from algs import Algs
from app_exceptions import OpAborted
from cube import Cube
from cube_operator import Operator


@unique
class SolveStep(Enum):
    ALL = "ALL"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3x = "L3x"


class Solver(ISolver):
    __slots__ = ["_op", "_cube", "_debug", "_aborted",
                 "_running_solution",
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

        # allow solver to not put annotations
        self._running_solution = False
        self._debug: bool = False

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

    def solve(self, debug: bool|None = None, animation=True, what: SolveStep = SolveStep.ALL):

        if debug is None:
            debug = self._debug

        with self._op.suspended_animation(not animation):
            try:
                return self._solve(debug, what)
            except OpAborted:
                return

    def _solve(self, _debug=True, what: SolveStep = SolveStep.ALL):
        if self._cube.solved:
            return

        _d = self._debug
        try:
            self._debug = _debug

            match what:

                case SolveStep.ALL | SolveStep.L3:
                    self.l1_cross.solve_l0_cross()
                    self.l1_corners.solve()
                    self.l2.solve()
                    self.l3_cross.solve()
                    self.l3_corners.solve()

                case SolveStep.L3x:
                    self.l1_cross.solve_l0_cross()
                    self.l1_corners.solve()
                    self.l2.solve()
                    self.l3_cross.solve()

                case SolveStep.L2:
                    self.l1_cross.solve_l0_cross()
                    self.l1_corners.solve()
                    self.l2.solve()

                case SolveStep.L1:
                    self.l1_cross.solve_l0_cross()
                    self.l1_corners.solve()

        finally:
            self._debug = _d

    def debug(self, *args):
        if self._debug:
            print("Solver:", *args)

    @property
    def running_solution(self):
        return self._running_solution

    def solution(self):
        if self.is_solved:
            return Algs.alg(None)

        rs = self._running_solution
        self._running_solution = True
        try:
            n = len(self.op.history)
            solution_algs = []

            with self._op.suspended_animation():

                with self._op.save_history():  # not really needed
                    self.solve(debug=False, animation=False)
                    while n < len(self.op.history):
                        step = self.op.undo(animation=False)
                        # s=str(step)
                        if step:
                            solution_algs.insert(0, step)

                return Algs.alg(None, *solution_algs)
        finally:
            self._running_solution = rs
