"""
GUI Protocol definitions.

This module exports all protocol interfaces that backends must implement.
"""

from cube.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.gui.protocols.DisplayListManager import DisplayListManager
from cube.gui.protocols.ViewStateManager import ViewStateManager
from cube.gui.protocols.Renderer import Renderer
from cube.gui.protocols.TextRenderer import TextRenderer
from cube.gui.protocols.Window import Window
from cube.gui.protocols.EventLoop import EventLoop
from cube.gui.protocols.AnimationBackend import AnimationBackend
from cube.gui.protocols.AppWindow import AppWindow

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
