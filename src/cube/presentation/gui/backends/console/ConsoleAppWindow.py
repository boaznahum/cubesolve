"""
Console AppWindow implementation.

Provides a text-based application window for console mode.
Uses existing main_console.viewer for cube rendering.

Key Handling:
- Console keys are mapped to abstract Keys
- Inverse mode (') sets SHIFT modifier
- All command logic is in handle_key() via lookup_command + command.execute()
"""

from cube.application.AbstractApp import AbstractApp
from cube.presentation.gui.factory import GUIBackend
from cube.presentation.gui.protocols import AppWindow
from cube.presentation.gui.types import Keys, Modifiers
from cube.presentation.gui.backends.pyglet.AppWindowBase import AppWindowBase

from cube.presentation.gui.backends.console import ConsoleViewer as console_viewer
from cube.presentation.gui.backends.console.ConsoleKeys import Keys as ConsoleKeys

from cube.presentation.gui.backends.console.ConsoleRenderer import ConsoleRenderer
from cube.presentation.gui.backends.console.ConsoleEventLoop import ConsoleEventLoop


# Mapping from console key characters to abstract Keys
_CONSOLE_TO_KEYS: dict[str, int] = {
    ConsoleKeys.R: Keys.R,
    ConsoleKeys.L: Keys.L,
    ConsoleKeys.U: Keys.U,
    ConsoleKeys.F: Keys.F,
    ConsoleKeys.B: Keys.B,
    ConsoleKeys.D: Keys.D,
    ConsoleKeys.X: Keys.X,
    ConsoleKeys.Y: Keys.Y,
    ConsoleKeys.M: Keys.M,
    ConsoleKeys.CLEAR: Keys.C,
    ConsoleKeys.SCRAMBLE_RANDOM: Keys._0,
    ConsoleKeys.SCRAMBLE_1: Keys._1,
    ConsoleKeys.SCRAMBLE_2: Keys._2,
    ConsoleKeys.SCRAMBLE_3: Keys._3,
    ConsoleKeys.SCRAMBLE_4: Keys._4,
    ConsoleKeys.SCRAMBLE_5: Keys._5,
    ConsoleKeys.SCRAMBLE_6: Keys._6,
    ConsoleKeys.SOLVE: Keys.SLASH,
    ConsoleKeys.UNDO: Keys.COMMA,
    ConsoleKeys.QUIT: Keys.Q,
}


class ConsoleAppWindow(AppWindowBase, AppWindow):
    """Console-based AppWindow implementation.

    Inherits from AppWindowBase for shared logic and handle_key().
    Inherits from AppWindow protocol for PyCharm visibility.
    Uses console_viewer.plot() for text-based cube display.
    """

    def __init__(
        self,
        app: AbstractApp,
        width: int,
        height: int,
        title: str,
        backend: GUIBackend,
    ):
        """Initialize the Console AppWindow.

        Args:
            app: Application instance (cube, operator, solver)
            width: Ignored in console mode
            height: Ignored in console mode
            title: Window title (printed to console)
            backend: GUI backend for rendering
        """
        # Initialize base class (sets _app, _backend, _animation_manager, etc.)
        super().__init__(app, backend)

        # Console doesn't support animation - disable animation manager
        self._animation_manager = None

        # Console-specific attributes
        self._renderer: ConsoleRenderer = backend.renderer  # type: ignore
        self._event_loop: ConsoleEventLoop = backend.event_loop  # type: ignore
        self._title = title
        self._closed = False
        self._inv_mode = False  # Inverse mode toggle
        self._debug = False

        # Set up event loop - pass our on_key_press as the handler
        self._event_loop.set_key_handler(self._on_console_key_event)

        # Print title
        print(f"\n=== {title} ===\n")

    @property
    def renderer(self) -> ConsoleRenderer:
        """Access the renderer (console-specific type)."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Console mode doesn't support animation."""
        return False

    def run(self) -> None:
        """Run the main event loop."""
        self._draw()
        self._event_loop.run()

    def close(self) -> None:
        """Close the application."""
        self._closed = True
        self._event_loop.stop()

    def update_gui_elements(self) -> None:
        """Update GUI - redraw the cube."""
        self._draw()

    def _draw(self) -> None:
        """Draw the cube using text-based viewer."""
        if self._closed:
            return

        print("\n" + "=" * 40)
        console_viewer.plot(self._app.cube)
        print("=" * 40)
        self._print_status()

    def _print_status(self) -> None:
        """Print status information."""
        app = self._app
        cube = app.cube
        slv = app.slv
        op = app.op

        print(f"Status: {slv.status}")
        print(f"Solved: {cube.solved}")
        print(f"History: #{op.count}")

        if self._inv_mode:
            print("[INV MODE ON] ", end="")

        if app.error:
            print(f"Error: {app.error}")

        print("\nCommands: R L U F B D (faces), X Y M (rotations)")
        print("          ' (inv toggle), 0-6 (scramble), ? (solve), < (undo), C (clear), Q (quit)")

    def _on_console_key_event(self, key: str) -> bool:
        """Native key event handler from ConsoleEventLoop.

        Converts console key to abstract Keys and calls handle_key().

        Args:
            key: The key that was pressed (uppercase).

        Returns:
            True if the application should quit.
        """
        # Handle inverse mode toggle (console-specific state)
        if key == ConsoleKeys.INV:
            self._inv_mode = not self._inv_mode
            return False

        # Handle Ctrl+C as quit
        if key == ConsoleKeys.CTRL_C:
            return True

        # Convert console key to abstract key
        abstract_key = _CONSOLE_TO_KEYS.get(key)
        if abstract_key is None:
            return False  # Unknown key, ignore

        # Apply modifiers (inverse mode → SHIFT)
        modifiers = Modifiers.SHIFT if self._inv_mode else 0

        # Call protocol method
        self.handle_key(abstract_key, modifiers)

        # Reset inverse mode after operation
        self._inv_mode = False

        # Redraw after command
        self._draw()

        # Check for quit
        return abstract_key == Keys.Q

    # handle_key() inherited from AppWindowBase
    # inject_key() inherited from AppWindowBase

    def set_mouse_visible(self, visible: bool) -> None:
        """No-op for console mode."""
        pass

    def _request_redraw(self) -> None:
        """Request redraw (no-op for console mode - draws immediately)."""
        pass

    def get_opengl_info(self) -> str:
        """Get OpenGL version information (not applicable for console).

        Returns:
            Empty string (console backend has no OpenGL context).
        """
        return ""
