"""
WindowBase - Base class with real shared implementation for Window protocol.

This class provides common window functionality that all backend Window
implementations share, including event handler storage and event queue management.

Hierarchy:
    Window (Protocol/Interface)
        └── AbstractWindow (no-op defaults)
            └── WindowBase (real shared implementation) <-- YOU ARE HERE
                └── Concrete implementations (HeadlessWindow, etc.)

Note: PygletWindow and TkinterWindow cannot inherit from WindowBase due to
metaclass conflicts with pyglet.window.Window and tkinter.Tk. They implement
the Window protocol via duck typing.
"""

from typing import Callable, Sequence

from cube.presentation.gui.types import KeyEvent, MouseEvent
from cube.presentation.gui.protocols.AbstractWindow import AbstractWindow
from cube.presentation.gui.protocols.TextRenderer import TextRenderer


class WindowBase(AbstractWindow):
    """Base class providing real shared implementation for Window protocol.

    Provides:
    - Event handler storage and setter methods
    - Event queue management for testing
    - Common window state (width, height, title, visible, closed)

    Subclasses must:
    - Provide a TextRenderer via the text property
    - Override methods that need backend-specific behavior
    """

    def __init__(
        self,
        width: int = 720,
        height: int = 720,
        title: str = "Cube",
    ) -> None:
        """Initialize window base.

        Args:
            width: Initial window width
            height: Initial window height
            title: Window title
        """
        self._width = width
        self._height = height
        self._title = title
        self._visible = False
        self._closed = False
        self._mouse_visible = True

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

        # Event queues for testing
        self._key_event_queue: list[KeyEvent] = []
        self._mouse_event_queue: list[MouseEvent] = []

        # Track redraw requests
        self._redraw_requested = False

    # Properties

    @property
    def width(self) -> int:
        """Window width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Window height in pixels."""
        return self._height

    @property
    def closed(self) -> bool:
        """Whether window has been closed."""
        return self._closed

    # Window operations

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

    # Event queue management (for testing)

    def queue_key_events(self, events: Sequence[KeyEvent]) -> None:
        """Queue key events for later processing."""
        self._key_event_queue.extend(events)

    def queue_mouse_events(self, events: Sequence[MouseEvent]) -> None:
        """Queue mouse events for later processing."""
        self._mouse_event_queue.extend(events)

    def process_queued_key_events(self) -> int:
        """Process all queued key events. Returns count processed."""
        count = len(self._key_event_queue)
        while self._key_event_queue:
            event = self._key_event_queue.pop(0)
            if self._key_press_handler:
                self._key_press_handler(event)
        return count

    def process_queued_mouse_events(self) -> int:
        """Process all queued mouse events. Returns count processed."""
        count = len(self._mouse_event_queue)
        while self._mouse_event_queue:
            event = self._mouse_event_queue.pop(0)
            if self._mouse_press_handler:
                self._mouse_press_handler(event)
        return count

    @property
    def queued_key_event_count(self) -> int:
        """Number of queued key events."""
        return len(self._key_event_queue)

    @property
    def queued_mouse_event_count(self) -> int:
        """Number of queued mouse events."""
        return len(self._mouse_event_queue)

    def has_queued_events(self) -> bool:
        """Check if there are queued events waiting."""
        return bool(self._key_event_queue or self._mouse_event_queue)

    def clear_event_queue(self) -> None:
        """Clear all queued events."""
        self._key_event_queue.clear()
        self._mouse_event_queue.clear()
