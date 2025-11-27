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

# TODO: Implement tkinter backend
# from cube.gui.backends.tkinter.renderer import TkinterRenderer
# from cube.gui.backends.tkinter.window import TkinterWindow
# from cube.gui.backends.tkinter.event_loop import TkinterEventLoop


def register() -> None:
    """Register the tkinter backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    # TODO: Implement registration once backend classes are ready
    # from cube.gui.factory import BackendRegistry
    # BackendRegistry.register(
    #     "tkinter",
    #     renderer_factory=TkinterRenderer,
    #     window_factory=lambda w, h, t: TkinterWindow(w, h, t),
    #     event_loop_factory=TkinterEventLoop,
    #     animation_factory=None,  # Can add TkinterAnimation later
    # )
    pass


# Auto-register on import (commented out until implemented)
# register()
