from cube.app.app_exceptions import OpAborted
from cube.operator.Operator import Operator
from cube.solver.begginer.L1Cross import L1Cross
from cube.solver.common.BaseSolver import BaseSolver
from cube.solver.solver import BeginnerLBLReduce, SolveStep, SolverResults
from .OLL import OLL
from .PLL import PLL
from .F2L import F2L
from ..begginer.NxNCenters import NxNCenters
from ..begginer.NxNEdges import NxNEdges
from ..SolverName import SolverName


class CFOP(BaseSolver, BeginnerLBLReduce):
    """
    Based on https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/
    """

    __slots__ = ["l1_cross",
                 "f2l",
                 "oll",
                 "pll",
                 "nxn_centers", "nxn_edges"
                 ]

    def __init__(self, op: Operator) -> None:
        super().__init__(op)

        self.l1_cross = L1Cross(self)
        self.f2l = F2L(self)

        # temp -- still beginner
        self.oll = OLL(self)
        self.pll = PLL(self)

        self.nxn_centers = NxNCenters(self)
        self.nxn_edges = NxNEdges(self, True)

    @property
    def get_code(self):
        return SolverName.CFOP

    @property
    def status(self):

        s = ""

        def _add(x):
            nonlocal s
            if s:
                s += ","
            s += x

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
        f2f = self.f2l.solved()

        if cross and f2f:
            s = "F2L"
        else:

            s = ""
            if self.f2l.is_l1():
                _add("L1")
            elif cross:
                _add("L1 cross")

            if self.f2l.is_l2():
                _add("L2")

            if not s:
                s = "No F2L"

        is_oll = self.oll.is_solved
        is_pll = self.pll.is_solved
        if self.pll.is_solved:
            _add("L3")
        else:
            oll = self.oll.is_rotate_and_solved()
            pll = self.pll.is_rotate_and_solved()

            if oll or pll:
                if oll:
                    _add("OLL")

                if pll:
                    _add("PLL")
            else:
                _add("NO L3")

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


        def _centers():
            """ Centers and edges are independent"""
            self.nxn_centers.solve()

        def _edges():
            """ Centers and edges are independent"""
            self.nxn_edges.solve()

        def _reduce():
            _centers()
            _edges()

        def _l1x():
            _reduce()
            self.l1_cross.solve()

        def _f2l():
            _l1x()
            self.f2l.solve()

        def _l3oll():
            _f2l()
            self.oll.solve()

        def _l3pll():
            _l3oll()
            self.pll.solve()

        def _l3():
            _l3pll()

        _d = self._debug_override
        try:
            self._debug_override = _debug

            match what:

                case SolveStep.NxNCenters:
                    _centers()

                case SolveStep.NxNEdges:
                    _edges()

                # because CFOP knows only L1 cross, so we assume that what
                # user want when press F1
                case SolveStep.L1x | SolveStep.L1:
                    _l1x()

                case SolveStep.F2L | SolveStep.L2:
                    _f2l()

                case SolveStep.OLL:
                    _l3oll()

                case SolveStep.ALL | SolveStep.L3:
                    _l3()


        finally:
            self._debug_override = _d


        return sr
