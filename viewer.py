from collections.abc import Sequence
from typing import Hashable

import colorama

from cube import Cube
from elements import Face, Color, Part

_CELL_SIZE: int = 2


# def _color_2_str(c: Color) -> str:
#    return str(c.value)[0]


def _ansi_color(color, char: str):
    return color + colorama.Style.BRIGHT + char + colorama.Style.RESET_ALL


_inited = False

_colors: dict[Color, str] = {}


def _color_2_str(c: Color, x: str) -> str:
    global _inited
    global _colors

    if not _inited:
        colorama.init()

        _colors[Color.BLUE] = colorama.Fore.BLUE
        _colors[Color.ORANGE] = colorama.Fore.MAGENTA
        _colors[Color.YELLOW] = colorama.Fore.YELLOW
        _colors[Color.GREEN] = colorama.Fore.GREEN
        _colors[Color.RED] = colorama.Fore.RED
        _colors[Color.WHITE] = colorama.Fore.WHITE

        _inited = True

    #    return str(c.value)[0]
    return _ansi_color(_colors[c], x)


class _Cell:
    __slots__ = ["_chars"]

    def __init__(self) -> None:
        super().__init__()
        # to allow colors, each char is a string
        self._chars = [['.' for __ in range(0, _CELL_SIZE)] for _ in range(0, _CELL_SIZE)]

    def get_char(self, y: int, x: int) -> str:
        """

        :param x: [0 .. CELL_SIZE)
        :param y: [0 .. CELL_SIZE)
        :return: char at [y, x]
        """

        if y < 0 or y >= _CELL_SIZE:
            raise ValueError(f"y {y} must be in the range 0..{_CELL_SIZE}")

        if x < 0 or x >= _CELL_SIZE:
            raise ValueError(f"x {x} must be in the range 0..{_CELL_SIZE}")

        return self._chars[y][x]

    def put_char(self, x: int, y: int, c: str) -> None:
        """

        :param x: [0 .. CELL_SIZE)
        :param y: [0 .. CELL_SIZE)
        :param c:
        :return: char at [y, x]
        """

        if y < 0 or y >= _CELL_SIZE:
            raise ValueError(f"y {y} must be in the range 0..{_CELL_SIZE}")

        if x < 0 or x >= _CELL_SIZE:
            raise ValueError(f"x {x} must be in the range 0..{_CELL_SIZE}")

        self._chars[y][x] = c


_FACE_SIZE = 3


class _FaceBoard:
    """
     0,0 | 0,1 | 0,2
     ---------------
     1,0 | 1,1 | 1,2
     ---------------
     2,0 | 2,1 | 2,2
    """

    # face size in terms of cells
    _h_size: int = 1 * _FACE_SIZE
    _v_size: int = 1 * _FACE_SIZE

    def __init__(self, cells: Sequence[Sequence[_Cell]]) -> None:
        super().__init__()
        self._cells: Sequence[Sequence[_Cell]] = cells

    @property
    def h_size(self) -> int:
        return _FaceBoard._h_size

    @property
    def v_size(self) -> int:
        return _FaceBoard._v_size

    def get_char(self, y: int, x: int) -> str:
        """

        :param y: 0 .. _v_size
        :param x: 0 .. _h_size
        :return:
        """
        c_y = y // _CELL_SIZE
        yy = y % _CELL_SIZE

        c_x = x // _CELL_SIZE
        xx = x % _CELL_SIZE

        return self._cells[c_y][c_x].get_char(yy, xx)

    def __put_char(self, y: int, x: int, c: str) -> None:
        """

        :param c:
        :param y: 0 .. _v_size
        :param x: 0 .. _h_size
        :return:
        """
        c_y = y // _CELL_SIZE
        yy = y % _CELL_SIZE

        c_x = x // _CELL_SIZE
        xx = x % _CELL_SIZE

        self._cells[c_y][c_x].put_char(yy, xx, c)

    def put_cell_char(self, cy: int, cx: int, y: int, x: int, c: str) -> None:
        """

        :param c:
        :param cy: 0. _FACE_SIZE
        :param cx: 0 .. _FACE_SIZE
        :param y: 0 .. _CELL_SIZE
        :param x: 0 .. _CELL_SIZE
        :return:
        """
        self._cells[cy][cx].put_char(y, x, c)


