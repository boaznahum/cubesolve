"""
GUI Backend Factory.

Provides a unified interface to access all components of a GUI backend.
"""

from typing import TYPE_CHECKING, Callable

from cube.presentation.gui.protocols import (
    AnimationBackend,
    AppWindow,
    EventLoop,
    Renderer,
    Window,
)

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp


class GUIBackendFactory:
    """Factory for GUI backend components.

    Provides:
    - Lazy singleton access: renderer, event_loop
    - Factory methods: create_window(), create_event_loop(),
      create_animation(), create_app_window()

    Example:
        backend = BackendRegistry.get_backend("pyglet2")
        renderer = backend.renderer  # Lazily created, singleton
        app_window = backend.create_app_window(app)
    """

    def __init__(
        self,
        name: str,
        renderer_factory: Callable[[], Renderer],
        event_loop_factory: Callable[[], EventLoop],
        window_factory: Callable[[int, int, str], Window] | None = None,
        animation_factory: Callable[[], AnimationBackend] | None = None,
        app_window_factory: Callable[["AbstractApp", int, int, str, "GUIBackendFactory"], AppWindow] | None = None,
        is_headless: bool = False,
    ):
        self._name = name
        self._renderer_factory = renderer_factory
        self._event_loop_factory = event_loop_factory
        self._window_factory = window_factory
        self._animation_factory = animation_factory
        self._app_window_factory = app_window_factory
        self._is_headless = is_headless
        self._renderer: Renderer | None = None
        self._event_loop: EventLoop | None = None

    @property
    def renderer(self) -> Renderer:
        """Get or create the renderer (lazy, singleton)."""
        if self._renderer is None:
            self._renderer = self._renderer_factory()
        return self._renderer

    @property
    def event_loop(self) -> EventLoop:
        """Get or create the event loop (lazy, singleton)."""
        if self._event_loop is None:
            self._event_loop = self._event_loop_factory()
        return self._event_loop

    def create_window(self, width: int = 720, height: int = 720, title: str = "Cube") -> Window:
        """Create a new Window instance."""
        if self._window_factory is None:
            raise RuntimeError(f"Backend '{self._name}' does not have a window_factory")
        return self._window_factory(width, height, title)

    def create_event_loop(self) -> EventLoop:
        """Create a new EventLoop instance (non-singleton)."""
        return self._event_loop_factory()

    def create_animation(self) -> AnimationBackend | None:
        """Create a new AnimationBackend instance, or None if not supported."""
        if self._animation_factory:
            return self._animation_factory()
        return None

    @property
    def supports_animation(self) -> bool:
        """Check if this backend supports animation."""
        return self._animation_factory is not None

    @property
    def is_headless(self) -> bool:
        """Check if this backend is headless (no visual output).

        Headless backends (e.g., HeadlessBackend, ConsoleBackend) don't produce
        visual output, so texture direction updates can be skipped during rotations.
        """
        return self._is_headless

    def create_app_window(
        self,
        app: "AbstractApp",
        width: int = 720,
        height: int = 720,
        title: str = "Cube Solver",
    ) -> AppWindow:
        """Create an AppWindow for this backend.

        This also wires up the animation manager to the event loop
        and sets cube visibility based on whether the backend is headless.
        """
        # Wire up animation manager to event loop
        if app.am is not None:
            app.am.set_event_loop(self.event_loop)

        # Set cube visibility based on backend type (visual vs headless)
        # This allows skipping texture direction updates for headless backends
        app.cube.has_visible_presentation = not self._is_headless

        # Create AppWindow
        if self._app_window_factory is None:
            raise RuntimeError(f"Backend '{self._name}' does not have app_window_factory")
        return self._app_window_factory(app, width, height, title, self)
