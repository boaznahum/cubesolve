"""
GUI Backend implementations.

Each sub-package provides a complete implementation of the GUI protocols
for a specific rendering technology.

Available backends:
- pyglet: OpenGL 1.x rendering via pyglet 1.5 (legacy, stable)
- pyglet2: OpenGL 3.3+ rendering via pyglet 2.0 (modern, in development)
- headless: No-op implementation for testing without GUI
- tkinter: Canvas-based 2D rendering
- console: Text-based rendering for terminal
"""

# Backends are registered lazily when imported
# Example:
#   from cube.presentation.gui.backends import pyglet
#   # This registers the pyglet backend
#
#   from cube.presentation.gui.backends import pyglet2
#   # This registers the pyglet2 backend (requires pyglet>=2.0)
