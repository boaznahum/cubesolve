from collections.abc import Hashable, Iterable
from enum import Enum, unique
from typing import TYPE_CHECKING, Tuple, TypeAlias, Union

from cube.utils.config_protocol import ConfigProtocol

from cube.domain.model.Color import Color


@unique
class Direction(Enum):
    D0 = 0
    D90 = 90
    D180 = 180
    D270 = 270


@unique
class AxisName(Enum):
    """
    Whole cube Axis name
    """
    X = "X"  # Over R , against M
    Y = "Y"  # over U , against E
    Z = "Z"  # Over F,  With S


@unique
class EdgePosition(Enum):
    """
    Position of an edge relative to a face (when viewing the face from outside the cube).

    Used to get the edge at a specific position on a face via Face.get_edge().
    """
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


_Face: TypeAlias = "Face"  # type: ignore  # noqa: F821

if TYPE_CHECKING:
    from .Cube import Cube

# noinspection PyUnresolvedReferences
_Cube: TypeAlias = "Cube"  # type: ignore

PartColorsID: TypeAlias = frozenset[Color]
PartSliceHashID: TypeAlias = frozenset[Hashable]
PartFixedID: TypeAlias = "frozenset[PartSliceHashID]"

# order is important
PartSliceColors: TypeAlias = Union[Tuple[Color], Tuple[Color, Color], Tuple[Color, Color, Color]]

CubeState = dict[PartSliceHashID, PartSliceColors]


class PartName:

    def __init__(self) -> None:
        super().__init__()


class CHelper:

    @staticmethod
    def colors_id(c: Iterable[Color]):
        return frozenset(c)


EdgeSliceIndex = int
CenterSliceIndex = Tuple[int, int]
SliceIndex = EdgeSliceIndex | CenterSliceIndex  # type: ignore # row, column, must be hashable


class CubeElement:

    def __init__(self, cube: _Cube) -> None:
        super().__init__()
        self._cube: _Cube = cube

    @property
    def cube(self) -> _Cube:
        return self._cube

    @property
    def config(self) -> ConfigProtocol:
        """Get the configuration from the cube's service provider."""
        return self._cube.config

    @property
    def n_slices(self) -> int:
        return self.cube.n_slices

    def inv(self, i: int) -> int:
        return self.n_slices - 1 - i
