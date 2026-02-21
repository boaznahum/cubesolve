import sys
from collections import defaultdict
from collections.abc import Iterable, MutableSequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Sequence, Tuple

import numpy as np
from numpy import ndarray

from cube.application.state import ApplicationAndViewState
from cube.domain.model import (
    Center,
    CenterSlice,
    Corner,
    Edge,
    EdgeWing,
    Part,
    PartEdge,
    PartSlice,
    PartSliceHashID,
)
from cube.domain.model.Color import Color
from cube.domain.model.Face import Face
from cube.application.markers import MarkerToolkit, get_markers_from_part_edge
from cube.domain.geometric import geometry_utils as geometry
from cube.utils.config_protocol import ConfigProtocol

from ..gui.protocols import Renderer
from ..gui.types import DisplayList, Point3D, TextureCoord, TextureMap
from ..gui.ViewSetup import ViewSetup
from .TextureData import TextureData

_VColor = Tuple[int, int, int]

if TYPE_CHECKING:
    from ._faceboard import _FaceBoard

_inited = False

_colors: dict[Color, _VColor] = {}

# Complementary color map (0.0-1.0 float values for MarkerToolkit protocol)
# Keyed by 0-255 face color (matching _colors dict) for legacy renderer lookup.
_COMPLEMENTARY_MAP_FLOAT: dict[_VColor, tuple[float, float, float]] = {
    (255, 0, 0): (0.0, 1.0, 1.0),
    (0, 255, 0): (1.0, 0.0, 1.0),
    (0, 0, 255): (1.0, 1.0, 0.0),
    (255, 255, 0): (0.4, 0.2, 1.0),
    (255, 128, 0): (0.0, 1.0, 1.0),
    (255, 255, 255): (0.6, 0.0, 0.6),
}


def _color_float_to_vcolor(color: tuple[float, float, float]) -> _VColor:
    """Convert RGB color from 0.0-1.0 float to 0-255 int."""
    return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))


