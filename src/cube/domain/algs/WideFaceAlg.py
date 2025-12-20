"""
Wide Face Algorithm - Adaptive wide moves for NxN cubes.

WHY THIS IS NEEDED FOR CFOP
===========================

CFOP's F2L uses "wide" moves (lowercase d, u, r, l, f, b) that move a face
plus all inner layers, leaving only the opposite face stationary.

On a 3x3:
    d = D (just the D face, no inner layers exist)

On a 5x5:
    d = D + all 3 inner layers = D[0,1,2,3]
    This keeps edges paired because all layers move together.

THE PROBLEM WITH FIXED SLICES
=============================

When CFOP solves a shadow 3x3 cube, it creates algorithms like:

    d = Algs.D[1:1 + cube.n_slices]  # On 3x3: D[1:2]

The slice range [1:2] is STORED in the algorithm. When this algorithm
is later played on a 5x5 cube, it still uses [1:2], which only moves
2 layers instead of all 4. This BREAKS edge pairing:

    5x5 D[0,1]   -> moves 2 of 4 layers -> edges BROKEN
    5x5 D[0,1,2,3] -> moves all 4 layers -> edges PAIRED

THE SOLUTION: WideFaceAlg
=========================

WideFaceAlg computes the slice range at PLAY TIME based on the target
cube's size, not at creation time. It always moves:

    [0, 1, 2, ..., size-2]  = face + all inner layers

This makes the algorithm work correctly on ANY cube size:

    | Cube | WideFaceAlg(D) moves | Edges |
    |------|---------------------|-------|
    | 3x3  | D[0]                | OK    |
    | 4x4  | D[0,1,2]            | OK    |
    | 5x5  | D[0,1,2,3]          | OK    |
    | NxN  | D[0..N-2]           | OK    |

USAGE IN F2L
============

Before (broken on NxN):
    d = Algs.D[1:1 + cube.n_slices]

After (works on all sizes):
    d = Algs.d  # WideFaceAlg instance

STANDARD NOTATION
=================

In standard cubing notation:
    - Uppercase (R, D, U) = outer face only
    - Lowercase (r, d, u) = wide move (face + inner layers)

This class implements the lowercase wide moves that adapt to cube size.
"""

from typing import Tuple, Collection

from cube.domain.algs.FaceAlg import FaceAlg
from cube.domain.algs._internal_utils import _inv
from cube.domain.model import FaceName, Cube, PartSlice


class WideFaceAlg(FaceAlg):
    """
    Wide face move that adapts to cube size at play time.

    Moves the face + ALL inner layers (everything except opposite face).
    The slice range is computed dynamically based on the target cube's size.

    This is essential for CFOP algorithms that need to work on both
    shadow 3x3 cubes and real NxN cubes without breaking edge pairing.
    """

    def __init__(self, face: FaceName, n: int = 1) -> None:
        super().__init__(face, n)

    def play(self, cube: Cube, inv: bool = False):
        """
        Play the wide move, computing slices based on target cube size.

        On 3x3 (size=3): slices = [0]         (just the face)
        On 4x4 (size=4): slices = [0,1,2]     (face + 2 inner)
        On 5x5 (size=5): slices = [0,1,2,3]   (face + 3 inner)
        On NxN (size=N): slices = [0..N-2]    (face + all inner)
        """
        # All layers from the face side: [0, 1, ..., size-2]
        # This leaves only the opposite face unmoved
        slices = list(range(cube.size - 1))
        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """Get all parts involved in the wide move for animation."""
        slices = list(range(cube.size - 1))
        parts = cube.get_rotate_face_and_slice_involved_parts(self._face, slices)
        return self._face, parts

    def atomic_str(self) -> str:
        """Return lowercase letter to indicate wide move (standard notation)."""
        return self._face.value.lower()

    def clone(self) -> "WideFaceAlg":
        """Create a copy of this algorithm."""
        return WideFaceAlg(self._face, self._n)


# Pre-defined wide move instances (lowercase notation)
class _wd(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.D)


class _wu(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.U)


class _wr(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.R)


class _wl(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.L)


class _wf(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.F)


class _wb(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.B)
