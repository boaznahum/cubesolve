"""
Pyglet window implementation.

Wraps pyglet.window.Window to implement the Window protocol.
"""

from typing import Callable, Sequence

try:
    import pyglet
    from pyglet import gl
    from pyglet.window import key as pyglet_key
    from pyglet.window import mouse as pyglet_mouse
except ImportError as e:
    raise ImportError("pyglet is required for PygletWindow: pip install pyglet") from e

from cube.gui.types import KeyEvent, MouseEvent, Keys, Modifiers, MouseButton, Color4
from cube.gui.protocols import Window as WindowProtocol, TextRenderer


# Mapping from pyglet key codes to our abstract Keys
_PYGLET_TO_KEYS: dict[int, int] = {
    pyglet_key.A: Keys.A, pyglet_key.B: Keys.B, pyglet_key.C: Keys.C,
    pyglet_key.D: Keys.D, pyglet_key.E: Keys.E, pyglet_key.F: Keys.F,
    pyglet_key.G: Keys.G, pyglet_key.H: Keys.H, pyglet_key.I: Keys.I,
    pyglet_key.J: Keys.J, pyglet_key.K: Keys.K, pyglet_key.L: Keys.L,
    pyglet_key.M: Keys.M, pyglet_key.N: Keys.N, pyglet_key.O: Keys.O,
    pyglet_key.P: Keys.P, pyglet_key.Q: Keys.Q, pyglet_key.R: Keys.R,
    pyglet_key.S: Keys.S, pyglet_key.T: Keys.T, pyglet_key.U: Keys.U,
    pyglet_key.V: Keys.V, pyglet_key.W: Keys.W, pyglet_key.X: Keys.X,
    pyglet_key.Y: Keys.Y, pyglet_key.Z: Keys.Z,
    pyglet_key._0: Keys._0, pyglet_key._1: Keys._1, pyglet_key._2: Keys._2,
    pyglet_key._3: Keys._3, pyglet_key._4: Keys._4, pyglet_key._5: Keys._5,
    pyglet_key._6: Keys._6, pyglet_key._7: Keys._7, pyglet_key._8: Keys._8,
    pyglet_key._9: Keys._9,
    pyglet_key.ESCAPE: Keys.ESCAPE, pyglet_key.SPACE: Keys.SPACE,
    pyglet_key.RETURN: Keys.RETURN, pyglet_key.TAB: Keys.TAB,
    pyglet_key.BACKSPACE: Keys.BACKSPACE, pyglet_key.DELETE: Keys.DELETE,
    pyglet_key.INSERT: Keys.INSERT,
    pyglet_key.LEFT: Keys.LEFT, pyglet_key.RIGHT: Keys.RIGHT,
    pyglet_key.UP: Keys.UP, pyglet_key.DOWN: Keys.DOWN,
    pyglet_key.F1: Keys.F1, pyglet_key.F2: Keys.F2, pyglet_key.F3: Keys.F3,
    pyglet_key.F4: Keys.F4, pyglet_key.F5: Keys.F5, pyglet_key.F6: Keys.F6,
    pyglet_key.F7: Keys.F7, pyglet_key.F8: Keys.F8, pyglet_key.F9: Keys.F9,
    pyglet_key.F10: Keys.F10, pyglet_key.F11: Keys.F11, pyglet_key.F12: Keys.F12,
    pyglet_key.HOME: Keys.HOME, pyglet_key.END: Keys.END,
    pyglet_key.PAGEUP: Keys.PAGE_UP, pyglet_key.PAGEDOWN: Keys.PAGE_DOWN,
    pyglet_key.SLASH: Keys.SLASH, pyglet_key.APOSTROPHE: Keys.APOSTROPHE,
    pyglet_key.MINUS: Keys.MINUS, pyglet_key.EQUAL: Keys.EQUAL,
    pyglet_key.COMMA: Keys.COMMA, pyglet_key.PERIOD: Keys.PERIOD,
    pyglet_key.BACKSLASH: Keys.BACKSLASH,
    pyglet_key.BRACKETLEFT: Keys.BRACKETLEFT, pyglet_key.BRACKETRIGHT: Keys.BRACKETRIGHT,
    # Numpad
    pyglet_key.NUM_ADD: Keys.NUM_ADD, pyglet_key.NUM_SUBTRACT: Keys.NUM_SUBTRACT,
    pyglet_key.NUM_0: Keys.NUM_0, pyglet_key.NUM_1: Keys.NUM_1,
    pyglet_key.NUM_2: Keys.NUM_2, pyglet_key.NUM_3: Keys.NUM_3,
    pyglet_key.NUM_4: Keys.NUM_4, pyglet_key.NUM_5: Keys.NUM_5,
    pyglet_key.NUM_6: Keys.NUM_6, pyglet_key.NUM_7: Keys.NUM_7,
    pyglet_key.NUM_8: Keys.NUM_8, pyglet_key.NUM_9: Keys.NUM_9,
    # Modifier keys
    pyglet_key.LSHIFT: Keys.LSHIFT, pyglet_key.RSHIFT: Keys.RSHIFT,
    pyglet_key.LCTRL: Keys.LCTRL, pyglet_key.RCTRL: Keys.RCTRL,
    pyglet_key.LALT: Keys.LALT, pyglet_key.RALT: Keys.RALT,
}

