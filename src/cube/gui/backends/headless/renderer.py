"""
Headless renderer implementation.

Provides no-op implementations of all rendering protocols for testing
and headless operation.
"""

from typing import Sequence

from cube.gui.types import Point3D, Color3, Color4, DisplayList, Matrix4x4, TextureHandle, TextureMap
from cube.gui.protocols.renderer import ShapeRenderer, DisplayListManager, ViewStateManager, Renderer


class HeadlessShapeRenderer(ShapeRenderer):
    """No-op shape renderer for headless mode.

    All methods are no-ops that accept parameters but do nothing.
    """

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """No-op quad rendering."""
        pass

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op quad with border rendering."""
        pass

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """No-op triangle rendering."""
        pass

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """No-op line rendering."""
        pass

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """No-op sphere rendering."""
        pass

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """No-op cylinder rendering."""
        pass

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """No-op disk rendering."""
        pass

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """No-op lines rendering."""
        pass

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """No-op textured quad rendering."""
        pass

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op cross rendering."""
        pass

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op lines_in_quad rendering."""
        pass

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """No-op box rendering."""
        pass

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """No-op full_cylinder rendering."""
        pass


class HeadlessDisplayListManager(DisplayListManager):
    """In-memory display list manager for headless mode.

    Tracks display list IDs but doesn't store any rendering commands.
    """

    def __init__(self) -> None:
        self._next_id = 1
        self._active_lists: set[int] = set()
        self._compiling: int | None = None

    def create_list(self) -> DisplayList:
        """Create a new display list ID."""
        list_id = DisplayList(self._next_id)
        self._next_id += 1
        self._active_lists.add(list_id)
        return list_id

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin 'compiling' (no-op, just tracks state)."""
        self._compiling = list_id

    def end_compile(self) -> None:
        """End 'compiling'."""
        self._compiling = None

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a display list (no-op)."""
        pass

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists (no-op)."""
        pass

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list."""
        self._active_lists.discard(list_id)

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists."""
        for list_id in list_ids:
            self._active_lists.discard(list_id)


class HeadlessViewStateManager(ViewStateManager):
    """No-op view state manager for headless mode.

    Tracks basic state (matrix stack depth) but doesn't perform calculations.
    """

    def __init__(self) -> None:
        self._matrix_stack_depth = 0

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 50.0,
        near: float = 0.1,
        far: float = 100.0,
    ) -> None:
        """No-op projection setup."""
        pass

    def push_matrix(self) -> None:
        """Track matrix stack push."""
        self._matrix_stack_depth += 1

    def pop_matrix(self) -> None:
        """Track matrix stack pop."""
        if self._matrix_stack_depth > 0:
            self._matrix_stack_depth -= 1

    def load_identity(self) -> None:
        """No-op identity load."""
        pass

    def translate(self, x: float, y: float, z: float) -> None:
        """No-op translation."""
        pass

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """No-op rotation."""
        pass

    def scale(self, x: float, y: float, z: float) -> None:
        """No-op scaling."""
        pass

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """No-op matrix multiplication."""
        pass

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
        """No-op look-at setup."""
        pass

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Return origin for headless mode - no actual unprojection."""
        return (0.0, 0.0, 0.0)


class HeadlessRenderer(Renderer):
    """Headless renderer combining all no-op components.

    Use this for testing and headless operation where no actual
    rendering is needed.
    """

    def __init__(self) -> None:
        self._shapes = HeadlessShapeRenderer()
        self._display_lists = HeadlessDisplayListManager()
        self._view = HeadlessViewStateManager()
        self._frame_count = 0

    @property
    def shapes(self) -> HeadlessShapeRenderer:
        """Access shape rendering (no-op)."""
        return self._shapes

    @property
    def display_lists(self) -> HeadlessDisplayListManager:
        """Access display list management."""
        return self._display_lists

    @property
    def view(self) -> HeadlessViewStateManager:
        """Access view state management (no-op)."""
        return self._view

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """No-op clear."""
        pass

    def setup(self) -> None:
        """No-op setup."""
        pass

    def cleanup(self) -> None:
        """Cleanup (clear tracked state)."""
        self._display_lists._active_lists.clear()

    def begin_frame(self) -> None:
        """Begin frame (increment counter)."""
        self._frame_count += 1

    def end_frame(self) -> None:
        """No-op end frame."""
        pass

    def flush(self) -> None:
        """No-op flush."""
        pass

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """No-op texture loading (returns None)."""
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """No-op texture binding."""
        pass

    def delete_texture(self, texture: TextureHandle) -> None:
        """No-op texture deletion."""
        pass

    @property
    def frame_count(self) -> int:
        """Get number of frames rendered (for testing)."""
        return self._frame_count
