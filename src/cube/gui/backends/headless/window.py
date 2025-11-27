"""
Headless window implementation.

Provides a mock window for testing without actual GUI display.
"""

from typing import Callable

from cube.gui.types import KeyEvent, MouseEvent, Color4


class HeadlessTextRenderer:
    """No-op text renderer for headless mode."""

    def __init__(self) -> None:
        self._labels: list[tuple[str, int, int]] = []

    def draw_label(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 12,
        color: Color4 = (255, 255, 255, 255),
        bold: bool = False,
        anchor_x: str = "left",
        anchor_y: str = "bottom",
    ) -> None:
        """Record label for testing (no actual rendering)."""
        self._labels.append((text, x, y))

    def clear_labels(self) -> None:
        """Clear recorded labels."""
        self._labels.clear()

    @property
    def labels(self) -> list[tuple[str, int, int]]:
        """Get recorded labels for testing."""
        return self._labels.copy()


class HeadlessWindow:
    """Mock window for headless testing.

    Simulates a window without any actual display. Useful for:
    - Unit testing
    - Benchmarking
    - CI/CD pipelines
    - Batch processing

    Event handlers can be set and triggered programmatically for testing.
    """

    def __init__(self, width: int = 720, height: int = 720, title: str = "Cube") -> None:
        self._width = width
        self._height = height
        self._title = title
        self._visible = False
        self._closed = False
        self._mouse_visible = True
        self._text = HeadlessTextRenderer()

        # Event handlers
        self._draw_handler: Callable[[], None] | None = None
        self._resize_handler: Callable[[int, int], None] | None = None
        self._key_press_handler: Callable[[KeyEvent], None] | None = None
        self._key_release_handler: Callable[[KeyEvent], None] | None = None
        self._mouse_press_handler: Callable[[MouseEvent], None] | None = None
        self._mouse_release_handler: Callable[[MouseEvent], None] | None = None
        self._mouse_drag_handler: Callable[[MouseEvent], None] | None = None
        self._mouse_move_handler: Callable[[MouseEvent], None] | None = None
        self._mouse_scroll_handler: Callable[[int, int, float, float], None] | None = None
        self._close_handler: Callable[[], bool] | None = None

        # For testing: track redraw requests
        self._redraw_requested = False

    @property
    def width(self) -> int:
        """Window width."""
        return self._width

    @property
    def height(self) -> int:
        """Window height."""
        return self._height

    @property
    def text(self) -> HeadlessTextRenderer:
        """Access text renderer."""
        return self._text

    @property
    def closed(self) -> bool:
        """Whether window has been closed."""
        return self._closed

    def set_title(self, title: str) -> None:
        """Set window title."""
        self._title = title

    def set_visible(self, visible: bool) -> None:
        """Set window visibility."""
        self._visible = visible

    def set_size(self, width: int, height: int) -> None:
        """Set window size and trigger resize handler."""
        old_width, old_height = self._width, self._height
        self._width = width
        self._height = height
        if (old_width != width or old_height != height) and self._resize_handler:
            self._resize_handler(width, height)

    def close(self) -> None:
        """Close the window."""
        if self._close_handler:
            if not self._close_handler():
                return  # Close prevented
        self._closed = True

    def request_redraw(self) -> None:
        """Request window redraw."""
        self._redraw_requested = True

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse cursor visibility."""
        self._mouse_visible = visible

    # Event handler setters

    def set_draw_handler(self, handler: Callable[[], None] | None) -> None:
        """Set draw callback."""
        self._draw_handler = handler

    def set_resize_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """Set resize callback."""
        self._resize_handler = handler

    def set_key_press_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """Set key press callback."""
        self._key_press_handler = handler

    def set_key_release_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """Set key release callback."""
        self._key_release_handler = handler

    def set_mouse_press_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set mouse press callback."""
        self._mouse_press_handler = handler

    def set_mouse_release_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set mouse release callback."""
        self._mouse_release_handler = handler

    def set_mouse_drag_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set mouse drag callback."""
        self._mouse_drag_handler = handler

    def set_mouse_move_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set mouse move callback."""
        self._mouse_move_handler = handler

    def set_mouse_scroll_handler(
        self, handler: Callable[[int, int, float, float], None] | None
    ) -> None:
        """Set mouse scroll callback."""
        self._mouse_scroll_handler = handler

    def set_close_handler(self, handler: Callable[[], bool] | None) -> None:
        """Set close callback."""
        self._close_handler = handler

    # Testing helpers - simulate events

    def simulate_draw(self) -> None:
        """Simulate a draw event for testing."""
        self._redraw_requested = False
        if self._draw_handler:
            self._draw_handler()

    def simulate_key_press(self, event: KeyEvent) -> None:
        """Simulate a key press event for testing."""
        if self._key_press_handler:
            self._key_press_handler(event)

    def simulate_key_release(self, event: KeyEvent) -> None:
        """Simulate a key release event for testing."""
        if self._key_release_handler:
            self._key_release_handler(event)

    def simulate_mouse_press(self, event: MouseEvent) -> None:
        """Simulate a mouse press event for testing."""
        if self._mouse_press_handler:
            self._mouse_press_handler(event)

    def simulate_mouse_release(self, event: MouseEvent) -> None:
        """Simulate a mouse release event for testing."""
        if self._mouse_release_handler:
            self._mouse_release_handler(event)

    def simulate_mouse_drag(self, event: MouseEvent) -> None:
        """Simulate a mouse drag event for testing."""
        if self._mouse_drag_handler:
            self._mouse_drag_handler(event)

    def simulate_resize(self, width: int, height: int) -> None:
        """Simulate a resize event for testing."""
        self.set_size(width, height)