# Reverse mapping
_KEYS_TO_PYGLET: dict[int, int] = {v: k for k, v in _PYGLET_TO_KEYS.items()}


def _convert_modifiers(pyglet_mods: int) -> int:
    """Convert pyglet modifiers to our Modifiers flags."""
    result = 0
    if pyglet_mods & pyglet_key.MOD_SHIFT:
        result |= Modifiers.SHIFT
    if pyglet_mods & pyglet_key.MOD_CTRL:
        result |= Modifiers.CTRL
    if pyglet_mods & pyglet_key.MOD_ALT:
        result |= Modifiers.ALT
    if pyglet_mods & (pyglet_key.MOD_COMMAND | pyglet_key.MOD_WINDOWS):
        result |= Modifiers.META
    return result


def _convert_mouse_buttons(pyglet_buttons: int) -> int:
    """Convert pyglet mouse button flags to our MouseButton flags."""
    result = 0
    if pyglet_buttons & pyglet_mouse.LEFT:
        result |= MouseButton.LEFT
    if pyglet_buttons & pyglet_mouse.MIDDLE:
        result |= MouseButton.MIDDLE
    if pyglet_buttons & pyglet_mouse.RIGHT:
        result |= MouseButton.RIGHT
    return result


class PygletTextRenderer(TextRenderer):
    """Text renderer using pyglet labels."""

    def __init__(self, window: "PygletWindow") -> None:
        self._window = window
        self._labels: list[pyglet.text.Label] = []

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
        """Draw a text label."""
        label = pyglet.text.Label(
            text,
            x=x, y=y,
            font_size=font_size,
            color=color,
            bold=bold,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
        )
        self._labels.append(label)

    def clear_labels(self) -> None:
        """Clear all labels."""
        self._labels.clear()

    def render(self) -> None:
        """Render all labels (called during draw)."""
        # Set up orthographic projection for 2D text
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self._window.width, 0, self._window.height, -1, 1)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        # Disable depth test for text
        gl.glDisable(gl.GL_DEPTH_TEST)

        for label in self._labels:
            label.draw()

        gl.glEnable(gl.GL_DEPTH_TEST)

        # Restore matrices
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)


