from collections.abc import Iterable, Iterator
from contextlib import contextmanager, AbstractContextManager
from enum import unique, Enum
from typing import Tuple, Literal, Optional, TypeAlias, Callable

from cube._solver.isolver import ISolver
from cube.algs.algs import Algs
from cube.operator.cube_operator import Operator
from cube.model.cube import Cube, CubeSupplier
from cube.model.cube_face import Face
from cube.model.cube_queries import CubeQueries
from cube.model.elements import Part, PartColorsID, CenterSlice, EdgeSlice, PartSlice, Corner, Edge, PartEdge
from cube.operator.op_annotation import OpAnnotation
from cube.viewer.viewer_markers import VMarker, VIEWER_ANNOTATION_KEY

_SLice_Tracking_UniqID: int = 0

_HEAD: TypeAlias = Optional[str | Callable[[], str]]
_HEADS = Optional[Tuple[_HEAD, _HEAD, _HEAD]]


@unique
class AnnWhat(Enum):
    """
    If color is given , find its actual location and track it where it goes
    If part is given find it actual location and track it where it goes
    """
    FindLocationTrackByColor = 1
    Position = 2


class SolverElement(CubeSupplier):
    __slots__ = ["_solver", "_ann"]

    _solver: ISolver

    def __init__(self, solver: ISolver) -> None:
        self._solver = solver
        self._ann = OpAnnotation(solver.cube, solver.op)

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


