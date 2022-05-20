from collections.abc import Iterable

from cube_slice import Slice, SliceName
from elements import *
from cube_face import Face


class Cube:
    """
           0  1  2
           0:     U
           1:  L  F  R
           2:     D
           3:     B
    """
    __slots__ = [
        "_size",  # 3x3, 4x4
        "_front", "_left", "_up", "_right", "_down",
        "_back",
        "_color_2_face",
        "_faces",
        "_slice_m", "_slice_e", "_slice_s",
        "_slices"
    ]

    _front: Face
    _left: Face
    _up: Face
    _right: Face
    _down: Face
    _back: Face
    _color_2_face: dict[Color, Face]
    _faces: dict[FaceName, Face]
    _slices: dict[SliceName, Slice]

    def __init__(self, size: int) -> None:
        super().__init__()
        self._size = size
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

        for _f in self._faces.values():
            _f.finish_init()

        slice_s: Slice = Slice(self, SliceName.S,  # Middle over F
                               l.edge_top, u.center, r.edge_top,
                               r.center,
                               r.edge_bottom, d.center, l.edge_bottom,
                               l.center
                               )

        slice_m: Slice = Slice(self, SliceName.M,  # Middle over R
                               f.edge_top, u.center, b.edge_top,
                               b.center,
                               b.edge_bottom, d.center, f.edge_bottom,
                               f.center
                               )

        slice_e: Slice = Slice(self, SliceName.E,  # Middle over D
                               f.edge_left, f.center, f.edge_right,
                               r.center,
                               b.edge_left, b.center, b.edge_right,
                               l.center
                               )

        self._slices = {SliceName.S: slice_s, SliceName.M: slice_m, SliceName.E: slice_e}
        for s in self._slices.values():
            s.finish_init()

        # self.front.edge_top.annotate()

    @property
    def size(self) -> int:
        return self._size

    @property
    def n_slices(self) -> int:
        return self._size - 2

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

    def slice(self, name: SliceName) -> Slice:
        return self._slices[name]

    def reset_after_faces_changes(self):
        """
        Call after faces colors aare changes , M, S, E rotations
        :return:
        """
        self._color_2_face.clear()

        for f in self.faces:
            f.reset_after_faces_changes()

    def x_rotate(self, n):
        """
        Entire cube or R
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.M, 1)
            self.right.rotate()
            self.left.rotate(-1)

    def y_rotate(self, n=1):
        """
        entire over U  (please note that e is over D)
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.E, -1)
            self.up.rotate(1)
            self.down.rotate(-1)

    def z_rotate(self, n=1):
        """
        entire over F
        :param n:
        :return:
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.S, 1)
            self.front.rotate(1)
            self.back.rotate(-1)

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

    def rotate_slice(self, slice_name: SliceName, n: int):

        a_slice: Slice = self.slice(slice_name)
        a_slice.rotate(n)

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

    @property
    def is3x3(self):
        # todo: Optimize it !!!
        return all( f.is3x3 for f in self.faces)


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
    n = f1.cube.n_slices

    def _create_slice(i):
        p1: PartEdge = f1.create_part()
        p2: PartEdge = f2.create_part()

        return EdgeSlice(i, p1, p2)

    e: Edge = Edge([_create_slice(i) for i in range(n)])

    return e


def _create_corner(f1: Face, f2: Face, f3: Face) -> Corner:
    p1: PartEdge = f1.create_part()
    p2: PartEdge = f2.create_part()
    p3: PartEdge = f3.create_part()

    slice = PartSlice(0, p1, p2, p3)

    e: Corner = Corner(slice)

    return e
