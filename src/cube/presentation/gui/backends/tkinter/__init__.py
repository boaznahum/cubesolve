"""
Tkinter backend for GUI abstraction layer.

This backend provides 2D canvas-based rendering using Python's built-in
tkinter library. The cube is displayed using isometric projection.

Benefits:
- No external dependencies (tkinter is part of Python standard library)
- Simpler rendering (2D instead of 3D)
- Good for educational/debugging purposes
- Cross-platform support

Limitations:
- 2D isometric projection instead of true 3D
- No textures or advanced lighting
- Simpler animation (via canvas.after())

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("tkinter")
"""

from cube.presentation.gui.backends.tkinter.TkinterRenderer import TkinterRenderer
from cube.presentation.gui.backends.tkinter.TkinterWindow import TkinterWindow
from cube.presentation.gui.backends.tkinter.TkinterEventLoop import TkinterEventLoop
from cube.presentation.gui.backends.tkinter.TkinterAnimation import TkinterAnimation
from cube.presentation.gui.backends.tkinter.TkinterAppWindow import TkinterAppWindow

__all__ = [
    "TkinterRenderer",
    "TkinterWindow",
    "TkinterEventLoop",
    "TkinterAnimation",
    "TkinterAppWindow",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the tkinter backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="tkinter",
        renderer_factory=TkinterRenderer,
        event_loop_factory=TkinterEventLoop,
        window_factory=lambda w, h, t: TkinterWindow(w, h, t),
        animation_factory=TkinterAnimation,
        app_window_factory=lambda app, w, h, t, backend: TkinterAppWindow(app, w, h, t, backend),
    )
