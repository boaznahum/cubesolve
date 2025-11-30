"""
Console AppWindow implementation.

Provides a text-based application window for console mode.
Uses existing main_console.viewer for cube rendering.
"""

from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube.gui.factory import GUIBackend
from cube.gui.protocols.app_window import AppWindow
from cube.main_console import viewer as console_viewer
from cube.main_console.keys import Keys as ConsoleKeys

from cube.gui.backends.console.renderer import ConsoleRenderer
from cube.gui.backends.console.event_loop import ConsoleEventLoop


class ConsoleAppWindow(AppWindow):
    """Console-based AppWindow implementation.

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
        self._app = app
        self._backend = backend
        self._renderer: ConsoleRenderer = backend.renderer  # type: ignore
        self._event_loop: ConsoleEventLoop = backend.event_loop  # type: ignore
        self._title = title
        self._closed = False
        self._inv_mode = False  # Inverse mode toggle
        self._debug = False

        # Set up event loop
        self._event_loop.set_key_handler(self._handle_key)

        # Print title
        print(f"\n=== {title} ===\n")

    @property
    def app(self) -> AbstractApp:
        """Access the application instance."""
        return self._app

    @property
    def viewer(self):
        """Access the cube viewer - returns None for console mode."""
        return None

    @property
    def renderer(self) -> ConsoleRenderer:
        """Access the renderer."""
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

    def _handle_key(self, key: str) -> bool:
        """Handle a key press.

        Args:
            key: The key that was pressed (uppercase).

        Returns:
            True if the application should quit.
        """
        op = self._app.op
        slv = self._app.slv

        not_operation = False

        match key:
            case ConsoleKeys.INV:
                self._inv_mode = not self._inv_mode
                not_operation = True

            case ConsoleKeys.R:
                op.play(Algs.R, self._inv_mode)

            case ConsoleKeys.L:
                op.play(Algs.L, self._inv_mode)

            case ConsoleKeys.U:
                op.play(Algs.U, self._inv_mode)

            case ConsoleKeys.F:
                op.play(Algs.F, self._inv_mode)

            case ConsoleKeys.B:
                op.play(Algs.B, self._inv_mode)

            case ConsoleKeys.D:
                op.play(Algs.D, self._inv_mode)

            case ConsoleKeys.X:
                op.play(Algs.X, self._inv_mode)

            case ConsoleKeys.Y:
                op.play(Algs.Y, self._inv_mode)

            case ConsoleKeys.M:
                op.play(Algs.M, self._inv_mode)

            case ConsoleKeys.CLEAR:
                op.reset()

            case ConsoleKeys.SCRAMBLE_RANDOM:
                alg = Algs.scramble(self._app.cube.size)
                op.play(alg, self._inv_mode)

            case ConsoleKeys.SCRAMBLE_1 | ConsoleKeys.SCRAMBLE_2 | ConsoleKeys.SCRAMBLE_3 | \
                 ConsoleKeys.SCRAMBLE_4 | ConsoleKeys.SCRAMBLE_5 | ConsoleKeys.SCRAMBLE_6:
                alg = Algs.scramble(self._app.cube.size, int(key))
                op.play(alg, self._inv_mode)

            case ConsoleKeys.UNDO:
                op.undo()

            case ConsoleKeys.SOLVE:
                slv.solve()

            case ConsoleKeys.QUIT | ConsoleKeys.CTRL_C:
                return True  # Quit

            case _:
                not_operation = True

        if not not_operation:
            self._inv_mode = False
            self._draw()

        return False  # Continue

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press.

        Args:
            key: Key code (for console, this is the ASCII value).
            modifiers: Ignored in console mode.
        """
        # Convert key code to character
        if key < 256:
            char = chr(key).upper()
            self._handle_key(char)

    def inject_key_sequence(self, sequence: str) -> None:
        """Inject a sequence of key presses.

        Args:
            sequence: String of key characters to inject.
        """
        # Inject into event loop for processing
        self._event_loop.inject_sequence(sequence)
        self._event_loop.set_use_keyboard(False)

    def set_mouse_visible(self, visible: bool) -> None:
        """No-op for console mode."""
        pass
