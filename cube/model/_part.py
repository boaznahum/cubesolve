from abc import ABC, abstractmethod
from collections.abc import Sequence, Iterator, Iterable
from enum import Enum, unique
from typing import Tuple, TypeAlias, TYPE_CHECKING, TypeVar

from cube import config
from cube.model import PartEdge
from cube.model.cube_boy import FaceName, Color, color2long
from ._elements import CubeElement, PartColorsID, PartFixedID, SliceIndex, CenterSliceIndex, EdgeSliceIndex
from ._part_slice import PartSlice, CenterSlice, EdgeWing, CornerSlice
from cube.app_exceptions import InternalSWError

if TYPE_CHECKING:
    from .cube_face import Face
    from .cube import Cube

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore


class EdgeName(Enum):
    FL = "FL"
    FU = "FU"
    FR = "FR"
    FD = "FD"
    BL = "BL"
    BU = "BU"
    BR = "BR"
    BD = "BD"
    UR = "UR"
    RD = "RD"
    DL = "DL"
    LU = "LU"

    def __str__(self) -> str:
        return str(self.value)


_faces_to_edges: dict[frozenset[FaceName], EdgeName] = {}


def _faces_2_edge_name(faces: Iterable[FaceName]) -> EdgeName:
    global _faces_to_corners

    if not _faces_to_edges:
        def _a(f1, f2, cn: EdgeName):
            _faces_to_edges[frozenset([f1, f2])] = cn

        _a(FaceName.F, FaceName.L, EdgeName.FL)
        _a(FaceName.F, FaceName.U, EdgeName.FU)
        _a(FaceName.F, FaceName.R, EdgeName.FR)
        _a(FaceName.F, FaceName.D, EdgeName.FD)
        _a(FaceName.B, FaceName.L, EdgeName.BL)
        _a(FaceName.B, FaceName.U, EdgeName.BU)
        _a(FaceName.B, FaceName.R, EdgeName.BR)
        _a(FaceName.B, FaceName.D, EdgeName.BD)

        _a(FaceName.U, FaceName.R, EdgeName.UR)
        _a(FaceName.R, FaceName.D, EdgeName.RD)
        _a(FaceName.D, FaceName.L, EdgeName.DL)
        _a(FaceName.L, FaceName.U, EdgeName.LU)

    return _faces_to_edges[frozenset(faces)]


@unique
class CornerName(Enum):
    FLU = "FLU"
    FRU = "FRU"
    FRD = "FRD"
    FLD = "FLD"
    BLU = "BLU"
    BRU = "BRU"
    BRD = "BRD"
    BLD = "BLD"

    def __str__(self) -> str:
        return str(self.value)


_faces_to_corners: dict[frozenset[FaceName], CornerName] = {}


def _faces_2_corner_name(faces: Iterable[FaceName]):
    global _faces_to_corners

    if not _faces_to_corners:
        def _a(f1, f2, f3, cn: CornerName):
            _faces_to_corners[frozenset([f1, f2, f3])] = cn

        _a(FaceName.F, FaceName.L, FaceName.U, CornerName.FLU)
        _a(FaceName.F, FaceName.R, FaceName.U, CornerName.FRU)
        _a(FaceName.F, FaceName.R, FaceName.D, CornerName.FRD)
        _a(FaceName.F, FaceName.L, FaceName.D, CornerName.FLD)
        _a(FaceName.B, FaceName.L, FaceName.U, CornerName.BLU)
        _a(FaceName.B, FaceName.R, FaceName.U, CornerName.BRU)
        _a(FaceName.B, FaceName.R, FaceName.D, CornerName.BRD)
        _a(FaceName.B, FaceName.L, FaceName.D, CornerName.BLD)

    return _faces_to_corners[frozenset(faces)]


