"""
GUI Abstraction Layer for Cube Solver.

This package provides abstract interfaces for GUI backends, allowing
the cube solver to work with different rendering systems (pyglet/OpenGL,
tkinter, headless for testing, etc.).

Usage:
    from cube.gui import create_gui, BackendRegistry

    # Create GUI components for a specific backend
    renderer, window, event_loop, animation = create_gui(backend='pyglet')

    # Or use the default backend
    renderer, window, event_loop, animation = create_gui()
"""

from cube.gui.factory import BackendRegistry, create_gui
from cube.gui.types import (
    Point3D,
    Matrix4x4,
    Color3,
    Color4,
    DisplayList,
    KeyEvent,
    MouseEvent,
    Keys,
    Modifiers,
)

__all__ = [
    # Factory
    "BackendRegistry",
    "create_gui",
    # Types
    "Point3D",
    "Matrix4x4",
    "Color3",
    "Color4",
    "DisplayList",
    "KeyEvent",
    "MouseEvent",
    "Keys",
    "Modifiers",
]
