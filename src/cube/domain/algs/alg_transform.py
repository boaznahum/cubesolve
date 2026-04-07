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

Public API:
  - a.transform(w)               — transform algorithm a by whole-cube rotation w
  - a.transform(w, cube_size=5)  — same, with cube_size for sliced slice moves
  - compute_permutation(w)       — extract the FacePermutation from a rotation sequence
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
