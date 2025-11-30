"""
Pyglet/OpenGL backend for GUI abstraction layer.

This backend wraps the existing OpenGL rendering code to implement
the GUI protocols. It provides full 3D rendering and animation support.

Requirements:
    pip install pyglet

Usage:
    from cube.gui.backends import pyglet
    # Backend is automatically registered on import

    # Or explicitly:
    from cube.gui.backends.pyglet import register
    register()
"""

from cube.gui.backends.pyglet.PygletRenderer import PygletRenderer
from cube.gui.backends.pyglet.PygletWindow import PygletWindow
from cube.gui.backends.pyglet.PygletEventLoop import PygletEventLoop
from cube.gui.backends.pyglet.PygletAnimation import PygletAnimation
from cube.gui.backends.pyglet.PygletAppWindow import PygletAppWindow

__all__ = [
    "PygletRenderer",
    "PygletWindow",
    "PygletEventLoop",
    "PygletAnimation",
    "PygletAppWindow",
    "register",
]


def register() -> None:
    """Register the pyglet backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    from cube.gui.factory import BackendRegistry

    BackendRegistry.register(
        "pyglet",
        renderer_factory=PygletRenderer,
        window_factory=lambda w, h, t: PygletWindow(w, h, t),
        event_loop_factory=PygletEventLoop,
        animation_factory=PygletAnimation,
        app_window_factory=lambda app, w, h, t, backend: PygletAppWindow(app, w, h, t, backend),
    )


# Auto-register on import
register()
