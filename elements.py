from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from enum import Enum, unique
from typing import TypeAlias, MutableSequence, Tuple, Any, Sequence, Hashable


@unique
class Color(Enum):
    BLUE = "B"
    ORANGE = "O"
    YELLOW = "Y"
    GREEN = "G"
    RED = "R"
    WHITE = "W"


@unique
class Direction(Enum):
    D0 = 0
    D90 = 90
    D180 = 180
    D270 = 270


@unique
class FaceName(Enum):
    U = "U"
    D = "D"
    F = "F"
    B = "B"
    L = "L"
    R = "R"


@unique
class AxisName(Enum):
    """
    Whole cube Axis name
    """
    X = "X"
    Y = "Y"
    Z = "Z"


_Face: TypeAlias = "Face"  # type: ignore

# noinspection PyUnresolvedReferences
_Cube: TypeAlias = "Cube"  # type: ignore

PartColorsID = frozenset[Color]
PartFixedID = frozenset[FaceName]
PartSliceHashID = frozenset[FaceName]


class PartEdge:
    __slots__ = ["_face", "_color", "_annotated_by_color",
                 "_annotated_fixed_location",
                 "attributes", "c_attributes"]

    _face: _Face
    _color: Color

    def __init__(self, face: _Face, color: Color) -> None:
        super().__init__()
        self._face = face
        self._color = color
        self._annotated_by_color: bool = False
        self._annotated_fixed_location: bool = False
        self.attributes: dict[Hashable, Any] = defaultdict(bool)
        self.c_attributes: dict[Hashable, Any] = defaultdict(bool)

    @property
    def face(self) -> _Face:
        return self._face

    @property
    def color(self) -> Color:
        return self._color

    def __str__(self) -> str:
        return f"{self.c_attributes['n']}{self._color.name}@{self._face}"

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


EdgeSliceIndex = int | slice
CenterSliceIndex = Tuple[int, int]
SliceIndex = EdgeSliceIndex | CenterSliceIndex  # type: ignore # row, column, must be hashable


