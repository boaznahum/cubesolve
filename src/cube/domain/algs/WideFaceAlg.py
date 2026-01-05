"""
Wide Face Algorithm - Adaptive wide moves for NxN cubes.

NOTATION REFERENCE
==================

Standard cube notation uses lowercase letters for "wide" moves:

    d = D face + all inner layers between D and U (U stays fixed)
    u = U face + all inner layers between U and D (D stays fixed)
    r = R face + all inner layers between R and L (L stays fixed)
    l = L face + all inner layers between L and R (R stays fixed)
    f = F face + all inner layers between F and B (B stays fixed)
    b = B face + all inner layers between B and F (F stays fixed)

See: https://www.speedsolving.com/wiki/index.php/NxNxN_Notation
     https://ruwix.com/the-rubiks-cube/notation/advanced/

On a 3x3, lowercase = uppercase (no inner layers exist).
On NxN, lowercase moves ALL layers on one side, keeping opposite face fixed.

WHAT EXACTLY DOES 'd' DO?
=========================

'd' (lowercase d) rotates:
  - The D face itself
  - ALL inner layers between D and U

The U face does NOT move. This is equivalent to:
  - Holding the U face fixed
  - Rotating everything else around the Y axis

On different cube sizes:
    3x3: d moves [D, M]                 = 2 layers (same as Dw, standard)
    4x4: d moves [D, inner1, inner2]    = 3 layers (U stays)
    5x5: d moves [D, inner1, inner2, inner3] = 4 layers (U stays)
    NxN: d moves [D, all N-2 inner layers]   = N-1 layers (U stays)

NOTE: On 3x3 this matches standard notation (Rw = 2 layers).
On larger cubes, this differs from standard (which says Rw = always 2 layers).

WHY THIS IS NEEDED FOR CFOP ON NxN
==================================

CFOP's F2L uses wide moves to manipulate corner-edge pairs while keeping
the cross layer intact. On a 3x3, the original code used:

    d = Algs.D[1:1 + cube.n_slices]  # Creates D[1:2] on 3x3

PROBLEM: This stores FIXED slice indices [1:2]. When the same algorithm
is played on a 5x5, it still uses [1:2], moving only 2 of 4 layers:

    5x5 with D[0,1]:     moves 2 layers -> edges BROKEN (unequal pairing)
    5x5 with D[0,1,2,3]: moves 4 layers -> edges PAIRED (all move together)

SOLUTION: WideFaceAlg computes slices at PLAY TIME based on the target
cube's size. It always moves face + ALL inner layers:

    | Cube | Algs.d moves     | Layers | Edges  |
    |------|------------------|--------|--------|
    | 3x3  | D[0]             | 1      | OK     |
    | 4x4  | D[0,1,2]         | 3      | OK     |
    | 5x5  | D[0,1,2,3]       | 4      | OK     |
    | NxN  | D[0..N-2]        | N-1    | OK     |

USAGE IN F2L
============

    # OLD (fixed slices - breaks on NxN):
    d = Algs.D[1:1 + cube.n_slices]

    # NEW (adaptive - works on all sizes):
    d = Algs.d  # WideFaceAlg instance
"""

from abc import ABC
from typing import Collection, Self, Tuple

from cube.domain.algs._internal_utils import _inv, n_to_str
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.model import Cube, FaceName, PartSlice


class WideFaceAlg(AnimationAbleAlg, ABC):
    """
    Wide face move that adapts to cube size at play time.

    Moves the face + ALL inner layers (everything except opposite face).
    The slice range is computed dynamically based on the target cube's size.

    This is essential for CFOP algorithms that need to work on both
    shadow 3x3 cubes and real NxN cubes without breaking edge pairing.

    All instances are frozen (immutable) after construction.

    Inheritance: AnimationAbleAlg -> NSimpleAlg -> SimpleAlg -> Alg
    (NOT SliceAbleAlg - wide moves are not sliceable, they adapt dynamically)
    """

    __slots__ = ("_face",)

    def __init__(self, face: FaceName, n: int = 1) -> None:
        # Use lowercase face letter as the code
        super().__init__(face.value.lower(), n)
        self._face: FaceName = face
        # Note: _freeze() is called by concrete subclasses

    def _create_with_n(self, n: int) -> Self:
        """Create a new WideFaceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_face", self._face)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def play(self, cube: Cube, inv: bool = False) -> None:
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
        """Return lowercase letter with prime/double notation (standard notation)."""
        return n_to_str(self._face.value.lower(), self._n)


# Pre-defined wide move instances (lowercase notation)
class _wd(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.D)
        self._freeze()


class _wu(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.U)
        self._freeze()


class _wr(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.R)
        self._freeze()


class _wl(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.L)
        self._freeze()


class _wf(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.F)
        self._freeze()


class _wb(WideFaceAlg):
    def __init__(self) -> None:
        super().__init__(FaceName.B)
        self._freeze()
