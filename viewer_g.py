from collections import defaultdict
from collections.abc import Set, Collection
from contextlib import contextmanager
from typing import Hashable, Tuple, MutableSequence, Callable, Iterable, Sequence, Set

import colorama
import numpy as np
import numpy.linalg
import pyglet  # type: ignore
import pyglet.gl as gl  # type: ignore
from numpy import ndarray
from pyglet.gl import *  # type: ignore
from pyglet.graphics import Batch  # type: ignore

import shapes
from cube import Cube
from cube_face import Face
from cube_slice import SliceName
from elements import Color, Part, FaceName, PartFixedID, AxisName, SuperElement, CenterSlice
from elements import Corner, Edge, Center, PartSliceHashID, PartSlice

from view_state import ViewState

_CELL_SIZE: int = 30

_CORNER_SIZE = 0.2

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
        _colors[Color.ORANGE] = (255, 69, 0)  # (255,127,80) # (255, 165, 0)
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
        self._right_top_v3: ndarray | None = None
        self._left_bottom_v3: ndarray | None = None
        self._batch = batch
        self._face_board = face_board
        self._g_polygon: pyglet.shapes.Polygon | None = None
        self._g_lines: Sequence[pyglet.shapes.Line] | None = None
        # noinspection PyProtectedMember
        self._g_markers: Sequence[pyglet.shapes._ShapeBase] | None = None
        # self._create_objects(x0, y0, x1, y1, (255, 255, 255))

        self.gl_lists_movable: dict[PartSliceHashID, MutableSequence[int]] = defaultdict(list)
        self.gl_lists_unmovable: dict[PartSliceHashID, MutableSequence[int]] = defaultdict(list)

    def _clear_gl_lists(self):
        # delete and clear all lists
        for ls in self.gl_lists_movable.values():
            for ll in ls:
                gl.glDeleteLists(ll, 1)
        self.gl_lists_movable.clear()

        for ls in self.gl_lists_unmovable.values():
            for ll in ls:
                gl.glDeleteLists(ll, 1)
        self.gl_lists_unmovable.clear()

    def release_resources(self):
        self._clear_gl_lists()

    # noinspection PyUnusedLocal
    def create_objects(self, part: Part, vertexes: Sequence[ndarray], marker: str):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        marker = ""

        self._left_bottom_v3 = vertexes[0]
        self._right_top_v3 = vertexes[2]

        # delete and clear all lists
        self._clear_gl_lists()

        #         = [gl.glGenLists(1)]
        # print(f"{self.gl_lists=}")

        #       gl.glNewList(self.gl_lists_movable[0], gl.GL_COMPILE)

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(self.gl_lists_movable, part, vertexes)
        # if marker == "M":
        #     self._create_markers(vertexes, (255 - color[0], 255 - color[1], 255 - color[2]), True)

        # self._create_helpers()
        # gl.glEndList()

        # if marker == "F":
        #     self.gl_lists_unmovable = [gl.glGenLists(1)]
        #     gl.glNewList(self.gl_lists_unmovable[0], gl.GL_COMPILE)
        #     self._create_markers(vertexes, (255 - color[0], 255 - color[1], 255 - color[2]), True)
        #     gl.glEndList()

    def draw(self):

        lists: Sequence[int] = [ll for m in [self.gl_lists_movable, self.gl_lists_unmovable]
                                for ls in m.values() for ll in ls]

        if not lists:
            print(f"Error no gl lists in {self}")
            return

        hidden = self._face_board.board.get_hidden()

        if all(ll in hidden for ll in lists):
            return

        self._prepare_view_state()
        for ll in lists:
            if ll not in hidden:
                glCallList(ll)
        self._restore_view_state()

    def _prepare_view_state(self):

        vs: ViewState = self._face_board.board.vs
        vs.prepare_objects_view()

    def _restore_view_state(self):

        vs: ViewState = self._face_board.board.vs
        vs.restore_objects_view()

    @contextmanager
    def _gen_list_for_slice(self, p_slice: PartSlice, dest: dict[PartSliceHashID, MutableSequence[int]]):
        g_list = gl.glGenLists(1)

        gl.glNewList(g_list, gl.GL_COMPILE)

        try:
            yield None
        finally:
            gl.glEndList()

            dest[p_slice.fixed_id].append(g_list)

    def _slice_color(self, _slice: PartSlice):

        face = self._face_board.cube_face

        c: Color = _slice.get_face_edge(face).color

        slice_color = _color_2_v_color(c)

        return slice_color

    # noinspection PyMethodMayBeStatic
    def _create_polygon(self, dest: dict[PartSliceHashID, MutableSequence[int]],
                        part: Part,
                        vertexes: Sequence[ndarray]):

        # vertex = [left_bottom, right_bottom, right_top, left_top]

        lc = (0, 0, 0)
        lw = 4
        cross_width = 5
        cross_width_x = 8
        cross_width_y = 2
        cross_color = (0, 0, 0)
        cross_color_x = (138, 43, 226)  # blueviolet	#8A2BE2	rgb(138,43,226)
        cross_color_y = (0, 191, 255)  # deepskyblue	#00BFFF	rgb(0,191,255)

        n: int = part.cube.n_slices

        fb: _FaceBoard = self._face_board
        cube_face: Face = fb.cube_face

        if isinstance(part, Corner):

            corner_slice = part.slice
            with self._gen_list_for_slice(corner_slice, dest):
                shapes.quad_with_line(vertexes,
                                      self._slice_color(corner_slice),
                                      lw, lc)
                if cube_face.corner_bottom_left is part:
                    shapes.cross(vertexes, cross_width, cross_color)
                elif cube_face.corner_bottom_right is part:
                    shapes.cross(vertexes, cross_width_x, cross_color_x)
                if cube_face.corner_top_left is part:
                    shapes.cross(vertexes, cross_width_y, cross_color_y)


        elif isinstance(part, Edge):
            # shapes.quad_with_line(vertexes, color, lw, lc)

            n = part.n_slices

            left_bottom = vertexes[0]
            right_bottom = vertexes[1]
            if part is cube_face.edge_left or part is cube_face.edge_right:

                left_top = vertexes[3]

                d = (left_top - left_bottom) / n

                for i in range(n):
                    ix = i

                    _slice = part.get_ltr_index(cube_face, ix)
                    color = self._slice_color(_slice)
                    with self._gen_list_for_slice(_slice, dest):
                        vx = [left_bottom, right_bottom,
                              right_bottom + d, left_bottom + d]
                        shapes.quad_with_line(vx, color, lw, lc)
                        nn: int = _slice.get_face_edge(cube_face).c_attributes["n"]
                        shapes.lines_in_quad(vx, nn, 5, (138, 43, 226))
                        # if _slice.get_face_edge(cube_face).attributes["origin"]:
                        #     shapes.cross(vx, cross_width, cross_color)
                        # if _slice.get_face_edge(cube_face).attributes["on_x"]:
                        #     shapes.cross(vx, cross_width_x, cross_color_x)
                        # if _slice.get_face_edge(cube_face).attributes["on_y"]:
                        #     shapes.cross(vx, cross_width_y, cross_color_y)

                    left_bottom += d
                    right_bottom += d

            else:  # top or bottom

                left_top = vertexes[3]
                d = (right_bottom - left_bottom) / n

                # if is_back:
                #     d = -d

                for i in range(n):
                    ix = i  # _inv(i, is_back)
                    _slice = part.get_ltr_index(cube_face, ix)
                    color = self._slice_color(_slice)
                    with self._gen_list_for_slice(_slice, dest):
                        vx = [left_bottom,
                              left_bottom + d,
                              left_top + d,
                              left_top]
                        shapes.quad_with_line(vx, color, lw, lc)
                        nn: int = _slice.get_face_edge(cube_face).c_attributes["n"]
                        shapes.lines_in_quad(vx, nn, 5, (138, 43, 226))
                        # if _slice.get_face_edge(cube_face).attributes["origin"]:
                        #     shapes.cross(vx, cross_width, cross_color)
                        # if _slice.get_face_edge(cube_face).attributes["on_x"]:
                        #     shapes.cross(vx, cross_width_x, cross_color_x)
                        # if _slice.get_face_edge(cube_face).attributes["on_y"]:
                        #     shapes.cross(vx, cross_width_y, cross_color_y)

                    left_bottom += d
                    left_top += d

        else:
            assert isinstance(part, Center)
            # shapes.quad_with_line(vertexes, color, 4, (0, 0, 1))
            n = part.n_slices

            lb = vertexes[0]
            rb = vertexes[1]
            lt = vertexes[3]
            dx = (rb - lb) / n
            dy = (lt - lb) / n
            for x in range(n):
                for y in range(n):

                    ix = x
                    iy = y

                    # ix = _inv(ix, is_back)

                    _slice: CenterSlice = part.get_slice((iy, ix))

                    color = self._slice_color(_slice)
                    with self._gen_list_for_slice(_slice, dest):
                        vx = [lb + x * dx + y * dy,
                              lb + (x + 1) * dx + y * dy,
                              lb + (x + 1) * dx + (y + 1) * dy,
                              lb + x * dx + (y + 1) * dy]

                        edge = _slice.get_face_edge(cube_face)
                        attributes = edge.attributes
                        shapes.quad_with_line(vx, color, lw, lc)

                        if attributes["origin"]:
                            shapes.cross(vx, cross_width, cross_color)
                        if attributes["on_x"]:
                            shapes.cross(vx, cross_width_x, cross_color_x)
                        if attributes["on_y"]:
                            shapes.cross(vx, cross_width_y, cross_color_y)

                        if _slice.edge.c_attributes["annotation"]:
                            self._create_markers(vx, (0, 0, 0), True)

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

    def _create_markers(self, vertexes: Sequence[ndarray], color, marker: bool):

        if not marker:
            return

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        ortho_dir: ndarray = self._face_board.ortho_direction
        norm = np.linalg.norm(ortho_dir)
        ortho_dir /= norm

        vx = vertexes

        gl.glLineWidth(3)
        gl.glColor3ub(*color)

        center = (vx[0] + vx[2]) / 2

        # a unit vectors
        v1: list[ndarray] = [(v - center) / numpy.linalg.norm(v - center) for v in vx]

        # [left_bottom3, right_bottom3, right_top3, left_top3]
        bottom: list[ndarray] = []
        top: list[ndarray] = []

        _face_size = np.linalg.norm(vertexes[0] - vertexes[2])

        height = 2
        half_bottom_size = _face_size * 0.8 / 2.0
        half_top_size = _face_size * 0.5 / 2.0

        for v in v1:
            p = center + v * half_bottom_size
            bottom.append(p)
            p = center + height * ortho_dir + v * half_top_size
            top.append(p)

        shapes.box_with_lines(bottom, top, color, 3, (0, 0, 0))

    def gui_movable_gui_objects(self) -> Iterable[int]:
        return [ll for ls in self.gl_lists_movable.values() for ll in ls]

    def gui_slice_movable_gui_objects(self, _slice: PartSlice) -> Iterable[int]:

        _id = _slice.fixed_id

        d: dict[frozenset[FaceName], MutableSequence[int]] = self.gl_lists_movable

        # does it work for default dict ?
        sl = d.get(_id, None)
        if not sl:
            return
        else:
            yield from sl

    @property
    def left_bottom_v3(self) -> ndarray:
        assert self._left_bottom_v3 is not None
        return self._left_bottom_v3

    @property
    def right_top_v3(self) -> ndarray:
        assert self._right_top_v3 is not None
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
                 ortho_direction: ndarray
                 ) -> None:
        super().__init__()
        self._batch = batch
        self._board: "_Board" = board
        self.cube_face_supplier = cube_face_supplier
        # self.flip_h = flip_h
        # self.flip_v = flip_v
        self.f0: np.ndarray = f0
        self.left_right_direction: ndarray = left_right_direction
        self.left_top_direction: ndarray = left_top_direction
        self._ortho_direction: ndarray = ortho_direction

        self._cells: dict[PartFixedID, _Cell] = {}

        self.reset()

    def reset(self):

        c: _Cell
        for c in self._cells.values():
            c.release_resources()

        self._cells: dict[PartFixedID, _Cell] = {p.fixed_id: _Cell(self, self._batch) for p in
                                                 self.cube_face_supplier().parts}

    @property
    def cube_face(self) -> Face:
        return self.cube_face_supplier()

    # noinspection PyUnusedLocal

    def draw_init(self):

        f: Face = self.cube_face

        def _plot_cell(cy: int, cx: int, part: Part):

            left_bottom3, left_top3, right_bottom3, right_top3 = self._calc_cell_quad_coords(part, cx, cy)

            box: MutableSequence[np.ndarray] = [left_bottom3, right_bottom3, right_top3, left_top3]

            # why it is needed
            l_box = [x.reshape((3,)) for x in box]

            # # convert to gl,
            # # but this is waste of time, when calculating center and rotate axis, we again convert to ndarray
            # for i in range(len(l_box)):
            #     l_box[i] = [c_float(l_box[i][0]), c_float(l_box[i][1]), c_float(l_box[i][2])]

            _marker = ""
            if part.annotated_by_color:
                _marker = "M"
            elif part.annotated_fixed:
                _marker = "F"

            self._cells[part.fixed_id].create_objects(part, l_box, _marker)

        _plot_cell(2, 0, f.corner_top_left)
        _plot_cell(2, 1, f.edge_top)
        _plot_cell(2, 2, f.corner_top_right)
        _plot_cell(1, 0, f.edge_left)
        _plot_cell(1, 1, f.center)
        _plot_cell(1, 2, f.edge_right)
        _plot_cell(0, 0, f.corner_bottom_left)
        _plot_cell(0, 1, f.edge_bottom)
        _plot_cell(0, 2, f.corner_bottom_right)

    def _calc_cell_quad_coords(self, part: Part, cx, cy):

        face_size: float = _CELL_SIZE * 3.0

        corner_size: float = face_size * _CORNER_SIZE
        center_size = face_size - 2 * corner_size

        cell_width: float
        cell_height: float

        x0: float
        y0: float

        if isinstance(part, Corner):
            # cx = 0 | 2
            # cy = 0 | 2
            x0 = cx / 2.0 * (corner_size + center_size)
            x1 = x0 + corner_size  # corner_size or face_size

            y0 = cy / 2.0 * (corner_size + center_size)
            y1 = y0 + corner_size  # edge_with or face_size
        elif isinstance(part, Edge):
            # cx, cy:
            #  0, 1 - left     x= 0, corner  y = corner, corner+center
            #  2, 1 - right    x= corner + center, corner + center + corner
            #  1, 0 - bottom   x = corner
            #  1, 2 - up
            match (cx, cy):
                case (0, 1):  # left
                    x0 = 0
                    x1 = x0 + corner_size
                    y0 = corner_size
                    y1 = y0 + center_size
                case (2, 1):  # right
                    x0 = face_size - corner_size
                    x1 = face_size
                    y0 = corner_size
                    y1 = y0 + center_size

                case (1, 0):  # bottom
                    x0 = corner_size
                    x1 = x0 + center_size
                    y0 = 0
                    y1 = y0 + corner_size

                case (1, 2):  # top
                    x0 = corner_size
                    x1 = x0 + center_size
                    y0 = face_size - corner_size
                    y1 = face_size

                case _:
                    assert False

        else:
            assert isinstance(part, Center)
            x0 = corner_size
            x1 = x0 + center_size

            y0 = corner_size
            y1 = y0 + center_size

        l_r_d = self.left_right_direction
        l_t_d = self.left_top_direction
        left_bottom3 = self.f0 + l_r_d * x0 + l_t_d * y0

        right_bottom3 = self.f0 + l_r_d * x1 + l_t_d * y0

        right_top3 = self.f0 + l_r_d * x1 + l_t_d * y1

        left_top3 = self.f0 + l_r_d * x0 + l_t_d * y1

        return left_bottom3, left_top3, right_bottom3, right_top3

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
            lists.extend(c.gui_movable_gui_objects())

        return lists

    def get_center(self) -> ndarray:

        face: Face = self.cube_face
        bl: ndarray = self._cells[face.corner_bottom_left.fixed_id].left_bottom_v3
        rt: ndarray = self._cells[face.corner_top_right.fixed_id].right_top_v3

        _bl = bl
        _rt = rt

        center = (_bl + _rt) / 2

        return center

    def center_and_gui_objects(self) -> Tuple[ndarray, Sequence[int]]:

        return self.get_center(), self.gui_objects()

    def get_part_gui_object(self, p: Part) -> Iterable[int]:
        return self._cells[p.fixed_id].gui_movable_gui_objects()

    def get_cell(self, _id: PartFixedID) -> _Cell:
        return self._cells[_id]

    @property
    def ortho_direction(self) -> ndarray:
        return self._ortho_direction


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

        # why sequence, because we can have multiple back faces
        self._cells: dict[PartFixedID, MutableSequence[_Cell]] = dict()

    def reset(self):
        for f in self._faces:
            f.reset()

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def create_face(self, cube_face: Callable[[], Face],
                    f0: ndarray,
                    left_right_direction: ndarray,
                    left_top_direction: ndarray,
                    ortho_direction: ndarray):
        f = _FaceBoard(self, cube_face, self.batch, f0, left_right_direction, left_top_direction, ortho_direction)
        self._faces.append(f)
        return f

    def finish_faces(self):

        cells: dict[PartFixedID:list[_Cell]] = defaultdict(list)

        for fb in self._faces:

            f: Face = fb.cube_face
            for p in f.parts:
                _id = p.fixed_id
                cell: _Cell = fb.get_cell(_id)
                cells[_id].append(cell)

        self._cells = cells

    def get_cells(self, _id: PartFixedID) -> Sequence[_Cell]:
        """
        PArt can appear more than none due to multiple faces
        :param _id: 
        :return: 
        """
        return self._cells[_id]

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

    # todo: to delete
    def get_all_cells_gui_elements(self, element: SuperElement) -> Set[int]:

        lists: set[int] = set()

        # need to optimize !!!
        for s in element.slices:

            c: _Cell
            for cs in self._cells.values():
                for c in cs:
                    lists.update(c.gui_slice_movable_gui_objects(s))

        return lists

    def get_all_gui_elements(self, for_parts: Collection[PartSlice]) -> Set[int]:

        lists: set[int] = set()

        # need otpimization !!!
        c: _Cell
        for cs in self._cells.values():
            for c in cs:
                for s in for_parts:
                    lists.update(c.gui_slice_movable_gui_objects(s))

        return lists


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
               orthogonal_direction: list[int]
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

    _ortho: ndarray = np.array(orthogonal_direction, dtype=float).reshape((3,))

    fb: _FaceBoard = b.create_face(f, f0, _left_right_d, _left_top_d, _ortho)

    fb.draw_init()


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board", "_test",
                 "_hidden_objects", "_vs"]

    def __init__(self, batch: Batch, cube: Cube, vs: ViewState) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch
        self._vs = vs

        #        self._test = pyglet.shapes.Line(0, 0, 20, 20, width=10, color=(255, 255, 255), batch=batch)

        self._board: _Board = _Board(self._batch, vs)

        self._init_gui()

    def update(self):
        self._board.update()

    def draw(self):
        self._board.draw()

    def reset(self):
        self._board.reset()
        self._init_gui()

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

        _plot_face(b, lambda: cube.up, [0, 1, 1], [1, 0, 0], [0, 0, -1], [0, 1, 0])

        _plot_face(b, lambda: cube.left, [-0, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])
        if self._vs.draw_shadows:
            # -0.75 from it x location, so we can see it in isometric view
            _plot_face(b, lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])

        _plot_face(b, lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1])

        _plot_face(b, lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0], [1, 0, 0])

        _plot_face(b, lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0], [0, 0, -1])
        if self._vs.draw_shadows:
            # -2 far away so we can see it
            _plot_face(b, lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0], [0, 0, -1])

        _plot_face(b, lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])
        if self._vs.draw_shadows:
            # -05 below so we see it
            _plot_face(b, lambda: cube.down, [0, -0.5, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])

        self._board.finish_faces()

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

    # todo:cleanup: delete
    def git_slice_objects(self, slice_name, hide=True) -> Tuple[ndarray, ndarray, Iterable[int]]:

        face_name: FaceName

        match slice_name:

            case SliceName.S:  # over F
                face_name = FaceName.F

            case SliceName.M:  # over R
                face_name = FaceName.R

            case SliceName.E:  # over D
                face_name = FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {slice_name}")

        right: _FaceBoard = self._get_face(face_name)
        left: _FaceBoard = self._get_face(self._cube.face(face_name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        left_center: ndarray = left.get_center()

        objects: set[int] = set()

        objects.update(self._board.get_all_cells_gui_elements(self._cube.get_slice(slice_name)))

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects

    def get_slices_movable_gui_objects(self, face_name_rotate_axis: FaceName,
                                       cube_parts: Collection[PartSlice],
                                       hide=True) -> Tuple[ndarray, ndarray, Iterable[int]]:

        face_name: FaceName = face_name_rotate_axis

        right: _FaceBoard = self._get_face(face_name)
        left: _FaceBoard = self._get_face(self._cube.face(face_name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        left_center: ndarray = left.get_center()

        objects: set[int] = set()

        objects.update(self._board.get_all_gui_elements(cube_parts))

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects
