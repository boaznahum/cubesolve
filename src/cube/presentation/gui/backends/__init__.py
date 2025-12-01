"""
GUI Backend implementations.

Each sub-package provides a complete implementation of the GUI protocols
for a specific rendering technology.

Available backends:
- pyglet: OpenGL-based 3D rendering via pyglet library
- headless: No-op implementation for testing without GUI
- tkinter: Canvas-based 2D rendering (future)
"""

# Backends are registered lazily when imported
# Example:
#   from cube.presentation.gui.backends import pyglet
#   # This registers the pyglet backend
