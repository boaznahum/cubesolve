"""
GUI Abstraction Layer for Cube Solver.

This package provides abstract interfaces for GUI backends, allowing
the cube solver to work with different rendering systems (pyglet/OpenGL,
tkinter, headless for testing, etc.).

Usage:
    from cube.gui import BackendRegistry

    # Create renderer for a specific backend
    renderer = BackendRegistry.create_renderer(backend='pyglet')

    # Or use the default backend
    renderer = BackendRegistry.create_renderer()
"""

from cube.gui.factory import BackendRegistry
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
