"""
Face Rotation Transformations (FRotation)
==========================================

This module defines transformations for points on a cube face when the face rotates.

Two classes:
- FUnitRotation: Unit rotation (size-independent), defines the rotation amount
- FRotation: Size-specific rotation that can transform (row, col) coordinates

Both support multiplication (*) for composition and negation (-) for inverse.

Usage::

    # Get a sized rotation from a unit rotation
    fr = FUnitRotation.CW1.of_n_slices(3)  # For 3x3 face

    # Transform coordinates (origin at bottom-left, r=row, c=col)
    new_r, new_c = fr(0, 0)  # (0, 0) -> (2, 0) for CW1 on 3x3

    # Composition
    fr2 = FUnitRotation.CW1 * FUnitRotation.CW1  # = CW2

    # Inverse
    fr_inv = -FUnitRotation.CW1  # = CW3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from cube.domain.geometric.geometry_types import Point

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


def _apply_cw(r: int, c: int, n_slices: int, n_rotation: int) -> Point:
    for _ in range(n_rotation):
        r, c = (n_slices - 1 - c, r)

    return Point(r, c)


@dataclass(frozen=True)
class FRotation:
    """
    A face rotation transformation for a specific cube size.

    This class can transform (row, col) coordinates according to the rotation.
    Supports composition (*) and inverse (-).

    Attributes:
        n_slices: The cube size (number of rows/columns on a face)
        n_rotation: Number of 90° clockwise rotations (0-3)
    """
    n_slices: int
    n_rotation: int  # 0-3 quarter turns clockwise

    def __call__(self, r: int, c: int) -> Point:
        """Transform a coordinate (r, c) according to this rotation."""
        return _apply_cw(r, c, self.n_slices, self.n_rotation)

    def __mul__(self, other: FRotation) -> FRotation:
        """Compose two rotations: (self * other) means apply other first, then self."""
        if self.n_slices != other.n_slices:
            raise ValueError(f"Cannot multiply rotations with different sizes: {self.n_slices} vs {other.n_slices}")
        return FRotation(n_slices=self.n_slices, n_rotation=(self.n_rotation + other.n_rotation) % 4)

    def __neg__(self) -> FRotation:
        """Return the inverse rotation."""
        return FRotation(n_slices=self.n_slices, n_rotation=(4 - self.n_rotation) % 4)

    @property
    def is_identity(self) -> bool:
        """True if this is the identity rotation."""
        return self.n_rotation % 4 == 0

    @property
    def unit(self) -> FUnitRotation:
        """The unit rotation (size-independent), returns singleton constant."""
        return _UNIT_ROTATIONS[self.n_rotation % 4]

    def __repr__(self) -> str:
        return f"FRotation(CW{self.n_rotation % 4}, n={self.n_slices})"

@dataclass(frozen=True)
class FUnitRotation:
    """
    Unit face rotation transformation (size-independent).

    This class represents a rotation amount without knowing the cube size.
    Use of_cube() or of_n_slices() to get a FRotation that can transform coordinates.
    Supports composition (*) and inverse (-).

    Predefined instances:
        FUnitRotation.CW0 - Identity (no rotation)
        FUnitRotation.CW1 - 90 degrees clockwise
        FUnitRotation.CW2 - 180 degrees (half turn)
        FUnitRotation.CW3 - 270 degrees clockwise (= 90 degrees counter-clockwise)
    """
    _n_rotation: int  # 0-3 quarter turns clockwise
    _str: str = field(init=False)

    def __post_init__(self) -> None:
        # Compute what (0,0) transforms to on a 2x2 face for display
        result = _apply_cw(0, 0, 2, self._n_rotation)
        object.__setattr__(self, '_str', f"CW{self._n_rotation % 4}{result}")

    # Class-level constants (declared for type checkers)
    CW0: ClassVar[FUnitRotation]  # Identity (no rotation)
    CW1: ClassVar[FUnitRotation]  # 90 degrees clockwise
    CW2: ClassVar[FUnitRotation]  # 180 degrees (half turn)
    CW3: ClassVar[FUnitRotation]  # 270 degrees clockwise (= 90 degrees counter-clockwise)

    def of_cube(self, cube: "Cube") -> FRotation:
        """Create a sized rotation for the given cube."""
        return FRotation(n_slices=cube.n_slices, n_rotation=self._n_rotation)

    def of_n_slices(self, n: int) -> FRotation:
        """Create a sized rotation for an n x n face."""
        return FRotation(n_slices=n, n_rotation=self._n_rotation)

    def __mul__(self, other: FUnitRotation) -> FUnitRotation:
        """Compose two rotations: (self * other) means apply other first, then self."""
        return FUnitRotation(_n_rotation=(self._n_rotation + other._n_rotation) % 4)

    def __neg__(self) -> FUnitRotation:
        """Return the inverse rotation."""
        return FUnitRotation(_n_rotation=(4 - self._n_rotation) % 4)

    @property
    def is_identity(self) -> bool:
        """True if this is the identity rotation."""
        return self._n_rotation % 4 == 0

    def __repr__(self) -> str:
        return self._str

    @staticmethod
    def of(n_slices: int, source: Point, target: Point) -> FUnitRotation:

        """
        Given two points on known cube size, compute the unit transform such that
          >>> ut: FUnitRotation = ...
          >>> ut.of_n_slices(n_slices)(source) == target
        :param n_slices:
        :param source:
        :param target:
        :return:

        :raises ValueError: In no such trasfrom exists
        """
        # Determine which FUnitRotation matches this transformation
        for unit_rot in [FUnitRotation.CW0, FUnitRotation.CW1, FUnitRotation.CW2, FUnitRotation.CW3]:
            if unit_rot.of_n_slices(n_slices)(*source) == target:
                return unit_rot
        raise ValueError(
            f"No valid transformation found between {source} and {target}"
        )


# Predefined unit rotations
FUnitRotation.CW0 = FUnitRotation(_n_rotation=0)
FUnitRotation.CW1 = FUnitRotation(_n_rotation=1)
FUnitRotation.CW2 = FUnitRotation(_n_rotation=2)
FUnitRotation.CW3 = FUnitRotation(_n_rotation=3)

# Lookup tuple for FRotation.unit property
_UNIT_ROTATIONS: tuple[FUnitRotation, ...] = (
    FUnitRotation.CW0,
    FUnitRotation.CW1,
    FUnitRotation.CW2,
    FUnitRotation.CW3,
)
