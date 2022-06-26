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

from .. import config
from cube.app_state import ApplicationAndViewState
from cube.model.cube_boy import Color, FaceName
from cube.model.cube_face import Face
from cube.model.elements import PartSliceHashID, PartEdge, Part, PartSlice, Corner, Edge, EdgeSlice, Center, CenterSlice
from cube.utils import geometry
from . import shapes
from .viewer_markers import VIEWER_ANNOTATION_KEY, VMarker

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


class _RectGeometry:
    _two_d_draw_rect: Sequence[ndarray]  # [left_bottom, right_bottom, right_top, left_top]
    three_d_search_box: Tuple[Sequence[ndarray], Sequence[ndarray]]

    def __init__(self, two_d_rect: Sequence[ndarray], ortho_dir: ndarray) -> None:
        self._two_d_draw_rect = two_d_rect
        for v in two_d_rect:
            v.flags.writeable = False

        norm = np.linalg.norm(ortho_dir)
        ortho_dir /= norm

        ortho_dir *= 2

        self._bottom_quad = [p - ortho_dir for p in two_d_rect]
        self._top_quad = [p + ortho_dir for p in two_d_rect]

    @property
    def two_d_draw_rect(self) -> Sequence[ndarray]:
        return self._two_d_draw_rect

    @property
    def box_bottom(self) -> Sequence[ndarray]:
        return self._bottom_quad

    @property
    def box_top(self) -> Sequence[ndarray]:
        return self._top_quad

    def in_box(self, x, y, z):
        return geometry.in_box(x, y, z, self._bottom_quad, self._top_quad)


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
        self.facets: dict[PartEdge, _RectGeometry] = {}
        # noinspection PyTypeChecker
        self.cell_geometry: _RectGeometry = None  # type: ignore

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
    def prepare_geometry(self, part: Part, vertexes: Sequence[ndarray]):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        marker = ""

        self._left_bottom_v3 = vertexes[0]
        self._right_top_v3 = vertexes[2]

        self.cell_geometry = _RectGeometry(vertexes, self._face_board.ortho_direction)

        # delete and clear all lists
        self._clear_gl_lists()
        self.facets.clear()

        self._part: Part = part

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._create_polygon(self.gl_lists_movable, part, vertexes)

    def update_drawing(self):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        # delete and clear all lists
        self._clear_gl_lists()

        # vertexes = [(x0, y0), (x1, y0), [x1, y1], [x0, y1], [x0, y0]]
        self._update_polygon(self.gl_lists_movable, True)
        self._update_polygon(self.gl_lists_unmovable, False)

    def get_all_gui_elements(self, dest: set[int]):
        m: dict[frozenset[FaceName], MutableSequence[int]]

        dicts: list[dict[PartSliceHashID, MutableSequence[int]]] = [self.gl_lists_movable, self.gl_lists_unmovable]

        # when we try to use values() pycharm complains
        lists: Sequence[int] = [ll for m in dicts
                                for _, ls in m.items() for ll in ls]

        if not lists:
            print(f"Error no gl lists in {self}", file=sys.stderr)
            return

        dest.update(lists)

    def _prepare_view_state(self):

        vs: ApplicationAndViewState = self._face_board.board.vs
        vs.prepare_objects_view()

    def _restore_view_state(self):

        vs: ApplicationAndViewState = self._face_board.board.vs
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

    def _get_slice_edge(self, _slice) -> PartEdge:
        face = self._face_board.cube_face
        edge = _slice.get_face_edge(face)
        return edge

    # to do remove - use edge color
    def _slice_color(self, _slice: PartSlice):

        edge = self._get_slice_edge(_slice)

        c: Color = edge.color

        slice_color = _color_2_v_color(c)

        return slice_color

    def _edge_color(self, edge: PartEdge):

        c: Color = edge.color

        slice_color = _color_2_v_color(c)

        return slice_color

    # noinspection PyMethodMayBeStatic
    def _create_polygon(self, g_list_dest: dict[PartSliceHashID, MutableSequence[int]],
                        part: Part,
                        vertexes: Sequence[ndarray]):

        # vertex = [left_bottom, right_bottom, right_top, left_top]

        # xlc = (0, 0, 0)
        # lxw = 4

        from ._faceboard import _FaceBoard
        fb: _FaceBoard = self._face_board
        cube_face: Face = fb.cube_face

        if isinstance(part, Corner):

            corner_slice = part.slice
            with self._gen_list_for_slice(corner_slice, g_list_dest):

                crg: _RectGeometry = _RectGeometry(vertexes, self._face_board.ortho_direction)

                self.facets[self._get_slice_edge(corner_slice)] = crg



        elif isinstance(part, Edge):
            # shapes.quad_with_line(vertexes, color, lw, lc)

            n = part.n_slices

            nn: int
            left_bottom = vertexes[0]
            right_bottom = vertexes[1]
            left_top = vertexes[3]

            if part is cube_face.edge_left or part is cube_face.edge_right:
                is_left_right = True
                d = (left_top - left_bottom) / n
            else:
                is_left_right = False
                d = (right_bottom - left_bottom) / n

            for i in range(n):
                ix = i

                _slice: EdgeSlice = part.get_slice_by_ltr_index(cube_face, ix)
                with self._gen_list_for_slice(_slice, g_list_dest):

                    # set a rect and advanced to the next one
                    if is_left_right:

                        vx = [left_bottom,
                              right_bottom,
                              right_bottom + d,
                              left_bottom + d]

                        # be aware of += - you kept references to them
                        left_bottom = left_bottom + d
                        right_bottom = right_bottom + d
                    else:
                        vx = [left_bottom,
                              left_bottom + d,
                              left_top + d,
                              left_top]
                        left_bottom = left_bottom + d
                        left_top = left_top + d

                    erg: _RectGeometry = _RectGeometry(vx, self._face_board.ortho_direction)

                    self.facets[self._get_slice_edge(_slice)] = erg




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

                        center_rg: _RectGeometry = _RectGeometry(vx, self._face_board.ortho_direction)
                        self.facets[edge] = center_rg

    def _update_polygon(self, g_list_dest: dict[PartSliceHashID, MutableSequence[int]], movable: bool):

        # vertex = [left_bottom, right_bottom, right_top, left_top]

        lc = (0, 0, 0)
        lw = 4
        cross_width = 5
        cross_width_x = 8
        cross_width_y = 2
        cross_color = (0, 0, 0)
        cross_color_x = (138, 43, 226)  # blueviolet	#8A2BE2	rgb(138,43,226)
        cross_color_y = (0, 191, 255)  # deepskyblue	#00BFFF	rgb(0,191,255)

        annotation_key = VIEWER_ANNOTATION_KEY

        from ._faceboard import _FaceBoard
        fb: _FaceBoard = self._face_board
        cube_face: Face = fb.cube_face

        part: Part = self._part

        n: int = part.n_slices

        markers: dict[str, Tuple[int, int, int]] = config.MARKERS

        def draw_facet(part_edge: PartEdge, _vx):

            # vertex = [left_bottom, right_bottom, right_top, left_top]

            _color = self._edge_color(part_edge)

            if movable:
                shapes.quad_with_line(_vx, _color, lw, lc)

                if config.GUI_DRAW_MARKERS:
                    nn = part_edge.c_attributes["n"]
                    shapes.lines_in_quad(_vx, nn, 5, (138, 43, 226))

            # if _slice.get_face_edge(cube_face).attributes["origin"]:
            #     shapes.cross(vx, cross_width, cross_color)
            # if _slice.get_face_edge(cube_face).attributes["on_x"]:
            #     shapes.cross(vx, cross_width_x, cross_color_x)
            # if _slice.get_face_edge(cube_face).attributes["on_y"]:
            #     shapes.cross(vx, cross_width_y, cross_color_y)

            marker = edge.c_attributes.get(annotation_key) or edge.f_attributes.get(annotation_key)
            if marker:
                assert isinstance(marker, VMarker)

                if movable == (marker == VMarker.C1):
                    _marker_color = markers[marker.value]
                    self._create_markers(_vx, _marker_color, marker == VMarker.C2)

        if isinstance(part, Corner):

            corner_slice = part.slice
            with self._gen_list_for_slice(corner_slice, g_list_dest):
                edge = self._get_slice_edge(corner_slice)

                vertexes = self.facets[edge].two_d_draw_rect

                draw_facet(edge, vertexes)

                if config.GUI_DRAW_MARKERS:
                    if cube_face.corner_bottom_left is part:
                        shapes.cross(vertexes, cross_width, cross_color)
                    elif cube_face.corner_bottom_right is part:
                        shapes.cross(vertexes, cross_width_x, cross_color_x)
                    if cube_face.corner_top_left is part:
                        shapes.cross(vertexes, cross_width_y, cross_color_y)


        elif isinstance(part, Edge):
            # shapes.quad_with_line(vertexes, color, lw, lc)

            nn: int

            for i in range(n):
                ix = i

                _slice: EdgeSlice = part.get_slice_by_ltr_index(cube_face, ix)
                color = self._slice_color(_slice)
                edge = self._get_slice_edge(_slice)
                vx = self.facets[edge].two_d_draw_rect

                with self._gen_list_for_slice(_slice, g_list_dest):
                    draw_facet(edge, vx)

                    # if _slice.get_face_edge(cube_face).attributes["origin"]:
                    #     shapes.cross(vx, cross_width, cross_color)
                    # if _slice.get_face_edge(cube_face).attributes["on_x"]:
                    #     shapes.cross(vx, cross_width_x, cross_color_x)
                    # if _slice.get_face_edge(cube_face).attributes["on_y"]:
                    #     shapes.cross(vx, cross_width_y, cross_color_y)



        else:
            assert isinstance(part, Center)
            # shapes.quad_with_line(vertexes, color, 4, (0, 0, 1))
            n = part.n_slices

            for x in range(n):
                for y in range(n):

                    ix = x
                    iy = y

                    # ix = _inv(ix, is_back)

                    center_slice: CenterSlice = part.get_slice((iy, ix))
                    edge = center_slice.get_face_edge(cube_face)

                    vx = self.facets[edge].two_d_draw_rect

                    color = self._edge_color(edge)
                    with self._gen_list_for_slice(center_slice, g_list_dest):

                        draw_facet(edge, vx)

                        if config.GUI_DRAW_MARKERS:
                            attributes = edge.attributes

                            if attributes["origin"]:
                                shapes.cross(vx, cross_width, cross_color)
                            if attributes["on_x"]:
                                shapes.cross(vx, cross_width_x, cross_color_x)
                            if attributes["on_y"]:
                                shapes.cross(vx, cross_width_y, cross_color_y)

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

    def _create_markers_sphere(self, vertexes: Sequence[ndarray], facet_color, marker_color, marker: bool):

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

        # this is also supported by glCallLine
        shapes.sphere(center, radius, marker_color)
    def _create_markers(self, vertexes: Sequence[ndarray], marker_color, is_fixed: bool):


        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]
        vx = vertexes

        center = (vx[0] + vx[2]) / 2

        l1: float = np.linalg.norm(vertexes[0] - vertexes[1])  # type: ignore
        l2: float = np.linalg.norm(vertexes[0] - vertexes[3])  # type: ignore
        _face_size = min([l1, l2])

        radius = _face_size / 2.0 * 0.8
        radius = min([radius, config.MAX_MARKER_RADIUS])

        r1 = radius
        r2 = radius * 0.2

        height: float = 0.01
        if is_fixed:
            r_outher = radius
            r_inner = radius * 0.8
        else:
            # movable above fixed
            r_outher = radius * 0.75
            r_inner = 0

        p1 = center + self._face_board.ortho_direction * height
        p2 = center - self._face_board.ortho_direction * height

        # this is also supported by glCallLine
        #shapes.cylinder(p1, p2, r1, r2, marker_color)
        shapes.disk(p1, p2, r_outher, r_inner, marker_color)

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