class PartSlice(ABC):
    """


    Parts never chane position, only the color of the parts


    n = 1 - center
    n = 2 - edge
    n = 3 - corner
    """
    __slots__ = ["_cube", "_index", "_edges", "_colors_id_by_pos",
                 "_fixed_id",
                 "_colors_id_by_colors"]
    _edges: MutableSequence[PartEdge]

    def __init__(self, index: SliceIndex, *edges: PartEdge) -> None:
        super().__init__()

        self._cube: _Cube = edges[0].face.cube  # we have at least one edge
        self._index: SliceIndex = index

        self._edges: MutableSequence[PartEdge] = [*edges]

        self._colors_id_by_pos: PartColorsID | None = None
        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartSliceHashID | None = None

    def finish_init(self):
        """
        Assign a part a fixed _id, that is not changed when face color is changed
        Must be called before any face changed
        :return:
        """
        _id = frozenset(tuple([self._index]) + tuple(p.face.name for p in self._edges))

        if self._fixed_id:
            if _id != self._fixed_id:
                raise Exception(f"SW error, you are trying to re assign part id was: {self._fixed_id}, new: {_id}")
        else:
            self._fixed_id = _id

    @property
    def fixed_id(self) -> PartSliceHashID:
        """
        An ID that is not changed when color ir parent face color is changed
        It actaully track the instance of the edge, but it will same for all instances of cube
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
        for e in self._edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    def __str__(self) -> str:
        s = str([str(e) for e in self._edges])

        s = "[" + str(self._index) + "]" + s

        if self.match_faces:
            s = "+" + s
        else:
            s = "-" + s

        return s

    def __repr__(self):
        return self.__str__()

    def _replace_colors(self, source_part: "Part", *source_dest: Tuple[_Face, _Face]):

        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains source_dest[i][0] and copy it to
        edge part that matches source_dest[i][0]

        :param source:
        :return:
        """
        source: _Face
        target: _Face
        for source, target in source_dest:
            source_edge: PartEdge = source_part.get_face_edge(source)
            target_edge: PartEdge = self.get_face_edge(target)

            target_edge.copy_color(source_edge)

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
        for p in self._edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def in_position(self):
        """
        :return: true if part in position, position id same as color id
        """
        return self.colors_id_by_pos == self.colors_id_by_color

    @property
    def colors_id_by_pos(self) -> PartColorsID:
        """
        Return the parts required colors, assume it was in place, not actual colors
        the colors of the faces it is currently on
        :return:
        """

        by_pos: PartColorsID | None = self._colors_id_by_pos

        if not by_pos:
            by_pos = frozenset(e.face.color for e in self._edges)
            self._colors_id_by_pos = by_pos

        return by_pos

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

        if not colors_id:
            colors_id = frozenset(e.color for e in self._edges)
            self._colors_id_by_colors = colors_id

        return colors_id

    def reset_colors_id(self):
        self._colors_id_by_colors = None

    def on_face(self, f: _Face) -> PartEdge | None:
        """
        :param f:
        :return: true if any edge/facet is on f
        """
        for p in self._edges:
            if p.face is f:
                return p

        return None

    def on_face_by_name(self, name: FaceName) -> PartEdge | None:

        for p in self._edges:
            if p.face.name == name:
                return p

        return None

    def face_of_actual_color(self, c: Color):

        """
        Not the color the edge is on !!!
        :param c:
        :return:
        """

        for p in self._edges:
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
        for p in self._edges:
            p.annotate(fixed_location)

    def un_annotate(self):
        for p in self._edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any(p.annotated for p in self._edges)

    @property
    def annotated_by_color(self) -> bool:
        return any(p.annotated_by_color for p in self._edges)

    @property
    def annotated_fixed(self) -> bool:
        return any(p.annotated_fixed for p in self._edges)

    @property
    def edges(self):
        return self._edges

    def _clone_edges(self) -> Iterable[PartEdge]:
        return [e.clone() for e in self._edges]

    def clone(self) -> "PartSlice":
        return PartSlice(self._index, *self._clone_edges())


