"""
Renderer protocol definition.

This is the main renderer protocol combining all rendering capabilities.
"""

from typing import Protocol, runtime_checkable

from cube.presentation.gui.types import Color4, TextureHandle
from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer
from cube.presentation.gui.protocols.DisplayListManager import DisplayListManager
from cube.presentation.gui.protocols.ViewStateManager import ViewStateManager


@runtime_checkable
class Renderer(Protocol):
    """Main renderer protocol combining all rendering capabilities.

    This is the primary interface that backends implement. It provides
    access to shape rendering, display lists, and view transformations.
    """

    @property
    def shapes(self) -> ShapeRenderer:
        """Access shape rendering methods."""
        ...

    @property
    def display_lists(self) -> DisplayListManager:
        """Access display list management."""
        ...

    @property
    def view(self) -> ViewStateManager:
        """Access view transformation methods."""
        ...

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Clear the rendering surface.

        Args:
            color: RGBA clear color (default: black)
        """
        ...

    def setup(self) -> None:
        """Initialize renderer (called once at startup).

        Sets up any required rendering state, contexts, etc.
        """
        ...

    def cleanup(self) -> None:
        """Release renderer resources (called at shutdown).

        Frees display lists, textures, and other resources.
        """
        ...

    def begin_frame(self) -> None:
        """Begin a new frame (called before drawing).

        Prepares for rendering a new frame.
        """
        ...

    def end_frame(self) -> None:
        """End frame and present (called after drawing).

        Finalizes rendering and presents the frame.
        """
        ...

    def flush(self) -> None:
        """Flush any pending rendering commands."""
        ...

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """Load a texture from a file.

        Args:
            file_path: Path to image file (PNG, etc.)

        Returns:
            Texture handle for use with quad_with_texture, or None if not supported
        """
        ...

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """Bind a texture for subsequent rendering.

        Args:
            texture: Texture handle from load_texture, or None to unbind
        """
        ...

    def delete_texture(self, texture: TextureHandle) -> None:
        """Delete a texture and free resources.

        Args:
            texture: Texture handle to delete
        """
        ...
