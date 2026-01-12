"""
Headless AppWindow implementation.

Provides a no-output application window for testing and automation.
"""
from __future__ import annotations

from collections.abc import Callable

from cube.application.AbstractApp import AbstractApp
from cube.application.protocols import AnimatableViewer
from cube.presentation.gui.backends.headless.HeadlessEventLoop import HeadlessEventLoop
from cube.presentation.gui.backends.headless.HeadlessRenderer import HeadlessRenderer
from cube.presentation.gui.backends.headless.HeadlessWindow import HeadlessWindow
from cube.presentation.gui.factory import GUIBackend
from cube.presentation.gui.protocols import AppWindow
from cube.presentation.gui.protocols.AppWindowBase import AppWindowBase
from cube.presentation.gui.types import KeyEvent
from cube.presentation.viewer.GCubeViewer import GCubeViewer


class HeadlessAppWindow(AppWindowBase, AppWindow):
    """Headless AppWindow implementation for testing.

    Inherits from AbstractAppWindow for shared logic and handle_key().
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
        # Initialize base class (sets _app, _backend, _animation_manager, etc.)
        super().__init__(app, backend)

        # Headless-specific attributes
        self._width = width
        self._height = height
        self._renderer: HeadlessRenderer = backend.renderer  # type: ignore
        self._event_loop: HeadlessEventLoop = backend.event_loop  # type: ignore
        self._window = HeadlessWindow(width, height, title)
        self._closed = False

        # Create viewer (for API compatibility, though not rendered)
        self._viewer = GCubeViewer(app.cube, app.vs, renderer=self._renderer)

    # app property inherited from AppWindowBase
    # animation_running property inherited from AppWindowBase

    @property
    def viewer(self) -> AnimatableViewer:
        """Access the cube viewer (AnimatableViewer protocol)."""
        assert self._viewer is not None
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
        """Access the renderer (headless-specific type)."""
        return self._renderer

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
        if self._viewer:
            self._viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

    def _request_redraw(self) -> None:
        """Request window redraw."""
        self._window.request_redraw()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse visibility (no-op in headless mode)."""
        self._window.set_mouse_visible(visible)

    # CURSOR_WAIT, get_system_mouse_cursor(), set_mouse_cursor() inherited from AppWindowBase
    # handle_key(), inject_key(), inject_command() inherited from AppWindowBase

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

    def get_opengl_info(self) -> str:
        """Get OpenGL version information (not applicable for headless).

        Returns:
            Empty string (headless backend has no OpenGL context).
        """
        return ""

    def schedule_once(self, callback: "Callable[[float], None]", delay: float) -> None:
        """Schedule a callback to run after a delay (non-blocking).

        Args:
            callback: Function to call after delay, receives dt (elapsed time)
            delay: Time in seconds to wait before calling
        """
        self._event_loop.schedule_once(callback, delay)

    # adjust_brightness() and get_brightness() inherited from AppWindowBase (return None)
