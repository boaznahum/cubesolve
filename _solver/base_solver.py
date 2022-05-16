from contextlib import contextmanager

from _solver.isolver import ISolver
from algs import Algs
from cube import Cube
from cube_face import Face
from cube_operator import Operator
from elements import Part


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

    @property
    def running_solution(self):
        return self._solver.running_solution

    def annotate(self, *parts: Part, un_an: bool = False):

        if self.running_solution or not self.op.is_with_animation:
            return

        if un_an:
            for p in parts:
                p.un_annotate()
        else:
            for p in parts:
                p.annotate()

        self.op.op(Algs.AN)

    @contextmanager
    def w_annotate(self, *parts: Part):

        colors = [p.colors_id_by_color for p in parts]

        self.annotate(*parts)
        try:
            yield None
        finally:
            self.annotate(*[self.cube.find_part_by_colors(c) for c in colors], un_an=True)
