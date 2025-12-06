"""
Pyglet Window wrapper for composition pattern.

This class inherits from pyglet.window.Window and delegates all events
to a parent PygletAppWindow. This allows PygletAppWindow to inherit from
AppWindowBase and satisfy the AppWindow protocol without metaclass conflicts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import pyglet
except ImportError as e:
    raise ImportError("pyglet2 backend requires: pip install 'pyglet>=2.0'") from e

if TYPE_CHECKING:
    from cube.presentation.gui.backends.pyglet2.PygletAppWindow import PygletAppWindow


class PygletWindow(pyglet.window.Window):
    """Pyglet window that delegates events to parent PygletAppWindow.

    This wrapper allows PygletAppWindow to use composition instead of
    inheritance, avoiding metaclass conflicts with AppWindowBase.
    """

    def __init__(
        self,
        parent: "PygletAppWindow",
        width: int,
        height: int,
        title: str,
    ):
        """Initialize the pyglet window.

        Args:
            parent: The PygletAppWindow that will handle all events
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        self._parent = parent
        super().__init__(width, height, title, resizable=True)

    # === Delegate all pyglet events to parent ===

    def on_draw(self) -> None:
        """Delegate draw event to parent."""
        self._parent.on_draw()

    def on_resize(self, width: int, height: int) -> None:
        """Delegate resize event to parent."""
        self._parent.on_resize(width, height)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Delegate key press event to parent."""
        self._parent.on_key_press(symbol, modifiers)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Delegate mouse drag event to parent."""
        return self._parent.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Delegate mouse press event to parent."""
        return self._parent.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Delegate mouse release event to parent."""
        return self._parent.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Delegate mouse scroll event to parent."""
        return self._parent.on_mouse_scroll(x, y, scroll_x, scroll_y)
