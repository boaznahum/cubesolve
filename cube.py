from typing import Collection, Callable, Tuple, Mapping, Hashable, Sequence

from cube_face import Face
from cube_slice import Slice, SliceName
from elements import *
from elements import Color


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
        "_slices",
        "_modify_counter",
        "_last_sanity_counter"
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
        self._modify_counter = 0
        self._last_sanity_counter = 0
        self._reset()

    def _reset(self, cube_size=None):

        if cube_size:
            self._size = cube_size

        self._modify_counter = 0
        self._last_sanity_counter = 0

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

        # see document right-top-left-coordinates.jpg
        # 12 edges
        f._edge_top = u._edge_bottom = _create_edge(f, u, True)
        f._edge_left = l._edge_right = _create_edge(f, l, True)
        f._edge_right = r._edge_left = _create_edge(f, r, True)
        f._edge_bottom = d._edge_top = _create_edge(f, d, True)

        l._edge_top = u._edge_left = _create_edge(l, u, False)
        l._edge_bottom = d._edge_left = _create_edge(l, d, True)

        d._edge_right = r._edge_bottom = _create_edge(d, r, False)
        d._edge_bottom = b._edge_bottom = _create_edge(d, b, False)

        r._edge_right = b._edge_left = _create_edge(r, b, True)

        l._edge_left = b._edge_right = _create_edge(l, b, True)

        u._edge_top = b._edge_top = _create_edge(u, b, False)
        u._edge_right = r._edge_top = _create_edge(u, r, True)

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

    def inv(self, i: int) -> int:
        return self.n_slices - 1 - i

    @property
    def front(self) -> Face:
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

    def get_slice(self, name: SliceName) -> Slice:
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

    def rotate_slice(self, slice_name: SliceName, n: int, slice_index: int | slice | None = None):

        """

        :param slice_index: [0..n-2-1] [0, n_slices-1], default is [0, n_slices-1]
        :param slice_name:
        :param n:
        :return:
        """

        a_slice: Slice = self.get_slice(slice_name)

        a_slice.rotate(n, slice_index)

    def get_rotate_slice_involved_parts(self, slice_name: SliceName, slice_index: int | slice | None = None) -> \
            Collection[PartSlice]:

        """

        :param slice_index: [0..n-2-1] [0, n_slices-1], default is [0, n_slices-1]
        :param slice_name:
        :param n:
        :return:
        """

        a_slice: Slice = self.get_slice(slice_name)

        return a_slice.get_rotate_involved_parts(slice_index)

    def _get_face_and_rotation_info(self, face_name: FaceName, _slice: slice = None) -> Tuple[slice, bool, SliceName]:
        """

        :param face_name:
        :param _slice:
        :return: indexes (of face and slices), neg slices, slice name
        """

        if not _slice:
            _slice = slice(1, 1)

        stop = _slice.stop
        assert stop is not None

        start = _slice.start

        if not start:
            start = 0

        assert start is not None

        size = self.size

        assert start <= stop
        assert 0 <= start <= size - 2
        assert 0 <= stop <= size - 2

        neg_slice_index: bool
        slice_name: SliceName

        match face_name:

            case FaceName.R:
                slice_name, neg_slice_index = (SliceName.M, False)
            case FaceName.L:
                slice_name, neg_slice_index = (SliceName.M, True)

            case FaceName.U:
                slice_name, neg_slice_index = (SliceName.E, True)
            case FaceName.D:
                slice_name, neg_slice_index = (SliceName.E, False)
            case FaceName.F:
                slice_name, neg_slice_index = (SliceName.S, False)
            case FaceName.B:
                slice_name, neg_slice_index = (SliceName.S, True)

            case _:
                raise InternalSWError(f"Unknown face {face_name}")

        return slice(start, stop), neg_slice_index, slice_name

    def rotate_face_and_slice(self, n: int, face_name: FaceName, _slice: slice = None):

        """

        :param n:
        :param face_name:
        :param _slice: [0, n-2]    not including last face
        :return:
        """

        start_stop: slice
        neg_slice_index: bool
        slice_name: SliceName

        start_stop, neg_slice_index, slice_name = self._get_face_and_rotation_info(face_name, _slice)

        start = start_stop.start
        stop = start_stop.stop

        if start == 0:
            self.face(face_name).rotate(n)
            start += 1

        if neg_slice_index:
            n = -n

        # slice index is cube index -1
        for si in range(start - 1, stop + 1 - 1):
            if neg_slice_index:
                si = self.inv(si)
            self.rotate_slice(slice_name, n, si)

    def get_rotate_face_and_slice_involved_parts(self, face_name: FaceName, _slice: slice = None) -> \
            Collection[PartSlice]:

        """

        :param face_name:
        :param _slice: [0, n-2]    not including last face
        :return:
        """

        start_stop: slice
        neg_slice_index: bool
        slice_name: SliceName

        start_stop, neg_slice_index, slice_name = self._get_face_and_rotation_info(face_name, _slice)

        parts: MutableSequence[PartSlice] = []

        start = start_stop.start
        stop = start_stop.stop

        if start == 0:
            face = self.face(face_name)
            parts.extend(face.slices)
            start += 1

        # slice index is cube index -1
        # stop + 1 because it is a range
        r = range(start - 1, stop + 1 - 1)
        if r:
            a_slice: Slice = self.get_slice(slice_name)

            for si in r:
                if neg_slice_index:
                    si = self.inv(si)

                _slice_parts = a_slice.get_rotate_involved_parts(si)
                parts.extend(_slice_parts)

        return parts

    def modified(self):
        self._modify_counter += 1

    def is_sanity(self, force_check=False) -> bool:
        # noinspection PyBroadException
        try:
            self.sanity()
            return True
        except:
            return False

    def sanity(self, force_check=False):

        if self._modify_counter == self._last_sanity_counter:
            return

        # if True:
        #     return

        # noinspection PyUnreachableCode
        try:
            self._do_sanity(force_check)
            self._last_sanity_counter = self._modify_counter
        except:
            raise

    def _do_sanity(self, force_check=False):

        if not (force_check or config.CHECK_CUBE_SANITY):
            return

        # find all corners , NxN still have simple corners

        corners = [
            (Color.YELLOW, Color.ORANGE, Color.BLUE),
            (Color.YELLOW, Color.RED, Color.BLUE),
            (Color.YELLOW, Color.ORANGE, Color.GREEN),
            (Color.YELLOW, Color.RED, Color.GREEN),
            (Color.WHITE, Color.ORANGE, Color.BLUE),
            (Color.WHITE, Color.RED, Color.BLUE),
            (Color.WHITE, Color.ORANGE, Color.GREEN),
            (Color.WHITE, Color.RED, Color.GREEN),
        ]

        for c in corners:
            self.find_corner_by_colors(CHelper.colors_id(c))

        # very expansive, but there is a corruption
        if True:

            n_slices = self.n_slices

            from cube_queries import CubeQueries

            dist: Mapping[Color, Mapping[Hashable, Sequence[tuple[int, int]]]] = CubeQueries.get_dist(self)

            for clr in Color:
                clr_dist= dist[clr]

                def _print_clr():
                    for k, v in clr_dist.items():
                        if len(v) != 4:
                            m = "!!!"
                        else:
                            m = "+++"
                        print(clr, k, f"{m}{len(v)}{m}", v)

                clr_n = sum(len(s) for s in clr_dist.values())

                if clr_n != n_slices * n_slices:
                    s = f"Too few entries for color {clr}"
                    _print_clr()
                    print(s)
                    raise InternalSWError(s)
                for k, v in clr_dist.items():
                    if len(v) != 4:
                        if n_slices % 2 and k == frozenset([*CubeQueries.get_four_center_points(self, n_slices//2, n_slices //2)]):
                            if len(v) != 1:
                                s = f"Wrong middle center {k} entries for color {clr}"
                                _print_clr()
                                print(s)
                                raise InternalSWError(s)

                        else:
                            s = f"Too few point {k} entries for color {clr}"
                            _print_clr()
                            print(s)
                            raise InternalSWError(s)

            for clr in Color:

                def _c_pred(_r, _c):

                    def pred(cs: CenterSlice) -> bool:
                        if not cs.color == clr:
                            return False

                        return cs.index in CubeQueries.get_four_center_points(self, _r, _c)
                        #return cs.index == rc

                    return pred

                for r in range(self.n_slices):
                    for c in range(self.n_slices):
                        if not CubeQueries.find_center_slice(self, _c_pred(r, c)):
                            n = 0
                            counter = defaultdict(int)
                            for f in self.faces:
                                for r in range(self.n_slices):
                                    for c in range(self.n_slices):
                                        s = f.center.get_center_slice((r,c))
                                        if s.color == clr:
                                            n += 1
                                            key = frozenset([*CubeQueries.get_four_center_points(self, r, c)])
                                            counter[key] += 1
                                            print(n, "]", s, *CubeQueries.get_four_center_points(self, r, c))
                            for k,v in counter.items():
                                print(k, v)

                            raise InternalSWError(f"{(clr, r, c)}")
                            assert CubeQueries.find_center_slice(self, _c_pred(r, c)), f"{(clr, r, c)}"



        if not self.is3x3:
            return

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
        return all(f.is3x3 for f in self.faces)

    def reset(self, cube_size=None):
        self._reset(cube_size)

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

    def get_all_parts(self) -> Collection[PartSlice]:

        # set - because faces share parts
        parts: set[PartSlice] = set()

        for f in self.faces:
            parts.update(f.slices)

        return parts


def _create_edge(f1: Face, f2: Face, right_top_left_same_direction: bool) -> Edge:
    """

    :param f1:
    :param f2:
    :param right_top_left_same_direction: tru if on both faces, the left to top/right is on same direction
    See right-top-left-coordinates.jpg
    :return:
    """

    n = f1.cube.n_slices

    def _create_slice(i):
        p1: PartEdge = f1.create_part()
        p2: PartEdge = f2.create_part()

        return EdgeSlice(i, p1, p2)

    e: Edge = Edge(f1, f2, right_top_left_same_direction, [_create_slice(i) for i in range(n)])

    return e


def _create_corner(f1: Face, f2: Face, f3: Face) -> Corner:
    p1: PartEdge = f1.create_part()
    p2: PartEdge = f2.create_part()
    p3: PartEdge = f3.create_part()

    _slice = PartSlice(0, p1, p2, p3)

    e: Corner = Corner(_slice)

    return e
