"""CubeColorScheme — face-to-color mapping with rotation-aware comparison.

A color scheme assigns one of the six colors to each face of the cube.
The standard scheme is BOY (Blue-Orange-Yellow on the Front-Left-Up corner),
but a scrambled cube can yield any valid permutation.

NOT a singleton — unlike SchematicCube (fixed geometry), color schemes vary.

When are two schemes the same?
==============================

Two color schemes are considered *the same* if one can be rotated (whole-cube
rotation) to match the other.  The comparison (``same()``) checks:

1. **Color set** — both schemes must use the same 6 colors.
2. **Opposite-color pairs** — if Blue↔Green in one, then Blue↔Green in the other.
3. **Orientation** — after aligning Front and Up colors, the Left color must match.

This means the *physical arrangement* of stickers is identical; only the
observer's point of view differs.

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


class CubeColorScheme:
    """A face-to-color mapping for a Rubik's cube.

    Supports:
    - Face-to-color lookup (``scheme[FaceName.F]``)
    - Color-to-face reverse lookup
    - Edge color enumeration (all valid two-color pairs)
    - Scheme comparison accounting for whole-cube rotations
    - Cloning for in-place mutation
    """

    __slots__ = ("_faces", "_read_only", "_scheme", "_edge_colors")

    def __init__(self, faces: Mapping[FaceName, Color], *,
                 read_only: bool = False) -> None:
        self._faces: dict[FaceName, Color] = dict(faces)
        self._read_only = read_only
        self._scheme: SchematicCube = SchematicCube.inst()
        self._edge_colors: Collection[frozenset[Color]] | None = None

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

    def _is_face(self, color: Color) -> FaceName | None:
        """Face holding *color*, or ``None`` if absent."""
        for f, c in self._faces.items():
            if c == color:
                return f
        return None

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

        Algorithm:
        1. Verify all colors in *other* exist in *self*.
        2. Verify opposite-color pairs match.
        3. Rotate a clone of *self* so Front and Up match *other*.
        4. Check that Left also matches (fully determines orientation).
        """
        # All colors in other must exist in self
        for c in other.colors():
            if not self._is_face(c):
                return False

        this = self.clone()
        _scheme = self._scheme

        # Check opposite-color pairs
        for f1 in (FaceName.F, FaceName.U, FaceName.L):
            f2 = _scheme.opposite(f1)
            c1 = other[f1]
            c2 = other[f2]

            this_c1_face: FaceName = this._find_face(c1)
            this_c2_face = _scheme.opposite(this_c1_face)
            this_c2 = this._faces[this_c2_face]
            if c2 != this_c2:
                return False

        # Bring other's front color to front on clone
        other_f_color: Color = other[FaceName.F]
        this._bring_face_to_front(this._find_face(other_f_color))
        assert this._faces[FaceName.F] == other_f_color

        # Bring other's up color to up, preserving front
        other_u_color = other[FaceName.U]
        this_u_match = this._find_face(other_u_color)
        if this_u_match == FaceName.B:
            return False  # on this it is on Back, can't match
        this._bring_face_up_preserve_front(this_u_match)
        assert this._faces[FaceName.U] == other_u_color

        return this._faces[FaceName.L] == other[FaceName.L]

    # ------------------------------------------------------------------
    # Clone
    # ------------------------------------------------------------------

    def clone(self) -> CubeColorScheme:
        """Mutable copy of this scheme (always read_only=False)."""
        return CubeColorScheme(self._faces, read_only=False)

    # ------------------------------------------------------------------
    # Rotation helpers — derived from SchematicCube
    # ------------------------------------------------------------------
    #
    # Each whole-cube rotation permutes the four faces around an axis.
    # The permutation cycle is the *reversed* CW-neighbor list of the
    # axis face (from SchematicCube.get_face_neighbors_cw_names).
    #
    # A single ``_rotate(axis_face, n)`` replaces the old
    # ``_rotate_x / _rotate_y / _rotate_z`` triple.

    def _rotate(self, axis_face: FaceName, n: int) -> None:
        """Apply *n* quarter-turns around *axis_face*.

        Positive *n* = clockwise when viewed from *axis_face*.
        """
        assert not self._read_only
        cycle = list(reversed(
            self._scheme.get_face_neighbors_cw_names(axis_face)
        ))
        faces = self._faces
        for _ in range(n % 4):
            saved = faces[cycle[0]]
            for i in range(len(cycle) - 1):
                faces[cycle[i]] = faces[cycle[i + 1]]
            faces[cycle[-1]] = saved

    def _cycle_distance(
        self, axis_face: FaceName, source: FaceName, target: FaceName,
    ) -> int:
        """Quarter-turns around *axis_face* to move *source* to *target*."""
        cycle = list(reversed(
            self._scheme.get_face_neighbors_cw_names(axis_face)
        ))
        return (cycle.index(source) - cycle.index(target)) % 4

    def _bring_face_to_front(self, f: FaceName) -> None:
        """Rotate so that face *f* becomes Front.

        Tries X-axis (R) first, then Y-axis (U).
        """
        if f == FaceName.F:
            return

        for axis_face in (FaceName.R, FaceName.U):
            cycle = list(reversed(
                self._scheme.get_face_neighbors_cw_names(axis_face)
            ))
            if f in cycle:
                n = self._cycle_distance(axis_face, f, FaceName.F)
                self._rotate(axis_face, n)
                return

        raise InternalSWError(f"Cannot bring {f} to front")

    def _bring_face_up_preserve_front(self, face: FaceName) -> None:
        """Rotate so *face* becomes Up while keeping Front fixed.

        Uses Z-axis (rotation around F) so Front is unaffected.
        Only works for faces adjacent to Front (not Back).
        """
        if face == FaceName.U:
            return

        if face == FaceName.B:
            raise InternalSWError(f"{face} is not supported")

        n = self._cycle_distance(FaceName.F, face, FaceName.U)
        self._rotate(FaceName.F, n)

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
