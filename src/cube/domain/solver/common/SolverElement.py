from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, ContextManager, Tuple, TypeAlias, final

from cube.utils.prefixed_logger import MutablePrefixLogger
from cube.domain.model.Cube import Cube, CubeSupplier
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.protocols import (
    AnnotationProtocol,
    OperatorProtocol,
    SolverElementsProvider,
    SupportsAnnotation,
)

from ...algs import Alg
from ...model.CubeQueries2 import CubeQueries2

if TYPE_CHECKING:
    from .CommonOp import CommonOp

_Common: TypeAlias = "CommonOp"


class SolverElement(CubeSupplier):
    __slots__ = ["_solver", "_ann",
                 "_cmn",
                 "_cube",
                 "_cqr",
                 "_logger"
                 ]

    _solver: SolverElementsProvider

    def __init__(self, solver: SolverElementsProvider) -> None:
        self._solver = solver
        self._ann = solver.op.annotation
        self._cmn = solver.cmn
        self._cube = solver.cube
        self._cqr = solver.cube.cqr
        # MutablePrefixLogger: prefix can be set later via _set_debug_prefix
        self._logger: MutablePrefixLogger = MutablePrefixLogger(solver._logger)

    def _set_debug_prefix(self, prefix: str) -> None:
        """Set the debug prefix for this element's logger."""
        self._logger.set_prefix(prefix)

    def debug(self, *args) -> None:
        """Output debug information.

        DEPRECATED: Use self._logger.debug(None, ...) instead.
        """
        self._logger.debug(None, *args)

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def n_slices(self) -> int:
        return self._cube.n_slices

    @property
    def cqr(self) -> CubeQueries2:
        return self._cqr

    @property
    def op(self) -> OperatorProtocol:
        return self._solver.op

    def play(self, alg: Alg):
        self.op.play(alg)


    @property
    def ann(self) -> AnnotationProtocol:
        """
        :deprecated, use annotate() directly
        :return:
        """
        return self._ann

    def annotate(self, *elements: Tuple[SupportsAnnotation, AnnWhat],
                 h1: str | Callable[[], str] | None = None,
                 h2: str | Callable[[], str] | None = None,
                 h3: str | Callable[[], str] | None = None,
                 animation: bool = True) -> ContextManager[None]:
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
    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver)

    @abstractmethod
    def solve(self):
        pass

    @property
    @abstractmethod
    def is_solved(self) -> bool:
        pass




