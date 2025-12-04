"""
AbstractRenderer - base class with no-op defaults for Renderer protocol.

Use this for partial implementations that only need a subset of Renderer methods.
"""
from __future__ import annotations

from cube.presentation.gui.types import Color4, TextureHandle
from cube.presentation.gui.protocols.Renderer import Renderer
from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.presentation.gui.protocols.DisplayListManager import DisplayListManager
from cube.presentation.gui.protocols.ViewStateManager import ViewStateManager


class AbstractRenderer(Renderer):
    """Abstract base class providing default no-op implementations for Renderer.

    Inherit from this class when you only need to implement a subset of
    Renderer methods. All methods have no-op defaults that do nothing.

    Note: Subclasses MUST provide implementations for the properties
    (shapes, display_lists, view) since these cannot have no-op defaults.
    """

    @property
    def shapes(self) -> ShapeRenderer:
        """Access shape rendering methods. Must be overridden."""
        raise NotImplementedError("Subclass must provide shapes property")

    @property
    def display_lists(self) -> DisplayListManager:
        """Access display list management. Must be overridden."""
        raise NotImplementedError("Subclass must provide display_lists property")

    @property
    def view(self) -> ViewStateManager:
        """Access view transformation methods. Must be overridden."""
        raise NotImplementedError("Subclass must provide view property")

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Clear the rendering surface. No-op default."""
        pass

    def setup(self) -> None:
        """Initialize renderer. No-op default."""
        pass

    def cleanup(self) -> None:
        """Release renderer resources. No-op default."""
        pass

    def begin_frame(self) -> None:
        """Begin a new frame. No-op default."""
        pass

    def end_frame(self) -> None:
        """End frame and present. No-op default."""
        pass

    def flush(self) -> None:
        """Flush any pending rendering commands. No-op default."""
        pass

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """Load a texture from a file. No-op default returns None."""
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """Bind a texture for subsequent rendering. No-op default."""
        pass

    def delete_texture(self, texture: TextureHandle) -> None:
        """Delete a texture and free resources. No-op default."""
        pass
