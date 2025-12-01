"""
Tkinter window implementation.

Provides a tk.Tk window with Canvas for 2D rendering.
"""

import tkinter as tk
from typing import Callable

from cube.presentation.gui.types import KeyEvent, MouseEvent, Color4, Keys, Modifiers, MouseButton
from cube.presentation.gui.protocols import Window as WindowProtocol, TextRenderer


# Key mapping from Tkinter keysyms to abstract Keys
_TK_KEY_MAP = {
    # Letters (lowercase and uppercase)
    "a": Keys.A, "b": Keys.B, "c": Keys.C, "d": Keys.D, "e": Keys.E,
    "f": Keys.F, "g": Keys.G, "h": Keys.H, "i": Keys.I, "j": Keys.J,
    "k": Keys.K, "l": Keys.L, "m": Keys.M, "n": Keys.N, "o": Keys.O,
    "p": Keys.P, "q": Keys.Q, "r": Keys.R, "s": Keys.S, "t": Keys.T,
    "u": Keys.U, "v": Keys.V, "w": Keys.W, "x": Keys.X, "y": Keys.Y,
    "z": Keys.Z,
    "A": Keys.A, "B": Keys.B, "C": Keys.C, "D": Keys.D, "E": Keys.E,
    "F": Keys.F, "G": Keys.G, "H": Keys.H, "I": Keys.I, "J": Keys.J,
    "K": Keys.K, "L": Keys.L, "M": Keys.M, "N": Keys.N, "O": Keys.O,
    "P": Keys.P, "Q": Keys.Q, "R": Keys.R, "S": Keys.S, "T": Keys.T,
    "U": Keys.U, "V": Keys.V, "W": Keys.W, "X": Keys.X, "Y": Keys.Y,
    "Z": Keys.Z,
    # Numbers (use _0 style for the Keys class)
    "0": Keys._0, "1": Keys._1, "2": Keys._2, "3": Keys._3,
    "4": Keys._4, "5": Keys._5, "6": Keys._6, "7": Keys._7,
    "8": Keys._8, "9": Keys._9,
    # Special keys
    "Escape": Keys.ESCAPE, "Return": Keys.RETURN, "space": Keys.SPACE,
    "Tab": Keys.TAB, "BackSpace": Keys.BACKSPACE,
    "Left": Keys.LEFT, "Right": Keys.RIGHT, "Up": Keys.UP, "Down": Keys.DOWN,
    "Home": Keys.HOME, "End": Keys.END, "Page_Up": Keys.PAGE_UP, "Page_Down": Keys.PAGE_DOWN,
    "Insert": Keys.INSERT, "Delete": Keys.DELETE,
    # Punctuation
    "plus": Keys.PLUS, "minus": Keys.MINUS, "equal": Keys.EQUAL,
    "slash": Keys.SLASH, "backslash": Keys.BACKSLASH,
    "bracketleft": Keys.BRACKETLEFT, "bracketright": Keys.BRACKETRIGHT,
    "apostrophe": Keys.APOSTROPHE, "comma": Keys.COMMA, "period": Keys.PERIOD,
    # Function keys
    "F1": Keys.F1, "F2": Keys.F2, "F3": Keys.F3, "F4": Keys.F4,
    "F5": Keys.F5, "F6": Keys.F6, "F7": Keys.F7, "F8": Keys.F8,
    "F9": Keys.F9, "F10": Keys.F10, "F11": Keys.F11, "F12": Keys.F12,
}


def _convert_modifiers(state: int | str) -> int:
    """Convert Tkinter modifier state to abstract Modifiers.

    Args:
        state: Tkinter modifier state (usually int, but can be str in some edge cases)
    """
    # Tkinter event.state can sometimes be a string representation
    if isinstance(state, str):
        try:
            state = int(state)
        except ValueError:
            return 0

    mods = 0
    if state & 0x0001:  # Shift
        mods |= Modifiers.SHIFT
    if state & 0x0004:  # Control
        mods |= Modifiers.CTRL
    if state & 0x0008:  # Alt (Mod1)
        mods |= Modifiers.ALT
    if state & 0x0080:  # Meta/Command (Mod4 on some systems)
        mods |= Modifiers.META
    return mods


def _convert_mouse_button(num: int) -> int:
    """Convert Tkinter mouse button number to abstract MouseButton."""
    if num == 1:
        return MouseButton.LEFT
    elif num == 2:
        return MouseButton.MIDDLE
    elif num == 3:
        return MouseButton.RIGHT
    return 0


