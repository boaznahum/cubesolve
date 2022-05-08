from collections.abc import Sequence
from typing import Hashable, Tuple, MutableSequence

import colorama
import pyglet
from pyglet.graphics import Batch

from cube import Cube
from elements import Face, Color, Part

_CELL_SIZE: int = 20

# def _color_2_str(c: Color) -> str:
#    return str(c.value)[0]

_VColor = Tuple[int, int, int]

_TRACKER = []


def _track(obj):
    """
    Your issue is due to garbage collection.
    Sprites and Shapes will automatically delete themselves from the Batch when they fall out of scope.
    Labels do not have the same behavior (maybe they should?).
    Sprites have always had this behavior, and the new Shapes module was modeled after that behavior.
    :param obj:
    :return:
    """
    global _TRACKER
    _TRACKER.append(obj)


def _ansi_color(color, char: str):
    return color + colorama.Style.BRIGHT + char + colorama.Style.RESET_ALL


_inited = False

_colors: dict[Color, _VColor] = {}


def _color_2_v_color(c: Color) -> _VColor:
    global _inited
    global _colors

    if not _inited:
        colorama.init()

        #  https://www.rapidtables.com/web/color/blue-color.html

        _colors[Color.BLUE] = (0, 0, 255)
        _colors[Color.ORANGE] = (255, 165, 0)
        _colors[Color.YELLOW] = (255, 255, 0)
        _colors[Color.GREEN] = (0, 255, 0)
        _colors[Color.RED] = (255, 0, 0)
        _colors[Color.WHITE] = (255, 255, 255)

        _inited = True

    #    return str(c.value)[0]
    return _colors[c]


class _Cell(pyglet.shapes.BorderedRectangle):
    def __init__(self, batch: Batch, x: int, y: int) -> None:
        super().__init__(x, y, _CELL_SIZE, _CELL_SIZE, batch=batch, border=2, border_color=(0, 0, 0))

    def set_attributes(self, x: int, y: int, c: _VColor):
        self.position = (x, y)
        self.color = c


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

    def __init__(self, cube_face: Face, batch: Batch, y0, x0, flip_v, flip_h) -> None:
        super().__init__()
        self.cube_face = cube_face
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.fy0 = y0
        self.fx0 = x0
        self._cells: Sequence[Sequence[_Cell]] = [[_Cell(batch, 0, 0) for _ in range(0, _FaceBoard._h_size)] for _ in
                                                  range(0, _FaceBoard._v_size)]


    def set_cell(self, cy: int, cx: int, y: int, x: int, c: _VColor) -> None:
        """

        :param c:
        :param cy: 0. _FACE_SIZE
        :param cx: 0 .. _FACE_SIZE
        :param y: 0 .. _CELL_SIZE
        :param x: 0 .. _CELL_SIZE
        :return:
        """
        self._cells[cy][cx].set_attributes(x, y, c)

    def draw_init(self):

        fb: _FaceBoard = self

        f: Face = self.cube_face

        def _plot_cell(cy: int, cx: int, p: Part):

            c: Color
            char: str
            if p:
                c = p.get_face_edge(f).color
            else:
                c = f.color

            s = _color_2_v_color(c)

            fb.set_cell(cy, cx, self.fy0 - cy * _CELL_SIZE, self.fx0 + cx * _CELL_SIZE, s)

        if self.flip_v:
            y0 = 2
            y2 = 0
        else:
            y0 = 0
            y2 = 2

        if self.flip_h:
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


    def update(self):
        # need to optimize, no need to change position
        self.draw_init()


class _Board:
    """

        Face coordinates

           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B
    """

    _y_faces = 4
    _x_faces = 3
    # in terms of faces
    _h_size: int = _FACE_SIZE * 3  # L F R
    _v_size: int = _FACE_SIZE * 4  # U F D B

    def __init__(self, batch: Batch) -> None:
        super().__init__()
        self.batch = batch
        self._faces: Sequence[MutableSequence[_FaceBoard | None]] = [[None for _ in range(0, _Board._x_faces)]
                                                                     for _ in range(0, _Board._y_faces)]

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def create_face(self, cube_face: Face, y_index: int, x_index: int, y0, x0, flip_v, flip_h):
        f = _FaceBoard(cube_face, self.batch, y0, x0, flip_v, flip_h)
        self._faces[y_index][x_index] = f
        return f

    def update(self):
        for fs in self._faces:
            for f in fs:
                if f:
                    f.update()


_parts: dict[Hashable, int] = {}


def _part_id(p: Part) -> str:
    p_id = p.colors_id_by_color

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

    fy0 = 480 - 100 - (fy * _FACE_SIZE * _CELL_SIZE)
    fx0 = 10 + fx * _FACE_SIZE * _CELL_SIZE

    # cell start
    fb: _FaceBoard = b.create_face(f, fy, fx, fy0, fx0, flip_v, flip_h)

    fb.draw_init()


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board"]

    def __init__(self, batch: Batch, cube: Cube) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch

        self._init_gui()

    def plot(self):
        self._board.update()

    def _init_gui(self):
        self._board: _Board = _Board(self._batch)

        b = self._board
        cube = self._cube

        """
             Face coordinates

                    0  1  2
                0:     U
                1:  L  F  R
                2:     D
                3:     B

         """

        _plot_face(b, cube.up, 0, 1)
        _plot_face(b, cube.left, 1, 0)
        _plot_face(b, cube.front, 1, 1)
        _plot_face(b, cube.right, 1, 2)
        _plot_face(b, cube.down, 2, 1)
        _plot_face(b, cube.back, 3, 1, flip_v=True, flip_h=True)
