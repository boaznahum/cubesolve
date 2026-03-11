"""
Standard Wide Layer Algorithm — nRw / nr notation.

WCA STANDARD NOTATION
=====================

Wide moves turn n outermost layers from a face side.
Default n=2 (omitted in string representation).

    Rw  = 2Rw = 2 outermost layers from R (R face + 1 inner)
    3Rw = 3 outermost layers from R (R face + 2 inner)
    nRw = n outermost layers from R

Lowercase form is equivalent:
    r   = Rw  = 2 layers
    3r  = 3Rw = 3 layers

WCA uses the uppercase+w form officially. Lowercase is informal but widely used.

ALL-BUT-LAST MODE (layers=ALL_BUT_LAST)
=======================================

When layers=-1 (ALL_BUT_LAST sentinel), the move adapts to cube size at play time,
turning ALL layers except the opposite face (= cube.size - 1 layers).

    str() = "[:-1]Rw" or "[:-1]r"

This is used by CFOP F2L algorithms that need to work on both shadow 3x3
cubes and real NxN cubes without breaking edge pairing.

    3x3: [:-1]Rw moves [0, 1]          = 2 layers (R + 1 inner)
    4x4: [:-1]Rw moves [0, 1, 2]       = 3 layers (R + 2 inner)
    5x5: [:-1]Rw moves [0, 1, 2, 3]    = 4 layers (R + 3 inner)
    NxN: [:-1]Rw moves [0, ..., N-2]   = N-1 layers

SLICE INDICES
=============

At play time, computes 0-based slice indices [0, 1, ..., layers-1]:
    Rw  (layers=2): [0, 1]       = face + 1 inner
    3Rw (layers=3): [0, 1, 2]    = face + 2 inner
    nRw (layers=n): [0, ..., n-1] = face + (n-1) inner
"""

from typing import Collection, Self, Tuple

from cube.domain.algs._internal_utils import _inv, n_to_str
from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
from cube.domain.algs.SimpleAlg import SimpleAlg
from cube.domain.model import Cube, FaceName, PartSlice

# Sentinel value: all layers except the opposite face (adaptive to cube size)
ALL_BUT_LAST = -1


class WideLayerAlg(AnimationAbleAlg):
    """
    Standard wide move: nRw = n outermost layers from face side.

    Default layers=2 (omitted in str). Rw = r = 2 layers.
    3Rw = 3r = 3 layers. nRw = nr = n layers.
    layers=ALL_BUT_LAST (-1): adaptive, all-but-last (str = [:-1]Rw / [:-1]r).

    Two display modes:
    - uppercase+w: Rw, 3Rw, [:-1]Rw (WCA official)
    - lowercase: r, 3r, [:-1]r (informal equivalent)

    All instances are frozen (immutable) after construction.
    """

    __slots__ = ("_face", "_layers", "_lowercase")

    def __init__(self, face: FaceName, layers: int = 2, n: int = 1,
                 *, lowercase: bool = False) -> None:
        if lowercase:
            code = face.value.lower()  # "r"
        else:
            code = face.value + "w"  # "Rw"
        super().__init__(code, n)
        self._face: FaceName = face
        self._layers: int = layers
        self._lowercase: bool = lowercase
        self._freeze()

    def _create_with_n(self, n: int) -> Self:
        """Create a new WideLayerAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_face", self._face)
        object.__setattr__(instance, "_layers", self._layers)
        object.__setattr__(instance, "_lowercase", self._lowercase)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def with_layers(self, layers: int) -> "WideLayerAlg":
        """Create a new WideLayerAlg with different layer count."""
        if layers == self._layers:
            return self
        return WideLayerAlg(self._face, layers, self._n, lowercase=self._lowercase)

    def _effective_layers(self, cube: Cube) -> int:
        """Compute actual layer count for this cube.

        For ALL_BUT_LAST (-1): returns cube.size - 1 (adaptive).
        For fixed layers: clamps to cube.size - 1 (can't exceed available layers).
        """
        if self._layers == ALL_BUT_LAST:
            return cube.size - 1
        return min(self._layers, cube.size - 1)

    def play(self, cube: Cube, inv: bool = False) -> None:
        """
        Play the wide move, turning `layers` outermost layers.

        On any cube size:
            Rw  (layers=2): slices [0, 1]       = face + 1 inner
            3Rw (layers=3): slices [0, 1, 2]    = face + 2 inner
            nRw (layers=n): slices [0, ..., n-1] = face + (n-1) inner
            [:-1]Rw (layers=-1): slices [0, ..., size-2] = all but opposite face

        Layers are clamped to cube.size - 1 (can't exceed available layers).
        """
        slices = list(range(self._effective_layers(cube)))
        cube.rotate_face_and_slice(_inv(inv, self._n), self._face, slices)

    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """Get all parts involved in the wide move for animation."""
        slices = list(range(self._effective_layers(cube)))
        parts = cube.get_rotate_face_and_slice_involved_parts(self._face, slices)
        return self._face, parts

    def atomic_str(self) -> str:
        """Return nRw or nr notation.

        layers=-1 (ALL_BUT_LAST): [:-1]Rw / [:-1]r
        layers=2: Rw / r (prefix omitted, 2 is default)
        layers=3: 3Rw / 3r
        layers=n: nRw / nr
        """
        if self._lowercase:
            base = self._face.value.lower()
        else:
            base = self._face.value + "w"

        if self._layers == ALL_BUT_LAST:
            return "[:-1]" + n_to_str(base, self._n)

        prefix = str(self._layers) if self._layers != 2 else ""
        return prefix + n_to_str(base, self._n)

    def same_form(self, a: "SimpleAlg") -> bool:
        if not isinstance(a, WideLayerAlg):
            return False
        return self._face == a._face and self._layers == a._layers

    @property
    def face_name(self) -> FaceName:
        return self._face

    @property
    def layers(self) -> int:
        return self._layers
