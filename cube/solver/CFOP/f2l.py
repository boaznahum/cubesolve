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
        :return: true if 4 middle slice match faces, don't try to rotate
        """

        return False


    def solve(self):
        """
        Must be called after L1 is solved
        :return:
        """

        if self.solved():
            return  # avoid rotating cube


