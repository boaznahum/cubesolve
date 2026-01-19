"""
Console backend for GUI abstraction layer.

This backend provides text-based rendering using Python's built-in
print functions and colorama for colored output.

Benefits:
- No GUI dependencies required
- Works over SSH and in terminals without display
- Good for testing and automation
- Simple to debug

Limitations:
- Text-based rendering only
- No animation support
- No mouse input

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("console")
"""

from typing import TYPE_CHECKING

from cube.presentation.gui.backends.console import ConsoleKeys, ConsoleViewer
from cube.presentation.gui.backends.console.ConsoleAppWindow import ConsoleAppWindow
from cube.presentation.gui.backends.console.ConsoleEventLoop import ConsoleEventLoop
from cube.presentation.gui.backends.console.ConsoleRenderer import ConsoleRenderer

if TYPE_CHECKING:
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

__all__ = [
    "ConsoleRenderer",
    "ConsoleEventLoop",
    "ConsoleAppWindow",
    "ConsoleViewer",
    "ConsoleKeys",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the console backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="console",
        renderer_factory=ConsoleRenderer,
        event_loop_factory=ConsoleEventLoop,
        window_factory=None,  # Console doesn't use Window protocol
        animation_factory=None,  # Console doesn't support animation
        app_window_factory=lambda app, w, h, t, backend: ConsoleAppWindow(app, w, h, t, backend),
        is_headless=True,  # No visual output - skip texture updates
    )
