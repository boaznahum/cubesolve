import sys
from collections import defaultdict
from collections.abc import Sequence, MutableSequence, Iterable
from contextlib import contextmanager
from typing import Tuple, TYPE_CHECKING

import numpy as np
import pyglet  # type: ignore
from numpy import ndarray
from pyglet import gl
from pyglet.graphics import Batch  # type: ignore

import config
from app_state import AppState
from model.cube_boy import Color, FaceName
from model.cube_face import Face
from model.elements import PartSliceHashID, PartEdge, Part, PartSlice, Corner, Edge, EdgeSlice, Center, CenterSlice
from viewer import shapes

_CELL_SIZE: int = config.CELL_SIZE

_CORNER_SIZE = config.CORNER_SIZE

_VColor = Tuple[int, int, int]

if TYPE_CHECKING:
    from ._faceboard import _FaceBoard


_inited = False

_colors: dict[Color, _VColor] = {}


def _color_2_v_color(c: Color) -> _VColor:
    global _inited
    global _colors

    if not _inited:

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

        # the boxes of the part PartEdge
        #  # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]
        self.facets: dict[PartEdge, Sequence[ndarray]] = {}

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
        self.facets.clear()

    # noinspection PyUnusedLocal
    def create_objects(self, part: Part, vertexes: Sequence[ndarray], marker: str):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        marker = ""

        self._left_bottom_v3 = vertexes[0]
        self._right_top_v3 = vertexes[2]

        # delete and clear all lists
        self._clear_gl_lists()
        self.facets.clear()

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(self.gl_lists_movable, part, vertexes)

    def draw(self):

        # self.gl_lists_movable: dict[PartSliceHashID, MutableSequence[int]] = defaultdict(list)
        m: dict[frozenset[FaceName], MutableSequence[int]]
        lists: Sequence[int] = [ll for m in [self.gl_lists_movable, self.gl_lists_unmovable]
                                for ls in m.values() for ll in ls]

        if not lists:
            print(f"Error no gl lists in {self}", file=sys.stderr)
            return

        hidden = self._face_board.board.get_hidden()

        if all(ll in hidden for ll in lists):
            return

        self._prepare_view_state()
        for ll in lists:
            if ll not in hidden:
                gl.glCallList(ll)

        # vs: ViewState = self._face_board.board.vs
        #
        # # [left_bottom, right_bottom, right_top, left_top]
        # tx = vs.tx
        # ty = vs.ty
        # tz = vs.tz
        # p0 = np.array([tx, ty, tz])
        # lx = np.array([1.0, 0.0, 0.0]) * 10
        # ly = np.array([0.0, 1.0, 0.0]) * 10
        #
        # shapes.quad_with_line( [p0, p0 + lx, p0 + lx + ly , p0 + ly],(0, 0, 0), 10, (255, 0, 0))

        self._restore_view_state()

    def get_all_gui_elements(self, dest: set[int]):
        m: dict[frozenset[FaceName], MutableSequence[int]]
        lists: Sequence[int] = [ll for m in [self.gl_lists_movable, self.gl_lists_unmovable]
                                for ls in m.values() for ll in ls]

        if not lists:
            print(f"Error no gl lists in {self}", file=sys.stderr)
            return

        dest.update(lists)

    def _prepare_view_state(self):

        vs: AppState = self._face_board.board.vs
        vs.prepare_objects_view()

    def _restore_view_state(self):

        vs: AppState = self._face_board.board.vs
        vs.restore_objects_view()

    @contextmanager
    def _gen_list_for_slice(self, p_slice: PartSlice, dest: dict[PartSliceHashID, MutableSequence[int]]):
        """
        Generate new gl list and on exit add this list to slice
        :param p_slice:
        :param dest:
        :return:
        """
        g_list = gl.glGenLists(1)

        gl.glNewList(g_list, gl.GL_COMPILE)

        try:
            yield None
        finally:
            gl.glEndList()

            dest[p_slice.fixed_id].append(g_list)

    def _get_slice_edge(self, _slice):
        face = self._face_board.cube_face
        edge = _slice.get_face_edge(face)
        return edge

    def _slice_color(self, _slice: PartSlice):

        edge = self._get_slice_edge(_slice)

        c: Color = edge.color

        slice_color = _color_2_v_color(c)

        return slice_color

    # noinspection PyMethodMayBeStatic
    def _create_polygon(self, g_list_dest: dict[PartSliceHashID, MutableSequence[int]],
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

        from ._faceboard import _FaceBoard
        fb: _FaceBoard = self._face_board
        cube_face: Face = fb.cube_face

        if isinstance(part, Corner):

            corner_slice = part.slice
            with self._gen_list_for_slice(corner_slice, g_list_dest):
                shapes.quad_with_line(vertexes,
                                      self._slice_color(corner_slice),
                                      lw, lc)

                self.facets[self._get_slice_edge(corner_slice)] = vertexes

                if config.GUI_DRAW_MARKERS:
                    if cube_face.corner_bottom_left is part:
                        shapes.cross(vertexes, cross_width, cross_color)
                    elif cube_face.corner_bottom_right is part:
                        shapes.cross(vertexes, cross_width_x, cross_color_x)
                    if cube_face.corner_top_left is part:
                        shapes.cross(vertexes, cross_width_y, cross_color_y)


        elif isinstance(part, Edge):
            # shapes.quad_with_line(vertexes, color, lw, lc)

            n = part.n_slices

            nn: int
            left_bottom = vertexes[0]
            right_bottom = vertexes[1]
            if part is cube_face.edge_left or part is cube_face.edge_right:

                left_top = vertexes[3]

                d = (left_top - left_bottom) / n

                for i in range(n):
                    ix = i

                    _slice: EdgeSlice = part.get_slice_by_ltr_index(cube_face, ix)
                    color = self._slice_color(_slice)
                    with self._gen_list_for_slice(_slice, g_list_dest):
                        vx = [left_bottom, right_bottom,
                              right_bottom + d, left_bottom + d]

                        self.facets[self._get_slice_edge(_slice)] = vx

                        shapes.quad_with_line(vx, color, lw, lc)

                        if config.GUI_DRAW_MARKERS:
                            nn = _slice.get_face_edge(cube_face).c_attributes["n"]
                            shapes.lines_in_quad(vx, nn, 5, (138, 43, 226))
                        # if _slice.get_face_edge(cube_face).attributes["origin"]:
                        #     shapes.cross(vx, cross_width, cross_color)
                        # if _slice.get_face_edge(cube_face).attributes["on_x"]:
                        #     shapes.cross(vx, cross_width_x, cross_color_x)
                        # if _slice.get_face_edge(cube_face).attributes["on_y"]:
                        #     shapes.cross(vx, cross_width_y, cross_color_y)

                        if self._get_slice_edge(_slice).c_attributes["annotation"]:
                            self._create_markers(vx, color, (0, 0, 0), True)

                    # do not iadd, we keep references to thes coordinates
                    left_bottom = left_bottom + d
                    right_bottom = right_bottom + d

            else:  # top or bottom

                left_top = vertexes[3]
                d = (right_bottom - left_bottom) / n

                # if is_back:
                #     d = -d

                for i in range(n):
                    ix = i  # _inv(i, is_back)
                    _slice = part.get_slice_by_ltr_index(cube_face, ix)
                    color = self._slice_color(_slice)
                    with self._gen_list_for_slice(_slice, g_list_dest):
                        vx = [left_bottom,
                              left_bottom + d,
                              left_top + d,
                              left_top]

                        self.facets[self._get_slice_edge(_slice)] = vx
                        shapes.quad_with_line(vx, color, lw, lc)
                        if config.GUI_DRAW_MARKERS:
                            nn = _slice.get_face_edge(cube_face).c_attributes["n"]
                            shapes.lines_in_quad(vx, nn, 5, (138, 43, 226))

                        if self._get_slice_edge(_slice).c_attributes["annotation"]:
                            self._create_markers(vx, color, (0, 0, 0), True)

                        # if _slice.get_face_edge(cube_face).attributes["origin"]:
                        #     shapes.cross(vx, cross_width, cross_color)
                        # if _slice.get_face_edge(cube_face).attributes["on_x"]:
                        #     shapes.cross(vx, cross_width_x, cross_color_x)
                        # if _slice.get_face_edge(cube_face).attributes["on_y"]:
                        #     shapes.cross(vx, cross_width_y, cross_color_y)

                    # do not iadd, we keep references to thes coordinates
                    left_bottom = left_bottom + d
                    left_top = left_top + d

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

                    center_slice: CenterSlice = part.get_slice((iy, ix))

                    color = self._slice_color(center_slice)
                    with self._gen_list_for_slice(center_slice, g_list_dest):
                        vx = [lb + x * dx + y * dy,
                              lb + (x + 1) * dx + y * dy,
                              lb + (x + 1) * dx + (y + 1) * dy,
                              lb + x * dx + (y + 1) * dy]

                        edge = center_slice.get_face_edge(cube_face)
                        attributes = edge.attributes
                        shapes.quad_with_line(vx, color, lw, lc)

                        if config.GUI_DRAW_MARKERS:
                            if attributes["origin"]:
                                shapes.cross(vx, cross_width, cross_color)
                            if attributes["on_x"]:
                                shapes.cross(vx, cross_width_x, cross_color_x)
                            if attributes["on_y"]:
                                shapes.cross(vx, cross_width_y, cross_color_y)

                        if center_slice.edge.c_attributes["annotation"]:
                            self._create_markers(vx, color, (0, 0, 0), True)

    # noinspection PyMethodMayBeStatic
    def _create_lines(self, vertexes, color):

        gl.glPushAttrib(gl.GL_LINE_WIDTH)
        gl.glLineWidth(4)

        gl.glColor3ub(*color)

        for i in range(len(vertexes) - 1):
            gl.glBegin(gl.GL_LINES)
            gl.glVertex3f(*vertexes[i])
            gl.glVertex3f(*vertexes[i + 1])
            gl.glEnd()

        gl.glPopAttrib()

    # noinspection PyMethodMayBeStatic
    def _create_helpers(self):
        """
        For debug
        :return:
        """

        gl.glPushAttrib(gl.GL_LINE_WIDTH)
        gl.glLineWidth(6)

        gl.glBegin(gl.GL_LINES)

        # parallel to X axis with offset on z/y
        gl.glColor3ub(255, 255, 255)
        gl.glVertex3f(0, 0, 50)
        gl.glVertex3f(200, 0, 50)
        gl.glVertex3f(0, 50, 0)
        gl.glVertex3f(200, 50, 0)

        # the problematic one, the one on X
        gl.glColor3ub(255, 255, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(50, 0, 0)

        gl.glEnd()

        # parallel to Y axis with offset on x/z
        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(255, 0, 0)
        gl.glVertex3f(50, 0, 0)
        gl.glVertex3f(50, 200, 0)
        gl.glVertex3f(0, 0, 50)
        gl.glVertex3f(0, 200, 50)
        gl.glEnd()

        # line parallel to Z axis , with offset on X
        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(0, 255, 255)
        gl.glVertex3f(50, 0, 0)
        gl.glVertex3f(50, 0, 200)
        gl.glEnd()

        gl.glPopAttrib()  # line width

    def _create_markers_box(self, vertexes: Sequence[ndarray], color, marker: bool):

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
        v1: list[ndarray] = [(v - center) / np.linalg.norm(v - center) for v in vx]

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

    def _create_markers(self, vertexes: Sequence[ndarray], facet_color, color, marker: bool):

        if not marker:
            return

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]
        vx = vertexes

        center = (vx[0] + vx[2]) / 2

        l1: float = np.linalg.norm(vertexes[0] - vertexes[1])  # type: ignore
        l2: float = np.linalg.norm(vertexes[0] - vertexes[3])  # type: ignore
        _face_size = min([l1, l2])

        radius = _face_size / 2.0 * 0.8
        radius = min([radius, config.MAX_MARKER_RADIUS])

        # print(f"{radius=}")

        color = config.MARKER_COLOR

        # this is also supported by glCallLine
        shapes.sphere(center, radius, color)

        # # gluSphere( GLUquadric* ( quad ) , GLdouble ( radius ) , GLint ( slices ) , GLint ( stacks ) )-> void
        # gl.glMatrixMode(gl.GL_MODELVIEW)
        # gl.glPushMatrix()
        # gl.glTranslatef(center[0], center[1], center[2])
        # _sphere = glu.gluNewQuadric()
        # # gluSphere(GLUquadric * (quad), GLdouble(radius), GLint(slices), GLint(stacks))-> void
        # gl.glColor3ub(*color)
        # glu.gluSphere(_sphere, radius, 25, 25)
        # glu.gluDeleteQuadric(_sphere)
        # gl.glPopMatrix()

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
