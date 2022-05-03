from abc import ABC
from enum import Enum
from typing import TypeAlias, MutableSequence


class Color(Enum):
    BLUE = "B"
    ORANGE = "O"
    YELLOW = "Y"
    GREEN = "G"
    RED = "R"
    WHITE = "W"

class Direction(Enum):
    D0 = 0
    D90 = 90
    D180 = 180
    D270 = 270


_Face: TypeAlias = "Face"


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


class Part(ABC):
    """
    n = 1 - center
    n = 2 - edge
    n = 3 - corner
    """
    __slots__ = ["_edges"]
    _edges: MutableSequence[PartEdge]

    def __init__(self, *edges: PartEdge) -> None:
        super().__init__()
        self._edges: MutableSequence[PartEdge] = [*edges]

    def get_face(self, face: _Face) -> PartEdge:
        """
        retunr the edge belong to face, raise erro if not found
        :param face:
        :return:
        """
        for e in self._edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    def __str__(self) -> str:
        return str([ str(e.face.color) for e in self._edges ] )


class Center(Part):
    def __init__(self, center: PartEdge) -> None:
        super().__init__(center)

    def edg(self):
        return self._edges[0]

    @property
    def color(self):
        return self.edg().color


class Edge(Part):
    def __init__(self, e1: PartEdge, e2: PartEdge) -> None:
        super().__init__(e1, e2)


class Corner(Part):
    def __init__(self, e1: PartEdge, e2: PartEdge, e3: PartEdge) -> None:
        super().__init__(e1, e2, e3)


class Face:
    __slots__ = ["_center", "_direction",
                 "_edge_left", "_edge_top", "_edge_right", "_edge_bottom",
                 "_corner_top_left", "_corner_top_right", "_corner_bottom_right", "_corner_bottom_left",
                 "_parts"
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

    def __init__(self, color: Color) -> None:
        super().__init__()

        self._center = Center(PartEdge(self, color))
        self._direction = Direction.D0

        self._edge_left: Edge = None
        self._edge_top: Edge = None
        self._edge_right: Edge = None
        self._edge_bottom: Edge = None

        self._corner_top_left: Corner  = None
        self._corner_top_right: Corner  = None
        self._corner_bottom_right: Corner  = None
        self._corner_bottom_left: Corner  = None


    @property
    def center(self) -> Center:
        return self._center

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
        return f"Face: {self._center.edg().color}"

    # for constructing only, valid only after ctor
    def create_part(self) -> PartEdge:

        e: PartEdge = PartEdge(self, self.color)
        return e



