"""
GUI Protocol definitions.

This module exports all protocol interfaces that backends must implement.

Note: AppWindowBase and TextLabel are NOT exported here to avoid circular imports.
Import them directly: from cube.presentation.gui.protocols.AppWindowBase import AppWindowBase, TextLabel

Note: EventLoop and AnimatableViewer are defined in application.protocols (correct layer)
and re-exported here for backward compatibility.
"""

from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.presentation.gui.protocols.DisplayListManager import DisplayListManager
from cube.presentation.gui.protocols.ViewStateManager import ViewStateManager
from cube.presentation.gui.protocols.Renderer import Renderer
from cube.presentation.gui.protocols.TextRenderer import TextRenderer
from cube.presentation.gui.protocols.Window import Window
from cube.presentation.gui.protocols.AnimationBackend import AnimationBackend
from cube.presentation.gui.protocols.AppWindow import AppWindow
from cube.presentation.gui.protocols.AbstractWindow import AbstractWindow, AbstractTextRenderer
from cube.presentation.gui.protocols.WindowBase import WindowBase

# Re-export from application.protocols (canonical location)
from cube.application.protocols import EventLoop, AnimatableViewer

__all__ = [
    # Renderer protocols
    "ShapeRenderer",
    "DisplayListManager",
    "ViewStateManager",
    "Renderer",
    # Window protocols
    "Window",
    "TextRenderer",
    "AbstractWindow",
    "AbstractTextRenderer",
    "WindowBase",
    # Event loop
    "EventLoop",
    # Animation
    "AnimationBackend",
    "AnimatableViewer",
    # App window
    "AppWindow",
    # Note: AppWindowBase, TextLabel not exported - import directly to avoid circular import
]
