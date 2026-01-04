"""CubeLayout Protocol - Interface for cube face-color layouts.

A CubeLayout represents the mapping of faces to colors on a Rubik's cube.
It also provides geometric utilities for determining face relationships
(opposite, adjacent) which are fundamental to cube operations.

The standard layout is BOY (Blue-Orange-Yellow on Front-Left-Up corner).
See cube_boy.py for the canonical BOY definition.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Mapping, Protocol, runtime_checkable

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.model.geometric.slice_layout import SliceLayout

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.utils.config_protocol import ConfigProtocol
    from cube.utils.Cache import CacheManager


def _build_adjacent(all_opposite: Mapping[FaceName, FaceName]) -> Mapping[FaceName, tuple[FaceName, ...]]:
    """Build adjacent faces mapping from opposite faces mapping."""
    return {
        face: tuple(f for f in FaceName if f != face and f != all_opposite[face])
        for face in FaceName
    }


# Module-level constants for face geometry
_OPPOSITE: Mapping[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R
}

_REV_OPPOSITE: Mapping[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}

_ALL_OPPOSITE: Mapping[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}

_ADJACENT: Mapping[FaceName, tuple[FaceName, ...]] = _build_adjacent(_ALL_OPPOSITE)


# ============================================================================
# Geometry Functions (module-level, not part of protocol)
# ============================================================================

def opposite(fn: FaceName) -> FaceName:
    """Get the face opposite to the given face.

    Opposite faces never share an edge or corner. On a solved cube,
    opposite faces have complementary colors.

    Opposite pairs:
        F ↔ B (Front/Back)
        U ↔ D (Up/Down)
        L ↔ R (Left/Right)

    Args:
        fn: The face to get the opposite of, see :class:`FaceName`.

    Returns:
        The opposite :class:`FaceName`.

    Example:
        opposite(FaceName.F)  # Returns FaceName.B

    See Also:
        :func:`is_adjacent`: Check if two faces share an edge.
        :func:`get_adjacent_faces`: Get all 4 adjacent faces.
        :meth:`CubeLayout.opposite_color`: Get color on opposite face.
    """
    return _ALL_OPPOSITE[fn]


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


def get_adjacent_faces(face: FaceName) -> tuple[FaceName, ...]:
    """Get all faces adjacent to the given face (faces that share an edge).

    Each face has exactly 4 adjacent faces (all except itself and its opposite).

    Args:
        face: The face to get adjacent faces for.

    Returns:
        Tuple of 4 adjacent FaceNames.

    Example:
        get_adjacent_faces(FaceName.F)  # (U, R, D, L)
    """
    return _ADJACENT[face]


# ============================================================================
# CubeLayout Protocol
# ============================================================================

@runtime_checkable
class CubeLayout(Protocol):
    """Protocol for cube face-color layout management.

    A CubeLayout maps each face (F, R, U, L, D, B) to a color.

    Usage:
        layout = cube.layout
        color = layout[FaceName.F]  # Get front face color
        opp = layout.opposite_color(Color.BLUE)  # Get color opposite to blue
        opposite_face = layout.opposite(FaceName.F)  # Returns FaceName.B
        is_adj = layout.is_adjacent(FaceName.F, FaceName.U)  # Returns True
        adjacent = layout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)
    """

    @property
    @abstractmethod
    def config(self) -> "ConfigProtocol":
        """Get configuration via service provider."""
        ...

    @property
    @abstractmethod
    def cache_manager(self) -> "CacheManager":
        """Get the cache manager for this layout."""
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
        """Get the slice layout for a specific slice.

        Args:
            slice_name: The slice (M, E, or S).

        Returns:
            SliceLayout for that slice.
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

    # =========================================================================
    # Geometry Instance Methods
    # =========================================================================

    @abstractmethod
    def opposite(self, fn: FaceName) -> FaceName:
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
            The opposite FaceName.

        Example:
            layout.opposite(FaceName.F)  # Returns FaceName.B
        """
        ...

    @abstractmethod
    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
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
        ...

    @abstractmethod
    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face (faces that share an edge).

        Each face has exactly 4 adjacent faces (all except itself and its opposite).

        Args:
            face: The face to get adjacent faces for.

        Returns:
            Tuple of 4 adjacent FaceNames.

        Example:
            layout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)
        """
        ...

    @abstractmethod
    def iterate_orthogonal_face_center_pieces(
            self,
            cube: "Cube",
            layer1_face: "Face",
            side_face: "Face",
            layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """
        Yield (row, col) positions on side_face for the given layer slice.

        A "layer slice" is a horizontal layer parallel to layer1_face (L1).
        Layer slice 0 is the one closest to L1.

        Args:
            cube: The cube (for n_slices)
            layer1_face: The Layer 1 face (base layer, e.g., white face)
            side_face: A face orthogonal to layer1_face
            layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

        Yields:
            (row, col) in LTR coordinates on side_face

        Raises:
            ValueError: if side_face is not orthogonal to layer1_face

        Example 1: L1=DOWN, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U
                ┌───┬───┬───┐
            row2│   │   │   │  ← layer_slice_index=2 (closest to U)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│ * │ * │ * │  ← layer_slice_index=0 (closest to D=L1)
                └───┴───┴───┘
                      D (L1)

            layer_slice_index=0 yields: (0,0), (0,1), (0,2)

        Example 2: L1=LEFT, side_face=FRONT, 5x5 cube (n_slices=3)
        ==========================================================

            Looking at FRONT face:

                L1        R
                (L)
                ┌───┬───┬───┐
                │ * │   │   │  row2
                ├───┼───┼───┤
                │ * │   │   │  row1
                ├───┼───┼───┤
                │ * │   │   │  row0
                └───┴───┴───┘
                col0 col1 col2

                ↑ layer_slice_index=0 (closest to L=L1)

            layer_slice_index=0 yields: (0,0), (1,0), (2,0)

        Example 3: L1=UP, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U (L1)
                ┌───┬───┬───┐
            row2│ * │ * │ * │  ← layer_slice_index=0 (closest to U=L1)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│   │   │   │  ← layer_slice_index=2 (closest to D)
                └───┴───┴───┘
                      D

            layer_slice_index=0 yields: (2,0), (2,1), (2,2)
        """
        ...

    @abstractmethod
    def get_slices_between_faces(
            self,
            source_face: "Face",
            target_face: "Face",
    ) -> list[SliceName]:
        """
        Get the slice(s) that connect source_face to target_face.

        For adjacent faces: returns 1 slice
        For opposite faces: returns 2 slices (both pass through)

        Args:
            source_face: The source face
            target_face: The target face

        Returns:
            List of SliceName(s) that connect the faces

        Example:
            F → U: [M] (M slice connects F and U)
            F → B: [M, E] (both M and E connect opposite faces F and B)
        """
        ...
