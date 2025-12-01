"""
GUI Abstraction Layer for Cube Solver.

This package provides abstract interfaces for GUI backends, allowing
the cube solver to work with different rendering systems (pyglet/OpenGL,
tkinter, headless for testing, etc.).

Usage:
    from cube.presentation.gui import BackendRegistry, GUIBackendFactory

    # Get a backend instance (recommended)
    backend = BackendRegistry.get_backend("pyglet")
    renderer = backend.renderer

    # Or use the default backend
    backend = BackendRegistry.get_backend()
"""

from cube.presentation.gui.factory import BackendRegistry, GUIBackendFactory, GUIBackend
from cube.presentation.gui.protocols import AppWindow
from cube.presentation.gui.types import (
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
    "GUIBackendFactory",
    "GUIBackend",  # Alias for backward compatibility
    # Protocols
    "AppWindow",
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