class TkinterTextRenderer(TextRenderer):
    """Text renderer using Tkinter Canvas text items."""

    def __init__(self, get_canvas: Callable):
        self._get_canvas = get_canvas
        self._label_ids: list[int] = []

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
        """Draw text at position."""
        canvas = self._get_canvas()
        if not canvas:
            return

        # Convert color to hex
        r, g, b, a = color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # Convert anchor to Tkinter anchor
        anchor_map = {
            ("left", "top"): "nw",
            ("left", "center"): "w",
            ("left", "bottom"): "sw",
            ("center", "top"): "n",
            ("center", "center"): "center",
            ("center", "bottom"): "s",
            ("right", "top"): "ne",
            ("right", "center"): "e",
            ("right", "bottom"): "se",
        }
        tk_anchor = anchor_map.get((anchor_x, anchor_y), "sw")

        # Font
        weight = "bold" if bold else "normal"
        font = ("TkDefaultFont", font_size, weight)

        item_id = canvas.create_text(x, y, text=text, fill=hex_color, anchor=tk_anchor, font=font)
        self._label_ids.append(item_id)

    def clear_labels(self) -> None:
        """Clear all text labels."""
        canvas = self._get_canvas()
        if canvas:
            for item_id in self._label_ids:
                canvas.delete(item_id)
        self._label_ids.clear()


