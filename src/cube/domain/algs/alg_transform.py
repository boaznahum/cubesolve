"""Algorithm transformation by whole-cube rotations.

Implements T(W, A) = WA where:
  - W is a sequence of whole-cube rotations (X, Y, Z and their primes/multiples)
  - A is any cube algorithm
  - WA is A with all moves remapped by the face permutation W induces

Mathematical identity: W' A W ≡ WA
  (undo rotation, do original move, redo rotation = do transformed move)

Equivalently: A W = W WA
  (whole-cube rotations can be "pushed through" an algorithm by transforming each move)

Example:
  W = Y', A = F → WA = R
  Because Y' sends the F face to the R position.

Key insight: each whole-cube rotation is just a permutation of 6 face names.
Transforming any algorithm reduces to remapping face names through that permutation.
"""

from __future__ import annotations

from collections.abc import Sequence

from cube.domain.algs.Alg import Alg
from cube.domain.algs.FaceAlg import FaceAlg
from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg
from cube.domain.algs.WideLayerAlg import WideLayerAlg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.algs.MiddleSliceAlg import MiddleSliceAlg
from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg
from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.Inv import _Inv
from cube.domain.algs.Mul import _Mul
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.MarkerMeetAlg import MarkerMeetAlg
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
# Content movement direction matches code in Cube.x_rotate / y_rotate / z_rotate:
#   X (like R): F→U→B→D→F   R,L fixed
#   Y (like U): F→L→B→R→F   U,D fixed
#   Z (like F): U→R→D→L→U   F,B fixed

_X_PERM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.U, FaceName.U: FaceName.B,
    FaceName.B: FaceName.D, FaceName.D: FaceName.F,
    FaceName.R: FaceName.R, FaceName.L: FaceName.L,
}

_Y_PERM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.L, FaceName.L: FaceName.B,
    FaceName.B: FaceName.R, FaceName.R: FaceName.F,
    FaceName.U: FaceName.U, FaceName.D: FaceName.D,
}

