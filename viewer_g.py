from collections.abc import Sequence, Set
from ctypes import c_float
from typing import Hashable, Tuple, MutableSequence, Callable, Iterable

import colorama
import numpy as np
import pyglet  # type: ignore
from numpy import ndarray
from pyglet.gl import *  # type: ignore
import pyglet.gl as gl
from pyglet.graphics import Batch  # type: ignore

from cube import Cube
from cube_face import Face
from elements import Color, Part, FaceName, PartFixedID, AxisName
from view_state import ViewState

_CELL_SIZE: int = 25

_VColor = Tuple[int, int, int]

Vec3f = Tuple[c_float]


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
        self._right_top_v3: Sequence[c_float] | None = None
        self._left_bottom_v3: Sequence[c_float] | None = None
        self._batch = batch
        self._face_board = face_board
        self._g_polygon: pyglet.shapes.Polygon | None = None
        self._g_lines: Sequence[pyglet.shapes.Line] | None = None
        # noinspection PyProtectedMember
        self._g_markers: Sequence[pyglet.shapes._ShapeBase] | None = None
        # self._create_objects(x0, y0, x1, y1, (255, 255, 255))

        self.gl_lists = 0

    # noinspection PyUnusedLocal
    def create_objects(self, vertexes: Sequence[Vec3f], color, marker: int):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        self._left_bottom_v3 = vertexes[0]
        self._right_top_v3 = vertexes[2]

        if self.gl_lists:
            gl.glDeleteLists(self.gl_lists, 1)

        self.gl_lists = gl.glGenLists(1)
        # print(f"{self.gl_lists=}")

        gl.glNewList(self.gl_lists, gl.GL_COMPILE)

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(vertexes, color)
        self._create_lines(vertexes, [0, 0, 0])
        # self._create_helpers()
        # self._create_markers(vertexes, marker)
        gl.glEndList()

    def draw(self):

        lists: int = self.gl_lists

        if not self.gl_lists:
            print(f"Error no gl lists in {self}")
            return

        hidden = self._face_board.board.get_hidden()
        if hidden and lists in hidden:
            return

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
    def _create_polygon(self, vertexes: Sequence[Vec3f], color):

        # glBegin(GL_TRIANGLE_FAN)
        gl.glBegin(gl.GL_QUADS)

        gl.glColor3ub(*color)

        for v in vertexes:
            gl.glVertex3f(*v)
        gl.glEnd()

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

    def gui_objects(self) -> Iterable[int]:
        return [self.gl_lists]

    @property
    def left_bottom_v3(self):
        return self._left_bottom_v3

    @property
    def right_top_v3(self):
        return self._right_top_v3


_FACE_SIZE = 3


