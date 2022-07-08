from typing import Sequence

from cube.algs import Algs, Alg
from cube.model.cube_face import Face
from cube.model import PartColorsID, Part, Edge, Color
from cube.operator.op_annotation import AnnWhat
from cube.solver.common.solver_element import SolverElement
from cube.solver.common.common_op import CommonOp
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.tracker import EdgeTracker


def use(_):
    pass


class F2L(SolverElement):
    __slots__: list[str] = []

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)

    def solved(self) -> bool:
        """
        :return: True if 2 first layers solve d(but still L2 need rotation
        """

        return self._l1_l2_solved()

    def is_l1(self):
        return self.cmn.white_face.solved

    def is_l2(self):

        edges = self.cmn.l2_edges()

        return Part.all_match_faces(edges)


    def _l1_l2_solved(self):
        wf = self.cmn.white_face
        if not wf.solved:
            return False

        edges = [* self.cmn.l2_edges(), * wf.edges ]

        l2_edges_solved = Part.all_match_faces(edges)
        return l2_edges_solved

    def solve(self):
        """
        Must be called after L1 Cross is solved
        :return:
        """

        # L1-cross will roate if it is the thing that need
        if self.solved():
            return

        wf = self.cmn.white_face

        if self.is_l1() and self.is_l2():
            # OK, need only to rotate

            l1_edges = wf.edges
            self.cmn.rotate_till(wf, lambda: Part.all_match_faces(l1_edges))
            return

        return False


