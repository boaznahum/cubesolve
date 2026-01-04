"""
Face Rotation Transformations (FRotation)
==========================================

This module defines transformations for points on a cube face when the face rotates.

Two classes:
- FRotation: Unit rotation (size-independent), defines the transformation type
- SizedFRotation: Size-specific rotation that can transform (row, col) coordinates

Usage::

    # Get a sized rotation from a unit rotation
    fr_cw = FRotation.CW.of_n_slices(3)  # For 3x3 cube

    # Transform coordinates
    new_r, new_c = fr_cw(0, 0)  # (0, 0) -> (0, 2) for CW on 3x3

    # Or use with a cube
    fr_cw = FRotation.CW.of_cube(cube)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Tuple

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


@dataclass(frozen=True)
class SizedFRotation:
    """
    A face rotation transformation for a specific cube size.

    This class can transform (row, col) coordinates according to the rotation.

    Attributes:
        n: The cube size (number of rows/columns on a face)
        _transform: The transformation function (r, c, n) -> (new_r, new_c)
        name: Human-readable name of the rotation
    """
    n: int
    _transform: Callable[[int, int, int], Tuple[int, int]]
    name: str

    def __call__(self, r: int, c: int) -> Tuple[int, int]:
        """Transform a coordinate (r, c) according to this rotation."""
        return self._transform(r, c, self.n)

    def __repr__(self) -> str:
        return f"SizedFRotation({self.name}, n={self.n})"


# Transformation functions for each rotation type
def _identity(r: int, c: int, n: int) -> Tuple[int, int]:
    """No rotation: (r, c) -> (r, c)"""
    return (r, c)


def _cw(r: int, c: int, n: int) -> Tuple[int, int]:
    """90 degrees clockwise: (r, c) -> (c, n-1-r)"""
    return (c, n - 1 - r)


def _ccw(r: int, c: int, n: int) -> Tuple[int, int]:
    """90 degrees counter-clockwise: (r, c) -> (n-1-c, r)"""
    return (n - 1 - c, r)


def _r2(r: int, c: int, n: int) -> Tuple[int, int]:
    """180 degrees: (r, c) -> (n-1-r, n-1-c)"""
    return (n - 1 - r, n - 1 - c)


@dataclass(frozen=True)
class FRotation:
    """
    Unit face rotation transformation (size-independent).

    This class represents a rotation type without knowing the cube size.
    Use of_cube() or of_n_slices() to get a SizedFRotation that can
    transform coordinates.

    Predefined instances:
        FRotation.I   - Identity (no rotation)
        FRotation.CW  - 90 degrees clockwise
        FRotation.CCW - 90 degrees counter-clockwise
        FRotation.R2  - 180 degrees (half turn)
    """
    _transform: Callable[[int, int, int], Tuple[int, int]]
    name: str

    def of_cube(self, cube: "Cube") -> SizedFRotation:
        """Create a sized rotation for the given cube."""
        return SizedFRotation(n=cube.size, _transform=self._transform, name=self.name)

    def of_n_slices(self, n: int) -> SizedFRotation:
        """Create a sized rotation for an n x n face."""
        return SizedFRotation(n=n, _transform=self._transform, name=self.name)

    def __repr__(self) -> str:
        return f"FRotation.{self.name}"


# Predefined unit rotations
FRotation.I = FRotation(_transform=_identity, name="I")
FRotation.CW = FRotation(_transform=_cw, name="CW")
FRotation.CCW = FRotation(_transform=_ccw, name="CCW")
FRotation.R2 = FRotation(_transform=_r2, name="R2")
