"""CubeLayout Protocol - Interface for cube face-color layouts.

A CubeLayout represents the mapping of faces to colors on a Rubik's cube.
It also provides geometric utilities for determining face relationships
(opposite, adjacent) which are fundamental to cube operations.

The standard layout is BOY (Blue-Orange-Yellow on Front-Left-Up corner).
See cube_boy.py for the canonical BOY definition.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection
from typing import TYPE_CHECKING, ClassVar, Mapping, Protocol, runtime_checkable

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.model.cube_layout.slice_layout import SliceLayout

if TYPE_CHECKING:
    from cube.utils.config_protocol import ConfigProtocol


def _build_adjacent(all_opposite: Mapping[FaceName, FaceName]) -> Mapping[FaceName, tuple[FaceName, ...]]:
    """Build adjacent faces mapping from opposite faces mapping."""
    return {
        face: tuple(f for f in FaceName if f != face and f != all_opposite[face])
        for face in FaceName
    }


# Class-level constants for face geometry (shared by all implementations)
_OPPOSITE: Mapping[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R
}

_REV_OPPOSITE: Mapping[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}

_ALL_OPPOSITE: Mapping[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}

_ADJACENT: Mapping[FaceName, tuple[FaceName, ...]] = _build_adjacent(_ALL_OPPOSITE)


@runtime_checkable
class CubeLayout(Protocol):
    """Protocol for cube face-color layout management.

    A CubeLayout maps each face (F, R, U, L, D, B) to a color.
    It provides both instance methods for working with a specific layout
    and static methods for geometric face relationships.

    Instance Usage:
        layout = get_boy_layout(sp)
        color = layout[FaceName.F]  # Get front face color
        opposite = layout.opposite_color(Color.BLUE)  # Get color opposite to blue

    Static Usage (geometry):
        opposite_face = CubeLayout.opposite(FaceName.F)  # Returns FaceName.B
        is_adj = CubeLayout.is_adjacent(FaceName.F, FaceName.U)  # Returns True
        adjacent = CubeLayout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)

    Attributes:
        _opposite: Mapping of faces to their opposites (F→B, U→D, L→R)
        _all_opposite: Complete opposite mapping (both directions)
        _adjacent: Mapping of each face to its 4 adjacent faces
    """

    # Class-level geometry constants (shared by protocol and implementations)
    _opposite: ClassVar[Mapping[FaceName, FaceName]] = _OPPOSITE
    _all_opposite: ClassVar[Mapping[FaceName, FaceName]] = _ALL_OPPOSITE
    _adjacent: ClassVar[Mapping[FaceName, tuple[FaceName, ...]]] = _ADJACENT



    @property
    @abstractmethod
    def config(self) -> ConfigProtocol:
        """Get configuration via service provider."""
        ...

    @abstractmethod
    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face.

        Args:
            face: The face to get the color for.

        Returns:
            The color assigned to that face.

        Example:
            color = layout[FaceName.F]  # Get front face color
        """
        ...

    @abstractmethod
    def get_slice(self, slice_name: SliceName) -> SliceLayout:
        """Get the slice for a specific face.
        Args:

        """
        ...

    @abstractmethod
    def colors(self) -> Collection[Color]:
        """Get all colors in this layout.

        Returns:
            Collection of all 6 face colors.
        """
        ...

    @abstractmethod
    def edge_colors(self) -> Collection[frozenset[Color]]:
        """Get all valid edge color combinations.

        An edge has exactly 2 colors, from adjacent (non-opposite) faces.

        Returns:
            Collection of frozensets, each containing 2 colors that can
            appear together on an edge piece.
        """
        ...

    @staticmethod
    def opposite(fn: FaceName) -> FaceName:
        """Get the face opposite to the given face.

        Opposite faces never share an edge or corner. On a solved cube,
        opposite faces have complementary colors.

        Opposite pairs:
            F ↔ B (Front/Back)
            U ↔ D (Up/Down)
            L ↔ R (Left/Right)

        Args:
            fn: The face to get the opposite of.

        Returns:
            The opposite face.

        Example:
            CubeLayout.opposite(FaceName.F)  # Returns FaceName.B
        """
        return _ALL_OPPOSITE[fn]

    @staticmethod
    def is_adjacent(face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge).

        Two faces are adjacent if they are neither the same nor opposite.
        Adjacent faces share exactly one edge on the cube.

        Example:
            F and U are adjacent (share top edge of F)
            F and B are NOT adjacent (they are opposite)
            F and F are NOT adjacent (same face)

        Args:
            face1: First face.
            face2: Second face.

        Returns:
            True if faces share an edge, False otherwise.
        """
        return face2 in _ADJACENT[face1]

    @staticmethod
    def get_adjacent_faces(face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face (faces that share an edge).

        Each face has exactly 4 adjacent faces (all except itself and its opposite).

        Args:
            face: The face to get adjacent faces for.

        Returns:
            Tuple of 4 adjacent FaceNames.

        Example:
            CubeLayout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)
        """
        return _ADJACENT[face]

    @abstractmethod
    def opposite_color(self, color: Color) -> Color:
        """Get the color on the face opposite to the given color's face.

        Args:
            color: A color that appears on one of the faces.

        Returns:
            The color on the opposite face.

        Raises:
            InternalSWError: If color is not found in this layout.
        """
        ...

    @abstractmethod
    def same(self, other: CubeLayout) -> bool:
        """Check if this layout is equivalent to another.

        Two layouts are "same" if they represent the same color scheme,
        possibly with the cube rotated to a different orientation.

        This accounts for:
        - Opposite color pairs must match
        - Relative positions of colors around the cube

        Args:
            other: Another layout to compare with.

        Returns:
            True if layouts are equivalent, False otherwise.
        """
        ...

    @abstractmethod
    def is_boy(self) -> bool:
        """Check if this layout matches the standard BOY color scheme.

        BOY (Blue-Orange-Yellow) is the standard Rubik's cube color arrangement.
        The name comes from the Front-Left-Up corner colors: Blue-Orange-Yellow.

        UNFOLDED CUBE LAYOUT:
        ====================
                    ┌───────┐
                    │   Y   │
                    │   U   │  Yellow (Up)
                    │       │
            ┌───────┼───────┼───────┬───────┐
            │   O   │   B   │   R   │   G   │
            │   L   │   F   │   R   │   B   │
            │       │       │       │       │
            └───────┼───────┼───────┴───────┘
                    │   W   │
                    │   D   │  White (Down)
                    │       │
                    └───────┘

        OPPOSITE FACES:
            F (Blue)   ↔ B (Green)
            U (Yellow) ↔ D (White)
            L (Orange) ↔ R (Red)

        Returns:
            True if this layout matches the global BOY definition.
        """
        ...

    @abstractmethod
    def clone(self) -> CubeLayout:
        """Create a mutable copy of this layout.

        Returns:
            A new CubeLayout with the same face-color mapping,
            but with read_only=False.
        """
        ...
