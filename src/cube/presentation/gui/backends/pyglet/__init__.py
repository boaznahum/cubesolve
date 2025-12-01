"""
Pyglet/OpenGL backend for GUI abstraction layer.

This backend wraps the existing OpenGL rendering code to implement
the GUI protocols. It provides full 3D rendering and animation support.

Requirements:
    pip install pyglet

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("pyglet")
"""

from cube.presentation.gui.backends.pyglet.PygletRenderer import PygletRenderer
from cube.presentation.gui.backends.pyglet.PygletWindow import PygletWindow
from cube.presentation.gui.backends.pyglet.PygletEventLoop import PygletEventLoop
from cube.presentation.gui.backends.pyglet.PygletAnimation import PygletAnimation
from cube.presentation.gui.backends.pyglet.PygletAppWindow import PygletAppWindow

__all__ = [
    "PygletRenderer",
    "PygletWindow",
    "PygletEventLoop",
    "PygletAnimation",
    "PygletAppWindow",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the pyglet backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="pyglet",
        renderer_factory=PygletRenderer,
        event_loop_factory=PygletEventLoop,
        window_factory=lambda w, h, t: PygletWindow(w, h, t),
        animation_factory=PygletAnimation,
        app_window_factory=lambda app, w, h, t, backend: PygletAppWindow(app, w, h, t, backend),
    )
