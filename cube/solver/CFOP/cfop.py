from cube.operator.cube_operator import Operator
from .f2l import F2L
from cube.solver.begginer.l1_cross import L1Cross
from cube.solver.common.base_solver import BaseSolver
from cube.solver.solver import BeginnerLBLReduce, SolveStep, SolverResults
from cube import config
from cube.algs import Algs
from cube.app_exceptions import OpAborted, EvenCubeEdgeParityException, InternalSWError, EvenCubeCornerSwapException
from cube.model.cube import Cube


class CFOP(BaseSolver, BeginnerLBLReduce):
    """
    Based on https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/
    """

    __slots__ = ["_debug_override",
                 "l1_cross",
                 "f2l"]

    def __init__(self, op: Operator) -> None:
        super().__init__(op)

        self.l1_cross = L1Cross(self)
        self.l2 = F2L(self)

        self._debug_override: bool | None = None


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

    def solve(self, debug: bool | None = None, animation: bool | None = True,
              what: SolveStep = SolveStep.ALL) -> SolverResults:

        """

        :param debug:
        :param animation: not None force True/ Flalse
        :param what:
        :return:
        """

        if debug is None:
            debug = self._is_debug_enabled

        with self._op.with_animation(animation=animation):
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

        def _centers():
            """ Centers and edges are independent"""
            pass

        def _edges():
            """ Centers and edges are independent"""
            nonlocal partial_edge_was_detected

        def _reduce():
            _centers()
            _edges()

        def _l1x():
            _reduce()
            self.l1_cross.solve()

        def _f2l():
            _reduce()
            self.l1_cross.solve()
            self.f2l.solve()


        _d = self._debug_override
        try:
            self._debug_override = _debug

            match what:

                case SolveStep.L1x:
                    _l1x()

                case SolveStep.F2L:
                    _f2l()


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
            log_path = config.OPERATION_LOG_PATH if config.OPERATION_LOG else None
            if log_path:
                with open("operator.log", mode="a") as f:
                    print("Solver:", *args, file=f)
