"""
Console renderer implementation.

A null renderer for console mode - uses text-based output instead of graphics.
"""

from typing import Tuple

from cube.gui.protocols.renderer import Renderer, ShapeRenderer, DisplayListManager, ViewStateManager


class ConsoleShapeRenderer(ShapeRenderer):
    """Null shape renderer for console mode."""

    def draw_quad(
        self,
        vertices: list[Tuple[float, float, float]],
        color: Tuple[int, int, int, int],
        normal: Tuple[float, float, float] | None = None,
    ) -> None:
        """No-op for console mode."""
        pass

    def draw_triangle(
        self,
        vertices: list[Tuple[float, float, float]],
        color: Tuple[int, int, int, int],
        normal: Tuple[float, float, float] | None = None,
    ) -> None:
        """No-op for console mode."""
        pass

    def draw_line(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        color: Tuple[int, int, int, int],
        width: float = 1.0,
    ) -> None:
        """No-op for console mode."""
        pass


class ConsoleDisplayListManager(DisplayListManager):
    """Null display list manager for console mode."""

    def create_list(self) -> int:
        """Return dummy list ID."""
        return 0

    def begin_list(self, list_id: int) -> None:
        """No-op for console mode."""
        pass

    def end_list(self) -> None:
        """No-op for console mode."""
        pass

    def call_list(self, list_id: int) -> None:
        """No-op for console mode."""
        pass

    def delete_list(self, list_id: int) -> None:
        """No-op for console mode."""
        pass


class ConsoleViewStateManager(ViewStateManager):
    """Null view state manager for console mode."""

    def push_matrix(self) -> None:
        """No-op for console mode."""
        pass

    def pop_matrix(self) -> None:
        """No-op for console mode."""
        pass

    def translate(self, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        pass

    def rotate(self, angle: float, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        pass

    def scale(self, x: float, y: float, z: float) -> None:
        """No-op for console mode."""
        pass

    def load_identity(self) -> None:
        """No-op for console mode."""
        pass

    def set_projection(self, width: int, height: int) -> None:
        """No-op for console mode."""
        pass


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
        pass

    def clear(self, color: Tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        """No-op for console mode."""
        pass

    def end_frame(self) -> None:
        """No-op for console mode."""
        pass
