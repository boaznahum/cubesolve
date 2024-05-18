from collections.abc import Iterable, Hashable, Collection
from enum import Enum, unique
from typing import TypeAlias, Tuple, TYPE_CHECKING, Union

from .cube_boy import Color, FaceName


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
    X = "X"
    Y = "Y"
    Z = "Z"


_Face: TypeAlias = "Face"  # type: ignore

if TYPE_CHECKING:
    from .cube import Cube

# noinspection PyUnresolvedReferences
_Cube: TypeAlias = "Cube"  # type: ignore

PartColorsID = frozenset[Color]
PartSliceHashID = frozenset[Hashable]
PartFixedID = frozenset[PartSliceHashID]

# order is important
PartSliceColors = Union[Tuple[Color], Tuple[Color, Color], Tuple[Color, Color, Color]]

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
    def n_slices(self) -> int:
        return self.cube.n_slices

    def inv(self, i: int) -> int:
        return self.n_slices - 1 - i
