from collections.abc import Iterator, Iterable
from typing import TYPE_CHECKING, TypeAlias, Sequence, Self

from cube.model.Part import Part
from cube.model import EdgeWing, PartEdge, SliceIndex, PartSlice
from .Part import TPartType
from ._elements import EdgeSliceIndex
from ._part import EdgeName, _faces_2_edge_name
from ..app.app_exceptions import InternalSWError

if TYPE_CHECKING:
    from .Face import Face
    from .Cube import Cube

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore

class Edge(Part):

    def __init__(self, f1: _Face, f2: _Face, right_top_left_same_direction: bool,
                 slices: Sequence[EdgeWing]) -> None:
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[EdgeWing] = slices
        super().__init__()
        self._f1: _Face = f1
        self._f2: _Face = f2
        self.right_top_left_same_direction = right_top_left_same_direction

        assert f1 is not f2
        assert f1 is self.e1.face or f1 is self.e2.face
        assert f2 is self.e1.face or f2 is self.e2.face

        # FU, FR
        self._name: str = str(f1.name) + str(f2.name)

    @property
    def e1(self) -> "PartEdge":
        return self._3x3_representative_edges[0]

    @property
    def e2(self) -> "PartEdge":
        return self._3x3_representative_edges[1]

    def __hash__(self) -> int:
        # we use faces in set in nxn_centers
        return hash(self._name)

    def __eq__(self, __o: object) -> bool:
        # we use faces in set in nxn_centers
        return isinstance(__o, Edge) and __o._name == self._name

    @property
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        return self._slices[self.n_slices // 2].edges

    @property
    def is3x3(self) -> bool:
        slices = self.all_slices

        s0 = next(slices)

        c1, c2 = (s0.e1.color, s0.e2.color)

        for s in slices:
            _c1, _c2 = (s.e1.color, s.e2.color)

            if c1 != _c1 or c2 != _c2:
                return False

        return True

    @property
    def all_slices(self) -> Iterator[EdgeWing]:
        return self._slices.__iter__()

    @property
    def n_slices(self):
        return self.cube.size - 2

    def get_slice(self, index: SliceIndex) -> EdgeWing:
        """
        In unpractical order
        :param index:
        :return:
        """
        assert isinstance(index, int)
        return self._slices[index]

    def get_ltr_index_from_slice_index(self, face: _Face, i) -> int:
        """

        # todo: combine and optimize with get_face_edge
        Given an index of slice in direction from left to right, or left to top
        find it's actual slice
        :param face:
        :param i:
        :return:
        """
        assert face is self._f1 or face is self._f2

        if self.right_top_left_same_direction:
            return i
        else:
            if face is self._f1:
                return i  # arbitrary f1 was chosen
            else:
                # todo make it generic
                return self.inv_index(i)  # type: ignore

    def get_slice_index_from_ltr_index(self, face: _Face, ltr_i: int) -> int:
        assert face is self._f1 or face is self._f2

        si: int
        if self.right_top_left_same_direction:
            si = ltr_i
        else:
            if face is self._f1:
                si = ltr_i  # arbitrary f1 was chosen
            else:
                # todo make it generic
                si = self.inv_index(ltr_i)  # type: ignore

        assert ltr_i == self.get_ltr_index_from_slice_index(face, si)

        return si

    def get_slice_by_ltr_index(self, face: _Face, i) -> EdgeWing:
        """

        # todo: combine and optimize with get_face_edge
        Given an index of slice in direction from left to right, or left to top
        find it's actual slice
        :param face:
        :param i:
        :return:
        """
        return self.get_slice(self.get_ltr_index_from_slice_index(face, i))

    def get_left_top_left_edge(self, face: _Face, i) -> PartEdge:
        """
        todo: optimize, combine both methods
        :param face:
        :param i:
        :return:
        """
        return self.get_slice_by_ltr_index(face, i).get_face_edge(face)

    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:

        if index is not None:  # can be zero
            assert isinstance(index, int)
            if index < 0:
                yield from self.all_slices
            else:
                yield self.get_slice(index)
        else:
            yield from self.all_slices

    def get_other_face_edge(self, f: _Face) -> "PartEdge":

        """
        Get the edge that is on face that is not f
        :param f:
        :return:
        """
        return self._slices[0].get_other_face_edge(f)

    def get_other_face(self, f: _Face) -> _Face:

        return self.get_other_face_edge(f).face

    def replace_colors(self, on_face: _Face, source: "Edge"):
        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains on_face both in self and other face
        replace the edge part color on on_face with the matched color from source

        We assume that both source and self are belonged to on_face,

        :param on_face:
        :param source:
        :return:
        """

        this_face_source_edge: PartEdge = source.get_face_edge(on_face)
        this_face_target_edge: PartEdge = self.get_face_edge(on_face)

        this_face_target_edge.copy_color(this_face_source_edge)

        other_face_source: PartEdge = source.get_other_face_edge(on_face)
        other_face_target: PartEdge = self.get_other_face_edge(on_face)

        other_face_target.copy_color(other_face_source)

        self.reset_colors_id()

    def replace_colors2(self,
                        source: "Edge",
                        source_1: _Face, target_1: _Face,
                        source_2: _Face, target_2: _Face,
                        ):
        """
        Replace the colors of this corner with the colors from source
        Find the edge part contains on_face both in self and other face
        replace the edge part color on on_face with the matched color from source

        We assume that both source and self are belonged to on_face.

        :param source_1:
        :param source_2:
        :param target_2:
        :param target_1:
        :param source:
        :return:
        """

        self._replace_colors(source, (source_1, target_1), (source_2, target_2))

    def copy_colors_horizontal(self,
                               source: "Edge",
                               index: SliceIndex | None = None,
                               source_index: SliceIndex | None = None
                               ):
        """
        Copy from edge - copy from shared face
        self and source assume to share a face

        source_other_face, shared_face  --> this_other_face, shared_face

        other  |__     __|  other
              shared,  shared

        ;
        :param source_index:
        :param index:
        :param source
        """

        shared_face = self.single_shared_face(source)
        source_other = source.get_other_face(shared_face)
        dest_other = self.get_other_face(shared_face)

        self._replace_colors(source, (shared_face, shared_face), (source_other, dest_other),
                             index=index,
                             source_index=source_index)

    def copy_colors_ver(self,
                        source: "Edge",
                        index: SliceIndex | None = None,
                        source_index: SliceIndex | None = None
                        ):
        """
        Copy from vertical edge - copy from other face
        self and source assume to share a face

        other  |__     __|  other
              shared,  shared

        source_other_face, shared_face  --> shared_face,this_other_face

        :param source_index:
        :param index:
        :param source
        """

        shared_face = self.single_shared_face(source)
        source_other = source.get_other_face(shared_face)
        dest_other = self.get_other_face(shared_face)

        self._replace_colors(source, (source_other, shared_face),
                             (shared_face, dest_other),
                             index=index,
                             source_index=source_index)

    def copy(self) -> "Edge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        slices: list[EdgeWing] = [s.clone() for s in self._slices]
        return Edge(self._f1, self._f2, self.right_top_left_same_direction, slices)

    def single_shared_face(self, other: "Edge"):
        """
        Return a face that appears in both edges
        raise error more than one (how can it be) or no one
        :param other:
        :return:
        """

        return self._slices[0].single_shared_face(other._slices[0])

    def inv_index(self, slices_indexes: EdgeSliceIndex) -> EdgeSliceIndex:

        n = self.n_slices

        if isinstance(slices_indexes, int):
            return n - 1 - slices_indexes
        else:
            assert False

    def _find_cw(self, face: _Face, cw: int) -> PartEdge:
        """
        Don't use, not optimized
        :param face:
        :return:  values of 'n' ordered by 'cw'
        """
        sl: EdgeWing
        for sl in self.all_slices:
            e: PartEdge = sl.get_face_edge(face)
            _cw = e.attributes["cw"]
            if _cw == cw:
                return e

        assert False, f"No cw {cw} in edge {self} on face {_Face}"

    def cw_s(self, face: _Face):
        """

        :param face:
        :return:  values of 'n' ordered by 'cw'
        """
        n = self.n_slices
        cw_s = ""
        n_s = ""
        for i in range(n):
            sl: PartEdge = self._find_cw(face, i)
            cw_s += str(self.get_slice(i).get_face_edge(face).attributes["cw"])
            n_s += str(sl.c_attributes["n"])

        return cw_s + " " + n_s

    def opposite(self, face: _Face):
        """
        todo: optimize !!!
        :param face:
        :return: opposite edge on face
        """

        from .Face import Face

        my_other: Face = self.get_other_face(face)
        other_opposite = my_other.opposite

        for e in other_opposite.edges:
            if face.is_edge(e):
                return e

        raise InternalSWError(f"Can't find opposite of {self} on {face}")

    def __str__(self) -> str:
        return f"{self.e1.face.name.value}{self.e2.face.name.value} " + super().__str__()

    @property
    def part_name(self) -> str:
        return "Edge"

    @property
    def name(self) -> EdgeName:
        # todo: optimize it
        return _faces_2_edge_name((self.e1.face.name, self.e2.face.name))

    @property
    def required_position(self) -> "Edge":
        return self.cube.find_edge_by_pos_colors(self.colors_id)
