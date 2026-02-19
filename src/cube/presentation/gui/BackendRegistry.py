"""
Backend registry for GUI backends.

Provides get_backend() to obtain a GUIBackendFactory for a specific backend.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

# Available backends
BACKENDS = ("pyglet2", "headless", "console", "tkinter", "web")
DEFAULT_BACKEND = "pyglet2"


class BackendRegistry:
    """Registry for GUI backends.

    IMPORTANT: Do NOT call backend.create_app_window(app) directly.
    Use main_any_backend.create_app_window() — the single point of creation
    that wires app + backend together with correct animation support.

    Example:
        from cube.main_any_backend import create_app_window
        window = create_app_window("pyglet2", cube_size=3)
        window.run()
    """

    @classmethod
    def get_backend(cls, name: str | None = None) -> "GUIBackendFactory":
        """Get a GUIBackendFactory for the specified backend.

        Args:
            name: Backend name ('pyglet2', 'headless', 'console', 'tkinter', 'web'),
                  or None for default ('pyglet2')

        Returns:
            GUIBackendFactory instance

        Raises:
            ValueError: If backend name is unknown
        """
        backend_name = name or DEFAULT_BACKEND

        if backend_name == "pyglet2":
            from cube.presentation.gui.backends.pyglet2 import create_backend
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
        elif backend_name == "web":
            from cube.presentation.gui.backends.web import create_backend
            return create_backend()
        else:
            raise ValueError(f"Unknown backend: {backend_name}. Available: {BACKENDS}")
