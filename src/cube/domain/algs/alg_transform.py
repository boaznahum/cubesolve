"""Algorithm transformation by whole-cube rotations.

T(W, A) moves algorithm A to a different position on the cube.
If A acts on positions POS1 and W maps POS1 to POS2, then T(W, A)
acts on POS2.

Definition:  W · T(W, A) · W'  =  A

In practice, T just remaps face names in A through the permutation
that W induces. No cube operations are performed.

Example:
  W = Y', A = F  ->  T(Y', F) = R
  Because Y' maps F to R.

Public API:
  - a.transform(w)               — move algorithm a to W's position
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