class TkinterWindow(WindowProtocol):
    """Tkinter window with Canvas for rendering.

    Creates a tk.Tk root window with a Canvas widget for 2D rendering.
    """

    def __init__(self, width: int = 720, height: int = 720, title: str = "Cube"):
        self._width = width
        self._height = height
        self._title = title
        self._visible = False
        self._closed = False
        self._mouse_visible = True

        # Create Tk root window
        self._root = tk.Tk()
        self._root.title(title)
        self._root.geometry(f"{width}x{height}")
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Create canvas
        self._canvas = tk.Canvas(
            self._root,
            width=width,
            height=height,
            bg="#d9d9d9",
            highlightthickness=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Text renderer
        self._text = TkinterTextRenderer(lambda: self._canvas)

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

        # Track mouse state for drag detection
        self._mouse_pressed = False
        self._last_mouse_x = 0
        self._last_mouse_y = 0

        # Bind events
        self._bind_events()

    def _bind_events(self) -> None:
        """Bind Tkinter events to handlers."""
        # Keyboard
        self._root.bind("<KeyPress>", self._on_key_press)
        self._root.bind("<KeyRelease>", self._on_key_release)

        # Mouse
        self._canvas.bind("<ButtonPress>", self._on_mouse_press)
        self._canvas.bind("<ButtonRelease>", self._on_mouse_release)
        self._canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self._canvas.bind("<B2-Motion>", self._on_mouse_drag)
        self._canvas.bind("<B3-Motion>", self._on_mouse_drag)
        self._canvas.bind("<Motion>", self._on_mouse_move)
        self._canvas.bind("<MouseWheel>", self._on_mouse_scroll)  # Windows/Mac
        self._canvas.bind("<Button-4>", self._on_mouse_scroll)    # Linux scroll up
        self._canvas.bind("<Button-5>", self._on_mouse_scroll)    # Linux scroll down

        # Window resize
        self._canvas.bind("<Configure>", self._on_configure)

    def _on_key_press(self, event: tk.Event) -> None:
        """Handle key press event."""
        if self._key_press_handler:
            key_event = self._convert_key_event(event)
            if key_event:
                self._key_press_handler(key_event)

    def _on_key_release(self, event: tk.Event) -> None:
        """Handle key release event."""
        if self._key_release_handler:
            key_event = self._convert_key_event(event)
            if key_event:
                self._key_release_handler(key_event)

    def _convert_key_event(self, event: tk.Event) -> KeyEvent | None:
        """Convert Tkinter key event to abstract KeyEvent."""
        keysym = event.keysym
        symbol = _TK_KEY_MAP.get(keysym, 0)
        if symbol == 0 and len(keysym) == 1:
            # Try to map single character
            symbol = ord(keysym.upper()) if keysym.isalpha() else ord(keysym)

        modifiers = _convert_modifiers(event.state)
        char = event.char if event.char else None

        return KeyEvent(symbol=symbol, modifiers=modifiers, char=char)

    def _on_mouse_press(self, event: tk.Event) -> None:
        """Handle mouse press event."""
        self._mouse_pressed = True
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

        if self._mouse_press_handler:
            mouse_event = MouseEvent(
                x=event.x,
                y=self._height - event.y,  # Convert to bottom-left origin
                dx=0,
                dy=0,
                button=_convert_mouse_button(event.num),
                modifiers=_convert_modifiers(event.state)
            )
            self._mouse_press_handler(mouse_event)

    def _on_mouse_release(self, event: tk.Event) -> None:
        """Handle mouse release event."""
        self._mouse_pressed = False

        if self._mouse_release_handler:
            mouse_event = MouseEvent(
                x=event.x,
                y=self._height - event.y,
                dx=0,
                dy=0,
                button=_convert_mouse_button(event.num),
                modifiers=_convert_modifiers(event.state)
            )
            self._mouse_release_handler(mouse_event)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        """Handle mouse drag event."""
        if self._mouse_drag_handler:
            dx = event.x - self._last_mouse_x
            dy = self._last_mouse_y - event.y  # Flip Y

            mouse_event = MouseEvent(
                x=event.x,
                y=self._height - event.y,
                dx=dx,
                dy=dy,
                button=MouseButton.LEFT,  # Tkinter doesn't tell us which button during drag
                modifiers=_convert_modifiers(event.state)
            )
            self._mouse_drag_handler(mouse_event)

        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Handle mouse move event (no button pressed)."""
        if self._mouse_move_handler and not self._mouse_pressed:
            mouse_event = MouseEvent(
                x=event.x,
                y=self._height - event.y,
                dx=0,
                dy=0,
                button=0,
                modifiers=_convert_modifiers(event.state)
            )
            self._mouse_move_handler(mouse_event)

    def _on_mouse_scroll(self, event: tk.Event) -> None:
        """Handle mouse scroll event."""
        if self._mouse_scroll_handler:
            # Windows/Mac use event.delta, Linux uses Button-4/5
            if hasattr(event, 'delta'):
                scroll_y = event.delta / 120.0  # Normalize
            elif event.num == 4:
                scroll_y = 1.0
            elif event.num == 5:
                scroll_y = -1.0
            else:
                scroll_y = 0.0

            self._mouse_scroll_handler(event.x, self._height - event.y, 0.0, scroll_y)

    def _on_configure(self, event: tk.Event) -> None:
        """Handle window resize event."""
        if event.width != self._width or event.height != self._height:
            self._width = event.width
            self._height = event.height
            if self._resize_handler:
                self._resize_handler(event.width, event.height)

    def _on_close(self) -> None:
        """Handle window close event."""
        if self._close_handler:
            if not self._close_handler():
                return  # Close prevented
        self._closed = True
        self._root.destroy()

    @property
    def width(self) -> int:
        """Window width."""
        return self._width

    @property
    def height(self) -> int:
        """Window height."""
        return self._height

    @property
    def text(self) -> TkinterTextRenderer:
        """Access text renderer."""
        return self._text

    @property
    def canvas(self) -> tk.Canvas:
        """Access the canvas (for renderer)."""
        return self._canvas

    @property
    def root(self) -> tk.Tk:
        """Access the root window (for event loop)."""
        return self._root

    @property
    def closed(self) -> bool:
        """Whether window has been closed."""
        return self._closed

    def set_title(self, title: str) -> None:
        """Set window title."""
        self._title = title
        self._root.title(title)

    def set_visible(self, visible: bool) -> None:
        """Set window visibility."""
        self._visible = visible
        if visible:
            self._root.deiconify()
        else:
            self._root.withdraw()

    def set_size(self, width: int, height: int) -> None:
        """Set window size."""
        self._width = width
        self._height = height
        self._root.geometry(f"{width}x{height}")
        self._canvas.configure(width=width, height=height)

    def close(self) -> None:
        """Close the window."""
        self._on_close()

    def request_redraw(self) -> None:
        """Request window redraw."""
        if self._draw_handler and not self._closed:
            # Schedule redraw on next idle
            self._root.after_idle(self._do_redraw)

    def _do_redraw(self) -> None:
        """Perform the actual redraw."""
        if self._draw_handler and not self._closed:
            self._draw_handler()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse cursor visibility."""
        self._mouse_visible = visible
        if visible:
            self._root.config(cursor="")
        else:
            self._root.config(cursor="none")

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
