from collections.abc import Sequence
from typing import Hashable, Tuple, MutableSequence, Callable

import colorama
import numpy as np
import pyglet
from numpy import ndarray
from pyglet.graphics import Batch

import graphic_helper
from cube import Cube
from elements import Face, Color, Part

_CELL_SIZE: int = 30

# def _color_2_str(c: Color) -> str:
#    return str(c.value)[0]

_VColor = Tuple[int, int, int]

_TRACKER = []


def _track(obj):
    """
    Your issue is due to garbage collection.
    Sprites and Shapes will automatically delete themselves from the Batch when they fall out of scope.
    Labels do not have the same behavior (maybe they should?).
    Sprites have always had this behavior, and the new Shape's module was modeled after that behavior.
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


class _Cell:

    def __init__(self, batch: Batch) -> None:
        super().__init__()
        self._batch = batch
        self._g_polygon: pyglet.shapes.Polygon | None = None
        self._g_lines: Sequence[pyglet.shapes.Line] | None = None
        # noinspection PyProtectedMember
        self._g_markers: Sequence[pyglet.shapes._ShapeBase] | None = None
        # self._create_objects(x0, y0, x1, y1, (255, 255, 255))

    def _create_objects(self, vertexes: Sequence[Sequence[int]], color, marker: int):
        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(vertexes, color)
        self._create_lines(vertexes, [255, 255, 255])
        self._create_markers(vertexes, marker)

    def _create_polygon(self, vertexes: Sequence[Sequence[int, int]], color):

        vertexes = [[*p] for p in vertexes]  # need to copy, Polygon modify it
        g = pyglet.shapes.Polygon(
            *vertexes,  # must be lists and not tuples, the stupid one try to modify it
            color=color,
            batch=self._batch,
            # border=2, border_color=(0, 0, 0)
        )
        self._g_polygon: pyglet.shapes.Polygon = g

    def set_attributes(self, vertexes: Sequence[Sequence[int, int]], c: _VColor, marker):

        if self._g_polygon:
            p = self._g_polygon
            p.position = (10, 10)
            p.color = (255, 0, 0)
            p.delete()
            self._g_polygon = None
            del p

        if self._g_lines:
            lines = self._g_lines
            self._g_lines = None
            for i, l in enumerate(lines):
                l.position = (10, 10, 15, 15)
                l.color = (255, 0, 0)
                l.delete()
                del l

        if self._g_markers:
            lines = self._g_markers
            self._g_markers = None
            for i, l in enumerate(lines):
                l.position = (10, 10)
                l.color = (255, 0, 0)
                l.delete()
                del l

        self._create_objects(vertexes, c, marker)

    def _create_lines(self, vertexes, color):

        n = len(vertexes)
        lines = []
        for i in range(len(vertexes) - 1):
            line = pyglet.shapes.Line(vertexes[i][0], vertexes[i][1],
                                      vertexes[(i + 1) % n][0], vertexes[(i + 1) % n][1],
                                      width=2,
                                      color=color,
                                      batch=self._batch)
            lines.append(line)
        self._g_lines = lines

    def _create_markers(self, vertexes, marker):
        if not marker:
            return
        self._g_markers = []

        x0 = (vertexes[0][0] + vertexes[2][0]) // 2
        y0 = (vertexes[0][1] + vertexes[2][1]) // 2

        for i in range(marker + 1):
            self._g_markers.append(pyglet.shapes.Circle(x0, y0, i * 2, batch=self._batch, color=[0, 0, 0]))


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

    def __init__(self,
                 board: "_Board",
                 cube_face_supplier: Callable[[], Face], batch: Batch,
                 f0: np.ndarray, left_right_direction: ndarray, left_top_direction: ndarray
                 ) -> None:
        super().__init__()
        self._board: "_Board" = board
        self.cube_face_supplier = cube_face_supplier
        # self.flip_h = flip_h
        # self.flip_v = flip_v
        self.f0: np.ndarray = f0
        self.left_right_direction: ndarray = left_right_direction
        self.left_top_direction: ndarray = left_top_direction
        self._cells: Sequence[Sequence[_Cell]] = [[_Cell(batch) for _ in range(0, _FaceBoard._h_size)] for _
                                                  in
                                                  range(0, _FaceBoard._v_size)]

    @property
    def cube_face(self) -> Face:
        return self.cube_face_supplier()

    def set_cell(self, cy: int, cx: int, vertexes: Sequence[Sequence[int, int]], c: _VColor, marker: int) -> None:
        """

        :param marker:
        :param c:
        :param cy: 0. _FACE_SIZE
        :param cx: 0 .. _FACE_SIZE
        :param vertexes: four corners of edge
        :return:
        """
        self._cells[cy][cx].set_attributes(vertexes, c, marker)

    def draw_init(self):

        fb: _FaceBoard = self

        f: Face = self.cube_face

        alpha_x = self._board.alpha_x
        alpha_y = self._board.alpha_y
        alpha_z = self._board.alpha_z

        def _plot_cell(cy: int, cx: int, p: Part, marker: int = 0):

            c: Color
            char: str
            if p:
                c = p.get_face_edge(f).color
            else:
                c = f.color

            face_color = _color_2_v_color(c)

            left_bottom3 = self.f0 + self.left_right_direction * (cx * _CELL_SIZE) + self.left_top_direction * (
                    cy * _CELL_SIZE)

            right_bottom3 = self.f0 + self.left_right_direction * ((cx + 1) * _CELL_SIZE) + self.left_top_direction * (
                    cy * _CELL_SIZE)

            right_top3 = self.f0 + self.left_right_direction * ((cx + 1) * _CELL_SIZE) + self.left_top_direction * (
                    (cy + 1) * _CELL_SIZE)

            left_top3 = self.f0 + self.left_right_direction * (cx * _CELL_SIZE) + self.left_top_direction * (
                    (cy + 1) * _CELL_SIZE)

            screen0 = [200, 100]

            left_bottom2 = graphic_helper.vec3to2(left_bottom3, alpha_x, alpha_y, alpha_z, screen0)
            right_bottom2 = graphic_helper.vec3to2(right_bottom3, alpha_x, alpha_y, alpha_z, screen0)
            right_top2 = graphic_helper.vec3to2(right_top3, alpha_x, alpha_y, alpha_z, screen0)
            left_top2 = graphic_helper.vec3to2(left_top3, alpha_x, alpha_y, alpha_z, screen0)

            fb.set_cell(cy, cx, [left_bottom2, right_bottom2, right_top2, left_top2], face_color, marker)

        y0 = 2  # need to fix the code below, we flipped by mistake when copied from text board
        y2 = 0
        x0 = 0
        x2 = 2
        # if self.flip_v:
        #     _y0 = 2
        #     y2 = 0
        # else:
        #     _y0 = 0
        #     y2 = 2
        #
        # if self.flip_h:
        #     _x0 = 2
        #     x2 = 0
        # else:
        #     _x0 = 0
        #     x2 = 2

        _plot_cell(y0, x0, f.corner_top_left)
        _plot_cell(y0, 1, f.edge_top)
        _plot_cell(y0, x2, f.corner_top_right, marker=2)
        _plot_cell(1, x0, f.edge_left)
        _plot_cell(1, 1, f.center)
        _plot_cell(1, x2, f.edge_right)
        _plot_cell(y2, x0, f.corner_bottom_left, marker=1)
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
        self._alpha_x = 0
        self._alpha_y = 0
        self._alpha_z = 0

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def create_face(self, cube_face: Callable[[], Face],
                    y_index, x_index,
                    f0: ndarray,
                    left_right_direction: ndarray,
                    left_top_direction: ndarray):

        f = _FaceBoard(self, cube_face, self.batch, f0, left_right_direction, left_top_direction)
        self._faces[y_index][x_index] = f
        return f

    def update(self):
        for fs in self._faces:
            for f in fs:
                if f:
                    f.update()

    @property
    def alpha_x(self):
        return self._alpha_x

    @property
    def alpha_y(self):
        return self._alpha_y

    @property
    def alpha_z(self):
        return self._alpha_z


_parts: dict[Hashable, int] = {}


def _part_id(p: Part) -> str:
    p_id = p.colors_id_by_color

    _id = _parts.get(p_id)

    if not _id:
        _id = len(_parts) + 1
        _parts[p_id] = _id

    return chr(ord("A") + _id - 1)


def _plot_face(b: _Board, f: Callable[[], Face], fy: int, fx: int,
               left_bottom: list[int],  # 3d
               left_right_direction: list[int],  # 3d
               left_top_direction: list[int],  # 3d
               # flip_v=False, flip_h=False,
               ):
    """
     0,0 | 0,1 | 0,2
     ---------------
     1,0 | 1,1 | 1,2
     ---------------
     2,0 | 2,1 | 2,2
    """

    fy0 = 0  # 480 - 100
    fx0 = 0  # 10
    fz0 = 0

    f0: ndarray = np.array([fx0, fy0, fz0], dtype=float).reshape(3, 1)
    # left_bottom is length=1 vector, we convert it to face size in pixels
    fs = np.array(left_bottom).reshape(3, 1) * _FACE_SIZE * _CELL_SIZE

    f0 = f0 + fs
    _left_right_d: ndarray = np.array(left_right_direction, dtype=float).reshape(3, 1)
    _left_top_d: ndarray = np.array(left_top_direction, dtype=float).reshape(3, 1)

    fb: _FaceBoard = b.create_face(f, fy, fx, f0, _left_right_d, _left_top_d)

    fb.draw_init()


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board", "_test"]

    def __init__(self, batch: Batch, cube: Cube) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch

        self._test = pyglet.shapes.Line(0, 0, 20, 20, width=10, color=(255, 255, 255), batch=batch)

        self._board: _Board = _Board(self._batch)
        self._init_gui()

    def plot(self):
        self._board.update()

    def update(self, alpha_x, alpha_y, alpha_z):
        # print(f"{alpha_x=} {alpha_y=} {alpha_z=}")
        self._board._alpha_x = alpha_x
        self._board._alpha_y = alpha_y
        self._board._alpha_z = alpha_z
        self.plot()
        self._batch.invalidate()

    def _init_gui(self):
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

        # we pass a supplier to Face and not a face, because might reset itself

        # debug with # s.alpha_x=-0.30000000000000004 s.alpha_y=-0.5 s.alpha_z=0
        _plot_face(b, lambda : cube.back, 3, 1, [0, 0, 1], [1, 0, 0], [0, 1, 0])

        _plot_face(b, lambda : cube.up, 0, 1, [0, 1, 0], [1, 0, 0], [0, 0, 1])
        _plot_face(b, lambda : cube.left, 1, 0, [0, 0, 1], [0, 0, -1], [0, 1, 0])
        _plot_face(b, lambda : cube.front, 1, 1, [0, 0, 0], [1, 0, 0], [0, 1, 0])
        _plot_face(b, lambda : cube.right, 1, 2, [1, 0, 0], [0, 0, 1], [0, 1, 0])
        # _plot_face(b, cube.down, 2, 1, [0, 0, -1], [1, 0, 0], [0, 1, 0])

