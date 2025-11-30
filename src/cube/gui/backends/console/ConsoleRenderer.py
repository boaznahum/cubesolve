"""
Console renderer implementation.

A null renderer for console mode - uses text-based output instead of graphics.
"""

from typing import Sequence

from cube.gui.protocols import Renderer, ShapeRenderer, DisplayListManager, ViewStateManager
from cube.gui.types import Point3D, Color3, Color4, DisplayList as DisplayListType, Matrix4x4, TextureHandle, TextureMap


class ConsoleShapeRenderer(ShapeRenderer):
    """Null shape renderer for console mode."""

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """No-op for console mode."""
        return None

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """No-op for console mode."""
        return None

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """No-op for console mode."""
        return None

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """No-op for console mode."""
        return None

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """No-op for console mode."""
        return None

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """No-op for console mode."""
        return None


class ConsoleDisplayListManager(DisplayListManager):
    """Null display list manager for console mode."""

    _next_id: int = 1

    def create_list(self) -> DisplayListType:
        """Return dummy list ID."""
        list_id = DisplayListType(self._next_id)
        self._next_id += 1
        return list_id

    def begin_compile(self, list_id: DisplayListType) -> None:
        """No-op for console mode."""
        return None

    def end_compile(self) -> None:
        """No-op for console mode."""
        return None

    def call_list(self, list_id: DisplayListType) -> None:
        """No-op for console mode."""
        return None

    def call_lists(self, list_ids: Sequence[DisplayListType]) -> None:
        """No-op for console mode."""
        return None

    def delete_list(self, list_id: DisplayListType) -> None:
        """No-op for console mode."""
        return None

    def delete_lists(self, list_ids: Sequence[DisplayListType]) -> None:
        """No-op for console mode."""
        return None


class ConsoleViewStateManager(ViewStateManager):
    """Null view state manager for console mode."""

    def push_matrix(self) -> None:
        """No-op for console mode."""
        return None

    def pop_matrix(self) -> None:
        """No-op for console mode."""
        return None

    def translate(self, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        return None

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        return None

    def scale(self, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        return None

    def load_identity(self) -> None:
        """No-op for console mode."""
        return None

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """No-op for console mode."""
        return None

    def look_at(
        self,
        eye_x: float,
        eye_y: float,
        eye_z: float,
        center_x: float,
        center_y: float,
        center_z: float,
        up_x: float,
        up_y: float,
        up_z: float,
    ) -> None:
        """No-op for console mode."""
        return None

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Return origin for console mode."""
        return (0.0, 0.0, 0.0)

    def set_projection(
        self, width: int, height: int, fov_y: float = 50.0, near: float = 0.1, far: float = 100.0
    ) -> None:
        """No-op for console mode."""
        return None


class ConsoleRenderer(Renderer):
    """Console renderer - provides null implementations for text-based mode.

    In console mode, the cube is rendered as text using viewer.plot(),
    not through the graphics renderer.
    """

    def __init__(self) -> None:
        self._shapes = ConsoleShapeRenderer()
        self._display_lists = ConsoleDisplayListManager()
        self._view = ConsoleViewStateManager()

    @property
    def shapes(self) -> ShapeRenderer:
        """Access shape drawing operations."""
        return self._shapes

    @property
    def display_lists(self) -> DisplayListManager:
        """Access display list operations."""
        return self._display_lists

    @property
    def view(self) -> ViewStateManager:
        """Access view transformation operations."""
        return self._view

    def setup(self) -> None:
        """No-op for console mode."""
        return None

    def cleanup(self) -> None:
        """No-op for console mode."""
        return None

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """No-op for console mode."""
        return None

    def begin_frame(self) -> None:
        """No-op for console mode."""
        return None

    def end_frame(self) -> None:
        """No-op for console mode."""
        return None

    def flush(self) -> None:
        """No-op for console mode."""
        return None

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """No-op for console mode."""
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """No-op for console mode."""
        return None

    def delete_texture(self, texture: TextureHandle) -> None:
        """No-op for console mode."""
        return None
