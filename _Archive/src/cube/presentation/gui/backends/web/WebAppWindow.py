"""
Web application window implementation.

Thin shell that creates a SessionManager and delegates per-client logic
to ClientSession instances. Maintains AppWindow protocol compatibility.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from cube.presentation.gui.backends.web.SessionManager import SessionManager
from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop
from cube.presentation.gui.backends.web.WebRenderer import WebRenderer
from cube.presentation.gui.commands import Command
from cube.presentation.gui.protocols.AppWindow import AppWindow

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.gui.commands import CommandSequence
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory
    from cube.presentation.viewer.GCubeViewer import GCubeViewer


class WebAppWindow(AppWindow):
    """Web application window implementing AppWindow protocol.

    Acts as a thin shell: creates a SessionManager that manages per-client
    sessions. Each browser gets its own independent cube via ClientSession.

    Keeps minimal state for AppWindow protocol compatibility (e.g., the
    ``app`` property used by the backend factory).
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
        self._backend = backend
        self._width = width
        self._height = height
        self._title = title
        self._last_edge_solve_count: int = 0

        # Get event loop from backend (singleton)
        self._event_loop: WebEventLoop = backend.event_loop  # type: ignore[assignment]

        # Configure event loop with test mode from app config
        self._event_loop.gui_test_mode = app.config.gui_test_mode

        # Create session manager and wire to event loop
        self._session_manager = SessionManager(
            self._event_loop, gui_test_mode=app.config.gui_test_mode
        )
        self._event_loop.set_session_manager(self._session_manager)

    # ── AppWindow protocol properties ──

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def app(self) -> "AbstractApp":
        return self._app

    @property
    def backend(self) -> "GUIBackendFactory":
        return self._backend

    @property
    def viewer(self) -> "GCubeViewer":
        """Not applicable — each session has its own viewer."""
        raise RuntimeError("WebAppWindow does not have a single viewer; use ClientSession.viewer")

    @property
    def renderer(self) -> WebRenderer:
        """Singleton renderer from factory (stub — real rendering is per-session)."""
        return self._backend.renderer  # type: ignore[return-value]

    @property
    def animation_running(self) -> bool:
        """Check if any session has animation running."""
        for session in self._session_manager.all_sessions:
            if session.animation_running:
                return True
        return False

    # ── Lifecycle ──

    def run(self) -> None:
        """Run the main event loop (blocking)."""
        self._event_loop.run()

    def close(self) -> None:
        """Close and stop the event loop."""
        self._event_loop.stop()

    def cleanup(self) -> None:
        """Clean up resources."""
        for session in self._session_manager.all_sessions:
            session.cleanup()

    # ── Stubs for AppWindow protocol ──

    def update_gui_elements(self) -> None:
        """Update all sessions' GUI elements."""
        for session in self._session_manager.all_sessions:
            session.update_gui_elements()

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject key to all sessions (for testing)."""
        for session in self._session_manager.all_sessions:
            session.inject_key(key, modifiers)

    def inject_command(self, command: Command) -> None:
        """Inject command to all sessions (for testing)."""
        for session in self._session_manager.all_sessions:
            session.inject_command(command)

    def set_mouse_visible(self, visible: bool) -> None:
        pass

    def get_opengl_info(self) -> str:
        return "Web Backend (WebGL in browser)"

    def adjust_brightness(self, delta: float) -> float | None:
        return None

    def get_brightness(self) -> float | None:
        return None

    def adjust_background(self, delta: float) -> float | None:
        return None

    def get_background(self) -> float | None:
        return None

    def next_texture_set(self) -> str | None:
        return None

    def prev_texture_set(self) -> str | None:
        return None

    def toggle_texture(self) -> bool:
        return False

    def load_texture_set(self, directory: str) -> int:
        return 0

    def schedule_once(self, callback: "Callable[[float], None]", delay: float) -> None:
        self._event_loop.schedule_once(callback, delay)

    def inject_command_sequence(
        self,
        commands: "CommandSequence | list[Command]",
        on_complete: "Callable[[], None] | None" = None,
    ) -> None:
        """Inject command sequence to all sessions (for testing)."""
        for session in self._session_manager.all_sessions:
            session.inject_command_sequence(commands, on_complete)

    def show_popup(self, title: str, lines: list[str],
                   line_colors: list[tuple[int, int, int, int]] | None = None) -> None:
        pass