class _Board:
    """

        Face coordinates

           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B
    """
    # in terms of faces
    _h_size: int = _FACE_SIZE * 3  # L F R
    _v_size: int = _FACE_SIZE * 4  # U F D B

    def __init__(self) -> None:
        super().__init__()
        self._cells: Sequence[Sequence[_Cell]] = [[_Cell() for _ in range(0, _Board._h_size)] for _ in
                                                  range(0, _Board._v_size)]

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def get_char(self, y: int, x: int) -> str:
        """

        :param y: 0 .. _v_size
        :param x: 0 .. _h_size
        :return:
        """
        c_y = y // _CELL_SIZE
        yy = y % _CELL_SIZE

        c_x = x // _CELL_SIZE
        xx = x % _CELL_SIZE

        return self._cells[c_y][c_x].get_char(yy, xx)

    def print(self):
        for y in range(_CELL_SIZE * self.v_size):
            for x in range(_CELL_SIZE * self.h_size):
                c = self.get_char(y, x)
                print(c, end='')
            print()

    def get_face(self, fy: int, fx: int) -> _FaceBoard:

        cells: Sequence[Sequence[_Cell]] = [[self._cells[y][x]
                                             for x in range(fx * _FACE_SIZE, fx * _FACE_SIZE + _FACE_SIZE)]
                                            for y in range(fy * _FACE_SIZE, fy * _FACE_SIZE + _FACE_SIZE)]
        return _FaceBoard(cells)


_parts: dict[Hashable, int] = {}


def _part_id(p: Part) -> str:
    p_id = p.pos_id

    _id = _parts.get(p_id)

    if not _id:
        _id = len(_parts) + 1
        _parts[p_id] = _id

    return chr(ord("A") + _id - 1)


def _plot_face(b: _Board, f: Face, fy: int, fx: int, flip_v=False, flip_h=False):
    """
     0,0 | 0,1 | 0,2
     ---------------
     1,0 | 1,1 | 1,2
     ---------------
     2,0 | 2,1 | 2,2
    """

    # cell start
    fb: _FaceBoard = b.get_face(fy, fx)

    def _plot_cell(cy: int, cx: int, p: Part):

        c: Color
        char: str
        if p:
            c = p.get_face_edge(f).color
            char = _part_id(p)
        else:
            c = f.color
            char = "?"

        s = _color_2_str(c, char)

        for y in range(0, _CELL_SIZE):
            for x in range(0, _CELL_SIZE):
                fb.put_cell_char(cy, cx, y, x, s)

    if flip_v:
        y0 = 2
        y2 = 0
    else:
        y0 = 0
        y2 = 2

    if flip_h:
        x0 = 2
        x2 = 0
    else:
        x0 = 0
        x2 = 2

    _plot_cell(y0, x0, f.corner_top_left)
    _plot_cell(y0, 1, f.edge_top)
    _plot_cell(y0, x2, f.corner_top_right)
    _plot_cell(1, x0, f.edge_left)
    _plot_cell(1, 1, f.center)
    _plot_cell(1, x2, f.edge_right)
    _plot_cell(y2, x0, f.corner_bottom_left)
    _plot_cell(y2, 1, f.edge_bottom)
    _plot_cell(y2, x2, f.corner_bottom_right)


def plot(cube: Cube):
    """
        Face coordinates

               0  1  2
           0:     U
           1:  L  F  R
           2:     D
           3:     B

    """

    b: _Board = _Board()

    _plot_face(b, cube.up, 0, 1)
    _plot_face(b, cube.left, 1, 0)
    _plot_face(b, cube.front, 1, 1)
    _plot_face(b, cube.right, 1, 2)
    _plot_face(b, cube.down, 2, 1)
    _plot_face(b, cube.back, 3, 1, flip_v=True, flip_h=True)

    b.print()

