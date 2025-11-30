"""
Headless AppWindow implementation.

Provides a no-output application window for testing and automation.
"""

from cube.app.abstract_ap import AbstractApp
from cube.gui.factory import GUIBackend
from cube.gui.protocols.app_window import AppWindow
from cube.gui.types import Keys, KeyEvent
from cube.viewer.viewer_g import GCubeViewer

from cube.gui.backends.headless.renderer import HeadlessRenderer
from cube.gui.backends.headless.window import HeadlessWindow
from cube.gui.backends.headless.event_loop import HeadlessEventLoop


class HeadlessAppWindow(AppWindow):
    """Headless AppWindow implementation for testing.

    Inherits from AppWindow protocol for PyCharm visibility.

    Useful for:
    - Unit testing
    - Benchmarking solver algorithms
    - Batch processing / scripting
    - CI/CD pipelines
    """

    def __init__(
        self,
        app: AbstractApp,
        width: int,
        height: int,
        title: str,
        backend: GUIBackend,
    ):
        """Initialize the Headless AppWindow.

        Args:
            app: Application instance (cube, operator, solver)
            width: Ignored in headless mode
            height: Ignored in headless mode
            title: Ignored in headless mode
            backend: GUI backend for rendering
        """
        self._app = app
        self._backend = backend
        self._width = width
        self._height = height
        self._renderer: HeadlessRenderer = backend.renderer  # type: ignore
        self._event_loop: HeadlessEventLoop = backend.event_loop  # type: ignore
        self._window = HeadlessWindow(width, height, title)
        self._closed = False

        # Keyboard handler state
        self._last_edge_solve_count: int = 0

        # Create viewer (for API compatibility, though not rendered)
        self._viewer = GCubeViewer(app.cube, app.vs, renderer=self._renderer)

        # Animation manager connection
        self._animation_manager = app.am
        if self._animation_manager:
            self._animation_manager.set_window(self)  # type: ignore[arg-type]

    @property
    def app(self) -> AbstractApp:
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> GCubeViewer:
        """Access the cube viewer."""
        return self._viewer

    @property
    def width(self) -> int:
        """Window width (nominal, for headless)."""
        return self._width

    @property
    def height(self) -> int:
        """Window height (nominal, for headless)."""
        return self._height

    @property
    def renderer(self) -> HeadlessRenderer:
        """Access the renderer."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return bool(self._animation_manager and self._animation_manager.animation_running())

    def run(self) -> None:
        """Run the main event loop.

        In headless mode, this processes any queued events and returns.
        For continuous operation, use step() repeatedly.
        """
        # Process any queued key events
        self._window.process_queued_key_events()

        # Run event loop briefly to process callbacks
        self._event_loop.step(timeout=0.0)

    def close(self) -> None:
        """Close the application."""
        self._closed = True
        self._event_loop.stop()
        self._window.close()

    def update_gui_elements(self) -> None:
        """Update GUI elements (no-op in headless mode)."""
        self._viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

    def _request_redraw(self) -> None:
        """Request window redraw."""
        self._window.request_redraw()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse visibility (no-op in headless mode)."""
        self._window.set_mouse_visible(visible)

    # === Pyglet compatibility stubs (for keyboard handler) ===

    CURSOR_WAIT = "wait"  # Pyglet cursor constant

    def get_system_mouse_cursor(self, cursor_type: str) -> None:
        """Stub for pyglet compatibility - returns None."""
        return None

    def set_mouse_cursor(self, cursor) -> None:
        """Stub for pyglet compatibility - no-op."""
        pass

    # === Key Injection ===

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press.

        Args:
            key: Key code (from Keys enum).
            modifiers: Modifier flags.
        """
        event = KeyEvent(symbol=key, modifiers=modifiers)
        self._handle_key_event(event)

    def inject_key_sequence(self, sequence: str) -> None:
        """Inject a sequence of key presses.

        Args:
            sequence: String of key characters to inject.
        """
        key_map = {
            'R': Keys.R, 'L': Keys.L, 'U': Keys.U, 'D': Keys.D, 'F': Keys.F, 'B': Keys.B,
            'r': Keys.R, 'l': Keys.L, 'u': Keys.U, 'd': Keys.D, 'f': Keys.F, 'b': Keys.B,
            '0': Keys._0, '1': Keys._1, '2': Keys._2, '3': Keys._3, '4': Keys._4,
            '5': Keys._5, '6': Keys._6, '7': Keys._7, '8': Keys._8, '9': Keys._9,
            '/': Keys.SLASH, '?': Keys.SLASH,
            'Q': Keys.Q, 'q': Keys.Q,
            ' ': Keys.SPACE,
            '<': Keys.COMMA, ',': Keys.COMMA,
            '+': Keys.NUM_ADD, '-': Keys.NUM_SUBTRACT,
        }

        for char in sequence:
            key = key_map.get(char)
            if key is not None:
                self.inject_key(key, 0)

    def _handle_key_event(self, event: KeyEvent) -> None:
        """Handle a key event.

        Args:
            event: The key event to handle.
        """
        # Import directly to avoid pyglet dependency through main_window/__init__.py
        from cube.main_window.main_g_keyboard_input import handle_keyboard_input
        handle_keyboard_input(self, event.symbol, event.modifiers)

    # === Testing Helpers ===

    def step(self, timeout: float = 0.0) -> bool:
        """Step the event loop for testing.

        Args:
            timeout: Maximum time to wait.

        Returns:
            True if any callbacks were executed.
        """
        return self._event_loop.step(timeout)

    def queue_key_events(self, events: list[KeyEvent]) -> None:
        """Queue key events for later processing.

        Args:
            events: List of KeyEvent objects.
        """
        self._window.queue_key_events(events)

    def process_queued_events(self) -> int:
        """Process all queued key events.

        Returns:
            Number of events processed.
        """
        count = 0
        while self._window.has_queued_events():
            if self._window.process_next_key_event():
                count += 1
        return count
