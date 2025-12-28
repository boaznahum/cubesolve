"""
Face2FaceTranslator - Central API for face-to-face coordinate translation.

Documentation: docs/face-coordinate-system/Face2FaceTranslator.md

Replaces scattered methods in Edge.py, Face.py, and Slice.py:
- Edge.get_slice_index_from_ltr_index()
- Edge.get_ltr_index_from_slice_index()
- Face.is_bottom_or_top() for axis detection
- Slice navigation logic

DEFINITION:
    translate(source_face, dest_face, coord) returns a FaceTranslationResult with:

    - dest_coord: The position on dest_face that corresponds to coord on source_face
    - whole_cube_alg: Algorithm (X/Y/Z) that brings dest_face to source_face's position
    - slice_algorithms: Algorithm(s) (M/E/S) that bring content from dest to source

    USAGE CONTRACT:
        1. Place a marker at dest_coord on dest_face
        2. Apply any of the returned algorithms (whole_cube_alg or slice_algorithms)
        3. The marker will appear at coord on source_face

    This is the SINGLE definition that all algorithms must satisfy.

VIEWER PERSPECTIVE:
    The transformation is derived from: "If I mark coord on source_face and apply
    the algorithm that brings source to dest's position, where does the marker end up?"

    dest_coord is the answer - it's where source content appears on dest after rotation.

IMPLEMENTATION:
    Uses empirically-derived transformation table based on whole-cube rotations.
    Each face pair has one of 4 transformation types:
    - IDENTITY: (r, c) -> (r, c)
    - ROT_90_CW: (r, c) -> (inv(c), r)
    - ROT_90_CCW: (r, c) -> (c, inv(r))
    - ROT_180: (r, c) -> (inv(r), inv(c))

    where inv(x) = n - 1 - x (for an n×n cube).

    See: docs/face-coordinate-system/images/right-top-left-coordinates.jpg
    for the face coordinate system diagram (R = column direction, T = row direction).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Tuple

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.algs import Algs, Alg, WholeCubeAlg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.model.CubeLayout import CubeLayout

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge

from cube.domain.model.FaceName import FaceName
from cube.domain.model.cube_slice import SliceName


class TransformType(Enum):
    """
    Coordinate transformation types between faces.

    For an n×n cube with inv(x) = n - 1 - x:
    - IDENTITY: (r, c) -> (r, c) - no change
    - ROT_90_CW: (r, c) -> (inv(c), r) - 90° clockwise
    - ROT_90_CCW: (r, c) -> (c, inv(r)) - 90° counter-clockwise
    - ROT_180: (r, c) -> (inv(r), inv(c)) - 180° rotation
    """
    IDENTITY = auto()
    ROT_90_CW = auto()
    ROT_90_CCW = auto()
    ROT_180 = auto()


# =============================================================================
# TRANSFORMATION TABLE - Empirically derived from whole-cube rotations
# =============================================================================
#
# For each (source, dest) pair, this table specifies how coordinates transform
# when a marker on source face moves to dest face via whole-cube rotation.
#
# Derived by: tests/model/test_empirical_transforms.py::test_derive_all_transformations
#
_TRANSFORMATION_TABLE: dict[tuple[FaceName, FaceName], TransformType] = {
    # B face transitions
    (FaceName.B, FaceName.D): TransformType.ROT_180,  # via X
    (FaceName.B, FaceName.F): TransformType.ROT_180,  # via X2
    (FaceName.B, FaceName.L): TransformType.IDENTITY,  # via Y'
    (FaceName.B, FaceName.R): TransformType.IDENTITY,  # via Y
    (FaceName.B, FaceName.U): TransformType.ROT_180,  # via X'

    # D face transitions
    (FaceName.D, FaceName.B): TransformType.ROT_180,  # via X'
    (FaceName.D, FaceName.F): TransformType.IDENTITY,  # via X
    (FaceName.D, FaceName.L): TransformType.ROT_90_CW,  # via Z
    (FaceName.D, FaceName.R): TransformType.ROT_90_CCW,  # via Z'
    (FaceName.D, FaceName.U): TransformType.IDENTITY,  # via X2

    # F face transitions
    (FaceName.F, FaceName.B): TransformType.ROT_180,  # via X2
    (FaceName.F, FaceName.D): TransformType.IDENTITY,  # via X'
    (FaceName.F, FaceName.L): TransformType.IDENTITY,  # via Y
    (FaceName.F, FaceName.R): TransformType.IDENTITY,  # via Y'
    (FaceName.F, FaceName.U): TransformType.IDENTITY,  # via X

    # L face transitions
    (FaceName.L, FaceName.B): TransformType.IDENTITY,  # via Y
    (FaceName.L, FaceName.D): TransformType.ROT_90_CCW,  # via Z'
    (FaceName.L, FaceName.F): TransformType.IDENTITY,  # via Y'
    (FaceName.L, FaceName.R): TransformType.IDENTITY,  # via Y2
    (FaceName.L, FaceName.U): TransformType.ROT_90_CW,  # via Z

    # R face transitions
    (FaceName.R, FaceName.B): TransformType.IDENTITY,  # via Y'
    (FaceName.R, FaceName.D): TransformType.ROT_90_CW,  # via Z
    (FaceName.R, FaceName.F): TransformType.IDENTITY,  # via Y
    (FaceName.R, FaceName.L): TransformType.IDENTITY,  # via Y2
    (FaceName.R, FaceName.U): TransformType.ROT_90_CCW,  # via Z'

    # U face transitions
    (FaceName.U, FaceName.B): TransformType.ROT_180,  # via X
    (FaceName.U, FaceName.D): TransformType.IDENTITY,  # via X2
    (FaceName.U, FaceName.F): TransformType.IDENTITY,  # via X'
    (FaceName.U, FaceName.L): TransformType.ROT_90_CCW,  # via Z'
    (FaceName.U, FaceName.R): TransformType.ROT_90_CW,  # via Z
}


@dataclass(frozen=True)
class FaceTranslationResult:
    """
    Result of translating a coordinate from one face to another.

    Attributes:
        dest_coord: (row, col) on dest_face where the translated position is.
                   After applying any algorithm, a marker at dest_coord will
                   appear at coord on source_face.

        whole_cube_alg: Algorithm (X/Y/Z moves) that brings dest_face to source_face's
                       screen position.

        slice_algorithms: Slice algorithms (M/E/S moves) that bring dest content to
                         source position at coord. Each uses the same dest_coord.
                         - Adjacent faces: exactly 1 algorithm
                         - Opposite faces: exactly 2 algorithms

        shared_edge: Edge connecting source and dest faces.
                    - Not None: faces are adjacent (share this edge)
                    - None: faces are opposite (F↔B, U↔D, L↔R)

    USAGE CONTRACT:
        1. Place marker at dest_coord on dest_face
        2. Apply any algorithm (whole_cube_alg or any slice_algorithm)
        3. Marker appears at coord on source_face

    Example::

        result = translator.translate(cube.front, cube.up, (1, 2))
        # result.dest_coord = (1, 2)
        # result.whole_cube_alg = X'
        # result.slice_algorithms = [M[3]]
    """

    dest_coord: tuple[int, int]
    whole_cube_alg: Alg
    slice_algorithms: list[SliceAlgorithmResult]
    shared_edge: Edge | None

    @property
    def is_adjacent(self) -> bool:
        """True if faces share an edge, False if opposite."""
        return self.shared_edge is not None


@dataclass(frozen=True)
class SliceAlgorithmResult:
    """
    Result of computing a slice algorithm for face-to-face translation.

    Attributes:
        whole_slice_alg: The base slice algorithm (M, E, or S) without indexing
        on_slice: 1-based slice index (see SliceAbleAlg for indexing convention)
        n: Number of rotations (positive = clockwise, negative = counter-clockwise)

    Note on slice indexing:
        Slice indices are 1-based in the public API: E[1], E[2], ..., E[n_slices]
        This matches the convention in SliceAbleAlg where slices are "[1, n]" space.
        See SliceAbleAlg.normalize_slice_index() which converts to 0-based internally.
    """
    whole_slice_alg: SliceAlg  # not sliced
    on_slice: int  # 1-based slice index
    n: int  # n rotations

    def get_alg(self) -> Alg:
        return self.whole_slice_alg[self.on_slice] * self.n

    def get_whole_slice_alg(self) -> Alg:
        return self.whole_slice_alg * self.n

    def get_slice_alg(self, slice_index) -> Alg:
        return self.whole_slice_alg[slice_index] * self.n



# =============================================================================
# SLICE INDEX LOOKUP TABLE - Empirically derived
# =============================================================================
#
# For each (slice_type, source_face), this table specifies how to compute
# the slice index from source coordinates (row, col).
#
# The formula is one of: row, col, inv(row), inv(col)
# where inv(x) = n_slices - 1 - x
#
# Derived by: tests/model/derive_slice_index_table.py
#

class _SliceIndexFormula:
    """
    Formula types for computing slice index from (row, col).

    Coordinates (row, col) are 0-based: 0 to n_slices-1
    Slice indices are 1-based: 1 to n_slices (see SliceAbleAlg)

    Direct formulas add +1 to convert from 0-based to 1-based:
        ROW: slice_index = row + 1
        COL: slice_index = col + 1

    Inverse formulas naturally produce 1-based results:
        INV_ROW: slice_index = n_slices - row  (maps 0 → n_slices, n_slices-1 → 1)
        INV_COL: slice_index = n_slices - col  (maps 0 → n_slices, n_slices-1 → 1)
    """
    ROW = "row"           # slice_index = row + 1
    COL = "col"           # slice_index = col + 1
    INV_ROW = "inv_row"   # slice_index = n_slices - row
    INV_COL = "inv_col"   # slice_index = n_slices - col


_SLICE_INDEX_TABLE: dict[tuple[SliceName, FaceName], str] = {
    # M slice (affects F, U, D, B)
    (SliceName.M, FaceName.F): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.U): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.D): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.B): _SliceIndexFormula.INV_COL,

    # E slice (affects F, L, R, B)
    (SliceName.E, FaceName.F): _SliceIndexFormula.ROW,
    (SliceName.E, FaceName.L): _SliceIndexFormula.ROW,
    (SliceName.E, FaceName.R): _SliceIndexFormula.ROW,
    (SliceName.E, FaceName.B): _SliceIndexFormula.ROW,

    # S slice (affects L, U, R, D)
    (SliceName.S, FaceName.L): _SliceIndexFormula.INV_COL,
    (SliceName.S, FaceName.U): _SliceIndexFormula.ROW,
    (SliceName.S, FaceName.R): _SliceIndexFormula.COL,
    (SliceName.S, FaceName.D): _SliceIndexFormula.INV_ROW,
}


def _compute_slice_index(
    source_face: FaceName,
    slice_name: SliceName,
    coord: tuple[int, int],
    n_slices: int
) -> int:
    """
    Compute the 1-based slice index for a given source face and coordinate.

    Uses the empirically-derived lookup table (_SLICE_INDEX_TABLE) to determine
    which formula maps (row, col) to the correct slice index.

    Args:
        source_face: The face where the coordinate originates
        slice_name: Which slice type (M, E, S)
        coord: 0-based (row, col) on the source face, range [0, n_slices-1]
        n_slices: Number of inner slices (cube.n_slices = cube.size - 2)

    Returns:
        1-based slice index in range [1, n_slices], suitable for SliceAlg[index]

    Example:
        For a 5×5 cube (n_slices=3), coord (1, 2) on face F with slice E:
        - Formula is ROW (from lookup table)
        - slice_index = row + 1 = 1 + 1 = 2
        - Result: E[2] operates on the correct slice

    See Also:
        - SliceAbleAlg: Documents the 1-based slice indexing convention
        - _SLICE_INDEX_TABLE: The empirically-derived lookup table
    """
    row, col = coord
    formula = _SLICE_INDEX_TABLE.get((slice_name, source_face))

    if formula is None:
        raise ValueError(f"No slice index formula for {slice_name} on {source_face}")

    match formula:
        case _SliceIndexFormula.ROW:
            return row + 1
        case _SliceIndexFormula.COL:
            return col + 1
        case _SliceIndexFormula.INV_ROW:
            return n_slices - row
        case _SliceIndexFormula.INV_COL:
            return n_slices - col
        case _:
            raise ValueError(f"Unknown formula: {formula}")


# =============================================================================
# ROTATION CYCLES - Empirically derived from whole-cube rotations
# =============================================================================
#
# Each cycle lists faces in the direction content MOVES when applying the base alg.
# After the rotation, content at cycle[i] appears at cycle[i+1].
#
# Empirical observations:
#   X: D→F→U→B→D (D's content moves to F, F's to U, etc.)
#   Y: R→F→L→B→R (R's content moves to F, F's to L, etc.) - NOTE: opposite direction!
#   Z: L→U→R→D→L (L's content moves to U, U's to R, etc.)
#
# Cycles are ordered so that applying the base alg moves content from index i to i+1.

_X_CYCLE: list[FaceName] = [FaceName.D, FaceName.F, FaceName.U, FaceName.B]  # X moves +1
_Y_CYCLE: list[FaceName] = [FaceName.R, FaceName.F, FaceName.L, FaceName.B]  # Y moves +1
_Z_CYCLE: list[FaceName] = [FaceName.L, FaceName.U, FaceName.R, FaceName.D]  # Z moves +1


def _apply_transform(
        coord: tuple[int, int],
        transform_type: TransformType,
        n: int
) -> tuple[int, int]:
    """
    Apply a coordinate transformation.

    Args:
        coord: (row, col) to transform
        transform_type: One of IDENTITY, ROT_90_CW, ROT_90_CCW, ROT_180
        n: Cube size (for computing inv(x) = n - 1 - x)

    Returns:
        Transformed (row, col)
    """
    row, col = coord

    def inv(x: int) -> int:
        return n - 1 - x

    match transform_type:
        case TransformType.IDENTITY:
            return row, col
        case TransformType.ROT_90_CW:
            return inv(col), row
        case TransformType.ROT_90_CCW:
            return col, inv(row)
        case TransformType.ROT_180:
            return inv(row), inv(col)


def _derive_whole_cube_alg(source: FaceName, dest: FaceName) -> Tuple[WholeCubeAlg, int, Alg]:
    """
    Derive the whole-cube algorithm that brings dest to source's screen position.

    Uses rotation cycles to compute the minimal algorithm dynamically.

    The cycles are ordered so each base_alg application moves content from
    cycle[i] to cycle[i+1]. To move dest to source's position:
    - We need (dest_idx + steps) % 4 == src_idx
    - Therefore: steps = (src_idx - dest_idx) % 4
    """
    whole_cube_alg: WholeCubeAlg
    for cycle, whole_cube_alg in [(_X_CYCLE, Algs.X), (_Y_CYCLE, Algs.Y), (_Z_CYCLE, Algs.Z)]:
        if source in cycle and dest in cycle:
            src_idx = cycle.index(source)
            dst_idx = cycle.index(dest)
            # Steps needed to move dest to source position
            steps = (src_idx - dst_idx) % 4
            if steps == 0:
                # source == dest (shouldn't happen, but handle gracefully)
                raise InternalSWError("dource == dest")
                return Algs.no_op()

            return whole_cube_alg, steps, whole_cube_alg * steps


    # Should never reach here for valid face pairs
    raise ValueError(f"No rotation cycle contains both {source} and {dest}")


class Face2FaceTranslator:
    """
    Utility class for translating coordinates between cube faces.

    This is the ONE place that handles all face-to-face coordinate operations,
    ensuring consistency with the viewer-perspective definition.

    DEFINITION:
        translate(F, R, (row, col)) → (row', col') means:
        If you mark (row, col) on F and (row', col') on R, then apply Y' (R→F),
        both markers appear at the same screen position.

    IMPLEMENTATION:
        Uses rotation cycle analysis to derive whole-cube algorithms dynamically.
    """

    @staticmethod
    def translate(
            source_face: Face,
            dest_face: Face,
            coord: tuple[int, int]
    ) -> FaceTranslationResult:
        """
        Translate a coordinate from source_face to dest_face.

        The transformation is based on where a marker at coord on source_face
        would appear on dest_face after a whole-cube rotation that brings
        source_face to dest_face's position.

        Args:
            source_face: The face where the coordinate is defined
            dest_face: The face we want the corresponding coordinate on
            coord: (row, col) position on source_face (0-indexed)

        Returns:
            FaceTranslationResult with the destination coordinate and metadata

        Raises:
            ValueError: If source_face == dest_face (no translation needed)
            ValueError: If coord is out of bounds for cube size

        Example::

            result = Face2FaceTranslator.translate(cube.front, cube.right, (1, 2))
            print(result.dest_coord)  # Position on R face after F->R translation
        """
        if source_face is dest_face:
            raise ValueError("Cannot translate from a face to itself")

        # Use center n_slices for coordinate bounds (not cube size)
        # For 3x3 cube, centers are 1x1 (n_slices=1)
        # For 5x5 cube, centers are 3x3 (n_slices=3)
        n_slices = source_face.center.n_slices
        row, col = coord
        if not (0 <= row < n_slices and 0 <= col < n_slices):
            raise ValueError(f"Coordinate {coord} out of bounds for center grid (n_slices={n_slices})")

        source_name = source_face.name
        dest_name = dest_face.name

        # Derive whole-cube algorithm dynamically from rotation cycles
        whole_cube_base_alg, whole_cube_base_n, whole_cube_alg = _derive_whole_cube_alg(source_name, dest_name)

        # Get the transformation type from the empirically-derived table
        transform_type = _TRANSFORMATION_TABLE[(source_name, dest_name)]

        # Apply the transformation using center grid size
        dest_coord = _apply_transform(coord, transform_type, n_slices)

        # Find shared edge (None if faces are opposite)
        shared_edge = Face2FaceTranslator._find_shared_edge(source_face, dest_face)

        # Compute slice algorithms
        slice_algorithms = Face2FaceTranslator._compute_slice_algorithms(
            source_name, dest_name, coord, n_slices, whole_cube_base_alg, whole_cube_base_n
        )

        return FaceTranslationResult(
            dest_coord=dest_coord,
            whole_cube_alg=whole_cube_alg,
            slice_algorithms=slice_algorithms,
            shared_edge=shared_edge,
        )

    @staticmethod
    def _find_shared_edge(face1: Face, face2: Face) -> Edge | None:
        """
        Find the edge shared by two faces, or None if they're opposite.

        Returns:
            The shared Edge if faces are adjacent, None if opposite
        """

        return face1.find_shared_edge(face2)

    @staticmethod
    def _compute_slice_algorithms(
            source_name: FaceName,
            dest_name: FaceName,
            coord: tuple[int, int],
            n_slices: int,
            whole_cube_base_alg: WholeCubeAlg,
            whole_cube_base_n: int
    ) -> list[SliceAlgorithmResult]:
        """
        Compute slice algorithm(s) that bring content from dest to source at coord.

        All slice algorithms use the SAME dest_coord as the whole-cube algorithm.
        The slice index is calculated using the empirically-derived lookup table.

        Returns:
            List of SliceAlgorithmResult (1 for adjacent faces, 2 for opposite faces)
        """
        whole_on_face: FaceName = whole_cube_base_alg.get_face_name()

        slice_alg: SliceAlg

        for slice_alg in [Algs.S, Algs.M, Algs.E]:
            slice_alg_face_name = slice_alg.get_face_name()
            slice_name = slice_alg.slice_name
            assert slice_name is not None

            if whole_on_face == slice_alg_face_name:
                # Same direction as whole-cube rotation
                slice_index = _compute_slice_index(source_name, slice_name, coord, n_slices)
                return [SliceAlgorithmResult(slice_alg, slice_index, whole_cube_base_n)]
            elif whole_on_face is CubeLayout.opposite(slice_alg_face_name):
                # Opposite direction - negate n
                slice_index = _compute_slice_index(source_name, slice_name, coord, n_slices)
                return [SliceAlgorithmResult(slice_alg, slice_index, -whole_cube_base_n)]

        raise InternalSWError(f"Didnt find SliceAlg for {whole_cube_base_alg}")