class Part(ABC):
    """


    Parts never chane position, only the color of the parts


    n = 1 - center
    n = 2 - edge
    n = 3 - corner
    """
    __slots__ = ["_cube", "_fixed_id", "_colors_id_by_pos", "_colors_id_by_colors"]

    def __init__(self) -> None:
        super().__init__()

        self._cube: _Cube = self._edges[0].face.cube

        self._colors_id_by_pos: PartColorsID | None = None
        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartFixedID | None = None

        # todo - check that all slices matches faces
        #   all edges with same index has the same face, see is3x3
        # all edges with same size (1, 2, 3)

    @property
    @abstractmethod
    def _edges(self) -> Sequence[PartEdge]:
        """
        A represented edges, valid for 3x3 only (probably)
        :return:
        """
        pass

    @property
    @abstractmethod
    def all_slices(self) -> Iterable[PartSlice]:
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
        It actually track the instance of the edge, but it will same for all instances of cube
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
        for e in self._edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    @property
    def is3x3(self):
        # todo: Optimize it !!!, reset after slice rotation

        s0: PartSlice = iter(self.all_slices).__next__()

        colors = [e.color for e in s0.edges]

        for s in self.all_slices:
            for c1, c2 in zip(colors, (e.color for e in s.edges)):
                if c1 != c2:
                    return False

        return True

    def __str__(self) -> str:

        st = ""
        n_edges = len(self._edges)
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

        source: _Face
        target: _Face
        for source, target in source_dest:

            # we assume they are in same  order
            for source_slice, target_slice in zip(source_slices, dest_slices):
                source_edge: PartEdge = source_slice.get_face_edge(source)
                target_edge: PartEdge = target_slice.get_face_edge(target)

                target_edge.copy_color(source_edge)

                target_slice.reset_colors_id()

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
        for p in self._edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def in_position(self):
        """
        :return: true if part in position, position id same as color id
        """
        return self.colors_id_by_pos == self.colors_id_by_color

    @property
    def colors_id_by_pos(self) -> PartColorsID:
        """
        Return the parts required colors, assume it was in place, not actual colors
        the colors of the faces it is currently on
        :return:
        """

        by_pos: PartColorsID | None = self._colors_id_by_pos

        if not by_pos:
            by_pos = frozenset(e.face.color for e in self._edges)
            self._colors_id_by_pos = by_pos

        return by_pos

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

        if not colors_id:
            colors_id = frozenset(e.color for e in self._edges)
            self._colors_id_by_colors = colors_id

        return colors_id

    def reset_colors_id(self):
        self._colors_id_by_colors = None

    def on_face(self, f: _Face) -> PartEdge | None:
        """
        :param f:
        :return: true if any edge is on f
        """
        for p in self._edges:
            if p.face is f:
                return p

        return None

    def on_face_by_name(self, name: FaceName) -> PartEdge | None:

        for p in self._edges:
            if p.face.name == name:
                return p

        return None

    def face_of_actual_color(self, c: Color):

        """
        Not the color the edge is on !!!
        :param c:
        :return:
        """

        for p in self._edges:
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
        for p in self._edges:
            p.annotate(fixed_location)

    def un_annotate(self):
        for p in self._edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any(p.annotated for p in self._edges)

    @property
    def annotated_by_color(self) -> bool:
        return any(p.annotated_by_color for p in self._edges)

    @property
    def annotated_fixed(self) -> bool:
        return any(p.annotated_fixed for p in self._edges)


class Center(Part):
    __slots__ = "_slices"

    def __init__(self, center_slices: Sequence[Sequence[PartSlice]]) -> None:
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[Sequence[PartSlice]] = center_slices
        super().__init__()

    @property
    def face(self) -> _Face:
        # always true, even for non 3x3
        return self._slices[0][0].edges[0].face

    @property
    def _edges(self) -> Sequence[PartEdge]:
        return self._slices[0][0].edges

    @property
    def all_slices(self) -> Iterable[PartSlice]:
        for ss in self._slices:
            yield from ss

    @property
    def n_slices(self):
        return self.cube.size - 2

    def get_slice(self, index: SliceIndex) -> PartSlice:
        """

        :param index: row, column
        :return:
        """
        assert isinstance(index, tuple)
        return self._slices[index[0]][index[1]]

    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:

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

    def get_center_slice(self, index: CenterSliceIndex) -> PartSlice:
        return self._slices[index[0]][index[1]]

    def edg(self) -> PartEdge:
        return self._edges[0]

    @property
    def color(self):
        return self.edg().color

    def copy(self) -> "Center":
        n = self.n_slices

        my = self._slices

        _slices = [[my[i][j].clone() for j in range(n)] for i in range(n)]

        return Center(_slices)

    def copy_colors(self, other: "Center",
                    index: CenterSliceIndex = None,
                    source_index: CenterSliceIndex = None):
        # self._edges[0].copy_color(other.edg())
        self._replace_colors(other, (other.face, self.face), index=index, source_index=source_index)


class EdgeSlice(PartSlice):

    def __init__(self, index: int, *edges: PartEdge) -> None:
        super().__init__(index, *edges)

    def clone(self) -> "EdgeSlice":
        index = self._index
        assert isinstance(index, int)  # satisfy mypy

        return EdgeSlice(index, *self._clone_edges())