class LegacyCellToolkit(MarkerToolkit):
    """MarkerToolkit implementation for the legacy (display-list) renderer.

    Translates abstract marker drawing primitives into OpenGL calls
    via the Renderer's ShapeRenderer.

    Implements the MarkerToolkit protocol.
    """

    __slots__ = [
        '_vertexes', '_ortho_dir', '_renderer', '_face_color_255',
        '_face_color_float', '_complementary_float', '_face_size',
        '_base_radius', '_max_marker_radius',
    ]

    def __init__(
        self,
        vertexes: Sequence[ndarray],
        ortho_direction: ndarray,
        face_color_255: _VColor,
        renderer: "Renderer",
        max_marker_radius: float,
    ) -> None:
        self._vertexes = vertexes
        self._ortho_dir = ortho_direction
        self._renderer = renderer
        self._face_color_255 = face_color_255
        self._face_color_float: tuple[float, float, float] = (
            face_color_255[0] / 255.0,
            face_color_255[1] / 255.0,
            face_color_255[2] / 255.0,
        )
        self._complementary_float = _COMPLEMENTARY_MAP_FLOAT.get(
            face_color_255, (1.0, 0.0, 1.0)
        )
        self._max_marker_radius = max_marker_radius

        # Calculate cell size and base radius
        x_size: float = np.linalg.norm(vertexes[1] - vertexes[0])  # type: ignore
        y_size: float = np.linalg.norm(vertexes[3] - vertexes[0])  # type: ignore
        self._face_size: float = min(x_size, y_size)
        self._base_radius: float = min(
            self._face_size / 2.0 * 0.8, max_marker_radius
        )

    @property
    def cell_size(self) -> float:
        return self._face_size

    @property
    def face_color(self) -> tuple[float, float, float]:
        return self._face_color_float

    @property
    def complementary_color(self) -> tuple[float, float, float]:
        return self._complementary_float

    def draw_ring(
        self,
        inner_radius: float,
        outer_radius: float,
        color: tuple[float, float, float],
        height: float,
    ) -> None:
        vx = self._vertexes
        center = (vx[0] + vx[2]) / 2

        r_outer = self._base_radius * outer_radius
        r_inner = self._base_radius * inner_radius
        h = height * self._face_size

        p1 = center + self._ortho_dir * h
        p2 = center - self._ortho_dir * h

        marker_color = _color_float_to_vcolor(color)
        self._renderer.shapes.full_cylinder(
            _Cell._to_point3d(p1), _Cell._to_point3d(p2),
            r_outer, r_inner, marker_color,
        )

    def draw_filled_circle(
        self,
        radius: float,
        color: tuple[float, float, float],
        height: float,
    ) -> None:
        self.draw_ring(0.0, radius, color, height)

    def draw_cross(self, color: tuple[float, float, float]) -> None:
        vx = self._vertexes
        color_rgb = _color_float_to_vcolor(color)
        points = [_Cell._to_point3d(v) for v in vx]
        self._renderer.shapes.line(points[0], points[2], 2.0, color_rgb)
        self._renderer.shapes.line(points[1], points[3], 2.0, color_rgb)

    def draw_arrow(
        self,
        color: tuple[float, float, float],
        direction: float,
        radius_factor: float,
        thickness: float,
    ) -> None:
        # Arrow markers not supported in legacy renderer
        pass

    def draw_checkmark(
        self,
        color: tuple[float, float, float],
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        # Checkmark markers not supported in legacy renderer
        pass

    def draw_bold_cross(
        self,
        color: tuple[float, float, float],
        radius_factor: float,
        thickness: float,
        height_offset: float,
    ) -> None:
        # Bold cross markers not supported in legacy renderer
        pass

    def draw_character(
        self,
        character: str,
        color: tuple[float, float, float],
        radius_factor: float,
    ) -> None:
        # Character markers not supported in legacy renderer
        pass


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

    def __init__(self, face_board: "_FaceBoard") -> None:
        super().__init__()
        self._right_top_v3: ndarray | None = None
        self._left_bottom_v3: ndarray | None = None
        self._face_board = face_board

        # Store config reference to avoid repeated lookups
        self._config: ConfigProtocol = face_board._config

        self.gl_lists_movable: dict[PartSliceHashID, MutableSequence[int]] = defaultdict(list)
        self.gl_lists_unmovable: dict[PartSliceHashID, MutableSequence[int]] = defaultdict(list)

        # the boxes of the part PartEdge
        #  # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]
        self.facets: dict[PartEdge, _RectGeometry] = {}
        # noinspection PyTypeChecker
        self.cell_geometry: _RectGeometry = None  # type: ignore

        # noinspection PyTypeChecker
        self._part: Part = None  # type: ignore

        self._cubie_texture = (
            self._face_board.board.cubie_texture if
            self._face_board.cube_face.cube.size <= self._config.viewer_max_size_for_texture else None
        )

    @property
    def _renderer(self) -> Renderer:
        """Get the renderer from the parent hierarchy.

        Raises:
            RuntimeError: If renderer is not configured.
        """
        renderer = self._face_board.board.renderer
        if renderer is None:
            raise RuntimeError("Renderer is required but not configured. Use BackendRegistry.create_renderer()")
        return renderer

    @staticmethod
    def _to_point3d(v: ndarray) -> Point3D:
        """Convert numpy array to Point3D (ndarray)."""
        return v  # Point3D is already ndarray

    @staticmethod
    def _vertices_to_points(vertices: Sequence[ndarray]) -> list[Point3D]:
        """Convert sequence of numpy arrays to list of Point3D tuples."""
        return [_Cell._to_point3d(v) for v in vertices]

    @staticmethod
    def _texture_data_to_map(texture: TextureData | None) -> TextureMap | None:
        """Convert TextureData texture_map to TextureMap format."""
        if texture is None:
            return None
        tex_map = texture.texture_map
        if len(tex_map) >= 4:
            return (
                TextureCoord(tex_map[0][0], tex_map[0][1]),
                TextureCoord(tex_map[1][0], tex_map[1][1]),
                TextureCoord(tex_map[2][0], tex_map[2][1]),
                TextureCoord(tex_map[3][0], tex_map[3][1]),
            )
        return None

    def _clear_gl_lists(self):
        # delete and clear all lists
        renderer = self._renderer
        for ls in self.gl_lists_movable.values():
            for ll in ls:
                renderer.display_lists.delete_list(DisplayList(ll))
        self.gl_lists_movable.clear()

        for ls in self.gl_lists_unmovable.values():
            for ll in ls:
                renderer.display_lists.delete_list(DisplayList(ll))
        self.gl_lists_unmovable.clear()

    def release_resources(self):
        self._clear_gl_lists()
        self.facets.clear()

    # noinspection PyUnusedLocal
    def prepare_geometry(self, part: Part, vertexes: Sequence[ndarray]):

        # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]

        self._left_bottom_v3 = vertexes[0]
        self._right_top_v3 = vertexes[2]

        self.cell_geometry = _RectGeometry(vertexes, self._face_board.ortho_direction)

        # delete and clear all lists
        self._clear_gl_lists()
        self.facets.clear()

        self._part = part

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
        dicts: list[dict[PartSliceHashID, MutableSequence[int]]] = [self.gl_lists_movable, self.gl_lists_unmovable]

        # when we try to use values() pycharm complains
        lists: Sequence[int] = [ll for m in dicts
                                for _, ls in m.items() for ll in ls]

        if not lists:
            print(f"Error no gl lists in {self}", file=sys.stderr)
            return

        dest.update(lists)

    def _prepare_view_state(self) -> None:

        vs: ApplicationAndViewState = self._face_board.board.vs
        ViewSetup.prepare_objects_view(vs, self._renderer)

    def _restore_view_state(self) -> None:

        ViewSetup.restore_objects_view(self._renderer)

    @contextmanager
    def _gen_list_for_slice(self, p_slice: PartSlice, dest: dict[PartSliceHashID, MutableSequence[int]]):
        """
        Generate new gl list and on exit add this list to slice
        :param p_slice:
        :param dest:
        :return:
        """
        renderer = self._renderer
        list_handle = renderer.display_lists.create_list()
        renderer.display_lists.begin_compile(list_handle)
        g_list = int(list_handle)  # Store as int for backward compatibility

        try:
            yield None
        finally:
            renderer.display_lists.end_compile()
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

                _slice: EdgeWing = part.get_slice_by_ltr_index(cube_face, ix)
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
        lw = 3.75
        cross_width = 5
        cross_width_x = 8
        cross_width_y = 2
        cross_color = (0, 0, 0)
        cross_color_x = (138, 43, 226)  # blueviolet	#8A2BE2	rgb(138,43,226)
        # noinspection SpellCheckingInspection
        cross_color_y = (0, 191, 255)  # deepskyblue	#00BFFF	rgb(0,191,255)

        from ._faceboard import _FaceBoard
        fb: _FaceBoard = self._face_board
        cube_face: Face = fb.cube_face

        part: Part = self._part

        n: int = part.n_slices

        # Get config for this method
        cfg = self._config

        cubie_facet_texture: TextureData | None = self._cubie_texture
        renderer = self._renderer

        def draw_facet(part_edge: PartEdge, _vx):

            # vertex = [left_bottom, right_bottom, right_top, left_top]

            facet_color: _VColor = self._edge_color(part_edge)

            if movable:
                # Use renderer abstraction
                points = self._vertices_to_points(_vx)
                if cubie_facet_texture:
                    # Bind the texture for rendering
                    cubie_facet_texture.bind()
                    tex_handle = cubie_facet_texture.texture_handle
                    tex_map = self._texture_data_to_map(cubie_facet_texture)
                    renderer.shapes.quad_with_texture(points, facet_color, tex_handle, tex_map)
                else:
                    renderer.shapes.quad_with_border(points, facet_color, lw, lc)

                if cfg.markers_config.GUI_DRAW_MARKERS:
                    _nn = part_edge.moveable_attributes["n"]
                    points = self._vertices_to_points(_vx)
                    renderer.shapes.lines_in_quad(points, _nn, 5, (138, 43, 226))

            # Get markers and draw using toolkit pattern
            _markers = get_markers_from_part_edge(part_edge)

            if _markers:
                toolkit = LegacyCellToolkit(
                    vertexes=_vx,
                    ortho_direction=self._face_board.ortho_direction,
                    face_color_255=facet_color,
                    renderer=renderer,
                    max_marker_radius=cfg.max_marker_radius,
                )
                for marker in _markers:
                    marker.draw(toolkit)

        if isinstance(part, Corner):

            corner_slice = part.slice
            with self._gen_list_for_slice(corner_slice, g_list_dest):
                edge = self._get_slice_edge(corner_slice)

                vertexes = self.facets[edge].two_d_draw_rect

                draw_facet(edge, vertexes)

                if cfg.markers_config.GUI_DRAW_MARKERS:
                    points = self._vertices_to_points(vertexes)
                    if cube_face.corner_bottom_left is part:
                        renderer.shapes.cross(points, cross_width, cross_color)
                    elif cube_face.corner_bottom_right is part:
                        renderer.shapes.cross(points, cross_width_x, cross_color_x)
                    if cube_face.corner_top_left is part:
                        renderer.shapes.cross(points, cross_width_y, cross_color_y)

        elif isinstance(part, Edge):
            # shapes.quad_with_line(vertexes, color, lw, lc)

            for i in range(n):
                ix = i

                _slice: EdgeWing = part.get_slice_by_ltr_index(cube_face, ix)
                edge = self._get_slice_edge(_slice)
                vx = self.facets[edge].two_d_draw_rect

                with self._gen_list_for_slice(_slice, g_list_dest):
                    draw_facet(edge, vx)

                    if cfg.markers_config.GUI_DRAW_MARKERS:
                        attributes = edge.fixed_attributes
                        points = self._vertices_to_points(vx)
                        if attributes.get("origin", False):
                            renderer.shapes.cross(points, cross_width, cross_color)
                        if attributes.get("on_x", False):
                            renderer.shapes.cross(points, cross_width_x, cross_color_x)
                        if attributes.get("on_y", False):
                            renderer.shapes.cross(points, cross_width_y, cross_color_y)

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

                    with self._gen_list_for_slice(center_slice, g_list_dest):

                        draw_facet(edge, vx)

                        if cfg.markers_config.GUI_DRAW_MARKERS:
                            attributes = edge.fixed_attributes
                            points = self._vertices_to_points(vx)
                            if attributes.get("origin", False):
                                renderer.shapes.cross(points, cross_width, cross_color)
                            if attributes.get("on_x", False):
                                renderer.shapes.cross(points, cross_width_x, cross_color_x)
                            if attributes.get("on_y", False):
                                renderer.shapes.cross(points, cross_width_y, cross_color_y)

    def gui_movable_gui_objects(self) -> Iterable[int]:
        return [ll for ls in self.gl_lists_movable.values() for ll in ls]

    def gui_slice_movable_gui_objects(self, _slice: PartSlice) -> Iterable[int]:

        _id = _slice.fixed_id

        d: dict[PartSliceHashID, MutableSequence[int]] = self.gl_lists_movable

        # does it work for default dict?
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
