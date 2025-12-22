"""
Pyglet utility functions and classes.

Provides key/modifier conversion and text rendering utilities.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyglet.window import Window as PygletWindow
else:
    PygletWindow = Any  # Runtime: use Any since pyglet is imported dynamically

try:
    import pyglet
    # Pyglet 2.0 uses modern OpenGL by default - use gl_compat for legacy functions
    from pyglet.gl import gl_compat as gl
    from pyglet.window import key as pyglet_key
    from pyglet.window import mouse as pyglet_mouse
except ImportError as e:
    raise ImportError("pyglet2 backend requires: pip install 'pyglet>=2.0'") from e

from cube.presentation.gui.types import Keys, Modifiers, MouseButton, Color4
from cube.presentation.gui.protocols import TextRenderer


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

    def __init__(self, window: PygletWindow) -> None:
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
        # pyglet 2.x uses weight='bold' instead of bold=True
        weight = 'bold' if bold else 'normal'
        # Cast anchor values to satisfy mypy Literal types
        from typing import cast, Literal
        ax = cast(Literal['left', 'center', 'right'], anchor_x)
        ay = cast(Literal['top', 'bottom', 'center', 'baseline'], anchor_y)
        label = pyglet.text.Label(
            text,
            x=x, y=y,
            font_size=font_size,
            color=color,
            weight=weight,
            anchor_x=ax,
            anchor_y=ay,
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
