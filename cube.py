from elements import *


class Cube:
    """
           0  1  2
           0:     U
           1:  L  F  R
           2:     D
           3:     B
    """
    __slots__ = ["_front", "_left", "_up", "_right", "_down",
                 "_back",
                 "_color_2_face",
                 "_faces"
                 ]

    _front: Face
    _left: Face
    _up: Face
    _right: Face
    _down: Face
    _back: Face
    _color_2_face: dict[Color, Face]
    _faces: dict[FaceName, Face]

    def __init__(self) -> None:
        super().__init__()
        self._reset()

    def _reset(self):

        self._color_2_face = {}

        f: Face = Face(self, FaceName.F, Color.BLUE)
        l: Face = Face(self, FaceName.L, Color.ORANGE)
        u: Face = Face(self, FaceName.U, Color.YELLOW)
        r: Face = Face(self, FaceName.R, Color.RED)
        d: Face = Face(self, FaceName.D, Color.WHITE)
        b: Face = Face(self, FaceName.B, Color.GREEN)

        f.set_opposite(b)
        u.set_opposite(d)
        r.set_opposite(l)

        self._front = f
        self._left = l
        self._up = u
        self._right = r
        self._down = d
        self._back = b

        self._faces = {
            FaceName.F: f,
            FaceName.L: l,
            FaceName.U: u,
            FaceName.R: r,
            FaceName.D: d,
            FaceName.B: b
        }

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

        for f in self._faces.values():
            f.finish_init()

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
    def faces(self) -> Iterable[Face]:
        return self._faces.values()

    def face(self, name: FaceName) -> Face:
        return self._faces[name]

    def _reset_after_faces_changes(self):
        """
        Call after faces colors aare changes , M, S, E rotations
        :return:
        """
        self._color_2_face.clear()

        for f in self.faces:
            f.reset_after_faces_changes()

    def m_rotate(self, n=1):
        """
        middle over R
        :param n:
        :return:
        """

        self.sanity()

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

        self._reset_after_faces_changes()

        self.sanity()

    def x_rotate(self, n):
        """
        Entire cube or R
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

        self.sanity()

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

        self._reset_after_faces_changes()

        self.sanity()

    def y_rotate(self, n=1):
        """
        entire over U  (please note that e is over D)
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.e_rotate(-1)
            self.up.rotate(1)
            self.down.rotate(-1)

    def s_rotate(self, n=1):
        """
        middle over F
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.z_rotate()
            self.front.rotate(-1)
            self.back.rotate()

        self._reset_after_faces_changes()

    def z_rotate(self, n=1):
        """
        entire over F
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.y_rotate(1)
            self.x_rotate(-1)
            self.y_rotate(-1)

    def rotate_whole(self, axis_name: AxisName, n=1):
        match axis_name:

            case AxisName.X:
                self.x_rotate(n)

            case AxisName.Y:
                self.y_rotate(n)

            case AxisName.Z:
                self.z_rotate(n)

            case _:
                raise RuntimeError(f"Unknown Axis {axis_name}")

    def sanity(self):

        # if True:
        #     return

        # noinspection PyUnreachableCode
        self._do_sanity()

    def _do_sanity(self):

        for c in Color:
            self.find_part_by_colors(frozenset([c]))

        for c1, c2 in [
            (Color.WHITE, Color.ORANGE),
            (Color.WHITE, Color.BLUE),
            (Color.WHITE, Color.GREEN),
            (Color.WHITE, Color.RED),
            (Color.YELLOW, Color.ORANGE),
            (Color.YELLOW, Color.BLUE),
            (Color.YELLOW, Color.GREEN),
            (Color.YELLOW, Color.RED),

            (Color.ORANGE, Color.BLUE),
            (Color.BLUE, Color.RED),
            (Color.RED, Color.GREEN),
            (Color.GREEN, Color.ORANGE),
        ]:
            self.find_part_by_colors(frozenset([c1, c2]))

    @property
    def solved(self):
        return (self._front.solved and
                self._left.solved and
                self._right.solved and
                self._up.solved and
                self._back.solved and
                self._down.solved)

    def reset(self):
        self._reset()

    def color_2_face(self, c: Color) -> Face:
        if not self._color_2_face:
            self._color_2_face = {f.color: f for f in self._faces.values()}

        return self._color_2_face[c]

    def find_part_by_colors(self, part_colors_id: PartColorsID) -> Part:

        for f in self.faces:
            p = f.find_part_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain part {str(part_colors_id)}")

    def find_part_by_pos_colors(self, part_colors_id: PartColorsID) -> Part:

        """
        Given a color id, find where it should be located in cube
        :param part_colors_id:
        :return:
        """

        for f in self.faces:
            p = f.find_part_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain part {str(part_colors_id)}")

    def find_edge_by_color(self, part_colors_id: PartColorsID) -> Edge:

        """
        Find edge that its color id is part_colors_id
        :param part_colors_id:
        :return:
        """

        for f in self.faces:
            p = f.find_edge_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain edge {str(part_colors_id)}")

    def find_corner_by_colors(self, part_colors_id: PartColorsID) -> Corner:

        """
        Find edge that its color id is part_colors_id
        :param part_colors_id:
        :return:
        """

        assert len(part_colors_id) == 3  # it is a corner

        for f in self.faces:
            p = f.find_corner_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain corner {str(part_colors_id)}")

    def find_edge_by_pos_colors(self, part_colors_id: PartColorsID) -> Edge:
        """
        Find the edge that it's position matches color id
        :param part_colors_id:
        :return:
        """
        for f in self.faces:
            p = f.find_edge_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain edge {str(part_colors_id)}")

    def find_corner_by_pos_colors(self, part_colors_id: PartColorsID) -> Corner:
        """
        Find the edge that it's position matches color id
        :param part_colors_id:
        :return:
        """
        for f in self.faces:
            p = f.find_corner_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain corner {str(part_colors_id)}")


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
