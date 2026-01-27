from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, ContextManager, Tuple, TypeAlias, final

from cube.utils.config_protocol import ConfigProtocol
from cube.utils.logger_protocol import ILogger, LazyArg
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


class SolverHelper(CubeSupplier, SolverElementsProvider):
    __slots__ = ["_solver", "_ann",
                 "_cmn",
                 "_cube",
                 "_cqr",
                 "_SolverElement__logger"
                 ]

    _solver: SolverElementsProvider

    def __init__(self, solver: SolverElementsProvider, debug_prefix: str, _is_common_op: bool = False) -> None:
        self._solver = solver
        self._ann = solver.op.annotation
        self._cube = solver.cube
        self._cqr = solver.cube.cqr
        self.__logger: ILogger = solver._logger.with_prefix(debug_prefix)

        if _is_common_op:
            self._cmn = self  # type: ignore  # CommonOp is its own cmn
        else:
            from .CommonOp import CommonOp
            self._cmn = CommonOp(self)

    @property
    def _logger(self) -> ILogger:
        return self.__logger

    def debug(self, *args: LazyArg, level: int | None = None) -> None:
        """Output debug information with optional level filtering.

        Args:
            *args: Arguments to print. Can be regular values or Callable[[], Any]
                   for lazy evaluation.
            level: Optional debug level. If set, checks level <= threshold.
        """
        self._logger.debug(None, *args, level=level)

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

    @property
    def config(self) -> ConfigProtocol:
        return self._solver.config

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
        return self._cmn  # type: ignore[return-value]  # CommonOp sets self._cmn = self

    @property
    def white_face(self) -> Face:
        return self._cmn.white_face

    @property
    def yellow_face(self) -> Face:
        return self._cmn.white_face.opposite


class StepSolver(SolverHelper):
    def __init__(self, solver: SolverElementsProvider, debug_prefix: str) -> None:
        super().__init__(solver, debug_prefix)

    @abstractmethod
    def solve(self):
        pass

    @property
    @abstractmethod
    def is_solved(self) -> bool:
        pass




