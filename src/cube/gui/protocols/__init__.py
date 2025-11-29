"""
GUI Protocol definitions.

This module exports all protocol interfaces that backends must implement.
"""

from cube.gui.protocols.renderer import (
    ShapeRenderer,
    DisplayListManager,
    ViewStateManager,
    Renderer,
)
from cube.gui.protocols.window import Window, TextRenderer
from cube.gui.protocols.event_loop import EventLoop
from cube.gui.protocols.animation import AnimationBackend
from cube.gui.protocols.app_window import AppWindow

__all__ = [
    # Renderer protocols
    "ShapeRenderer",
    "DisplayListManager",
    "ViewStateManager",
    "Renderer",
    # Window protocols
    "Window",
    "TextRenderer",
    # Event loop
    "EventLoop",
    # Animation
    "AnimationBackend",
    # App window
    "AppWindow",
]
