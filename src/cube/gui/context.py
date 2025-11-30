"""
Rendering context for accessing the current Renderer.

This module provides a thread-local context for accessing the current
Renderer instance. This allows legacy code to use the renderer without
passing it through every function call.

Usage:
    # Set up the context (usually at app startup)
    from cube.gui.context import rendering_context
    rendering_context.set_renderer(my_renderer)

    # Access the renderer anywhere
    from cube.gui.context import rendering_context
    renderer = rendering_context.get_renderer()
    renderer.shapes.quad(vertices, color)
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.gui.protocols import Renderer


class RenderingContext:
    """Thread-local rendering context.

    Holds the current Renderer for the rendering thread.
    This allows legacy code to access the renderer without
    passing it through every function call.
    """

    def __init__(self) -> None:
        self._local = threading.local()

    def set_renderer(self, renderer: Renderer | None) -> None:
        """Set the current renderer for this thread.

        Args:
            renderer: The Renderer instance, or None to clear
        """
        self._local.renderer = renderer

    def get_renderer(self) -> Renderer:
        """Get the current renderer.

        Returns:
            The current Renderer instance

        Raises:
            RuntimeError: If no renderer has been set
        """
        renderer = getattr(self._local, 'renderer', None)
        if renderer is None:
            raise RuntimeError(
                "No renderer set in rendering context. "
                "Call rendering_context.set_renderer() first."
            )
        return renderer

    def has_renderer(self) -> bool:
        """Check if a renderer is set.

        Returns:
            True if a renderer is available
        """
        return getattr(self._local, 'renderer', None) is not None


# Global rendering context instance
rendering_context = RenderingContext()
