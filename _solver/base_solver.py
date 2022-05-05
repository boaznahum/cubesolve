from _solver.isolver import ISolver
from cube import Cube
from cube_operator import Operator
from elements import Face


class SolverElement:
    __slots__ = ["_solver"]

    _solver: ISolver

    def __init__(self, solver: ISolver) -> None:
        self._solver = solver

    def debug(self, *args):
        self._solver.debug(args)

    @property
    def cube(self) -> Cube:
        return self._solver.cube

    @property
    def op(self) -> Operator:
        return self._solver.op

    # noinspection PyUnresolvedReferences
    @property
    def _cmn(self) -> "CommonOp":
        return self._solver.cmn

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face

