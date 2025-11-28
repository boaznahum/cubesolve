"""
Backend factory and registry.

This module provides the BackendRegistry for managing GUI backends.
"""

from typing import Type, TypeVar, Callable, Any

from cube.gui.protocols import Renderer, Window, EventLoop, AnimationBackend

# Type variables for generic factory methods
R = TypeVar("R", bound=Renderer)
W = TypeVar("W", bound=Window)
E = TypeVar("E", bound=EventLoop)
A = TypeVar("A", bound=AnimationBackend)


class _BackendEntry:
    """Internal class holding backend component factories."""

    __slots__ = ["renderer_factory", "window_factory", "event_loop_factory", "animation_factory"]

    def __init__(
        self,
        renderer_factory: Callable[[], Renderer],
        window_factory: Callable[[int, int, str], Window],
        event_loop_factory: Callable[[], EventLoop],
        animation_factory: Callable[[], AnimationBackend] | None = None,
    ):
        self.renderer_factory = renderer_factory
        self.window_factory = window_factory
        self.event_loop_factory = event_loop_factory
        self.animation_factory = animation_factory


class BackendRegistry:
    """Registry for GUI backends.

    Backends register their component factories here. The registry
    manages default backend selection and component creation.

    Example:
        # Register a backend
        BackendRegistry.register(
            "pyglet",
            renderer_factory=PygletRenderer,
            window_factory=lambda w, h, t: PygletWindow(w, h, t),
            event_loop_factory=PygletEventLoop,
            animation_factory=PygletAnimation,
        )

        # Set as default
        BackendRegistry.set_default("pyglet")

        # Create components
        renderer = BackendRegistry.create_renderer()
    """

    _backends: dict[str, _BackendEntry] = {}
    _default: str | None = None

    @classmethod
    def register(
        cls,
        name: str,
        *,
        renderer_factory: Callable[[], Renderer],
        window_factory: Callable[[int, int, str], Window],
        event_loop_factory: Callable[[], EventLoop],
        animation_factory: Callable[[], AnimationBackend] | None = None,
    ) -> None:
        """Register a new backend.

        Args:
            name: Backend identifier (e.g., 'pyglet', 'tkinter', 'headless')
            renderer_factory: Callable that creates a Renderer instance
            window_factory: Callable(width, height, title) that creates a Window
            event_loop_factory: Callable that creates an EventLoop
            animation_factory: Optional callable that creates an AnimationBackend
        """
        cls._backends[name] = _BackendEntry(
            renderer_factory=renderer_factory,
            window_factory=window_factory,
            event_loop_factory=event_loop_factory,
            animation_factory=animation_factory,
        )

    @classmethod
    def unregister(cls, name: str) -> None:
        """Remove a registered backend.

        Args:
            name: Backend identifier to remove
        """
        cls._backends.pop(name, None)
        if cls._default == name:
            cls._default = None

    @classmethod
    def set_default(cls, name: str) -> None:
        """Set the default backend.

        Args:
            name: Backend identifier (must be registered)

        Raises:
            ValueError: If backend is not registered
        """
        if name not in cls._backends:
            raise ValueError(f"Unknown backend: {name}. Available: {list(cls._backends.keys())}")
        cls._default = name

    @classmethod
    def get_default(cls) -> str:
        """Get the default backend name.

        Returns:
            Name of the default backend

        Raises:
            RuntimeError: If no backends are registered
        """
        if cls._default:
            return cls._default

        # Auto-detect available backend (in preference order)
        for name in ["pyglet", "tkinter", "headless"]:
            if name in cls._backends:
                return name

        if cls._backends:
            return next(iter(cls._backends.keys()))

        raise RuntimeError("No GUI backend registered")

    @classmethod
    def available(cls) -> list[str]:
        """List available (registered) backends.

        Returns:
            List of backend names
        """
        return list(cls._backends.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a backend is registered.

        Args:
            name: Backend identifier

        Returns:
            True if registered, False otherwise
        """
        return name in cls._backends

    @classmethod
    def _get_entry(cls, backend: str | None) -> _BackendEntry:
        """Get backend entry, using default if not specified."""
        name = backend or cls.get_default()
        if name not in cls._backends:
            raise ValueError(f"Unknown backend: {name}. Available: {list(cls._backends.keys())}")
        return cls._backends[name]

    @classmethod
    def create_renderer(cls, backend: str | None = None) -> Renderer:
        """Create a renderer instance.

        Args:
            backend: Backend name, or None for default

        Returns:
            Renderer instance
        """
        entry = cls._get_entry(backend)
        return entry.renderer_factory()

    @classmethod
    def create_window(
        cls,
        width: int = 720,
        height: int = 720,
        title: str = "Cube",
        backend: str | None = None,
    ) -> Window:
        """Create a window instance.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            backend: Backend name, or None for default

        Returns:
            Window instance
        """
        entry = cls._get_entry(backend)
        return entry.window_factory(width, height, title)

    @classmethod
    def create_event_loop(cls, backend: str | None = None) -> EventLoop:
        """Create an event loop instance.

        Args:
            backend: Backend name, or None for default

        Returns:
            EventLoop instance
        """
        entry = cls._get_entry(backend)
        return entry.event_loop_factory()

    @classmethod
    def create_animation(cls, backend: str | None = None) -> AnimationBackend | None:
        """Create an animation backend instance.

        Args:
            backend: Backend name, or None for default

        Returns:
            AnimationBackend instance, or None if not supported
        """
        entry = cls._get_entry(backend)
        if entry.animation_factory:
            return entry.animation_factory()
        return None

    @classmethod
    def supports_animation(cls, backend: str | None = None) -> bool:
        """Check if a backend supports animation.

        Args:
            backend: Backend name, or None for default

        Returns:
            True if animation is supported
        """
        entry = cls._get_entry(backend)
        return entry.animation_factory is not None


def register_backend(
    name: str,
    *,
    renderer_factory: Callable[[], Renderer],
    window_factory: Callable[[int, int, str], Window],
    event_loop_factory: Callable[[], EventLoop],
    animation_factory: Callable[[], AnimationBackend] | None = None,
    set_as_default: bool = False,
) -> None:
    """Convenience function to register a backend.

    Args:
        name: Backend identifier
        renderer_factory: Callable that creates a Renderer
        window_factory: Callable(width, height, title) that creates a Window
        event_loop_factory: Callable that creates an EventLoop
        animation_factory: Optional callable that creates an AnimationBackend
        set_as_default: If True, set this backend as the default
    """
    BackendRegistry.register(
        name,
        renderer_factory=renderer_factory,
        window_factory=window_factory,
        event_loop_factory=event_loop_factory,
        animation_factory=animation_factory,
    )
    if set_as_default:
        BackendRegistry.set_default(name)
