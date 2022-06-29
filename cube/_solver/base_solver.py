from enum import unique, Enum

from cube._solver.isolver import ISolver
from cube.model.cube import Cube, CubeSupplier
from cube.model.cube_face import Face
from cube.operator.cube_operator import Operator
from cube.operator.op_annotation import OpAnnotation




class SolverElement(CubeSupplier):
    __slots__ = ["_solver", "_ann"]

    _solver: ISolver

    def __init__(self, solver: ISolver) -> None:
        self._solver = solver
        self._ann = solver.op.annotation

    def debug(self, *args):
        self._solver.debug(args)

    @property
    def cube(self) -> Cube:
        return self._solver.cube

    @property
    def op(self) -> Operator:
        return self._solver.op

    @property
    def ann(self):
        return self._ann

    # noinspection PyUnresolvedReferences
    @property
    def _cmn(self) -> "CommonOp":  # type: ignore
        return self._solver.cmn

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face


