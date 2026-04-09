"""Face permutation induced by whole-cube rotations.

A FacePermutation is a mapping of the 6 face names {U, D, F, B, L, R}
that captures the effect of whole-cube rotations (X, Y, Z) on face positions.

The permutation tables match the content movement in Cube.x_rotate / y_rotate / z_rotate:
    X (like R): F→U→B→D→F   R,L fixed
    Y (like U): F→L→B→R→F   U,D fixed
    Z (like F): U→R→D→L→U   F,B fixed

Helper functions are provided for remapping slices and axes through
face permutations, used by each Alg subclass's transform_by() method.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from cube.domain.model.FaceName import FaceName
from cube.domain.model.cube_slice import SliceName
from cube.domain.model._elements import AxisName
from cube.domain.geometric.geometry_fundamentals import (
    AXIS_FACE,
    FACE_TO_AXIS,
    FACE_TO_SLICE,
    SLICE_ROTATION_FACE,
)
from cube.domain.geometric.schematic_cube import SchematicCube

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Face permutation tables — one CW quarter-turn per axis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Each table maps face_before -> face_after for a single clockwise
# quarter-turn of the whole cube around the given axis.
#
# These follow "content movement" — the direction the stickers move,
# matching Cube.x_rotate / y_rotate / z_rotate in the domain model.
#
#   X (rotates like R): F->U->B->D->F cycle, R and L stay fixed
#   Y (rotates like U): F->L->B->R->F cycle, U and D stay fixed
#   Z (rotates like F): U->R->D->L->U cycle, F and B stay fixed
#
# For primes (e.g. X'), apply 3 times (since -1 % 4 = 3).
# For doubles (e.g. X2), apply 2 times.
# FacePermutation.from_axis() handles this via n % 4.
#
# _AXIS_PERM maps AxisName -> the corresponding table, so we can
# look up the right table given any axis.

# X axis (like R face): the 4 faces around the R-L axis cycle.
# Imagine grabbing the R face and rotating CW — F goes up, U goes back, etc.
_X_PERM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.U, FaceName.U: FaceName.B,
    FaceName.B: FaceName.D, FaceName.D: FaceName.F,
    FaceName.R: FaceName.R, FaceName.L: FaceName.L,
}

# Y axis (like U face): the 4 faces around the U-D axis cycle.
# Imagine grabbing the U face and rotating CW — F goes left, L goes back, etc.
_Y_PERM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.L, FaceName.L: FaceName.B,
    FaceName.B: FaceName.R, FaceName.R: FaceName.F,
    FaceName.U: FaceName.U, FaceName.D: FaceName.D,
}

# Z axis (like F face): the 4 faces around the F-B axis cycle.
# Imagine grabbing the F face and rotating CW — U goes right, R goes down, etc.
_Z_PERM: dict[FaceName, FaceName] = {
    FaceName.U: FaceName.R, FaceName.R: FaceName.D,
    FaceName.D: FaceName.L, FaceName.L: FaceName.U,
    FaceName.F: FaceName.F, FaceName.B: FaceName.B,
}

# Lookup: axis name -> its permutation table.
_AXIS_PERM: dict[AxisName, dict[FaceName, FaceName]] = {
    AxisName.X: _X_PERM,
    AxisName.Y: _Y_PERM,
    AxisName.Z: _Z_PERM,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FacePermutation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FacePermutation:
    """A permutation of the 6 face names induced by whole-cube rotations.

    Each whole-cube rotation (X, Y, Z) permutes face positions.
    This class captures that permutation and supports composition.
    """

    __slots__ = ("_map",)

    _IDENTITY: FacePermutation | None = None

    def __init__(self, face_map: dict[FaceName, FaceName]) -> None:
        self._map = dict(face_map)

    @staticmethod
    def identity() -> FacePermutation:
        """The identity permutation (no face changes)."""
        if FacePermutation._IDENTITY is None:
            FacePermutation._IDENTITY = FacePermutation({f: f for f in FaceName})
        return FacePermutation._IDENTITY

    @staticmethod
    def from_axis(axis: AxisName, n: int = 1) -> FacePermutation:
        """Build permutation for n quarter-turns around an axis.

        Handles any n via modular arithmetic (n % 4).
        """
        effective = n % 4
        if effective == 0:
            return FacePermutation.identity()

        base = _AXIS_PERM[axis]
        p: dict[FaceName, FaceName] = {f: f for f in FaceName}
        for _ in range(effective):
            p = {f: base[p[f]] for f in FaceName}
        return FacePermutation(p)

    def __call__(self, face: FaceName) -> FaceName:
        """Apply the permutation to a face name."""
        return self._map[face]

    def then(self, other: FacePermutation) -> FacePermutation:
        """Compose: first apply self, then other. Returns other(self(f))."""
        return FacePermutation({f: other._map[self._map[f]] for f in FaceName})

    def is_identity(self) -> bool:
        return all(self._map[f] == f for f in FaceName)

    def __repr__(self) -> str:
        changes = [f"{f.value}→{self._map[f].value}" for f in FaceName if self._map[f] != f]
        return f"FacePermutation({', '.join(changes) or 'identity'})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper functions for slice and axis remapping
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _remap_by_rotation_face(
    p: FacePermutation, rotation_face: FaceName, n: int,
    face_to_name: Mapping[FaceName, SliceName | AxisName],
) -> tuple[SliceName | AxisName, int, bool]:
    """Remap a slice or axis based on where its rotation face maps to.

    If the rotation face maps to a known rotation face → same direction.
    If it maps to the OPPOSITE of a known rotation face → negate direction.

    Returns:
        (new_name, new_n, direction_negated)
    """
    new_face = p(rotation_face)

    if new_face in face_to_name:
        return face_to_name[new_face], n, False

    opp = SchematicCube.inst().opposite(new_face)
    if opp in face_to_name:
        return face_to_name[opp], -n, True

    raise ValueError(f"Cannot remap rotation face {rotation_face}→{new_face}")


def transform_slice(
    p: FacePermutation, slice_name: SliceName, n: int,
) -> tuple[SliceName, int, bool]:
    """Transform a slice name and direction by the face permutation.

    Returns:
        (new_slice_name, new_n, direction_negated)
        When direction_negated is True, sliced indices must be mirrored.
    """
    rotation_face = SLICE_ROTATION_FACE[slice_name]
    new_name, new_n, negated = _remap_by_rotation_face(p, rotation_face, n, FACE_TO_SLICE)
    assert isinstance(new_name, SliceName)
    return new_name, new_n, negated


def transform_axis(
    p: FacePermutation, axis: AxisName, n: int,
) -> tuple[AxisName, int]:
    """Transform a whole-cube axis and direction by the face permutation."""
    rotation_face = AXIS_FACE[axis]
    new_name, new_n, _ = _remap_by_rotation_face(p, rotation_face, n, FACE_TO_AXIS)
    assert isinstance(new_name, AxisName)
    return new_name, new_n


def mirror_slice_indices(
    slices: slice | Sequence[int], n_slices: int,
) -> slice | Sequence[int]:
    """Mirror slice indices when direction is negated.

    When a slice's rotation face maps to the OPPOSITE of the new rotation face,
    slice index 1 (closest to the old rotation face) must become index n_slices
    (closest to the new rotation face's opposite = where the old face mapped).

    Slice indices are 1-based (see SliceAlgBase.normalize_slice_index).
    Formula: index i → n_slices + 1 - i

    Example on 5x5 (n_slices=3):
        M[3] (closest to R) → S[1] (closest to F)
        M[1] (closest to L) → S[3] (closest to B)
        M[1:2] → S[2:3]
    """
    mirror = n_slices + 1  # 1-based: mirror point
    if isinstance(slices, slice):
        start, stop = slices.start, slices.stop
        # Mirror: i → mirror - i, and swap start/stop since order reverses
        new_start = (mirror - stop) if stop is not None else None
        new_stop = (mirror - start) if start is not None else None
        return slice(new_start, new_stop)
    else:
        # Sequence of ints — mirror each and re-sort
        return sorted(mirror - i for i in slices)
