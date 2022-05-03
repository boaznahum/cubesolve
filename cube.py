from elements import *


class Cube:
    """
           0  1  2
           0:     U
           1:  L  F  R
           2:     D
           3:     B
    """
    __slots__ = ["_front", "_left", "_up", "_right", "_down", "_back"]

    _front: Face
    _left: Face
    _up: Face
    _right: Face
    _down: Face
    _back: Face

    def __init__(self) -> None:
        super().__init__()
        self._reset()

    def _reset(self):
        f: Face = Face(Color.BLUE)
        l: Face = Face(Color.ORANGE)
        u: Face = Face(Color.YELLOW)
        r: Face = Face(Color.RED)
        d: Face = Face(Color.WHITE)
        b: Face = Face(Color.GREEN)

        self._front = f
        self._left = l
        self._up = u
        self._right = r
        self._down = d
        self._back = b

        e: Edge

        f._edge_top = u._edge_bottom = _create_edge(f, u)
        f._edge_left = l._edge_right = _create_edge(f, l)
        f._edge_right = r._edge_left = _create_edge(f, r)
        f._edge_bottom = d._edge_top = _create_edge(f, d)

        l._edge_top = u._edge_left  = _create_edge(l, u)
        l._edge_bottom = d._edge_left = _create_edge(l, d)

        d._edge_right = r._edge_bottom  = _create_edge(d, r)
        d._edge_bottom = b._edge_bottom = _create_edge(d, b)

        r._edge_right = b._edge_left  = _create_edge(r, b)
        d._edge_bottom = b._edge_bottom = _create_edge(d, b)

        l._edge_left = b._edge_right  = _create_edge(l, b)

        u._edge_top = b._edge_top = _create_edge(u, b)
        u._edge_right = r._edge_top = _create_edge(u, r)


        f._corner_top_left = l._corner_top_right = u._corner_bottom_left = _create_corner(f, l, u)
        f._corner_top_right = r._corner_top_left = u._corner_bottom_right = _create_corner(f, r, u)
        f._corner_bottom_left = l._corner_bottom_right = d._corner_top_left = _create_corner(f, l, d)
        f._corner_bottom_right = r._corner_bottom_left = d._corner_top_right = _create_corner(f, r, d)

        b._corner_top_left = r._corner_top_right = u._corner_top_right = _create_corner(b, r, u)
        b._corner_top_right = l._corner_top_left = u._corner_top_left = _create_corner(b, l, u)
        b._corner_bottom_left = r._corner_bottom_right = d._corner_bottom_right = _create_corner(b, r, d)
        b._corner_bottom_right = l._corner_bottom_left = d._corner_bottom_left = _create_corner(b, l, d)

    @property
    def front(self):
        return self._front

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def up(self):
        return self._up

    @property
    def back(self):
        return self._back

    @property
    def down(self):
        return self._down



def _create_edge(f1: Face, f2: Face) -> Edge:
    p1: PartEdge = f1.create_part()
    p2: PartEdge = f2.create_part()

    e: Edge = Edge(p1, p2)

    return e


def _create_corner(f1: Face, f2: Face, f3: Face) -> Corner:
    p1: PartEdge = f1.create_part()
    p2: PartEdge = f2.create_part()
    p3: PartEdge = f3.create_part()

    e: Corner = Corner(p1, p2, p3)

    return e