class PygletWindow(pyglet.window.Window):
    """Pyglet window implementing Window protocol (WindowProtocol).

    Inherits from pyglet.window.Window to get native window functionality,
    and adds protocol-compliant handler registration.

    Note: Cannot inherit from WindowProtocol due to metaclass conflict with pyglet.
    Protocol compliance is verified at runtime via @runtime_checkable.
    """

    def __init__(
        self,
        width: int = 720,
        height: int = 720,
        title: str = "Cube",
        resizable: bool = True,
    ) -> None:
        super().__init__(width, height, title, resizable=resizable)

        self._text = PygletTextRenderer(self)

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

    @property
    def text(self) -> PygletTextRenderer:
        """Access text renderer."""
        return self._text

    def set_title(self, title: str) -> None:
        """Set window title."""
        self.set_caption(title)

    def set_size(self, width: int, height: int) -> None:
        """Set window size."""
        super().set_size(width, height)

    def request_redraw(self) -> None:
        """Request window redraw."""
        self.invalid = True

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

    # Pyglet event overrides

    def on_draw(self) -> None:
        """Handle draw event."""
        if self._draw_handler:
            self._draw_handler()
        # Render text labels
        self._text.render()

    def on_resize(self, width: int, height: int) -> None:
        """Handle resize event."""
        super().on_resize(width, height)
        gl.glViewport(0, 0, width, height)
        if self._resize_handler:
            self._resize_handler(width, height)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle key press event."""
        if self._key_press_handler:
            abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
            abstract_mods = _convert_modifiers(modifiers)
            event = KeyEvent(symbol=abstract_symbol, modifiers=abstract_mods)
            self._key_press_handler(event)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Handle key release event."""
        if self._key_release_handler:
            abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
            abstract_mods = _convert_modifiers(modifiers)
            event = KeyEvent(symbol=abstract_symbol, modifiers=abstract_mods)
            self._key_release_handler(event)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Handle mouse press event."""
        if self._mouse_press_handler:
            abstract_mods = _convert_modifiers(modifiers)
            event = MouseEvent(x=x, y=y, button=button, modifiers=abstract_mods)
            self._mouse_press_handler(event)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Handle mouse release event."""
        if self._mouse_release_handler:
            abstract_mods = _convert_modifiers(modifiers)
            event = MouseEvent(x=x, y=y, button=button, modifiers=abstract_mods)
            self._mouse_release_handler(event)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        """Handle mouse drag event."""
        if self._mouse_drag_handler:
            abstract_mods = _convert_modifiers(modifiers)
            event = MouseEvent(x=x, y=y, dx=dx, dy=dy, button=buttons, modifiers=abstract_mods)
            self._mouse_drag_handler(event)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse motion event."""
        if self._mouse_move_handler:
            event = MouseEvent(x=x, y=y, dx=dx, dy=dy)
            self._mouse_move_handler(event)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        """Handle mouse scroll event."""
        if self._mouse_scroll_handler:
            self._mouse_scroll_handler(x, y, scroll_x, scroll_y)

    def on_close(self) -> None:
        """Handle close event."""
        if self._close_handler:
            if not self._close_handler():
                return  # Close prevented
        super().on_close()

    # Testing helpers - simulate events (for test compatibility)

    def queue_key_events(self, events: Sequence[KeyEvent]) -> None:
        """Queue key events for later processing.

        For pyglet, we store them for process_queued_key_events.
        """
        if not hasattr(self, '_key_event_queue'):
            self._key_event_queue: list[KeyEvent] = []
        self._key_event_queue.extend(events)

    def process_queued_key_events(self) -> int:
        """Process all queued key events.

        For pyglet, this calls the key handler directly.
        """
        if not hasattr(self, '_key_event_queue'):
            return 0

        count = len(self._key_event_queue)
        while self._key_event_queue:
            event = self._key_event_queue.pop(0)
            if self._key_press_handler:
                self._key_press_handler(event)
        return count

    @property
    def queued_key_event_count(self) -> int:
        """Number of queued key events."""
        if not hasattr(self, '_key_event_queue'):
            return 0
        return len(self._key_event_queue)