class Part(ABC, CubeElement):
    """


    Parts never chane position, only the color of the parts


    n = 1 - center
    n = 2 - edge
    n = 3 - corner
    """
    __slots__ = ["_cube", "_fixed_id", "_colors_id_by_pos", "_colors_id_by_colors"]

    def __init__(self) -> None:
        cube = next(self.all_slices).cube
        super().__init__(cube)

        self._colors_id_by_pos: PartColorsID | None = None
        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartFixedID | None = None

        s: PartSlice
        for s in self.all_slices:
            s.set_parent(self)

        # todo - check that all slices matches faces
        #   all edges with same index has the same face, see is3x3
        # all edges with same size (1, 2, 3)

    @property
    @abstractmethod
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        """
        A 3x3 representative edges, valid for 3x3 only (probably)
        :return:
        """
        pass

    @property
    @abstractmethod
    def all_slices(self) -> Iterator[PartSlice]:
        pass

    @abstractmethod
    def get_slice(self, index: SliceIndex) -> PartSlice:
        pass

    # todo: fix to iterator
    @abstractmethod
    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:
        pass

    def finish_init(self):
        """
        Assign a part a fixed _id, that is not changed when face color is changed
        Must be called before any face changed
        :return:
        """

        for s in self.all_slices:
            s.finish_init()

        _id = frozenset(s.fixed_id for s in self.all_slices)

        if self._fixed_id:
            if _id != self._fixed_id:
                raise Exception(f"SW error, you are trying to re assign part id was: {self._fixed_id}, new: {_id}")
        else:
            self._fixed_id = _id

    @property
    def fixed_id(self) -> PartFixedID:
        """
        An ID that is not changed when color ir parent face color is changed
        It actually tracks the instance of the edge, but it will same for all instances of cube
        :return:
        """
        assert self._fixed_id
        return self._fixed_id

    def get_face_edge(self, face: _Face) -> PartEdge:
        """
        return the edge belong to face, raise error if not found
        :param face:
        :return:
        """
        for e in self._3x3_representative_edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    @property
    @abstractmethod
    def is3x3(self) -> bool:
        pass

    def __str__(self) -> str:

        st = ""
        n_edges = len(self._3x3_representative_edges)
        for i in range(n_edges):
            es = ""
            s: PartSlice
            for s in self.all_slices:
                e = s.edges[i]
                es += str(e) + "|"
            st += es + " "

        # s = str([str(e) for e in self.all_slices])

        if self.match_faces:
            st = "+" + st
        else:
            st = "-" + st

        return st

    def __repr__(self):
        return self.__str__()

    def _replace_colors(self, source_part: "Part", *source_dest: Tuple[_Face, _Face],
                        index: SliceIndex | None = None,
                        source_index: SliceIndex = None):

        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains source_dest[i][0] and copy it to
        edge part that matches source_dest[i][0]

        :param source:
        :return:
        """

        if source_index is None:
            source_index = index

        source_slices: Iterable[PartSlice]
        dest_slices: Iterable[PartSlice]

        # for debug only unpack todo:
        source_slices = source_part.get_slices(source_index)
        dest_slices = self.get_slices(index)

        # without that they below doesn't work, it doesn't iterate all
        # slice rotate doesn't work
        source_slices = [*source_slices]
        dest_slices = [*dest_slices]

        source_slice: PartSlice
        target_slice: PartSlice

        for source_slice, target_slice in zip(source_slices, dest_slices):
            target_slice.copy_colors(source_slice, *source_dest)

        self.reset_colors_id()

    def f_color(self, f: _Face):
        """
        The color of part on given face
        :param f:
        :return:
        """
        return self.get_face_edge(f).color

    def match_face(self, face: _Face):
        """
        Part edge on given face match its color
        :return:
        """
        return self.get_face_edge(face).color == face.color

    @property
    def match_faces(self):
        """
        Part is in position, all colors match the faces
        :return:
        """
        for p in self._3x3_representative_edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def in_position(self):
        """
        :return: true if part in position, ignoring orientation, position id same as color id
        """
        return self.colors_id_by_pos == self.colors_id_by_color

    @property
    def position_id(self) -> PartColorsID:
        """
        Return the parts required colors, assume it was in place, not actual colors
        the colors of the faces it is currently on
        This id can be changed only if faces are changed in slice and whole cube rotation
        :return:
        """

        by_pos: PartColorsID | None = self._colors_id_by_pos

        if not by_pos or (False and config.DONT_OPTIMIZED_PART_ID):
            by_pos = frozenset(e.face.color for e in self._3x3_representative_edges)
            self._colors_id_by_pos = by_pos

        return by_pos

    @property
    def colors_id_by_pos(self) -> PartColorsID:
        """
        :deprecated, use :position_id
        """
        return self.position_id

    @classmethod
    def parts_id_by_pos(cls, parts: Sequence["Part"]) -> Sequence[PartColorsID]:

        return [p.colors_id_by_pos for p in parts]

    def reset_after_faces_changes(self):
        self._colors_id_by_pos = None

    @property
    def colors_id_by_color(self) -> PartColorsID:
        """
        Return the parts actual color
        the colors of the faces it is currently on
        :return:
        """

        colors_id: PartColorsID | None = self._colors_id_by_colors

        if not colors_id or config.DONT_OPTIMIZED_PART_ID:

            new_colors_id = frozenset(e.color for e in self._3x3_representative_edges)

            if colors_id and new_colors_id != colors_id:
                print("Bug here !!!!")

            colors_id = new_colors_id

            self._colors_id_by_colors = new_colors_id

        return colors_id

    def reset_colors_id(self):
        self._colors_id_by_colors = None

    def on_face(self, f: _Face) -> PartEdge | None:
        """
        :param f:
        :return: true if any edge is on f
        """
        for p in self._3x3_representative_edges:
            if p.face is f:
                return p

        return None

    def on_face_by_name(self, name: FaceName) -> PartEdge | None:

        for p in self._3x3_representative_edges:
            if p.face.name == name:
                return p

        return None

    def face_of_actual_color(self, c: Color):

        """
        Not the color the edge is on !!!
        :param c:
        :return:
        """

        for p in self._3x3_representative_edges:
            if p.color == c:
                return p.face

        raise ValueError(f"No color {c} on {self}")

    @classmethod
    def all_match_faces(cls, parts: Sequence["Part"]):
        """
        Return true if all parts match - each part edge matches the face it is located on
        :param parts:
        :return:
        """
        return all(p.match_faces for p in parts)

    @classmethod
    def all_in_position(cls, parts: Sequence["Part"]):
        """
        Return true if all parts match - each part edge matches the face it is located on
        :param parts:
        :return:
        """
        return all(p.in_position for p in parts)

    @property
    def cube(self) -> _Cube:
        return self._cube

    def annotate(self, fixed_location: bool):
        for p in self._3x3_representative_edges:
            p.annotate(fixed_location)

    def un_annotate(self):
        for p in self._3x3_representative_edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any(p.annotated for p in self._3x3_representative_edges)

    @property
    def annotated_by_color(self) -> bool:
        return any(p.annotated_by_color for p in self._3x3_representative_edges)

    @property
    def annotated_fixed(self) -> bool:
        return any(p.annotated_fixed for p in self._3x3_representative_edges)

    @property
    def name(self):
        raise NotImplementedError

    @property
    def name_n_faces(self) -> str:  # for animation
        """
        return the name of the part with face id - name of faces is on
        Good also for non 3x3 because it is the name of the face, not color
        :return: e.g. 'Edge Front/Right'
        """
        # s1 = ""
        # s2 = ""
        #
        # for e in self._3x3_representative_edges:
        #     s1 += str(e.face.name.value)

        return self.part_name + " " + str(self.name)

    def name_n_faces_colors(self) -> str:  # for animation
        """
        return the name of the part with color ID
        For is3x3 only
        :return: e.g. 'Edge White/Red'
        """
        s1 = ""
        s2 = ""

        for e in self._3x3_representative_edges:
            s1 += str(e.face.name.value)
            s2 += str(color2long(e.color).value) + "/"

        s2 = s2[0:-1]

        return self.part_name + " " + s1 + " " + s2

    @property
    def name_n_colors(self) -> str:  # for animation
        """
        return the name of the part with color Faces ID and colors
        Actual colors and not colors of face(position)
        :return: e.g. 'Edge White/Red'
        """
        s_colors = ""

        for e in self._3x3_representative_edges:
            s_colors += str(color2long(e.color).value) + "/"

        s_colors = s_colors[0:-1]

        return self.part_name + " " + s_colors

    @property
    @abstractmethod
    def part_name(self) -> str:
        pass


TPartType = TypeVar("TPartType", bound="Part")


class Center(Part):
    __slots__ = "_slices"

    def __init__(self, center_slices: Sequence[Sequence[CenterSlice]]) -> None:
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[Sequence[CenterSlice]] = center_slices
        super().__init__()

    @property
    def face(self) -> _Face:
        # always true, even for non 3x3
        # todo: can be optimized, it is always the same name
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
                return self.all_slices
            elif i < 0:
                for i in range(self.n_slices):
                    yield self.get_slice((i, j))
            elif j < 0:
                for j in range(self.n_slices):
                    yield self.get_slice((i, j))
            else:
                yield self.get_slice((i, j))
        else:
            return self.all_slices

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
                    index: CenterSliceIndex = None,
                    source_index: CenterSliceIndex = None):
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

    def get_slice(self, i) -> EdgeWing:
        """
        In unpractical order
        :param i:
        :return:
        """
        return self._slices[i]

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
                               source_index: SliceIndex = None
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
                        source_index: SliceIndex = None
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

        from .cube_face import Face

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


class Corner(Part):
    __slots__ = ["_slice"]

    def __init__(self, a_slice: CornerSlice) -> None:
        self._slice = a_slice
        super().__init__()

    @property
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        """
        In case of Corner it is also the actual edges
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
        Used as temporary for rotate, must not be used in cube
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
        Find the edge part contains on_face both in self and other face
        replace the edge part color on on_face with the matched color from source

        We assume that both source and self are belonged to on_face,
        :param target_3:
        :param source_3:
        :param target_2:
        :param source_2:
        :param on_face:
        :param source:
        :return:
        """

        self._replace_colors(source, (on_face, on_face), (source_2, target_2), (source_3, target_3))

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


