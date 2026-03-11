"""
WebGL backend for GUI abstraction layer.

This backend sends cube STATE to the browser (not rendering commands).
The Three.js client builds and owns the 3D model locally, rendering
at 60fps on the GPU with no per-frame server dependency.

Each browser connection gets its own independent cube session
via ClientSession, managed by SessionManager.

Architecture:
    Server sends state → Client builds 3D model + animates (smart)

Usage:
    from cube.presentation.gui import BackendRegistry
    backend = BackendRegistry.get_backend("webgl")
"""

from typing import TYPE_CHECKING

from cube.presentation.gui.backends.webgl.ClientSession import ClientSession
from cube.presentation.gui.backends.webgl.SessionManager import SessionManager
from cube.presentation.gui.backends.webgl.WebglAppWindow import WebglAppWindow
from cube.presentation.gui.backends.webgl.WebglEventLoop import WebglEventLoop
from cube.presentation.gui.backends.webgl.WebglRenderer import WebglRenderer

if TYPE_CHECKING:
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

__all__ = [
    "ClientSession",
    "SessionManager",
    "WebglRenderer",
    "WebglEventLoop",
    "WebglAppWindow",
    "create_backend",
]


def create_backend() -> "GUIBackendFactory":
    """Create a GUIBackendFactory for the webgl backend."""
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory

    return GUIBackendFactory(
        name="webgl",
        renderer_factory=WebglRenderer,
        event_loop_factory=WebglEventLoop,
        window_factory=None,
        animation_factory=None,  # WebGL uses client-side animation
        app_window_factory=lambda app, w, h, t, backend: WebglAppWindow(app, w, h, t, backend),
    )
