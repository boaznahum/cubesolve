from abc import ABC
from collections.abc import Sequence, Iterable
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


_Face: TypeAlias = "Face"

# noinspection PyUnresolvedReferences
_Cube: TypeAlias = "Cube"

PartColorsID = frozenset(Color)


class PartEdge:
    __slots__ = ["_face", "_color"]

    _face: _Face
    _color: Color

    def __init__(self, face: _Face, color: Color) -> None:
        super().__init__()
        self._face = face
        self._color = color

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

    def copy(self) -> "PartEdge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        return PartEdge(self._face, self._color)


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
        self._colors_id_by_pos: PartColorsID = None
        self._colors_id_by_colors: PartColorsID = None

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
        return str([str(e) for e in self._edges])

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

        by_pos: PartColorsID = self._colors_id_by_pos

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

        colors_id: PartColorsID = self._colors_id_by_colors

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

    @property
    def cube(self) -> _Cube:
        return self._edges[0].face.cube


class Center(Part):
    def __init__(self, center: PartEdge) -> None:
        super().__init__(center)

    def edg(self) -> PartEdge:
        return self._edges[0]

    @property
    def color(self):
        return self.edg().color

    def copy(self):
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

    def copy(self) -> "Edge":
        """
        Used as temporary for rotate, must not used in cube
        :return:
        """
        return Edge(self.e1.copy(), self.e2.copy())


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


