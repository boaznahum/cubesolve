"""CubeColorScheme — face-to-color mapping with rotation-aware comparison.

A color scheme assigns one of the six colors to each face of the cube.
The standard scheme is BOY (Blue-Orange-Yellow on the Front-Left-Up corner),
but a scrambled cube can yield any valid permutation.

NOT a singleton — unlike SchematicCube (fixed geometry), color schemes vary.

When are two schemes the same?
==============================

Two color schemes are considered *the same* if one can be rotated (whole-cube
rotation) to match the other.  The comparison (``same()``) works without
any cloning or mutation:

1. Pick any color from scheme A, find its face in scheme B.
2. The opposite face must hold the same color in both — this fixes the axis.
3. The CW neighbor colors of that face must be a cyclic rotation of each
   other — this fixes orientation (the only remaining freedom is rotation
   around the axis, which is exactly a cyclic shift of the neighbors).

Standard BOY (Blue-Orange-Yellow) color scheme::

                ┌───────┐
                │   Y   │
                │   U   │  Yellow (Up)
                │       │
        ┌───────┼───────┼───────┬───────┐
        │   O   │   B   │   R   │   G   │
        │   L   │   F   │   R   │   B   │
        │       │       │       │       │
        └───────┼───────┼───────┴───────┘
                │   W   │
                │   D   │  White (Down)
                │       │
                └───────┘

    Opposite pairs:  F(Blue)↔B(Green)  U(Yellow)↔D(White)  L(Orange)↔R(Red)

See ``cube_color_schemes.py`` for predefined schemes (``boy_scheme()`` etc.).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.schematic_cube import SchematicCube
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName


def _is_cyclic_rotation(a: tuple[Color, ...], b: tuple[Color, ...]) -> bool:
    """True if *b* is a cyclic rotation of *a* (both length 4).

    Example::

        a = (Yellow, Red, White, Orange)
        b = (White, Orange, Yellow, Red)   → shift by 2 → True
        c = (Orange, White, Red, Yellow)   → reversed  → False (mirror)
    """
    n: int = len(a)
    return n == len(b) and any(a[i:] + a[:i] == b for i in range(n))


class CubeColorScheme:
    """A face-to-color mapping for a Rubik's cube.

    Supports:
    - Face-to-color lookup (``scheme[FaceName.F]``)
    - Color-to-face reverse lookup
    - Edge color enumeration (all valid two-color pairs)
    - Scheme comparison accounting for whole-cube rotations
    """

    __slots__ = ("_faces", "_scheme", "_edge_colors",
                 "_neighbor_colors_cache", "_color_to_face")

    def __init__(self, faces: Mapping[FaceName, Color]) -> None:
        self._faces: dict[FaceName, Color] = dict(faces)
        self._scheme: SchematicCube = SchematicCube.inst()
        self._edge_colors: Collection[frozenset[Color]] | None = None
        self._neighbor_colors_cache: dict[FaceName, tuple[Color, ...]] = {}
        self._color_to_face: dict[Color, FaceName] | None = None

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face.

        Args:
            face: The face to get the color for.

        Returns:
            The color assigned to that face.

        Example:
            color = layout[FaceName.F]  # Get front face color
        """
        return self._faces[face]

    @property
    def faces(self) -> Mapping[FaceName, Color]:
        """Read-only view of the face→color mapping."""
        return self._faces


    def colors(self) -> Collection[Color]:
        """All six colors in this scheme."""
        return [*self._faces.values()]

    def edge_colors(self) -> Collection[frozenset[Color]]:
        """All valid edge color pairs (adjacent, non-opposite faces)."""
        if self._edge_colors is not None:
            return self._edge_colors

        colors: set[frozenset[Color]] = set()
        scheme = self._scheme
        for f1, c1 in self._faces.items():
            for f2, c2 in self._faces.items():
                if f1 is not f2 and f2 is not scheme.opposite(f1):
                    colors.add(frozenset((c1, c2)))

        self._edge_colors = colors
        return self._edge_colors

    def opposite_color(self, color: Color) -> Color:
        """Color on the face opposite to the face holding *color*."""
        return self._faces[self._scheme.opposite(self._find_face(color))]

    # ------------------------------------------------------------------
    # Color ↔ face reverse lookup
    # ------------------------------------------------------------------

    def _ensure_color_to_face(self) -> dict[Color, FaceName]:
        """Build reverse mapping on first use, then return cached dict."""
        if self._color_to_face is None:
            self._color_to_face = {c: f for f, c in self._faces.items()}
        return self._color_to_face

    def _is_face(self, color: Color) -> FaceName | None:
        """Face holding *color*, or ``None`` if absent."""
        return self._ensure_color_to_face().get(color)

    def _find_face(self, color: Color) -> FaceName:
        """Face holding *color*; raises if not found."""
        fn = self._is_face(color)
        if fn:
            return fn
        raise InternalSWError(f"No such color {color} in {self}")

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def same(self, other: CubeColorScheme) -> bool:
        """Check if two schemes are identical up to whole-cube rotation.

        No cloning, no mutation — pure comparison.

        Algorithm:

        1. Pick self's Front color as a reference.  Find which face holds
           that color in *other*.  If absent → different color sets → False.

        2. The opposite face must hold the same color in both schemes.
           This verifies the axis is consistent.

        3. The four CW-neighbor colors around the reference face must be
           a *cyclic rotation* of each other.  The only remaining degree
           of freedom (after fixing the axis) is rotation around it, which
           is exactly a cyclic shift of the neighbor ring.

        Example — BOY (self) vs the same cube viewed from the right::

            self (BOY):      F=Blue  B=Green  U=Yellow D=White  L=Orange R=Red
            other (rotated): F=Red   B=Orange U=Yellow D=White  L=Blue   R=Green

            Step 1: ref_color = Blue (self's Front)
                    other_face = L   (Blue is on Left in other)

            Step 2: self  opposite(F) = B → Green
                    other opposite(L) = R → Green  ✓  axis OK

            Step 3: CW neighbors of F = [U, R, D, L]
                    CW neighbors of L = [U, F, D, B]

                    self  neighbors(F) → [Yellow, Red,  White, Orange]
                    other neighbors(L) → [Yellow, Red,  White, Orange]
                                          identical (shift=0) → ✓ same!

        The neighbor cycle comparison catches both orientation and chirality
        (a mirror image would reverse the cycle, not shift it).

        Neighbor-color tuples are cached per face, so repeated calls are
        cheap after the first.
        """
        # 1. Pick self's Front color, find it in other
        ref_color: Color = self._faces[FaceName.F]
        other_face: FaceName | None = other._is_face(ref_color)
        if other_face is None:
            return False  # different color sets

        # 2. Opposite colors must match (same axis)
        self_opp: Color = self._faces[self._scheme.opposite(FaceName.F)]
        other_opp: Color = other._faces[self._scheme.opposite(other_face)]
        if self_opp != other_opp:
            return False

        # 3. CW neighbor colors must be a cyclic rotation
        self_cycle: tuple[Color, ...] = self._neighbor_colors(FaceName.F)
        other_cycle: tuple[Color, ...] = other._neighbor_colors(other_face)
        return _is_cyclic_rotation(self_cycle, other_cycle)

    def _neighbor_colors(self, face: FaceName) -> tuple[Color, ...]:
        """CW neighbor colors for *face* (cached)."""
        cached: tuple[Color, ...] | None = self._neighbor_colors_cache.get(face)
        if cached is not None:
            return cached
        result: tuple[Color, ...] = tuple(
            self._faces[f]
            for f in self._scheme.get_face_neighbors_cw_names(face)
        )
        self._neighbor_colors_cache[face] = result
        return result

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        faces = self._faces

        def _f(fn: FaceName) -> str:
            if fn in faces:
                return "[" + fn.value + ":" + str(faces[fn].value) + "]"
            return f"[{fn.value} ❌❌]"

        return (
            "-" + _f(FaceName.B) + "-\n"
            "-" + _f(FaceName.U) + "-\n"
            + _f(FaceName.L) + _f(FaceName.F) + _f(FaceName.R) + "\n"
            "-" + _f(FaceName.D) + "-\n"
        )

    def __repr__(self) -> str:
        return self.__str__()
