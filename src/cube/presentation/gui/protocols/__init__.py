"""
GUI Protocol definitions.

This module exports all protocol interfaces that backends must implement.
"""

from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.presentation.gui.protocols.DisplayListManager import DisplayListManager
from cube.presentation.gui.protocols.ViewStateManager import ViewStateManager
from cube.presentation.gui.protocols.Renderer import Renderer
from cube.presentation.gui.protocols.TextRenderer import TextRenderer
from cube.presentation.gui.protocols.Window import Window
from cube.presentation.gui.protocols.EventLoop import EventLoop
from cube.presentation.gui.protocols.AnimationBackend import AnimationBackend
from cube.presentation.gui.protocols.AppWindow import AppWindow
from cube.presentation.gui.protocols.AnimatableViewer import AnimatableViewer

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
    "AnimatableViewer",
    # App window
    "AppWindow",
]
