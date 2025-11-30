import importlib.resources as pkg_resources
from collections.abc import Sequence
from typing import TYPE_CHECKING

from . import res
from cube.gui.types import TextureHandle

if TYPE_CHECKING:
    from cube.gui.protocols import Renderer


class TextureData:
    """Texture data loaded via the renderer abstraction layer."""

    __slots__ = ["_texture_handle",
                 "_texture_map",
                 "_renderer"
                 ]

    _texture_handle: TextureHandle | None
    _texture_map: Sequence[tuple[int, int]]
    _renderer: "Renderer"

    def __init__(self) -> None:
        super().__init__()

    @property
    def texture_handle(self) -> TextureHandle | None:
        """Get the texture handle for use with renderer."""
        return self._texture_handle

    @property
    def texture_map(self) -> Sequence[tuple[int, int]]:
        return self._texture_map

    def bind(self) -> None:
        """Bind this texture for rendering."""
        self._renderer.bind_texture(self._texture_handle)

    def cleanup(self) -> None:
        """Release resources upon exit."""
        if self._texture_handle is not None:
            self._renderer.delete_texture(self._texture_handle)
            self._texture_handle = None

    @staticmethod
    def load(file_name: str, texture_map: Sequence[tuple[int, int]],
             renderer: "Renderer") -> "TextureData":
        """Load a texture from a file.

        Args:
            file_name: Filename under viewer/res directory
            texture_map: Texture coordinates mapping
            renderer: Renderer to use for loading

        Returns:
            TextureData instance with loaded texture
        """
        td = TextureData()
        td._renderer = renderer
        td._texture_map = texture_map

        # Get the file path from package resources
        with pkg_resources.path(res, file_name) as path:
            # Use the renderer's texture loading capability
            td._texture_handle = renderer.load_texture(str(path))

        return td