class Face:
    """
    Faces never chane position, only the color of the parts
    """
    __slots__ = ["_cube",
                 "_center", "_direction", "_name",
                 "_edge_left", "_edge_top", "_edge_right", "_edge_bottom",
                 "_corner_top_left", "_corner_top_right", "_corner_bottom_right", "_corner_bottom_left",
                 "_parts",
                 "_edges",
                 "_corners",
                 "_opposite"
                 ]

    _center: Center
    _direction: Direction

    _edge_left: Edge
    _edge_top: Edge
    _edge_right: Edge
    _edge_bottom: Edge

    _corner_top_left: Corner
    _corner_top_right: Corner
    _corner_bottom_right: Corner
    _corner_bottom_left: Corner

    _edges: Sequence[Edge]
    _corners: Sequence[Corner]
    _parts: Sequence[Part]

    _opposite: _Face

    def __init__(self, cube: _Cube, name: FaceName, color: Color) -> None:
        super().__init__()

        self._cube = cube
        self._name = name
        self._center = Center(PartEdge(self, color))
        self._direction = Direction.D0

        # all others are created by Cube#reset

    def finish_init(self):
        self._edges = (self._edge_top, self._edge_left, self._edge_right, self._edge_bottom)

        self._corners = [self.corner_top_left,
                         self._corner_top_right,
                         self._corner_bottom_right,
                         self._corner_bottom_left]

        self._parts = (self._center, *self._edges, *self._corners)

    # noinspection PyUnresolvedReferences
    @property
    def cube(self) -> _Cube:
        return self._cube

    @property
    def name(self) -> FaceName:
        return self._name

    @property
    def center(self) -> Center:
        return self._center

    @property
    def edges(self) -> Sequence[Edge]:
        # need to cache
        return self._edges

    @property
    def corners(self) -> Sequence[Corner]:
        # need to cache
        return self._corners

    @property
    def edge_left(self) -> Edge:
        return self._edge_left

    @property
    def edge_top(self) -> Edge:
        return self._edge_top

    @property
    def edge_right(self) -> Edge:
        return self._edge_right

    @property
    def edge_bottom(self) -> Edge:
        return self._edge_bottom

    @property
    def corner_top_right(self) -> Corner:
        return self._corner_top_right

    @property
    def corner_top_left(self) -> Corner:
        return self._corner_top_left

    @property
    def corner_bottom_right(self) -> Corner:
        return self._corner_bottom_right

    @property
    def corner_bottom_left(self) -> Corner:
        return self._corner_bottom_left

    @property
    def color(self):
        return self.center.color

    def __str__(self) -> str:
        return f"{self._center.edg().color.name}@{self._name.value}"

    def __repr__(self):
        return self.__str__()

    # for constructing only, valid only after ctor
    def create_part(self) -> PartEdge:
        e: PartEdge = PartEdge(self, self.color)
        return e

    def _get_other_face(self, e: Edge) -> _Face:
        return e.get_other_face(self)

    def rotate(self, n=1):
        def _rotate():
            left: Face = self._get_other_face(self._edge_left)
            right: Face = self._get_other_face(self._edge_right)
            top: Face = self._get_other_face(self._edge_top)
            bottom: Face = self._get_other_face(self._edge_bottom)

            # top -> right -> bottom -> left -> top

            saved_top: Edge = self._edge_top.copy()
            # left --> top
            self._edge_top.replace_colors(self, self._edge_left)
            self._edge_left.replace_colors(self, self._edge_bottom)
            self._edge_bottom.replace_colors(self, self._edge_right)
            self._edge_right.replace_colors(self, saved_top)

            saved_bottom_left = self._corner_bottom_left.copy()

            # bottom_left -> top_left -> top_right -> bottom_right -> bottom_left
            self._corner_bottom_left.replace_colors(self, self._corner_bottom_right, right, bottom, bottom, left)
            self._corner_bottom_right.replace_colors(self, self._corner_top_right, top, right, right, bottom)
            self._corner_top_right.replace_colors(self, self._corner_top_left, top, right, left, top)
            self._corner_top_left.replace_colors(self, saved_bottom_left, left, top, bottom, left)

        for _ in range(0, n % 4):
            # -1 --> 3
            _rotate()

    @property
    def solved(self):
        return (self.center.color ==
                self._edge_top.f_color(self) ==
                self._edge_right.f_color(self) ==
                self._edge_bottom.f_color(self) ==
                self._edge_left.f_color(self) ==
                self._corner_top_left.f_color(self) ==
                self._corner_top_right.f_color(self) ==
                self._corner_bottom_left.f_color(self) ==
                self._corner_bottom_right.f_color(self)
                )

    def reset_after_faces_changes(self):
        """
        Call after faces colors aare changes , M, S, E rotations
        """
        for p in self._parts:
            p.reset_after_faces_changes()

    def find_part_by_colors(self, part_colors_id: PartColorsID) -> Part | None:
        for p in self._parts:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_part_by_pos_colors(self, part_colors_id: PartColorsID) -> Part | None:

        n = len(part_colors_id)

        assert n in range(1, 4)

        if n == 1:
            if self.center._colors_id_by_pos == part_colors_id:
                return self.center
            else:
                return None
        elif n == 2:
            return self.find_edge_by_pos_colors(part_colors_id)
        else:
            return self.find_corner_by_pos_colors(part_colors_id)

    def find_edge_by_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_corner_by_colors(self, part_colors_id: PartColorsID) -> Corner | None:
        for p in self._corners:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_edge_by_pos_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.colors_id_by_pos:
                return p
        return None

    def find_corner_by_pos_colors(self, part_colors_id: PartColorsID) -> Corner | None:

        for p in self._corners:
            if part_colors_id == p.colors_id_by_pos:
                return p
        return None

    def adjusted_faces(self) -> Iterable[_Face]:

        # todo: optimize
        for e in self.edges:
            yield e.get_other_face(self)

    def is_left_or_right(self, edge: Edge) -> bool:

        if self._edge_left is edge:
            return True
        elif self._edge_right is edge:
            return True
        else:
            return False

    def is_edge(self, edge: Edge) -> bool:
        """
        This edge belongs to face
        :param edge:
        :return:
        """
        return edge in self._edges

    @property
    def opposite(self) -> _Face:
        return self._opposite

    def set_opposite(self, o: _Face):
        """
        By cube constructor only
        :return:
        """
        self._opposite = o
        o._opposite = self

    @property
    def is_front(self):
        return self.name is FaceName.F

    @property
    def is_back(self):
        return self.name is FaceName.B

    @property
    def is_down(self):
        return self.name is FaceName.D

    @property
    def is_up(self):
        return self.name is FaceName.U

    @property
    def is_right(self):
        return self.name is FaceName.R

    @property
    def is_left(self):
        return self.name is FaceName.L
