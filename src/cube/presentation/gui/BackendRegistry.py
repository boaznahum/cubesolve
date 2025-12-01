"""
Backend registry for GUI backends.

Provides get_backend() to obtain a GUIBackendFactory for a specific backend.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

# Available backends
BACKENDS = ("pyglet", "headless", "console", "tkinter")
DEFAULT_BACKEND = "pyglet"


class BackendRegistry:
    """Registry for GUI backends.

    Example:
        backend = BackendRegistry.get_backend("pyglet")
        renderer = backend.renderer
        app_window = backend.create_app_window(app)
    """

    @classmethod
    def get_backend(cls, name: str | None = None) -> "GUIBackendFactory":
        """Get a GUIBackendFactory for the specified backend.

        Args:
            name: Backend name ('pyglet', 'headless', 'console', 'tkinter'),
                  or None for default ('pyglet')

        Returns:
            GUIBackendFactory instance

        Raises:
            ValueError: If backend name is unknown
        """
        backend_name = name or DEFAULT_BACKEND

        if backend_name == "pyglet":
            from cube.presentation.gui.backends.pyglet import create_backend
            return create_backend()
        elif backend_name == "headless":
            from cube.presentation.gui.backends.headless import create_backend
            return create_backend()
        elif backend_name == "console":
            from cube.presentation.gui.backends.console import create_backend
            return create_backend()
        elif backend_name == "tkinter":
            from cube.presentation.gui.backends.tkinter import create_backend
            return create_backend()
        else:
            raise ValueError(f"Unknown backend: {backend_name}. Available: {BACKENDS}")
