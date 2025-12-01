"""
Pyglet 2.0/Modern OpenGL backend for GUI abstraction layer.

This backend is a copy of the pyglet backend, intended for migration
to pyglet 2.0 and modern OpenGL (shaders, VBOs, VAOs).

Requirements:
    pip install pyglet>=2.0

Usage:
    from cube.presentation.gui.backends import pyglet2
    # Backend is automatically registered on import

    # Or explicitly:
    from cube.presentation.gui.backends.pyglet2 import register
    register()
"""

from cube.presentation.gui.backends.pyglet2.PygletRenderer import PygletRenderer
from cube.presentation.gui.backends.pyglet2.PygletWindow import PygletWindow
from cube.presentation.gui.backends.pyglet2.PygletEventLoop import PygletEventLoop
from cube.presentation.gui.backends.pyglet2.PygletAnimation import PygletAnimation
from cube.presentation.gui.backends.pyglet2.PygletAppWindow import PygletAppWindow

__all__ = [
    "PygletRenderer",
    "PygletWindow",
    "PygletEventLoop",
    "PygletAnimation",
    "PygletAppWindow",
    "register",
]


def register() -> None:
    """Register the pyglet2 backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    from cube.presentation.gui.factory import BackendRegistry

    BackendRegistry.register(
        "pyglet2",
        renderer_factory=PygletRenderer,
        window_factory=lambda w, h, t: PygletWindow(w, h, t),
        event_loop_factory=PygletEventLoop,
        animation_factory=PygletAnimation,
        app_window_factory=lambda app, w, h, t, backend: PygletAppWindow(app, w, h, t, backend),
    )


# Auto-register on import
register()