_Z_PERM: dict[FaceName, FaceName] = {
    FaceName.U: FaceName.R, FaceName.R: FaceName.D,
    FaceName.D: FaceName.L, FaceName.L: FaceName.U,
    FaceName.F: FaceName.F, FaceName.B: FaceName.B,
}

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
# Permutation computation from whole-cube rotation sequences
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_permutation(w: Alg) -> FacePermutation:
    """Compute the face permutation induced by whole-cube rotation sequence W.

    Args:
        w: Algorithm containing only whole-cube rotations (X, Y, Z).

    Returns:
        The composed FacePermutation.

    Raises:
        ValueError: If w contains non-whole-cube moves.
    """
    p = FacePermutation.identity()
    for move in w.flatten():
        if not isinstance(move, WholeCubeAlg):
            raise ValueError(
                f"W must contain only whole-cube rotations (X, Y, Z), got: {move}"
            )
        axis_p = FacePermutation.from_axis(move.axis_name, move.n)
        p = p.then(axis_p)
    return p


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Internal helpers for slice and axis remapping
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _remap_by_rotation_face(
    p: FacePermutation, rotation_face: FaceName, n: int,
    face_to_name: dict[FaceName, SliceName | AxisName],
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


def _transform_slice(
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


def _transform_axis(
    p: FacePermutation, axis: AxisName, n: int,
) -> tuple[AxisName, int]:
    """Transform a whole-cube axis and direction by the face permutation."""
    rotation_face = AXIS_FACE[axis]
    new_name, new_n, _ = _remap_by_rotation_face(p, rotation_face, n, FACE_TO_AXIS)
    assert isinstance(new_name, AxisName)
    return new_name, new_n


def _mirror_slice_indices(
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main transformation API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def transform(w: Alg, a: Alg, cube_size: int | None = None) -> Alg:
    """Transform algorithm A by whole-cube rotation W.

    Returns WA such that W' A W ≡ WA.

    Each move in A is remapped by the face permutation that W induces.

    Args:
        w: Whole-cube rotation sequence (only X, Y, Z moves).
        a: Any cube algorithm to transform.
        cube_size: Required when A contains sliced slice moves (e.g., M[2:3])
            AND the transform negates the slice direction. On direction negation,
            slice indices must be mirrored, which requires knowing n_slices = cube_size - 2.
            Not needed for face moves, unsliced slices, middle slices, or wide moves.

    Returns:
        The transformed algorithm WA.

    Examples:
        >>> from cube.domain.algs.Algs import Algs
        >>> transform(Algs.Y.prime, Algs.F)  # Y' transforms F → R
        R
        >>> transform(Algs.X, Algs.R)  # X transforms R → R (fixed axis)
        R
        >>> transform(Algs.X, Algs.F)  # X transforms F → U
        U
    """
    p = compute_permutation(w)
    n_slices = cube_size - 2 if cube_size is not None else None
    return _transform_alg(p, a, n_slices)


def transform_by_permutation(
    p: FacePermutation, a: Alg, cube_size: int | None = None,
) -> Alg:
    """Transform algorithm A by a precomputed face permutation.

    Useful when applying the same rotation to multiple algorithms.
    See transform() for cube_size semantics.
    """
    n_slices = cube_size - 2 if cube_size is not None else None
    return _transform_alg(p, a, n_slices)


def _transform_alg(p: FacePermutation, a: Alg, n_slices: int | None) -> Alg:
    """Recursively transform an algorithm by a face permutation."""

    # --- Face moves ---
    if isinstance(a, SlicedFaceAlg):
        # Must check before FaceAlg (SlicedFaceAlg is not a subclass of FaceAlg
        # but both inherit FaceAlgBase)
        return SlicedFaceAlg(p(a.face_name), a.n, a.slices)

    if isinstance(a, FaceAlg):
        from cube.domain.algs.Algs import Algs
        return Algs.of_face(p(a.face_name)).with_n(a.n)

    # --- Wide moves ---
    if isinstance(a, WideLayerAlg):
        return WideLayerAlg(
            p(a.face_name), a.layers, a.n,
            lowercase=a._lowercase,  # noqa: SLF001 - same package
        )

    # --- Slice moves (check subclasses before base) ---
    if isinstance(a, MiddleSliceAlg):
        new_slice, new_n, _ = _transform_slice(p, a.slice_name, a.n)
        return MiddleSliceAlg(new_slice).with_n(new_n)

    if isinstance(a, SlicedSliceAlg):
        new_slice, new_n, negated = _transform_slice(p, a.slice_name, a.n)
        slices = a.slices
        if negated:
            # When direction is negated, slice indices must be mirrored:
            # the "near side" of the axis swaps. See _mirror_slice_indices.
            if n_slices is None:
                raise ValueError(
                    f"cube_size is required to transform sliced slice {a} "
                    f"(direction negated: indices must be mirrored)"
                )
            slices = _mirror_slice_indices(slices, n_slices)
        return SlicedSliceAlg(new_slice, new_n, slices)

    if isinstance(a, SliceAlg):
        new_slice, new_n, _ = _transform_slice(p, a.slice_name, a.n)
        from cube.domain.algs.Algs import Algs
        return Algs.of_slice(new_slice).with_n(new_n)

    # --- Whole-cube rotations ---
    if isinstance(a, WholeCubeAlg):
        new_axis, new_n = _transform_axis(p, a.axis_name, a.n)
        return _get_axis_alg(new_axis).with_n(new_n)

    # --- Composite algorithms ---
    if isinstance(a, _Inv):
        return _transform_alg(p, a._alg, n_slices).inv()  # noqa: SLF001

    if isinstance(a, _Mul):
        return _transform_alg(p, a._alg, n_slices) * a._n  # noqa: SLF001

    if isinstance(a, SeqAlg):
        transformed = [_transform_alg(p, sub, n_slices) for sub in a.algs]
        return SeqAlg(a._name, *transformed)  # noqa: SLF001

    # --- Pass-through for annotations ---
    if isinstance(a, (AnnotationAlg, MarkerMeetAlg)):
        return a

    raise ValueError(f"Unknown algorithm type: {type(a).__name__}")


def _get_axis_alg(axis: AxisName) -> WholeCubeAlg:
    """Get the canonical WholeCubeAlg for an axis."""
    from cube.domain.algs.Algs import Algs
    if axis == AxisName.X:
        return Algs.X
    elif axis == AxisName.Y:
        return Algs.Y
    else:
        return Algs.Z
