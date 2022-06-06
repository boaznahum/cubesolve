from enum import Enum, unique

import config
from _solver.base_solver import ISolver
from _solver.common_op import CommonOp
from _solver.l1_corners import L1Corners
from _solver.l1_cross import L1Cross
from _solver.l2 import L2
from _solver.l3_corners import L3Corners
from _solver.l3_cross import L3Cross
from _solver.nxn_centers import NxNCenters
from _solver.nxn_edges import NxNEdges
from algs import Algs
from app_exceptions import OpAborted, EvenCubeEdgeParityException, InternalSWError, EvenCubeCornerSwapException
from cube import Cube
from cube_operator import Operator


@unique
class SolveStep(Enum):
    ALL = "ALL"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3x = "L3x"
    NxNCenters = "NxNCenters"
    NxNEdges = "NxNEdges"


class SolverResults:

    def __init__(self) -> None:
        super().__init__()
        self._was_corner_swap = False
        self._was_partial_edge_parity = False
        self._was_even_edge_parity = False

    @property
    def was_corner_swap(self):
        return self._was_corner_swap

    @property
    def was_even_edge_parity(self):
        return self._was_even_edge_parity

    @property
    def was_partial_edge_parity(self):
        return self._was_partial_edge_parity


class Solver(ISolver):
    __slots__ = ["_op", "_cube", "_debug_override", "_aborted",
                 "_running_solution",
                 "l1_cross",
                 "l1_corners",
                 "l2",
                 "l3_cross",
                 "l3_corners",
                 "nxn_centers",
                 "nxn_edges",
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
        self.nxn_centers = NxNCenters(self)
        self.nxn_edges = NxNEdges(self)

        # allow solver to not put annotations
        self._running_solution = False
        self._debug_override: bool | None = None

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
    def is_debug_config_mode(self) -> bool:
        return config.SOLVER_DEBUG

    @property
    def _is_debug_enabled(self) -> bool:
        if self._debug_override is None:
            return self.is_debug_config_mode
        else:
            return self._debug_override

    @property
    def status(self):

        if not self._cube.is3x3:
            if self._cube.is_boy:
                s = "Boy:True"
            else:
                s = "Boy:False"

            if self.nxn_centers.solved():
                s += ", Centers"
            else:
                s += ", No Centers"

            if self.nxn_edges.solved():
                s += ", Edges"
            else:
                s += ", No Edges"

            return s + ", Not 3x3"

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

    def solve(self, debug: bool | None = None, animation=True, what: SolveStep = SolveStep.ALL) -> SolverResults:

        if debug is None:
            debug = self._is_debug_enabled

        with self._op.suspended_animation(not animation):
            try:
                return self._solve(debug, what)
            except OpAborted:
                return SolverResults()

    def _solve(self, _debug: bool | None = True, what: SolveStep = SolveStep.ALL) -> SolverResults:
        sr: SolverResults = SolverResults()

        if self._cube.solved:
            return sr

        even_edge_parity_was_detected = False
        even_corner_swap_was_detected = False
        partial_edge_was_detected = False

        _d = self._debug_override
        try:
            self._debug_override = _debug
            for i in [1, 2, 3]:  # in case of even, we need 1 for edge parity and one for corner swap

                if self._cube.solved:
                    break

                self.debug(f"@@@@ Iteration # {i}")

                try:
                    match what:

                        case SolveStep.ALL | SolveStep.L3:
                            self.nxn_centers.solve()
                            if self.nxn_edges.solve():
                                partial_edge_was_detected = True
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

                        case SolveStep.NxNCenters:
                            self.nxn_centers.solve()

                        case SolveStep.NxNEdges:
                            # centres are not must
                            # self.nxn_centers.solve()
                            if self.nxn_edges.solve():
                                partial_edge_was_detected = True

                except EvenCubeEdgeParityException:
                    self.debug(f"Catch even edge parity in iteration #{i}")
                    if even_edge_parity_was_detected:
                        raise InternalSWError("already even_edge_parity_was_detected")
                    else:
                        even_edge_parity_was_detected = True
                        self.nxn_edges.do_edge_parity_on_any()
                        continue  # try again

                except EvenCubeCornerSwapException:
                    self.debug(f"Catch corner swap in iteration #{i}")
                    if even_corner_swap_was_detected:
                        raise InternalSWError("already even_corner_swap_was_detected")
                    else:
                        even_corner_swap_was_detected = True
                        continue  # try agin, swap was done by l3_corners

                if what == SolveStep.ALL and not self.is_solved:
                    raise InternalSWError(f"Non solved iteration {i}, but no parity detected")


        finally:
            self._debug_override = _d

        if even_edge_parity_was_detected:
            sr._was_even_edge_parity = True

        if even_corner_swap_was_detected:
            sr._was_corner_swap = True

        if partial_edge_was_detected:
            sr._was_partial_edge_parity = True

        return sr

    def debug(self, *args):
        if self._is_debug_enabled:
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
