"""
AbstractWindow - Abstract base class with no-op defaults for Window protocol.

This class provides empty/no-op implementations of all Window protocol methods.
Use this when you need a partial Window implementation where most methods
do nothing.

Hierarchy:
    Window (Protocol/Interface)
        └── AbstractWindow (no-op defaults)
            └── WindowBase (real shared implementation)
                └── Concrete implementations (PygletWindow, HeadlessWindow, etc.)
"""

from typing import Callable

from cube.presentation.gui.types import KeyEvent, MouseEvent
from cube.presentation.gui.protocols.Window import Window
from cube.presentation.gui.protocols.TextRenderer import TextRenderer


class AbstractTextRenderer(TextRenderer):
    """No-op TextRenderer implementation."""

    def draw_label(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 12,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        bold: bool = False,
        anchor_x: str = "left",
        anchor_y: str = "bottom",
    ) -> None:
        """No-op: does nothing."""
        pass

    def clear_labels(self) -> None:
        """No-op: does nothing."""
        pass


class AbstractWindow(Window):
    """Abstract base class providing no-op defaults for Window protocol.

    All methods do nothing by default. Subclasses override only what they need.
    This is useful for partial implementations or testing.
    """

    @property
    def width(self) -> int:
        """Default width."""
        return 0

    @property
    def height(self) -> int:
        """Default height."""
        return 0

    @property
    def text(self) -> TextRenderer:
        """Default no-op text renderer."""
        return AbstractTextRenderer()

    def set_title(self, title: str) -> None:
        """No-op: does nothing."""
        pass

    def set_visible(self, visible: bool) -> None:
        """No-op: does nothing."""
        pass

    def set_size(self, width: int, height: int) -> None:
        """No-op: does nothing."""
        pass

    def close(self) -> None:
        """No-op: does nothing."""
        pass

    def request_redraw(self) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_visible(self, visible: bool) -> None:
        """No-op: does nothing."""
        pass

    def set_draw_handler(self, handler: Callable[[], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_resize_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_key_press_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_key_release_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_press_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_release_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_drag_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_move_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """No-op: does nothing."""
        pass

    def set_mouse_scroll_handler(
        self, handler: Callable[[int, int, float, float], None] | None
    ) -> None:
        """No-op: does nothing."""
        pass

    def set_close_handler(self, handler: Callable[[], bool] | None) -> None:
        """No-op: does nothing."""
        pass
