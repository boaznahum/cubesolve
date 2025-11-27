"""
Window and text rendering protocol definitions.

These protocols define the interface for window management and text display.
"""

from typing import Protocol, Callable, runtime_checkable

from cube.gui.types import KeyEvent, MouseEvent, Color4


@runtime_checkable
class TextRenderer(Protocol):
    """Protocol for text rendering.

    Backends implement this to provide text display capabilities.
    """

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
        """Draw text at the specified position.

        Args:
            text: Text string to render
            x: X position in window coordinates
            y: Y position in window coordinates
            font_size: Font size in points
            color: RGBA text color
            bold: Whether to use bold font
            anchor_x: Horizontal anchor ('left', 'center', 'right')
            anchor_y: Vertical anchor ('top', 'center', 'bottom')
        """
        ...

    def clear_labels(self) -> None:
        """Clear all previously drawn labels.

        Called before redrawing text each frame.
        """
        ...


@runtime_checkable
class Window(Protocol):
    """Protocol for window management.

    Backends implement this to provide windowing capabilities.
    Event handlers are registered via set_*_handler methods.
    """

    @property
    def width(self) -> int:
        """Window width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Window height in pixels."""
        ...

    @property
    def text(self) -> TextRenderer:
        """Access text rendering capabilities."""
        ...

    def set_title(self, title: str) -> None:
        """Set window title.

        Args:
            title: Window title string
        """
        ...

    def set_visible(self, visible: bool) -> None:
        """Show or hide the window.

        Args:
            visible: True to show, False to hide
        """
        ...

    def set_size(self, width: int, height: int) -> None:
        """Set window size.

        Args:
            width: New width in pixels
            height: New height in pixels
        """
        ...

    def close(self) -> None:
        """Close the window.

        This should trigger the event loop to stop if this is the main window.
        """
        ...

    def request_redraw(self) -> None:
        """Request window redraw on next frame.

        Signals that the window contents need to be redrawn.
        """
        ...

    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor.

        Args:
            visible: True to show cursor, False to hide
        """
        ...

    # Event handler registration

    def set_draw_handler(self, handler: Callable[[], None] | None) -> None:
        """Set the draw callback.

        Args:
            handler: Function called when window needs redrawing, or None to clear
        """
        ...

    def set_resize_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """Set the resize callback.

        Args:
            handler: Function(width, height) called on window resize, or None
        """
        ...

    def set_key_press_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """Set the key press callback.

        Args:
            handler: Function(event) called on key press, or None
        """
        ...

    def set_key_release_handler(self, handler: Callable[[KeyEvent], None] | None) -> None:
        """Set the key release callback.

        Args:
            handler: Function(event) called on key release, or None
        """
        ...

    def set_mouse_press_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set the mouse button press callback.

        Args:
            handler: Function(event) called on mouse press, or None
        """
        ...

    def set_mouse_release_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set the mouse button release callback.

        Args:
            handler: Function(event) called on mouse release, or None
        """
        ...

    def set_mouse_drag_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set the mouse drag callback.

        Args:
            handler: Function(event) called on mouse drag, or None
        """
        ...

    def set_mouse_move_handler(self, handler: Callable[[MouseEvent], None] | None) -> None:
        """Set the mouse move callback (without button pressed).

        Args:
            handler: Function(event) called on mouse move, or None
        """
        ...

    def set_mouse_scroll_handler(
        self, handler: Callable[[int, int, float, float], None] | None
    ) -> None:
        """Set the mouse scroll callback.

        Args:
            handler: Function(x, y, scroll_x, scroll_y) called on scroll, or None
        """
        ...

    def set_close_handler(self, handler: Callable[[], bool] | None) -> None:
        """Set the window close callback.

        Args:
            handler: Function() called when window close is requested.
                     Return True to allow close, False to prevent.
                     If None, window always closes.
        """
        ...
