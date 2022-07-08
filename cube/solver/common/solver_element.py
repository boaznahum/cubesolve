from typing import final, TYPE_CHECKING, TypeAlias

from cube.model.cube import Cube, CubeSupplier
from cube.model.cube_face import Face
from cube.operator.cube_operator import Operator
from cube.solver.common.base_solver import BaseSolver

if TYPE_CHECKING:
    from .common_op import CommonOp

_Common: TypeAlias = "CommonOp"


class SolverElement(CubeSupplier):
    __slots__ = ["_solver", "_ann", "_cmn"]

    _solver: BaseSolver

    def __init__(self, solver: BaseSolver) -> None:
        self._solver = solver
        self._ann = solver.op.annotation
        self._cmn = solver.cmn

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

    @property
    @final
    def cmn(self) -> _Common:
        return self._cmn

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face
