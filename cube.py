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
        f: Face = Face(FaceName.F, Color.BLUE)
        l: Face = Face(FaceName.L, Color.ORANGE)
        u: Face = Face(FaceName.U, Color.YELLOW)
        r: Face = Face(FaceName.R, Color.RED)
        d: Face = Face(FaceName.D, Color.WHITE)
        b: Face = Face(FaceName.B, Color.GREEN)

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

        l._edge_top = u._edge_left = _create_edge(l, u)
        l._edge_bottom = d._edge_left = _create_edge(l, d)

        d._edge_right = r._edge_bottom = _create_edge(d, r)
        d._edge_bottom = b._edge_bottom = _create_edge(d, b)

        r._edge_right = b._edge_left = _create_edge(r, b)
        d._edge_bottom = b._edge_bottom = _create_edge(d, b)

        l._edge_left = b._edge_right = _create_edge(l, b)

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
    def right(self) -> Face:
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

    def m_rotate(self, n=1):
        """
        middle over R
        :param n:
        :return:
        """
        front: Face = self.front
        back: Face = self.back
        up: Face = self.up
        down: Face = self.down

        for _ in range(0, n % 4):
            saved_up: Center = self.up.center.copy()

            self.up.center.replace_colors(self.front.center)
            self.front.center.replace_colors(self.down.center)
            self.down.center.replace_colors(self.back.center)
            self.back.center.replace_colors(saved_up)

            saved_up_top: Edge = self.up.edge_top.copy()
            self.up.edge_top.replace_colors2(self.up.edge_bottom, up, back, front, up)
            self.front.edge_top.replace_colors2(self.front.edge_bottom, front, up, down, front)
            self.front.edge_bottom.replace_colors2(self.back.edge_bottom, down, front, back, down)
            self.back.edge_bottom.replace_colors2(saved_up_top, up, back, back, down)

    def x_rotate(self, n):
        """
        Entire cube or X
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.m_rotate()
            self.right.rotate()
            self.left.rotate(-1)

    def e_rotate(self, n=1):
        """
        middle over D
        :param n:
        :return:
        """
        front: Face = self.front
        back: Face = self.back
        left: Face = self.left
        right: Face = self.right

        for _ in range(0, n % 4):
            saved_front: Center = self.front.center.copy()

            self.front.center.replace_colors(self.left.center)
            self.left.center.replace_colors(self.back.center)
            self.back.center.replace_colors(self.right.center)
            self.right.center.replace_colors(saved_front)

            saved_front_left: Edge = self.front.edge_left.copy()
            self.front.edge_left.replace_colors2(self.left.edge_left, left, front, back, left)
            self.left.edge_left.replace_colors2(self.back.edge_left, back, left, right, back)
            self.back.edge_left.replace_colors2(self.right.edge_left, front, right, right, back)
            self.front.edge_right.replace_colors2(saved_front_left, front, right, left, front)

    def y_rotate(self, n=1):
        """
        entire over U  (please note that e is over D)
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.e_rotate()
            self.up.rotate(-1)
            self.down.rotate(1)

    def s_rotate(self, n=1):
        """
        middle over F
        :param n:
        :return:
        """
        pass

    def z_rotate(self, n=1):
        """
        entire over F
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.s_rotate()
            self.front.rotate()
            self.back.rotate(-1)

    @property
    def solved(self):
        return (self._front.solved and
                self._left.solved and
                self._right.solved and
                self._up.solved and
                self._back.solved and
                self._down.solved)

    def view(self) -> "CubeView":
        return CubeView(self)

    def reset(self):
        self._reset()


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


class CubeView:
    __slots__ = ["_cube",
                 "_front", "_left", "_up", "_right", "_down", "_back"]

    def __init__(self, cube: Cube) -> None:
        super().__init__()
        self._cube: Cube = cube

        self._front = cube.front
        self._left = cube.left
        self._up = cube.up
        self._right = cube.right
        self._down = cube.down
        self._back = cube.back

    @property
    def front(self):
        return self._front

    @property
    def left(self):
        return self._left

    @property
    def right(self) -> Face:
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

    @property
    def solved(self):
        return self._cube.solved
