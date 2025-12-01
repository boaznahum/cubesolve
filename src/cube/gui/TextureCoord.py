"""Texture coordinate type."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextureCoord:
    """UV texture coordinate for a vertex."""

    u: int
    v: int
