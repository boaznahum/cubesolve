"""CubeFaceColors — a simple face-to-color mapping.

Represents a concrete assignment of colors to faces, e.g. after a
whole-cube rotation.  Unlike CubeColorScheme (which also carries
edge-color caches and comparison logic), this is a lightweight
value object used to pass face-color assignments around.
"""

from __future__ import annotations

from collections.abc import Mapping

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName


class CubeFaceColors:
    """Immutable face-to-color mapping."""

    __slots__ = ("_mapping",)

    def __init__(self, mapping: Mapping[FaceName, Color]) -> None:
        self._mapping: dict[FaceName, Color] = dict(mapping)

    def __getitem__(self, face: FaceName) -> Color:
        return self._mapping[face]

    @property
    def mapping(self) -> Mapping[FaceName, Color]:
        """Read-only view of the face-to-color mapping."""
        return self._mapping

    def find_face(self, color: Color) -> FaceName:
        """Face holding the given color; raises ValueError if not found."""
        for fn, c in self._mapping.items():
            if c == color:
                return fn
        raise ValueError(f"Color {color} not in {self}")

    def __repr__(self) -> str:
        items = ", ".join(f"{fn.value}:{c.value}" for fn, c in self._mapping.items())
        return f"CubeFaceColors({items})"
