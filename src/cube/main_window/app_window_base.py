"""
AppWindowBase - Shared application window logic for all backends.

This module provides the common logic that all backend AppWindow implementations
share. Backend-specific implementations (PygletAppWindow, TkinterAppWindow, etc.)
inherit from this class and implement the abstract rendering methods.

Key Handling Architecture:
- All backends call handle_key_with_error_handling() for unified keyboard input
- This function wraps main_g_keyboard_input.handle_keyboard_input() with error handling
- Backends convert their native key events to abstract Keys before calling
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence, Protocol

from cube import config
from cube.algs import Algs, Alg
from cube.app.app_exceptions import AppExit, RunStop, OpAborted
from cube.gui.types import Keys, parse_key_string, Color4
from cube.main_window import main_g_keyboard_input, main_g_mouse

if TYPE_CHECKING:
    from cube.app.abstract_ap import AbstractApp
    from cube.viewer.viewer_g import GCubeViewer
    from cube.gui.factory import GUIBackend
    from cube.gui.protocols.renderer import Renderer


class _KeyHandlerWindow(Protocol):
    """Protocol for windows that handle keyboard input."""

    @property
    def app(self) -> "AbstractApp": ...
    def close(self) -> None: ...
    def update_gui_elements(self) -> None: ...


def handle_key_with_error_handling(
    window: _KeyHandlerWindow,
    symbol: int,
    modifiers: int
) -> None:
    """Handle keyboard input with unified error handling.

    This is the SINGLE ENTRY POINT for all keyboard input from all backends.
    All backends convert their native key events to abstract Keys and call this.

    Args:
        window: The window handling the key (must implement _KeyHandlerWindow protocol)
        symbol: Key code (from Keys enum)
        modifiers: Modifier flags (from Modifiers)

    Raises:
        AppExit: In test mode, re-raised after closing window
        Exception: In test mode with QUIT_ON_ERROR_IN_TEST_MODE, re-raised after closing
    """
    try:
        main_g_keyboard_input.handle_keyboard_input(window, symbol, modifiers)  # type: ignore[arg-type]

    except (AppExit, RunStop, OpAborted) as e:
        # In test mode, AppExit should actually exit
        if config.GUI_TEST_MODE and isinstance(e, AppExit):
            window.close()
            raise
        else:
            # Normal GUI mode - show error message
            window.app.set_error("Asked to stop")
            window.update_gui_elements()

    except Exception as e:
        # In test mode, exceptions should propagate
        if config.GUI_TEST_MODE and config.QUIT_ON_ERROR_IN_TEST_MODE:
            window.close()
            raise
        else:
            # Normal GUI mode - show error in GUI
            traceback.print_exc()
            msg = str(e)
            error_text = "Some error occurred:"
            if msg:
                error_text += msg
            window.app.set_error(error_text)
            window.update_gui_elements()


@dataclass
class TextLabel:
    """Backend-agnostic text label definition.

    Backends convert these to their native text rendering format.
    """
    text: str
    x: int
    y: int
    font_size: int = 10
    color: Color4 = (255, 255, 255, 255)
    bold: bool = False


class AppWindowBase(ABC):
    """Base class for application windows.

    Provides shared logic for:
    - Keyboard input handling (delegates to main_g_keyboard_input)
    - Mouse input handling (delegates to main_g_mouse)
    - Key sequence injection
    - GUI element coordination
    - Text label building

    Subclasses must implement abstract methods for:
    - run() - Main event loop
    - close() - Close window
    - _render_text() - Render text labels
    - _request_redraw() - Request window redraw
    """

    # Pyglet cursor constant (for compatibility with keyboard handler)
    CURSOR_WAIT = "wait"

    def __init__(self, app: "AbstractApp", backend: "GUIBackend"):
        """Initialize the base window.

        Args:
            app: Application instance providing cube, operator, solver
            backend: GUI backend for rendering and events
        """
        self._app = app
        self._backend = backend
        self._viewer: "GCubeViewer | None" = None
        self._animation_manager = app.am

        # Keyboard handler state
        self._last_edge_solve_count: int = 0

        # Connect animation manager to this window
        if self._animation_manager:
            self._animation_manager.set_window(self)  # type: ignore[arg-type]

        # Text labels built by update_text()
        self._status_labels: list[TextLabel] = []
        self._animation_labels: list[TextLabel] = []

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> "GCubeViewer":
        """Access the cube viewer."""
        if self._viewer is None:
            raise RuntimeError("Viewer not initialized")
        return self._viewer

    @property
    def renderer(self) -> "Renderer":
        """Access the renderer."""
        return self._backend.renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return bool(self._animation_manager and self._animation_manager.animation_running())

    @abstractmethod
    def run(self) -> None:
        """Run the main event loop. Blocks until close() is called."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the window and stop the event loop."""
        ...

    @abstractmethod
    def _request_redraw(self) -> None:
        """Request window redraw on next frame."""
        ...

    @abstractmethod
    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor."""
        ...

    def get_system_mouse_cursor(self, cursor_type: str) -> None:
        """Get a system mouse cursor. Returns None for non-pyglet backends."""
        return None

    def set_mouse_cursor(self, cursor: object) -> None:
        """Set the mouse cursor. No-op for non-pyglet backends."""
        pass

    def update_gui_elements(self) -> None:
        """Update all GUI elements after state changes.

        Coordinates viewer update, animation manager update, and text updates.
        """
        if self._viewer:
            self._viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

        self._update_animation_text()

        if not self.animation_running:
            self._update_status_text()

        self._request_redraw()

    def _on_native_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle a key press from any backend.

        This is the SINGLE ENTRY POINT for all keyboard input.
        All backends convert their native events to abstract keys and call this.

        Args:
            symbol: Key code (from Keys enum)
            modifiers: Modifier flags (from Modifiers)
        """
        handle_key_with_error_handling(self, symbol, modifiers)

    def handle_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle a key press event.

        DEPRECATED: Use _on_native_key_press() instead.
        This method exists for backward compatibility.
        """
        self._on_native_key_press(symbol, modifiers)

    def handle_mouse_drag(self, x: int, y: int, dx: int, dy: int,
                          buttons: int, modifiers: int) -> None:
        """Handle mouse drag event.

        Args:
            x, y: Current mouse position
            dx, dy: Movement delta
            buttons: Mouse button flags
            modifiers: Modifier flags
        """
        main_g_mouse.on_mouse_drag(self, x, y, dx, dy, buttons, modifiers)  # type: ignore[arg-type]

    def handle_mouse_press(self, x: int, y: int, modifiers: int) -> None:
        """Handle mouse press event.

        Args:
            x, y: Mouse position
            modifiers: Modifier flags
        """
        main_g_mouse.on_mouse_press(self, self._app.vs, x, y, modifiers)  # type: ignore[arg-type]

    def handle_mouse_release(self) -> None:
        """Handle mouse release event."""
        main_g_mouse.on_mouse_release()

    def handle_mouse_scroll(self, scroll_y: float) -> None:
        """Handle mouse scroll event.

        Args:
            scroll_y: Vertical scroll amount
        """
        main_g_mouse.on_mouse_scroll(self, scroll_y)  # type: ignore[arg-type]

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press.

        Args:
            key: Key code (from Keys enum)
            modifiers: Modifier flags
        """
        self._on_native_key_press(key, modifiers)

    def inject_key_sequence(self, sequence: str) -> None:
        """Inject a sequence of key presses.

        Common sequences:
        - "RURU" - Manual moves
        - "1" - Scramble preset 1
        - "?" or "/" - Solve
        - "Q" - Quit

        Args:
            sequence: String of key characters
        """
        # Extend the mapping for cube-specific commands
        extended_map = {
            '?': Keys.SLASH,  # Solve command
            '<': Keys.COMMA,  # Undo
            '+': Keys.NUM_ADD,
            '-': Keys.NUM_SUBTRACT,
        }

        for char in sequence:
            # Check extended map first
            if char in extended_map:
                self.inject_key(extended_map[char], 0)
            else:
                # Use parse_key_string for standard keys
                events = parse_key_string(char)
                for event in events:
                    self.inject_key(event.symbol, event.modifiers)

    def _update_status_text(self) -> None:
        """Build status text labels.

        Updates self._status_labels with TextLabel objects that backends render.
        """
        app = self._app
        slv = app.slv
        cube = app.cube
        vs = app.vs
        op = app.op

        def _b(b: bool) -> str:
            return "On" if b else "Off"

        self._status_labels.clear()
        y = 10

        # Status line
        self._status_labels.append(TextLabel(
            f"Status:{slv.status}", x=10, y=y, font_size=10
        ))
        y += 20

        # History (simplified)
        h = Algs.simplify(*op.history(remove_scramble=True))
        sh = str(h)[-120:]
        self._status_labels.append(TextLabel(
            f"History(simplified): #{h.count()}  {sh}", x=10, y=y, font_size=10
        ))
        y += 20

        # History (full)
        hist = op.history()
        sh = str(h)[-70:]
        self._status_labels.append(TextLabel(
            f"History: #{Algs.count(*hist)}  {sh}", x=10, y=y, font_size=10
        ))
        y += 20

        # Recording state
        is_recording = op.is_recording
        s = f"Recording: {_b(is_recording)}"
        recording: Sequence[Alg] | None = vs.last_recording
        if recording is not None:
            sh = str(recording)[-70:]
            s += f", #{Algs.count(*recording)}  {sh}"
        self._status_labels.append(TextLabel(s, x=10, y=y, font_size=10))
        y += 20

        # Help line
        help_text = "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q 0-9 scramble1, <undo, Test"
        self._status_labels.append(TextLabel(help_text, x=10, y=y, font_size=10))
        y += 20

        # Sanity and error
        s = f"Sanity:{cube.is_sanity(force_check=True)}"
        if app.error:
            s += f", Error:{app.error}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(255, 0, 0, 255), bold=True
        ))
        y += 20

        # Animation settings
        s = f"Animation:{_b(op.animation_enabled)}"
        s += f", [{vs.get_speed_index}] {vs.get_speed.get_speed()}"
        s += f", Sanity check:{_b(config.CHECK_CUBE_SANITY)}"
        s += f", Debug={_b(slv.is_debug_config_mode)}"
        s += f", SS Mode:{_b(vs.single_step_mode)}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(255, 255, 0, 255), bold=True
        ))
        y += 20

        # Solver info
        s = f"Solver:{slv.name},"
        s += f"S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"
        s += f", Slices  [{vs.slice_start}, {vs.slice_stop}]"
        s += f", {vs.slice_alg(cube, Algs.L)}"
        s += f", {vs.slice_alg(cube, Algs.M)}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(0, 255, 0, 255), bold=True
        ))
        y += 20

        # Pause message
        if vs.paused_on_single_step_mode:
            self._status_labels.append(TextLabel(
                f"PAUSED: {vs.paused_on_single_step_mode}. press space",
                x=10, y=y, font_size=15, color=(0, 255, 0, 255), bold=True
            ))

    def _update_animation_text(self) -> None:
        """Build animation text labels.

        Updates self._animation_labels with TextLabel objects.
        """
        vs = self._app.vs
        self._animation_labels.clear()

        at = vs.animation_text
        for i in range(3):
            prop = config.ANIMATION_TEXT[i]
            line = at.get_line(i)
            if line:
                x = prop[0]
                # Note: y needs window height - backends handle this
                y_from_top = prop[1]
                size = prop[2]
                color: Color4 = prop[3]
                bold: bool = prop[4]
                self._animation_labels.append(TextLabel(
                    line, x=x, y=y_from_top, font_size=size, color=color, bold=bold
                ))

    @property
    def status_labels(self) -> list[TextLabel]:
        """Get current status text labels."""
        return self._status_labels

    @property
    def animation_labels(self) -> list[TextLabel]:
        """Get current animation text labels."""
        return self._animation_labels
