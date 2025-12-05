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
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("headless")
"""

from cube.presentation.gui.backends.headless.HeadlessRenderer import HeadlessRenderer
from cube.presentation.gui.backends.headless.HeadlessEventLoop import HeadlessEventLoop
from cube.presentation.gui.backends.headless.HeadlessAppWindow import HeadlessAppWindow

__all__ = [
    "HeadlessRenderer",
    "HeadlessEventLoop",
    "HeadlessAppWindow",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the headless backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="headless",
        renderer_factory=HeadlessRenderer,
        event_loop_factory=HeadlessEventLoop,
        window_factory=None,
        animation_factory=None,  # Headless doesn't support animation
        app_window_factory=lambda app, w, h, t, backend: HeadlessAppWindow(app, w, h, t, backend),
    )
