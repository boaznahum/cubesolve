"""
Pyglet 2.0/Modern OpenGL backend for GUI abstraction layer.

This backend uses pyglet 2.0 with modern OpenGL (shaders, VBOs, VAOs)
instead of legacy immediate mode rendering.

Requirements:
    pip install pyglet>=2.0

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("pyglet2")
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
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the pyglet2 backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="pyglet2",
        renderer_factory=PygletRenderer,
        event_loop_factory=PygletEventLoop,
        window_factory=lambda w, h, t: PygletWindow(w, h, t),
        animation_factory=PygletAnimation,
        app_window_factory=lambda app, w, h, t, backend: PygletAppWindow(app, w, h, t, backend),
    )
