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
Each Alg subclass implements its own transform_by() method (polymorphic dispatch).
"""

from __future__ import annotations

from cube.domain.algs.Alg import Alg
from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
from cube.domain.algs.face_permutation import FacePermutation


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


def transform(w: Alg, a: Alg, cube_size: int | None = None) -> Alg:
    """Transform algorithm A by whole-cube rotation W.

    Returns WA such that W' A W ≡ WA.

    Each move in A is remapped by the face permutation that W induces.
    Each Alg subclass handles its own remapping via transform_by().

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
    return a.transform_by(p, n_slices)


def transform_by_permutation(
    p: FacePermutation, a: Alg, cube_size: int | None = None,
) -> Alg:
    """Transform algorithm A by a precomputed face permutation.

    Useful when applying the same rotation to multiple algorithms.
    See transform() for cube_size semantics.
    """
    n_slices = cube_size - 2 if cube_size is not None else None
    return a.transform_by(p, n_slices)
