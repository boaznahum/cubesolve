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
    from cube.presentation.gui.backends import console
    # Backend is automatically registered on import

    # Or explicitly:
    from cube.presentation.gui.backends.console import register
    register()
"""

from cube.presentation.gui.backends.console.ConsoleRenderer import ConsoleRenderer
from cube.presentation.gui.backends.console.ConsoleEventLoop import ConsoleEventLoop
from cube.presentation.gui.backends.console.ConsoleAppWindow import ConsoleAppWindow
from cube.presentation.gui.backends.console import ConsoleViewer
from cube.presentation.gui.backends.console import ConsoleKeys

__all__ = [
    "ConsoleRenderer",
    "ConsoleEventLoop",
    "ConsoleAppWindow",
    "ConsoleViewer",
    "ConsoleKeys",
    "register",
]


def _create_event_loop() -> ConsoleEventLoop:
    """Factory function for creating ConsoleEventLoop."""
    return ConsoleEventLoop()


def register() -> None:
    """Register the console backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    from cube.presentation.gui.factory import BackendRegistry

    if not BackendRegistry.is_registered("console"):
        BackendRegistry.register(
            "console",
            renderer_factory=ConsoleRenderer,
            window_factory=None,  # Console doesn't use Window protocol
            event_loop_factory=_create_event_loop,
            animation_factory=None,  # Console doesn't support animation
            app_window_factory=lambda app, w, h, t, backend: ConsoleAppWindow(app, w, h, t, backend),
        )


# Auto-register on import
register()
