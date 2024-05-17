from collections import defaultdict
from collections.abc import Hashable
from typing import Any, TYPE_CHECKING, TypeAlias

from .cube_boy import Color
from .. import config

if TYPE_CHECKING:
    from .cube_face import Face
    from .cube import Cube
    from ._part_slice import PartSlice

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore
_PartSlice: TypeAlias = "PartSlice"  # type: ignore


class PartEdge:
    """
    THe smallest part of the cube, aggregated by the :class:`PartSlice`
    """
    __slots__ = ["_face", "_parent", "_color", "_annotated_by_color",
                 "_annotated_fixed_location",
                 "attributes", "c_attributes",
                 "f_attributes"]

    _face: _Face
    _color: Color

    def __init__(self, face: _Face, color: Color) -> None:
        super().__init__()
        self._face = face
        self._color = color
        self._annotated_by_color: bool = False
        self._annotated_fixed_location: bool = False
        self.attributes: dict[Hashable, Any] = {}
        self.c_attributes: dict[Hashable, Any] = {}

        # fixed attributes that are not moved around with the slice
        self.f_attributes: dict[Hashable, Any] = defaultdict(bool)

        self._parent: _PartSlice

    @property
    def face(self) -> _Face:
        return self._face

    @property
    def parent(self) -> _PartSlice:
        return self._parent

    @property
    def color(self) -> Color:
        return self._color

    def __str__(self) -> str:
        if config.SHORT_PART_NAME:
            return str(self._color.name)
        else:
            return f"{self._color.name}@{self._face}"

    def copy_color(self, source: "PartEdge"):
        self._color = source._color
        self._annotated_by_color = source._annotated_by_color
        self.c_attributes.clear()
        self.c_attributes.update(source.c_attributes)

    def clone(self) -> "PartEdge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        p = PartEdge(self._face, self._color)
        p._annotated_by_color = self._annotated_by_color
        p.attributes = self.attributes.copy()
        p.c_attributes = self.c_attributes.copy()

        return p

    def annotate(self, fixed_location: bool):
        if fixed_location:
            self._annotated_fixed_location = True
        else:
            self._annotated_by_color = True

    def un_annotate(self):
        self._annotated_by_color = False
        self._annotated_fixed_location = False

    @property
    def annotated(self) -> Any:
        return self._annotated_by_color or self._annotated_fixed_location

    @property
    def annotated_by_color(self) -> Any:
        return self._annotated_by_color

    @property
    def annotated_fixed(self) -> Any:
        return self._annotated_fixed_location