class Edge(Part):

    def __init__(self, f1: _Face, f2: _Face, right_top_left_same_direction: bool,
                 slices: Sequence[EdgeSlice]) -> None:
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[EdgeSlice] = slices
        super().__init__()
        self._f1: _Face = f1
        self._f2: _Face = f2
        self.right_top_left_same_direction = right_top_left_same_direction

        assert f1 is not f2
        assert f1 is self.e1.face or f1 is self.e2.face
        assert f2 is self.e1.face or f2 is self.e2.face

    @property
    def e1(self) -> "PartEdge":
        return self._edges[0]

    @property
    def e2(self) -> "PartEdge":
        return self._edges[1]

    @property
    def _edges(self) -> Sequence[PartEdge]:
        return self._slices[0].edges

    @property
    def all_slices(self) -> Iterable[EdgeSlice]:
        return self._slices

    @property
    def n_slices(self):
        return self.cube.size - 2

    def get_slice(self, i) -> PartSlice:
        """
        In unpractical order
        :param i:
        :return:
        """
        return self._slices[i]

    def get_left_top_left_slice_index(self, face: _Face, i) -> int:
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

        assert ltr_i == self.get_left_top_left_slice_index(face, si)

        return si


    def get_left_top_left_slice(self, face: _Face, i) -> PartSlice:
        """

        # todo: combine and optimize with get_face_edge
        Given an index of slice in direction from left to right, or left to top
        find it's actual slice
        :param face:
        :param i:
        :return:
        """
        return self.get_slice(self.get_left_top_left_slice_index(face, i))

    def get_left_top_left_edge(self, face: _Face, i) -> PartEdge:
        """
        todo: optimize, combine both methods
        :param face:
        :param i:
        :return:
        """
        return self.get_left_top_left_slice(face, i).get_face_edge(face)

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

        e1 = self.e1
        e2 = self.e2
        if e1.face is f:
            return e2
        elif e2.face is f:
            return e1
        else:
            raise ValueError(f"Face {f} not in edge {self}")

    def get_other_face(self, f: _Face) -> _Face:

        return self.get_other_face_edge(f).face

    def replace_colors(self, on_face: _Face, source: "Edge"):
        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains on_face both in self and other face
        replace the edge part color on on_face with the matched color from source

        We assume that both source and self are belonged to on_face.

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

        We assume that both source and self are belonged to on_face

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
        Used as temporary for rotate, must not used in cube
        :return:
        """
        slices: list[EdgeSlice] = [s.clone() for s in self._slices]
        return Edge(self._f1, self._f2, self.right_top_left_same_direction, slices)

    def single_shared_face(self, other: "Edge"):
        """
        Return a face that appears in both edges
        raise error more than one (how can it be) or no one
        :param other:
        :return:
        """

        f1: _Face = self._edges[0].face
        f2: _Face = self._edges[1].face

        of1: _Face = other._edges[0].face
        of2: _Face = other._edges[1].face

        e11 = f1 is of1
        e12 = f1 is of2

        e21 = f2 is of1
        e22 = f2 is of2

        count = sum([e11, e12, e21, e22])

        if count == 0:
            raise RuntimeError(f"No matches: {f1} {f2} and {of1} {of2}")

        if count > 1:
            raise RuntimeError(f"Too many matches: {f1} {f2} and {of1} {of2}")

        if e11 or e12:
            return f1
        else:
            return f2

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
        sl: EdgeSlice
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


class Corner(Part):
    __slots__ = ["_slice"]

    def __init__(self, a_slice: PartSlice) -> None:
        self._slice = a_slice
        super().__init__()

    @property
    def _edges(self) -> Sequence[PartEdge]:
        return self._slice.edges

    @property
    def all_slices(self) -> Iterable[PartSlice]:
        return [self._slice]

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


class SuperElement:
    __slots__ = ["_cube",
                 "_parts",
                 ]

    def __init__(self, cube: _Cube) -> None:
        super().__init__()

        self._cube = cube
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
    def cube(self) -> _Cube:
        return self._cube

    @property
    @abstractmethod
    def slices(self) -> Iterable[PartSlice]:
        pass
