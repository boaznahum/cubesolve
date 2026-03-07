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
from cube.domain.geometric.cube_face_colors import CubeFaceColors
from cube.domain.geometric.schematic_cube import SchematicCube
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName

# ---------------------------------------------------------------------------
# Whole-cube rotation permutations (forward: old_face → new_face)
# ---------------------------------------------------------------------------
# For each source face, the permutation that brings it to UP.
# These are the 6 single/double rotations around X/Y/Z axes.
#
#   From U: identity
#   From D: X2  (U↔D, F↔B)
#   From F: X'  (F→U, U→B, B→D, D→F)
#   From B: X   (B→U, U→F, F→D, D→B)
#   From L: Z   (L→U, U→R, R→D, D→L)
#   From R: Z'  (R→U, U→L, L→D, D→R)

_U, _D, _F, _B, _L, _R = (
    FaceName.U, FaceName.D, FaceName.F, FaceName.B, FaceName.L, FaceName.R,
)

_BRING_TO_UP: dict[FaceName, dict[FaceName, FaceName]] = {
    _U: {_U: _U, _D: _D, _F: _F, _B: _B, _L: _L, _R: _R},
    _D: {_U: _D, _D: _U, _F: _B, _B: _F, _L: _L, _R: _R},
    _F: {_F: _U, _U: _B, _B: _D, _D: _F, _L: _L, _R: _R},
    _B: {_B: _U, _U: _F, _F: _D, _D: _B, _L: _L, _R: _R},
    _L: {_L: _U, _U: _R, _R: _D, _D: _L, _F: _F, _B: _B},
    _R: {_R: _U, _U: _L, _L: _D, _D: _R, _F: _F, _B: _B},
}

# Inverse permutations: bring UP to target face.
_BRING_FROM_UP: dict[FaceName, dict[FaceName, FaceName]] = {
    target: {new: old for old, new in perm.items()}
    for target, perm in _BRING_TO_UP.items()
}


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
    # Cycle checks (cheap — no cube rotation)
    # ------------------------------------------------------------------

    def find_face_by_color(self, color: Color) -> FaceName:
        """Find which face in this scheme holds the given color.

        Args:
            color: The color to look up.

        Returns:
            The face name holding that color in this scheme.

        Raises:
            InternalSWError: If color is not in this scheme.
        """
        return self._find_face(color)

    def is_valid_neighbor_cycle(
        self, face: FaceName, actual_cw_colors: tuple[Color, ...],
    ) -> bool:
        """Check if actual CW neighbor colors are a valid rotation of the scheme.

        Given a face name and the actual colors on the adjacent edges (in CW
        order: top, right, bottom, left), returns True if those colors are a
        cyclic rotation of the expected neighbor colors from the color scheme.

        This is a *cheap* alternative to ``rotate_face_and_check`` — no cube
        mutation, just tuple comparison.

        Note: After whole-cube rotations, use ``find_face_by_color(face.color)``
        to get the correct scheme face name, not ``face.name``.

        Args:
            face: The scheme face whose neighbors to check.
            actual_cw_colors: The 4 actual edge colors on adjacent faces,
                              in CW order (top, right, bottom, left).

        Returns:
            True if actual colors are a cyclic rotation of expected colors.
        """
        expected: tuple[Color, ...] = self._neighbor_colors(face)
        return _is_cyclic_rotation(expected, actual_cw_colors)

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def bring_color_to_face(
        self, colors: CubeFaceColors, color: Color, target: FaceName,
    ) -> CubeFaceColors:
        """Return a new CubeFaceColors with *color* on *target* face.

        Simulates the whole-cube rotation that moves the face currently
        holding *color* to *target*, preserving all face relationships
        (opposites stay opposite, neighbors stay neighbors).

        The *colors* mapping must represent the same color scheme as
        ``self`` (verified via ``same()``).

        Args:
            colors: The current face-color assignment (must match self).
            color:  The color to move.
            target: The face where *color* should end up.

        Returns:
            A new CubeFaceColors reflecting the rotation.
        """
        assert self.same(CubeColorScheme(colors.mapping)), (
            f"colors {colors} is not the same scheme as {self}"
        )

        source: FaceName = colors.find_face(color)
        if source == target:
            return colors

        # Compose: bring source→UP, then UP→target.
        perm1: dict[FaceName, FaceName] = _BRING_TO_UP[source]
        perm2: dict[FaceName, FaceName] = _BRING_FROM_UP[target]
        # Forward composition: composed[old] = perm2[perm1[old]]
        new_mapping: dict[FaceName, Color] = {
            perm2[perm1[f]]: colors[f] for f in FaceName
        }
        return CubeFaceColors(new_mapping)

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
