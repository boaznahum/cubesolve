from collections.abc import Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Tuple, TypeAlias

from cube.domain.exceptions import InternalSWError

from ._elements import SliceIndex
from ._part import CornerName, _faces_2_corner_name
from ._part_slice import CornerSlice, PartSlice
from .cube_boy import Color
from .Part import Part
from .PartEdge import PartEdge

if TYPE_CHECKING:
    from .Cube import Cube
    from .Face import Face

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore


class Corner(Part):
    __slots__ = ["_slice"]

    def __init__(self, a_slice: CornerSlice) -> None:
        self._slice = a_slice
        super().__init__()

    @property
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        """
        In the case of Corner it is also the actual edges
        """
        return self._slice.edges

    @property
    def all_slices(self) -> Iterator[CornerSlice]:
        yield self._slice

    def get_slice(self, index: SliceIndex) -> PartSlice:
        return self._slice

    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:
        return self.all_slices

    @property
    def slice(self) -> PartSlice:
        return self._slice

    def copy(self) -> "Corner":
        """
        Used as temporary for rotating, must not be used in cube
        :return:
        """
        return Corner(self._slice.clone())

    def replace_colors(self, on_face: _Face,
                       source: "Corner",
                       source_2: _Face, target_2: _Face,
                       source_3: _Face, target_3: _Face,
                       ):
        """
        Replace the colors of this corner with the colors from source
        Find the edge part contains on_face both in self and the other face,
        replaces the edge part color on on_face with the matched color from source

        We assume that both source and self are belonged to on_face.
        :param target_3:
        :param source_3:
        :param target_2:
        :param source_2:
        :param on_face:
        :param source:
        :return:
        """

        self._replace_colors(source, (on_face, on_face), (source_2, target_2), (source_3, target_3))

    def get_other_faces_color(self, face: _Face) -> Tuple[Color, Color]:

        edges = self._slice.edges
        e1 = edges[0]
        e2 = edges[1]
        e3 = edges[2]

        if face is e1.face:
            return e2.color, e3.color
        elif face is e2.face:
            return e1.color, e3.color
        elif face is e3.face:
            return e1.color, e2.color
        else:
            raise InternalSWError(f"Face {face} is not on {self}")

    @property
    def is3x3(self) -> bool:
        return True

    @property
    def name(self) -> CornerName:
        # todo: optimize it
        return _faces_2_corner_name((e.face.name for e in self._slice.edges))

    @property
    def part_name(self) -> str:
        return "Corner"

    def __str__(self) -> str:
        return str(self.name.value) + " " + super().__str__()

    @property
    def required_position(self) -> "Corner":
        return self.cube.find_corner_by_pos_colors(self.colors_id)
