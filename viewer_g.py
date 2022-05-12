from collections.abc import Sequence
from typing import Hashable, Tuple, MutableSequence, Callable

import colorama
import numpy as np
import pyglet
from numpy import ndarray
from pyglet.gl import *
from pyglet.graphics import Batch

from cube import Cube
from elements import Face, Color, Part
from view_state import ViewState

_CELL_SIZE: int = 25

_VColor = Tuple[int, int, int]


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


# noinspection PyMethodMayBeStatic
class _Cell:

    def __init__(self, face_board: "_FaceBoard", batch: Batch) -> None:
        super().__init__()
        self._batch = batch
        self._face_board = face_board
        self._g_polygon: pyglet.shapes.Polygon | None = None
        self._g_lines: Sequence[pyglet.shapes.Line] | None = None
        # noinspection PyProtectedMember
        self._g_markers: Sequence[pyglet.shapes._ShapeBase] | None = None
        # self._create_objects(x0, y0, x1, y1, (255, 255, 255))

        self.gl_lists = 0

    def create_objects(self, vertexes: Sequence[Sequence[int]], color, marker: int):

        # p = (GLint)()
        # glGetIntegerv(GL_MATRIX_MODE, p)
        # print(p, GL_MODELVIEW)
        # default is GL_MODELVIEW, but we need to make sue by push attributes

        if self.gl_lists:
            glDeleteLists(self.gl_lists, 1)

        self.gl_lists = glGenLists(1)
        # print(f"{self.gl_lists=}")

        glNewList(self.gl_lists, GL_COMPILE)

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(vertexes, color)
        self._create_lines(vertexes, [0, 0, 0])
        # self._create_helpers()
        # self._create_markers(vertexes, marker)
        glEndList()

    def draw(self):
        if not self.gl_lists:
            print(f"Error no gl lists in {self}")
        self._prepare_view_state()
        glCallList(self.gl_lists)
        self._restore_view_state()

    def _prepare_view_state(self):

        vs: ViewState = self._face_board.board.vs
        vs.prepare_objects_view()

    def _restore_view_state(self):

        vs: ViewState = self._face_board.board.vs
        vs.restore_objects_view()

    # noinspection PyMethodMayBeStatic
    def _create_polygon(self, vertexes: Sequence[Sequence[int, int, int]], color):

        # glBegin(GL_TRIANGLE_FAN)
        glBegin(GL_QUADS)

        glColor3ub(*color)

        for v in vertexes:
            glVertex3f(*v)
        glEnd()

    # noinspection PyMethodMayBeStatic
    def _create_lines(self, vertexes, color):

        glPushAttrib(GL_LINE_WIDTH)
        glLineWidth(4)

        glColor3ub(*color)

        for i in range(len(vertexes) - 1):
            glBegin(GL_LINES)
            glVertex3f(*vertexes[i])
            glVertex3f(*vertexes[i + 1])
            glEnd()

        glPopAttrib()

    # noinspection PyMethodMayBeStatic
    def _create_helpers(self):
        """
        For debug
        :return:
        """

        glPushAttrib(GL_LINE_WIDTH)
        glLineWidth(6)

        glBegin(GL_LINES)

        # parallel to X axis with offset on z/y
        glColor3ub(255, 255, 255)
        glVertex3f(0, 0, 50)
        glVertex3f(200, 0, 50)
        glVertex3f(0, 50, 0)
        glVertex3f(200, 50, 0)

        # the problematic one, the one on X
        glColor3ub(255, 255, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(50, 0, 0)

        glEnd()

        # parallel to Y axis with offset on x/z
        glBegin(GL_LINES)
        glColor3ub(255, 0, 0)
        glVertex3f(50, 0, 0)
        glVertex3f(50, 200, 0)
        glVertex3f(0, 0, 50)
        glVertex3f(0, 200, 50)
        glEnd()

        # line parallel to Z axis , with offset on X
        glBegin(GL_LINES)
        glColor3ub(0, 255, 255)
        glVertex3f(50, 0, 0)
        glVertex3f(50, 0, 200)
        glEnd()

        glPopAttrib()  # line width

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
        self._cells: Sequence[Sequence[_Cell]] = [[_Cell(self, batch) for _ in range(0, _FaceBoard._h_size)] for _
                                                  in
                                                  range(0, _FaceBoard._v_size)]

    @property
    def cube_face(self) -> Face:
        return self.cube_face_supplier()

    def set_cell(self, cy: int, cx: int, vertexes: Sequence[[int, int, int]], c: _VColor, marker: int) -> None:
        """

        :param marker:
        :param c:
        :param cy: 0. _FACE_SIZE
        :param cx: 0 .. _FACE_SIZE
        :param vertexes: four corners of edge
        :return:
        """
        self._cells[cy][cx].create_objects(vertexes, c, marker)

    def draw_init(self):

        fb: _FaceBoard = self

        f: Face = self.cube_face

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

            box: MutableSequence[np.ndarray] = [left_bottom3, right_bottom3, right_top3, left_top3]

            lbox = [x.reshape((3,)).tolist() for x in box]

            for i in range(len(lbox)):
                lbox[i] = [GLfloat(lbox[i][0]), GLfloat(lbox[i][1]), GLfloat(lbox[i][2])]

            fb.set_cell(cy, cx, lbox, face_color, marker)

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
        self.draw_init()

    def draw(self):
        # need to optimize, no need to change position
        for cs in self._cells:
            for c in cs:
                if c:
                    c.draw()

    @property
    def board(self):
        return self._board


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

    def __init__(self, batch: Batch, vs: ViewState) -> None:
        super().__init__()
        self.batch = batch
        self._faces: MutableSequence[_FaceBoard] = []
        self._vs = vs

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def create_face(self, cube_face: Callable[[], Face],
                    f0: ndarray,
                    left_right_direction: ndarray,
                    left_top_direction: ndarray):
        f = _FaceBoard(self, cube_face, self.batch, f0, left_right_direction, left_top_direction)
        self._faces.append(f)
        return f

    def update(self):
        for face in self._faces:
            face.update()

    def draw(self):
        for face in self._faces:
            face.draw()

    @property
    def alpha_x(self):
        return self._vs.alpha_x

    @property
    def alpha_y(self):
        return self._vs.alpha_y

    @property
    def alpha_z(self):
        return self._vs.alpha_z

    @property
    def vs(self):
        return self._vs


_parts: dict[Hashable, int] = {}


def _part_id(p: Part) -> str:
    p_id = p.colors_id_by_color

    _id = _parts.get(p_id)

    if not _id:
        _id = len(_parts) + 1
        _parts[p_id] = _id

    return chr(ord("A") + _id - 1)


def _plot_face(b: _Board, f: Callable[[], Face], left_bottom: list[float],  # 3d
               left_right_direction: list[int],  # 3d
               left_top_direction: list[int],  # 3d
               # flip_v=False, flip_h=False,
               ):
    """

    :param b:
    :param f:
    :param left_bottom: in units of faces
    :param left_right_direction:
    :param left_top_direction:
    :return:
    """
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
    fs = np.array(left_bottom, dtype=float).reshape(3, 1) * _FACE_SIZE * _CELL_SIZE

    f0 = f0 + fs
    _left_right_d: ndarray = np.array(left_right_direction, dtype=float).reshape(3, 1)
    _left_top_d: ndarray = np.array(left_top_direction, dtype=float).reshape(3, 1)

    fb: _FaceBoard = b.create_face(f, f0, _left_right_d, _left_top_d)

    fb.draw_init()


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board", "_test"]

    def __init__(self, batch: Batch, cube: Cube, vs: ViewState) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch

        #        self._test = pyglet.shapes.Line(0, 0, 20, 20, width=10, color=(255, 255, 255), batch=batch)

        self._board: _Board = _Board(self._batch, vs)

        self._init_gui()

    def update(self):
        self._board.update()

    def draw(self):
        self._board.draw()

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

        # OK
        _plot_face(b, lambda: cube.up, [0, 1, 1], [1, 0, 0], [0, 0, -1])

        # -0.75 from it x location, so we can see it in isometric view
        # OK
        _plot_face(b, lambda: cube.left, [-0, 0, 0], [0, 0, 1], [0, 1, 0])
        _plot_face(b, lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0])

        # OK
        _plot_face(b, lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0])

        # OK
        _plot_face(b, lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0])

        # OK! -2 far away so we can see it
        _plot_face(b, lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0])
        _plot_face(b, lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0])

        # -05 below so we see it
        _plot_face(b, lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1])
        _plot_face(b, lambda: cube.down, [0, -0.5, 0], [1, 0, 0], [0, 0, 1])
