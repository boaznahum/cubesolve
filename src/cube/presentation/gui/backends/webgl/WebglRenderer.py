"""
No-op renderer for the webgl backend.

The webgl backend sends cube state (not rendering commands) to the browser.
The renderer satisfies the Renderer protocol but does nothing — all 3D
rendering is done client-side in Three.js.
"""

from __future__ import annotations

from typing import Sequence

from cube.presentation.gui.protocols import (
    DisplayListManager,
    Renderer,
    ShapeRenderer,
    ViewStateManager,
)
from cube.presentation.gui.types import (
    Color3,
    Color4,
    DisplayList,
    Matrix4x4,
    Point3D,
    TextureHandle,
    TextureMap,
)


class WebglShapeRenderer(ShapeRenderer):
    """No-op shape renderer — all rendering is client-side."""

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        pass

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        pass

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        pass

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        pass

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        pass

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        pass

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        pass

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        pass

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        pass

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        pass

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        pass

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        pass

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        pass

    def set_sticker_context(self, face: str, row: int, col: int,
                            slice_index: int = -1,
                            sx: int = -1, sy: int = -1) -> None:
        pass

    def clear_sticker_context(self) -> None:
        pass


class WebglDisplayListManager(DisplayListManager):
    """No-op display list manager."""

    def __init__(self) -> None:
        self._next_id = 1

    def create_list(self) -> DisplayList:
        list_id = DisplayList(self._next_id)
        self._next_id += 1
        return list_id

    def begin_compile(self, list_id: DisplayList) -> None:
        pass

    def end_compile(self) -> None:
        pass

    def call_list(self, list_id: DisplayList) -> None:
        pass

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        pass

    def delete_list(self, list_id: DisplayList) -> None:
        pass

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        pass


class WebglViewStateManager(ViewStateManager):
    """No-op view state manager."""

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 50.0,
        near: float = 0.1,
        far: float = 1000.0,
    ) -> None:
        pass

    def push_matrix(self) -> None:
        pass

    def pop_matrix(self) -> None:
        pass

    def load_identity(self) -> None:
        pass

    def translate(self, x: float, y: float, z: float) -> None:
        pass

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        pass

    def scale(self, x: float, y: float, z: float) -> None:
        pass

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        pass

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        pass

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        return (0.0, 0.0, 0.0)


class WebglRenderer(Renderer):
    """No-op renderer for the webgl backend.

    Satisfies the Renderer protocol but does nothing — all 3D rendering
    is done client-side. The server only sends cube state updates.
    """

    def __init__(self) -> None:
        self._shapes = WebglShapeRenderer()
        self._display_lists = WebglDisplayListManager()
        self._view = WebglViewStateManager()

    @property
    def shapes(self) -> WebglShapeRenderer:
        return self._shapes

    @property
    def display_lists(self) -> WebglDisplayListManager:
        return self._display_lists

    @property
    def view(self) -> WebglViewStateManager:
        return self._view

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        pass

    def setup(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def begin_frame(self) -> None:
        pass

    def end_frame(self) -> None:
        pass

    def flush(self) -> None:
        pass

    def load_texture(self, file_path: str) -> TextureHandle | None:
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        pass

    def delete_texture(self, texture: TextureHandle) -> None:
        pass
