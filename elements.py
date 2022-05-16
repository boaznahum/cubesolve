from abc import ABC
from collections.abc import Sequence
from enum import Enum, unique
from typing import TypeAlias, MutableSequence, Tuple


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


class PartEdge:
    __slots__ = ["_face", "_color", "_annotated"]

    _face: _Face
    _color: Color

    def __init__(self, face: _Face, color: Color) -> None:
        super().__init__()
        self._face = face
        self._color = color
        self._annotated: bool = False

    @property
    def face(self) -> _Face:
        return self._face

    @property
    def color(self) -> Color:
        return self._color

    def __str__(self) -> str:
        return f"{self._color.name}@{self._face}"

    def copy_color(self, source: "PartEdge"):
        self._color = source._color
        self._annotated = source._annotated

    def copy(self) -> "PartEdge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        p = PartEdge(self._face, self._color)
        p._annotated = self._annotated

        return p

    def annotate(self):
        self._annotated = True

    def un_annotate(self):
        self._annotated = False

    @property
    def annotated(self):
        return self._annotated


class Part(ABC):
    """


    Parts never chane position, only the color of the parts


    n = 1 - center
    n = 2 - edge
    n = 3 - corner
    """
    __slots__ = ["_edges", "_colors_id_by_pos", "_colors_id_by_colors"]
    _edges: MutableSequence[PartEdge]

    def __init__(self, *edges: PartEdge) -> None:
        super().__init__()
        self._edges: MutableSequence[PartEdge] = [*edges]

        self._pos_id = tuple(e.face.name for e in edges)
        self._colors_id_by_pos: PartColorsID | None = None
        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartFixedID | None = None

    def finish_init(self):
        """
        Assign a part a fixed _id, that is not changed when face color is changed
        Must be called before any face changed
        :return:
        """
        _id = frozenset((p.face.name for p in self._edges))

        if self._fixed_id:
            if _id != self._fixed_id:
                raise Exception(f"SW error, you are trying to re assign part id was: {self._fixed_id}, new: {_id}")
        else:
            self._fixed_id = _id

    @property
    def fixed_id(self) -> PartFixedID:
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
    def pos_id(self):
        """
        A unique ID according to pos
        :return:
        """
        return self._pos_id

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
        return self._edges[0].face.cube

    def annotate(self):
        for p in self._edges:
            p.annotate()

    def un_annotate(self):
        for p in self._edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any( p.annotated for p in self._edges )


class Center(Part):
    def __init__(self, center: PartEdge) -> None:
        super().__init__(center)

    def edg(self) -> PartEdge:
        return self._edges[0]

    @property
    def color(self):
        return self.edg().color

    def copy(self) -> "Center":
        return Center(self._edges[0].copy())

    def replace_colors(self, other: "Center"):
        self._edges[0].copy_color(other.edg())
        self.reset_colors_id()



class Edge(Part):
    def __init__(self, e1: PartEdge, e2: PartEdge) -> None:
        super().__init__(e1, e2)

    @property
    def e1(self) -> "PartEdge":
        return self._edges[0]

    @property
    def e2(self) -> "PartEdge":
        return self._edges[1]

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

    def copy_colors_ver(self,
                        source: "Edge"
                        ):
        """
        Copy from vertical edge
        self and source assume to share a face

        source_other_face, shared_face  --> shared_face,this_other_face

        :param source
        """

        shared_face = self.single_shared_face(source)
        source_other = source.get_other_face(shared_face)
        dest_other = self.get_other_face(shared_face)

        self._replace_colors(source, (source_other, shared_face), (shared_face, dest_other))

    def copy(self) -> "Edge":
        """
        Used as temporary for rotate, must not used in cube
        :return:
        """
        return Edge(self.e1.copy(), self.e2.copy())

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



class Corner(Part):
    def __init__(self, e1: PartEdge, e2: PartEdge, e3: PartEdge) -> None:
        super().__init__(e1, e2, e3)

    def copy(self) -> "Corner":
        """
        Used as temporary for rotate, must not used in cube
        :return:
        """
        return Corner(self._edges[0].copy(), self._edges[1].copy(), self._edges[2].copy())

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

