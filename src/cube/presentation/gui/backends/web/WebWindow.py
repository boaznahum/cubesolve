"""
Web window implementation.

Represents the browser window/canvas state.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.types import KeyEvent, MouseEvent


class WebTextRenderer:
    """Text renderer for web backend.

    Queues text labels to be rendered in browser.
    """

    def __init__(self):
        self._labels: list[dict] = []

    def draw_label(
        self,
        text: str,
        x: float,
        y: float,
        font_name: str = "Arial",
        font_size: int = 12,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        anchor_x: str = "left",
        anchor_y: str = "bottom",
    ) -> None:
        """Queue a text label for rendering."""
        self._labels.append({
            "text": text,
            "x": x,
            "y": y,
            "font": font_name,
            "size": font_size,
            "color": list(color),
            "anchor_x": anchor_x,
            "anchor_y": anchor_y
        })

    def clear_labels(self) -> None:
        """Clear all queued labels."""
        self._labels.clear()

    def get_labels(self) -> list[dict]:
        """Get queued labels for sending to browser."""
        return self._labels


class WebWindow:
    """Web window representing browser canvas.

    Tracks window state and event handlers.
    """

    def __init__(self, width: int, height: int, title: str):
        self._width = width
        self._height = height
        self._title = title
        self._visible = True
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
        self._mouse_scroll_handler: Callable[[float, float, float, float], None] | None = None
        self._close_handler: Callable[[], None] | None = None

    @property
    def width(self) -> int:
        """Window width."""
        return self._width

    @property
    def height(self) -> int:
        """Window height."""
        return self._height

    @property
    def text_renderer(self) -> WebTextRenderer:
        """Access text renderer."""
        return self._text_renderer

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

    def set_mouse_scroll_handler(
        self, handler: Callable[[float, float, float, float], None] | None
    ) -> None:
        """Set the mouse scroll handler."""
        self._mouse_scroll_handler = handler

    def set_close_handler(self, handler: Callable[[], None] | None) -> None:
        """Set the close handler."""
        self._close_handler = handler

    # Simulation methods for testing

    def simulate_key_press(self, key: int, modifiers: int = 0) -> None:
        """Simulate a key press event."""
        if self._key_press_handler:
            from cube.presentation.gui.types import KeyEvent
            event = KeyEvent(symbol=key, modifiers=modifiers)
            self._key_press_handler(event)

    def simulate_mouse_press(self, x: float, y: float, button: int) -> None:
        """Simulate a mouse press event."""
        if self._mouse_press_handler:
            from cube.presentation.gui.types import MouseEvent, MouseButton
            event = MouseEvent(x=x, y=y, button=MouseButton(button), dx=0, dy=0)
            self._mouse_press_handler(event)

    def simulate_mouse_drag(self, x: float, y: float, dx: float, dy: float) -> None:
        """Simulate a mouse drag event."""
        if self._mouse_drag_handler:
            from cube.presentation.gui.types import MouseEvent, MouseButton
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
