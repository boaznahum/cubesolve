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

    # Transform coordinates
    new_r, new_c = fr(0, 0)  # (0, 0) -> (0, 2) for CW1 on 3x3

    # Composition
    fr2 = FUnitRotation.CW1 * FUnitRotation.CW1  # = CW2

    # Inverse
    fr_inv = -FUnitRotation.CW1  # = CW3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Tuple

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


def _apply_cw_once(r: int, c: int, n: int) -> Tuple[int, int]:
    """Apply one 90° clockwise rotation: (r, c) -> (c, n-1-r)"""
    return (c, n - 1 - r)


@dataclass(frozen=True)
class FRotation:
    """
    A face rotation transformation for a specific cube size.

    This class can transform (row, col) coordinates according to the rotation.
    Supports composition (*) and inverse (-).

    Attributes:
        n: The cube size (number of rows/columns on a face)
        _n_rotation: Number of 90° clockwise rotations (0-3)
    """
    n: int
    _n_rotation: int  # 0-3 quarter turns clockwise

    def __call__(self, r: int, c: int) -> Tuple[int, int]:
        """Transform a coordinate (r, c) according to this rotation."""
        result = (r, c)
        for _ in range(self._n_rotation % 4):
            result = _apply_cw_once(result[0], result[1], self.n)
        return result

    def __mul__(self, other: FRotation) -> FRotation:
        """Compose two rotations: (self * other) means apply other first, then self."""
        if self.n != other.n:
            raise ValueError(f"Cannot multiply rotations with different sizes: {self.n} vs {other.n}")
        return FRotation(n=self.n, _n_rotation=(self._n_rotation + other._n_rotation) % 4)

    def __neg__(self) -> FRotation:
        """Return the inverse rotation."""
        return FRotation(n=self.n, _n_rotation=(4 - self._n_rotation) % 4)

    @property
    def is_identity(self) -> bool:
        """True if this is the identity rotation."""
        return self._n_rotation % 4 == 0

    @property
    def unit(self) -> FUnitRotation:
        """The unit rotation (size-independent), returns singleton constant."""
        return _UNIT_ROTATIONS[self._n_rotation % 4]

    def __repr__(self) -> str:
        return f"FRotation(CW{self._n_rotation % 4}, n={self.n})"


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

    # Class-level constants (declared for type checkers)
    CW0: ClassVar[FUnitRotation]
    CW1: ClassVar[FUnitRotation]
    CW2: ClassVar[FUnitRotation]
    CW3: ClassVar[FUnitRotation]

    def of_cube(self, cube: "Cube") -> FRotation:
        """Create a sized rotation for the given cube."""
        return FRotation(n=cube.n_slices, _n_rotation=self._n_rotation)

    def of_n_slices(self, n: int) -> FRotation:
        """Create a sized rotation for an n x n face."""
        return FRotation(n=n, _n_rotation=self._n_rotation)

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
        return f"FUnitRotation.CW{self._n_rotation % 4}"


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
