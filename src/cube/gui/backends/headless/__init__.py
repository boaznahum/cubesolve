"""
Headless backend for GUI abstraction layer.

This backend provides no-op implementations of all GUI protocols,
allowing the cube solver to run without any graphical output.
Useful for:
- Unit testing
- Benchmarking solver algorithms
- Batch processing / scripting
- CI/CD pipelines

Usage:
    from cube.gui.backends import headless
    # Backend is automatically registered on import

    # Or explicitly:
    from cube.gui.backends.headless import register
    register()
"""

from cube.gui.backends.headless.HeadlessRenderer import HeadlessRenderer
from cube.gui.backends.headless.HeadlessWindow import HeadlessWindow
from cube.gui.backends.headless.HeadlessEventLoop import HeadlessEventLoop
from cube.gui.backends.headless.HeadlessAppWindow import HeadlessAppWindow

__all__ = [
    "HeadlessRenderer",
    "HeadlessWindow",
    "HeadlessEventLoop",
    "HeadlessAppWindow",
    "register",
]


def register() -> None:
    """Register the headless backend with the BackendRegistry.

    This is called automatically on import, but can also be called
    explicitly to ensure registration.
    """
    from cube.gui.factory import BackendRegistry

    if not BackendRegistry.is_registered("headless"):
        BackendRegistry.register(
            "headless",
            renderer_factory=HeadlessRenderer,
            window_factory=lambda w, h, t: HeadlessWindow(w, h, t),
            event_loop_factory=HeadlessEventLoop,
            animation_factory=None,  # Headless doesn't support animation
            app_window_factory=lambda app, w, h, t, backend: HeadlessAppWindow(app, w, h, t, backend),
        )


# Auto-register on import
register()
