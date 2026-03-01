"""
Web window implementation.

Represents the browser window/canvas state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from cube.presentation.gui.protocols.TextRenderer import TextRenderer
from cube.presentation.gui.protocols.Window import Window

if TYPE_CHECKING:
    from cube.presentation.gui.types import KeyEvent, MouseEvent


class WebTextRenderer(TextRenderer):
    """Text renderer for web backend.

    Queues text labels to be rendered in browser.
    """

    def __init__(self) -> None:
        self._labels: list[dict] = []

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
        """Queue a text label for rendering."""
        self._labels.append({
            "text": text,
            "x": x,
            "y": y,
            "font": "Arial",
            "size": font_size,
            "color": list(color),
            "bold": bold,
            "anchor_x": anchor_x,
            "anchor_y": anchor_y
        })

    def clear_labels(self) -> None:
        """Clear all queued labels."""
        self._labels.clear()

    def get_labels(self) -> list[dict]:
        """Get queued labels for sending to browser."""
        return self._labels


class WebWindow(Window):
    """Web window representing browser canvas.

    Tracks window state and event handlers.
    """

    def __init__(self, width: int, height: int, title: str):
        self._width = width
        self._height = height
        self._title = title
        self._visible = True
        self._closed = False
        self._mouse_visible = True

        # Text renderer
        self._text_renderer = WebTextRenderer()

        # Event handlers
        self._draw_handler: Callable[[], None] | None = None
        self._resize_handler: Callable[[int, int], None] | None = None
        self._key_press_handler: Callable[["KeyEvent"], None] | None = None
        self._key_release_handler: Callable[["KeyEvent"], None] | None = None
        self._mouse_press_handler: Callable[["MouseEvent"], None] | None = None
        self._mouse_release_handler: Callable[["MouseEvent"], None] | None = None
        self._mouse_drag_handler: Callable[["MouseEvent"], None] | None = None
        self._mouse_move_handler: Callable[["MouseEvent"], None] | None = None
        self._mouse_scroll_handler: Callable[[int, int, float, float], None] | None = None
        self._close_handler: Callable[[], bool] | None = None

    @property
    def width(self) -> int:
        """Window width."""
        return self._width

    @property
    def height(self) -> int:
        """Window height."""
        return self._height

    @property
    def text(self) -> WebTextRenderer:
        """Access text renderer."""
        return self._text_renderer

    def set_title(self, title: str) -> None:
        """Set window title."""
        self._title = title

    def set_visible(self, visible: bool) -> None:
        """Show or hide the window."""
        self._visible = visible

    def set_size(self, width: int, height: int) -> None:
        """Set window size."""
        self._width = width
        self._height = height

    def request_redraw(self) -> None:
        """Request a redraw."""
        if self._draw_handler:
            self._draw_handler()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse visibility."""
        self._mouse_visible = visible

    def close(self) -> None:
        """Close the window."""
        if self._close_handler:
            self._close_handler()

    # Event handler setters

    def set_draw_handler(self, handler: Callable[[], None] | None) -> None:
        """Set the draw handler."""
        self._draw_handler = handler

    def set_resize_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """Set the resize handler."""
        self._resize_handler = handler

    def set_key_press_handler(self, handler: Callable[["KeyEvent"], None] | None) -> None:
        """Set the key press handler."""
        self._key_press_handler = handler

    def set_key_release_handler(self, handler: Callable[["KeyEvent"], None] | None) -> None:
        """Set the key release handler."""
        self._key_release_handler = handler

    def set_mouse_press_handler(self, handler: Callable[["MouseEvent"], None] | None) -> None:
        """Set the mouse press handler."""
        self._mouse_press_handler = handler

    def set_mouse_release_handler(self, handler: Callable[["MouseEvent"], None] | None) -> None:
        """Set the mouse release handler."""
        self._mouse_release_handler = handler

    def set_mouse_drag_handler(self, handler: Callable[["MouseEvent"], None] | None) -> None:
        """Set the mouse drag handler."""
        self._mouse_drag_handler = handler

    def set_mouse_move_handler(self, handler: Callable[["MouseEvent"], None] | None) -> None:
        """Set the mouse move handler (without button pressed)."""
        self._mouse_move_handler = handler

    def set_mouse_scroll_handler(
        self, handler: Callable[[int, int, float, float], None] | None
    ) -> None:
        """Set the mouse scroll handler."""
        self._mouse_scroll_handler = handler

    def set_close_handler(self, handler: Callable[[], bool] | None) -> None:
        """Set the close handler."""
        self._close_handler = handler

    # Simulation methods for testing

    def simulate_key_press(self, key: int, modifiers: int = 0) -> None:
        """Simulate a key press event."""
        if self._key_press_handler:
            from cube.presentation.gui.types import KeyEvent
            event = KeyEvent(symbol=key, modifiers=modifiers)
            self._key_press_handler(event)

    def simulate_mouse_press(self, x: int, y: int, button: int) -> None:
        """Simulate a mouse press event."""
        if self._mouse_press_handler:
            from cube.presentation.gui.types import MouseEvent
            event = MouseEvent(x=x, y=y, button=button, dx=0, dy=0)
            self._mouse_press_handler(event)

    def simulate_mouse_drag(self, x: int, y: int, dx: int, dy: int) -> None:
        """Simulate a mouse drag event."""
        if self._mouse_drag_handler:
            from cube.presentation.gui.types import MouseButton, MouseEvent
            event = MouseEvent(x=x, y=y, button=MouseButton.LEFT, dx=dx, dy=dy)
            self._mouse_drag_handler(event)

    def simulate_draw(self) -> None:
        """Simulate a draw event."""
        if self._draw_handler:
            self._draw_handler()

    def simulate_resize(self, width: int, height: int) -> None:
        """Simulate a resize event."""
        self._width = width
        self._height = height
        if self._resize_handler:
            self._resize_handler(width, height)
