from abc import abstractmethod
from collections.abc import Sequence, Iterable
from typing import TYPE_CHECKING, TypeAlias, Tuple

from .Part import Part
from ._elements import CubeElement
from ._part_slice import PartSlice

if TYPE_CHECKING:
    from .cube_face import Face
    from .cube import Cube

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore


class SuperElement(CubeElement):
    __slots__ = ["_cube",
                 "_parts",
                 ]

    def __init__(self, cube: _Cube) -> None:
        super().__init__(cube)
        self._parts: Tuple[Part, ...] = ()

    def set_parts(self, *parts: Part):
        self._parts = tuple(parts)

    @property
    def parts(self) -> Sequence[Part]:
        return self._parts

    def finish_init(self):
        for p in self._parts:
            p.finish_init()

    def set_and_finish_init(self, *parts: Part):
        self.set_parts(*parts)

        self.finish_init()

    @property
    @abstractmethod
    def slices(self) -> Iterable[PartSlice]:
        pass
