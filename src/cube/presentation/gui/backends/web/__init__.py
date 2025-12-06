"""
Web backend for GUI abstraction layer.

This backend renders the cube in a web browser using WebGL2,
with Python server communicating via WebSocket.

Benefits:
- Cross-platform (any modern browser)
- No local GUI dependencies
- Remote viewing capability
- Modern WebGL2 rendering with depth buffer

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("web")
"""

from typing import TYPE_CHECKING

from cube.presentation.gui.backends.web.WebRenderer import WebRenderer
from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop
from cube.presentation.gui.backends.web.WebAppWindow import WebAppWindow

if TYPE_CHECKING:
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

__all__ = [
    "WebRenderer",
    "WebEventLoop",
    "WebAppWindow",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the web backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="web",
        renderer_factory=WebRenderer,
        event_loop_factory=WebEventLoop,
        window_factory=None,
        animation_factory=None,  # Web uses JS-side animation
        app_window_factory=lambda app, w, h, t, backend: WebAppWindow(app, w, h, t, backend),
    )
