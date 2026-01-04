from collections.abc import Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Self, TypeAlias

from cube.domain.model._elements import CenterSliceIndex, SliceIndex
from cube.domain.model.PartSlice import CenterSlice
from cube.domain.model.geometric.cube_boy import FaceName
from cube.domain.model.Part import Part
from cube.domain.model.PartEdge import PartEdge

if TYPE_CHECKING:
    from .Face import Face

_Face: TypeAlias = "Face"


class Center(Part):
    __slots__ = "_slices"

    def __init__(self, center_slices: Sequence[Sequence[CenterSlice]]) -> None:
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[Sequence[CenterSlice]] = center_slices
        super().__init__()

    @property
    def face(self) -> _Face:
        return self._slices[0][0].edges[0].face

    @property
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        n2 = self.n_slices // 2
        return self._slices[n2][n2].edges

    @property
    def is3x3(self) -> bool:
        slices: Iterator[CenterSlice] = self.all_slices

        c = next(slices).color

        for s in slices:
            if c != s.color:
                return False

        return True

    @property
    def all_slices(self) -> Iterator["CenterSlice"]:
        for ss in self._slices:
            yield from ss

    @property
    def n_slices(self):
        return self.cube.size - 2

    def get_slice(self, index: SliceIndex) -> "CenterSlice":
        """

        :param index: row, column
        :return:
        """
        assert isinstance(index, tuple)
        return self._slices[index[0]][index[1]]

    def get_slices(self, index: SliceIndex | None) -> Iterable["CenterSlice"]:

        if index:
            assert isinstance(index, tuple)
            i = index[0]
            j = index[1]

            if i < 0 and j < 0:
                yield from self.all_slices
            elif i < 0:
                for i in range(self.n_slices):
                    yield self.get_slice((i, j))
            elif j < 0:
                for j in range(self.n_slices):
                    yield self.get_slice((i, j))
            else:
                yield self.get_slice((i, j))
        else:
            yield from self.all_slices

    def get_center_slice(self, index: CenterSliceIndex) -> "CenterSlice":
        """
        Row, Column
        :param index:
        :return:
        """
        return self._slices[index[0]][index[1]]

    def edg(self) -> PartEdge:
        return self._3x3_representative_edges[0]

    @property
    def color(self):
        """
        Meaningfully only for 3x3
        :return:
        """
        return self.edg().color

    def clone(self) -> "Center":
        n = self.n_slices

        my = self._slices

        _slices = [[my[i][j].clone() for j in range(n)] for i in range(n)]

        return Center(_slices)

    def copy_colors(self, other: "Center",
                    index: CenterSliceIndex | None = None,
                    source_index: CenterSliceIndex | None = None):
        # self._edges[0].copy_color(other.edg())
        self._replace_colors(other, (other.face, self.face), index=index, source_index=source_index)

    def __str__(self):
        s = str(self.face.name)
        for r in range(self.n_slices):
            for c in range(self.n_slices):
                # s += str(self.get_center_slice((r, c)).edge.c_attributes["n"]) + "|"
                s += str(self.get_center_slice((r, c)).color.name) + "|"
            s += "\n"

        return s

    @property
    def name(self) -> FaceName:
        """
        Not a typo, center and face have the same name
        :return:
        """
        return self.face.name

    @property
    def part_name(self) -> str:
        return "Center"

    @property
    def required_position(self: Self) -> "Center":
        return self.cube.find_center_by_pos_colors(self.colors_id)
