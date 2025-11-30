from abc import abstractmethod
from typing import final, TYPE_CHECKING, TypeAlias, Tuple, ContextManager

from cube.model.Cube import Cube, CubeSupplier
from cube.model.Face import Face
from cube.operator.Operator import Operator
from cube.solver.common.BaseSolver import BaseSolver
from ...algs import Alg
from ...model.CubeQueries2 import CubeQueries2
from ...operator.op_annotation import SupportsAnnotation, AnnWhat

if TYPE_CHECKING:
    from .CommonOp import CommonOp

_Common: TypeAlias = "CommonOp"


class SolverElement(CubeSupplier):
    __slots__ = ["_solver", "_ann",
                 "_cmn",
                 "_debug_prefix",
                 "_cube",
                 "_cqr"
                 ]

    _solver: BaseSolver

    def __init__(self, solver: BaseSolver) -> None:
        self._solver = solver
        self._ann = solver.op.annotation
        self._cmn = solver.cmn
        self._debug_prefix: str | None = None
        self._cube = solver.cube
        self._cqr = solver.cube.cqr

    def _set_debug_prefix(self, prefix: str):
        self._debug_prefix = prefix

    def debug(self, *args):
        if x := self._debug_prefix:
            self._solver.debug(x + ":", *args)
        else:
            self._solver.debug(*args)

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def cqr(self) -> CubeQueries2:
        return self._cqr

    @property
    def op(self) -> Operator:
        return self._solver.op

    def play(self, alg: Alg):
        self.op.play(alg)


    @property
    def ann(self):
        """
        :deprecated, use
        :return:
        """
        return self._ann

    def annotate(self, *elements: Tuple[SupportsAnnotation, AnnWhat],
                 h1=None,
                 h2=None,
                 h3=None,
                 animation=True) -> ContextManager[None]:
        return self.ann.annotate(*elements, h1=h1, h2=h2, h3=h3, animation=animation)


    @property
    @final
    def cmn(self) -> _Common:
        return self._cmn

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face

    @property
    def yellow_face(self) -> Face:
        return self._cmn.white_face.opposite


class StepSolver(SolverElement):
    def __init__(self, solver: BaseSolver) -> None:
        super().__init__(solver)

    @abstractmethod
    def solve(self):
        pass

    @property
    @abstractmethod
    def is_solved(self) -> bool:
        pass