# noinspection PyMethodMayBeStatic
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
                 f0: np.ndarray, left_right_direction: ndarray, left_top_direction: ndarray,
                 ) -> None:
        super().__init__()
        self._board: "_Board" = board
        self.cube_face_supplier = cube_face_supplier
        # self.flip_h = flip_h
        # self.flip_v = flip_v
        self.f0: np.ndarray = f0
        self.left_right_direction: ndarray = left_right_direction
        self.left_top_direction: ndarray = left_top_direction

        self._cells: dict[PartFixedID, _Cell] = {p.fixed_id: _Cell(self, batch) for p in cube_face_supplier().parts}

    @property
    def cube_face(self) -> Face:
        return self.cube_face_supplier()

    def set_cell(self, part: Part, vertexes: Sequence[Vec3f], c: _VColor, marker: int) -> None:
        """

        :param part:
        :param marker:
        :param c:
        :param vertexes: four corners of edge
        :return:
        """
        self._cells[part.fixed_id].create_objects(vertexes, c, marker)

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

            l_box = [x.reshape((3,)).tolist() for x in box]

            # convert to gl,
            # but this is waste of time, when calculating center and rotate axis, we again convert to ndarray
            for i in range(len(l_box)):
                l_box[i] = [c_float(l_box[i][0]), c_float(l_box[i][1]), c_float(l_box[i][2])]

            fb.set_cell(p, l_box, face_color, marker)

        _plot_cell(2, 0, f.corner_top_left)
        _plot_cell(2, 1, f.edge_top)
        _plot_cell(2, 2, f.corner_top_right, marker=2)
        _plot_cell(1, 0, f.edge_left)
        _plot_cell(1, 1, f.center)
        _plot_cell(1, 2, f.edge_right)
        _plot_cell(0, 0, f.corner_bottom_left, marker=1)
        _plot_cell(0, 1, f.edge_bottom)
        _plot_cell(0, 2, f.corner_bottom_right)

    def update(self):
        self.draw_init()

    @property
    def cells(self) -> Iterable[_Cell]:
        return self._cells.values()

    def draw(self):
        # need to optimize, no need to change position
        for c in self.cells:
            c.draw()

    @property
    def board(self):
        return self._board

    def gui_objects(self) -> Sequence[int]:
        lists: list[int] = []
        for c in self.cells:
            lists.extend(c.gui_objects())

        return lists

    def get_center(self) -> ndarray:

        face: Face = self.cube_face
        bl: Sequence[c_float] = self._cells[face.corner_bottom_left.fixed_id].left_bottom_v3
        rt: Sequence[c_float] = self._cells[face.corner_top_right.fixed_id].right_top_v3

        _bl = np.array([x.value for x in bl], dtype=float).reshape((3,))
        _rt = np.array([x.value for x in rt], dtype=float).reshape((3,))

        center = (_bl + _rt) / 2

        return center

    def center_and_gui_objects(self) -> Tuple[ndarray, Sequence[int]]:

        return self.get_center(), self.gui_objects()

    def get_part_gui_object(self, p: Part) -> Iterable[int]:
        return self._cells[p.fixed_id].gui_objects()


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
        self._hidden_objects: Set[int] = set()
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

    @property
    def faces(self):
        return self._faces

    def set_hidden(self, lists: Iterable[int]):
        self._hidden_objects = set(lists)

    def get_hidden(self) -> Set[int]:
        return self._hidden_objects

    def unhidden_all(self):
        self._hidden_objects = set()


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
    __slots__ = ["_batch", "_cube", "_board", "_test",
                 "_hidden_objects"]

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
        #_plot_face(b, lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0])

        # OK
        _plot_face(b, lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0])

        # OK
        _plot_face(b, lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0])

        # OK! -2 far away so we can see it
        _plot_face(b, lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0])
        #_plot_face(b, lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0])

        # -05 below so we see it
        _plot_face(b, lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1])
        #_plot_face(b, lambda: cube.down, [0, -0.5, 0], [1, 0, 0], [0, 0, 1])

    def _get_face(self, name: FaceName) -> _FaceBoard:
        for f in self._board.faces:
            if f.cube_face.name == name:
                return f

        assert False

    def _get_faces(self, name: FaceName) -> Iterable[_FaceBoard]:

        for f in self._board.faces:
            if f.cube_face.name == name:
                yield f

    def _get_face_gui_objects(self, f: _FaceBoard) -> Iterable[int]:

        lists: set[int] = set()

        this_face_objects = f.gui_objects()
        lists.update(this_face_objects)

        this_cube_face: Face = f.cube_face

        cube_face_adjusts: Iterable[Face] = this_cube_face.adjusted_faces()

        for adjust in cube_face_adjusts:
            adjust_board: _FaceBoard = self._get_face(adjust.name)
            for p in adjust.parts:
                if p.on_face(this_cube_face):
                    p_lists = adjust_board.get_part_gui_object(p)
                    lists.update(p_lists)

        return lists

    def _get_faces_gui_objects(self, fs: Iterable[_FaceBoard]) -> Iterable[int]:

        lists: set[int] = set()

        for f in fs:
            lists.update(self._get_face_gui_objects(f))

        return lists

    def unhidden_all(self):
        self._board.unhidden_all()

    def get_face_objects(self, name: FaceName, hide: bool = True) -> Tuple[ndarray, ndarray, Sequence[int]]:

        right: _FaceBoard = self._get_face(name)
        left: _FaceBoard = self._get_face(self._cube.face(name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        right_objects: Iterable[int] = self._get_faces_gui_objects(self._get_faces(name))
        left_center: ndarray = left.get_center()

        if hide:
            self._board.set_hidden(right_objects)

        return right_center, left_center, right_objects

    def git_whole_cube_objects(self, axis_name: AxisName, hide: bool = True) -> Tuple[ndarray, ndarray, Sequence[int]]:

        name: FaceName
        match axis_name:

            case AxisName.X:
                name = FaceName.R

            case AxisName.Y:
                name = FaceName.U

            case AxisName.Z:
                name = FaceName.F

            case _:
                raise RuntimeError(f"Unknown Axis {axis_name}")

        right: _FaceBoard = self._get_face(name)
        left: _FaceBoard = self._get_face(self._cube.face(name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        left_center: ndarray = left.get_center()

        objects = set()
        for f in  self._board.faces:
            objects.update(f.gui_objects())

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects
