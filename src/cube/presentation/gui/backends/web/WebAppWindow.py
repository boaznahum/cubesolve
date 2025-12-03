"""
Web application window implementation.

High-level window combining GUI and application logic.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from cube.presentation.gui.backends.web.WebWindow import WebWindow
from cube.presentation.gui.backends.web.WebRenderer import WebRenderer
from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop
from cube.presentation.gui.Command import Command, CommandContext
from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.application import config

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.viewer.GCubeViewer import GCubeViewer
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory


class WebAppWindow:
    """Web application window implementing AppWindow protocol.

    Combines WebWindow, WebRenderer, and WebEventLoop with
    application logic (cube, solver, animation).
    """

    def __init__(
        self,
        app: "AbstractApp",
        width: int,
        height: int,
        title: str,
        backend: "GUIBackendFactory",
    ):
        self._app = app
        self._width = width
        self._height = height
        self._title = title

        # Get components from backend (singletons)
        self._renderer: WebRenderer = backend.renderer  # type: ignore[assignment]
        self._event_loop: WebEventLoop = backend.event_loop  # type: ignore[assignment]
        self._window: WebWindow = backend.create_window(width, height, title)  # type: ignore[assignment]

        # Wire renderer to event loop for WebSocket communication
        self._renderer.set_event_loop(self._event_loop)

        # Create viewer
        from cube.presentation.viewer.GCubeViewer import GCubeViewer
        self._viewer = GCubeViewer(app.cube, app.vs, self._renderer)

        # Set up event handlers
        self._setup_handlers()

        # Animation state
        self._animation_running = False

    def _setup_handlers(self) -> None:
        """Set up window event handlers."""
        self._window.set_draw_handler(self._on_draw)
        self._window.set_resize_handler(self._on_resize)
        self._window.set_key_press_handler(self._on_key_press)
        self._window.set_close_handler(self._on_close)

    def _on_draw(self) -> None:
        """Handle draw event."""
        self._renderer.begin_frame()
        self._renderer.clear((217, 217, 217, 255))  # Light gray background

        # Set up view
        self._renderer.view.set_projection(self._width, self._height)
        self._renderer.view.load_identity()
        self._renderer.view.translate(0, 0, -400)

        # Draw cube
        self._viewer.draw()

        self._renderer.end_frame()

    def _on_resize(self, width: int, height: int) -> None:
        """Handle resize event."""
        self._width = width
        self._height = height
        self._renderer.view.set_projection(width, height)

    def _on_key_press(self, event) -> None:
        """Handle key press event."""
        from cube.presentation.gui.key_bindings import lookup_command

        command = lookup_command(event.symbol, event.modifiers, self._animation_running)
        if command:
            self.inject_command(command)

    def _on_close(self) -> None:
        """Handle close event."""
        self._event_loop.stop()

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> "GCubeViewer":
        """Access the cube viewer."""
        return self._viewer

    @property
    def renderer(self) -> WebRenderer:
        """Access the renderer."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return self._animation_running

    def run(self) -> None:
        """Run the main event loop."""
        # Initial draw after client connects
        self._event_loop.schedule_once(lambda dt: self._on_draw(), 0.5)

        # Run event loop (blocking)
        self._event_loop.run()

    def close(self) -> None:
        """Close the window and stop the event loop."""
        self._viewer.cleanup()
        self._renderer.cleanup()
        self._event_loop.stop()

    def update_gui_elements(self) -> None:
        """Update all GUI elements."""
        self._on_draw()

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a key press event."""
        self._window.simulate_key_press(key, modifiers)

    def inject_command(self, command: Command) -> None:
        """Inject a command directly."""
        try:
            ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
            result = command.execute(ctx)
            if not result.no_gui_update:
                self.update_gui_elements()
        except AppExit:
            if config.GUI_TEST_MODE:
                self.close()
                raise
            else:
                self._app.set_error("Asked to stop")
                self.update_gui_elements()
        except Exception as e:
            if config.GUI_TEST_MODE and config.QUIT_ON_ERROR_IN_TEST_MODE:
                self.close()
                raise
            else:
                traceback.print_exc()
                msg = str(e)
                error_text = "Some error occurred:"
                if msg:
                    error_text += msg
                self._app.set_error(error_text)
                self.update_gui_elements()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse visibility."""
        self._window.set_mouse_visible(visible)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._viewer:
            self._viewer.cleanup()
        self._renderer.cleanup()

    def get_opengl_info(self) -> str:
        """Get OpenGL info string (not applicable for web backend)."""
        return "Web Backend (WebGL in browser)"

    def adjust_brightness(self, delta: float) -> float | None:
        """Adjust lighting brightness (not supported in web backend)."""
        return None

    def get_brightness(self) -> float | None:
        """Get current brightness level (not supported in web backend)."""
        return None
