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
    from cube.gui.backends import tkinter
    # Backend is automatically registered on import

    # Or explicitly:
    from cube.gui.backends.tkinter import register
    register()
"""

from cube.gui.backends.tkinter.renderer import TkinterRenderer
from cube.gui.backends.tkinter.window import TkinterWindow
from cube.gui.backends.tkinter.event_loop import TkinterEventLoop
from cube.gui.backends.tkinter.animation import TkinterAnimation

__all__ = ["TkinterRenderer", "TkinterWindow", "TkinterEventLoop", "TkinterAnimation", "register"]


def _create_window(width: int, height: int, title: str) -> TkinterWindow:
    """Factory function for creating TkinterWindow."""
    return TkinterWindow(width, height, title)


def _create_event_loop() -> TkinterEventLoop:
    """Factory function for creating TkinterEventLoop."""
    return TkinterEventLoop()


def register() -> None:
    """Register the tkinter backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    from cube.gui.factory import BackendRegistry

    if not BackendRegistry.is_registered("tkinter"):
        BackendRegistry.register(
            "tkinter",
            renderer_factory=TkinterRenderer,
            window_factory=_create_window,
            event_loop_factory=_create_event_loop,
            animation_factory=TkinterAnimation,
        )


# Auto-register on import
register()
