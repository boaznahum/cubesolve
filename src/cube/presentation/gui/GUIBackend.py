"""
GUI Backend interface class.

Provides a unified interface to access all components of a GUI backend.
"""

from typing import TYPE_CHECKING

from cube.presentation.gui.protocols import Renderer, Window, EventLoop, AnimationBackend, AppWindow

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.gui.BackendRegistry import _BackendEntry


class GUIBackend:
    """Single entry point for all GUI backend components.

    Provides access to renderer, window, event loop, and animation
    components for a specific backend.

    Example:
        backend = BackendRegistry.get_backend("pyglet")
        renderer = backend.renderer  # Lazily created, singleton
        window = backend.create_window(720, 720, "Cube")
    """

    def __init__(self, name: str, entry: "_BackendEntry"):
        self._name = name
        self._entry = entry
        self._renderer: Renderer | None = None
        self._event_loop: EventLoop | None = None

    @property
    def name(self) -> str:
        """Get the backend name."""
        return self._name

    @property
    def renderer(self) -> Renderer:
        """Get or create the renderer (lazy, singleton per GUIBackend instance)."""
        if self._renderer is None:
            self._renderer = self._entry.renderer_factory()
        return self._renderer

    @property
    def event_loop(self) -> EventLoop:
        """Get or create the event loop (lazy, singleton per GUIBackend instance)."""
        if self._event_loop is None:
            self._event_loop = self._entry.event_loop_factory()
        return self._event_loop

    def create_window(self, width: int = 720, height: int = 720, title: str = "Cube") -> Window:
        """Create a window for this backend."""
        if self._entry.window_factory is None:
            raise RuntimeError(f"Backend '{self._name}' does not have a window_factory")
        return self._entry.window_factory(width, height, title)

    def create_event_loop(self) -> EventLoop:
        """Create an event loop for this backend."""
        return self._entry.event_loop_factory()

    def create_animation(self) -> AnimationBackend | None:
        """Create animation backend if supported."""
        if self._entry.animation_factory:
            return self._entry.animation_factory()
        return None

    @property
    def supports_animation(self) -> bool:
        """Check if this backend supports animation."""
        return self._entry.animation_factory is not None

    def create_app_window(
        self,
        app: "AbstractApp",
        width: int = 720,
        height: int = 720,
        title: str = "Cube Solver",
    ) -> AppWindow:
        """Create an AppWindow for this backend.

        This also wires up the animation manager to the event loop.

        Args:
            app: Application instance with cube, operator, solver.
            width: Window width in pixels (ignored for console/headless).
            height: Window height in pixels (ignored for console/headless).
            title: Window title.

        Returns:
            An AppWindow instance for this backend.

        Raises:
            RuntimeError: If this backend doesn't have an app_window_factory.
        """
        # Wire up animation manager to event loop
        if app.am is not None:
            app.am.set_event_loop(self.event_loop)

        # Create AppWindow
        if self._entry.app_window_factory is None:
            raise RuntimeError(f"Backend '{self._name}' does not have app_window_factory")
        return self._entry.app_window_factory(app, width, height, title, self)
