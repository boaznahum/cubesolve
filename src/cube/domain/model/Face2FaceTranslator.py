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
from typing import TYPE_CHECKING

from cube.domain.algs import Algs
from cube.domain.algs.Alg import Alg
from cube.domain.algs.SliceAlg import SliceAlg

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
    (FaceName.B, FaceName.D): TransformType.ROT_180,    # via X
    (FaceName.B, FaceName.F): TransformType.ROT_180,    # via X2
    (FaceName.B, FaceName.L): TransformType.IDENTITY,   # via Y'
    (FaceName.B, FaceName.R): TransformType.IDENTITY,   # via Y
    (FaceName.B, FaceName.U): TransformType.ROT_180,    # via X'

    # D face transitions
    (FaceName.D, FaceName.B): TransformType.ROT_180,    # via X'
    (FaceName.D, FaceName.F): TransformType.IDENTITY,   # via X
    (FaceName.D, FaceName.L): TransformType.ROT_90_CW,  # via Z
    (FaceName.D, FaceName.R): TransformType.ROT_90_CCW, # via Z'
    (FaceName.D, FaceName.U): TransformType.IDENTITY,   # via X2

    # F face transitions
    (FaceName.F, FaceName.B): TransformType.ROT_180,    # via X2
    (FaceName.F, FaceName.D): TransformType.IDENTITY,   # via X'
    (FaceName.F, FaceName.L): TransformType.IDENTITY,   # via Y
    (FaceName.F, FaceName.R): TransformType.IDENTITY,   # via Y'
    (FaceName.F, FaceName.U): TransformType.IDENTITY,   # via X

    # L face transitions
    (FaceName.L, FaceName.B): TransformType.IDENTITY,   # via Y
    (FaceName.L, FaceName.D): TransformType.ROT_90_CCW, # via Z'
    (FaceName.L, FaceName.F): TransformType.IDENTITY,   # via Y'
    (FaceName.L, FaceName.R): TransformType.IDENTITY,   # via Y2
    (FaceName.L, FaceName.U): TransformType.ROT_90_CW,  # via Z

    # R face transitions
    (FaceName.R, FaceName.B): TransformType.IDENTITY,   # via Y'
    (FaceName.R, FaceName.D): TransformType.ROT_90_CW,  # via Z
    (FaceName.R, FaceName.F): TransformType.IDENTITY,   # via Y
    (FaceName.R, FaceName.L): TransformType.IDENTITY,   # via Y2
    (FaceName.R, FaceName.U): TransformType.ROT_90_CCW, # via Z'

    # U face transitions
    (FaceName.U, FaceName.B): TransformType.ROT_180,    # via X
    (FaceName.U, FaceName.D): TransformType.IDENTITY,   # via X2
    (FaceName.U, FaceName.F): TransformType.IDENTITY,   # via X'
    (FaceName.U, FaceName.L): TransformType.ROT_90_CCW, # via Z'
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
    slice_algorithms: list[Alg]
    shared_edge: Edge | None

    @property
    def is_adjacent(self) -> bool:
        """True if faces share an edge, False if opposite."""
        return self.shared_edge is not None


@dataclass(frozen=True)
class SliceAlgorithmResult:
    """
    Result of finding slice algorithm(s) to bring destination face content to source position.

    A slice algorithm (M, E, or S with specific index) rotates an inner layer that,
    when applied, brings content from dest_face to cover the position at coord on source_face.

    Attributes:
        algorithms: List of Alg objects. Each algorithm brings dest content to source.
                   - Adjacent faces: exactly 1 algorithm (single path)
                   - Opposite faces: exactly 2 algorithms (two possible paths)

        source_face_name: The face where we want the content to arrive.
        dest_face_name: The face where the content originates.
        coord: The (row, col) position on source_face.

    Example::

        result = Face2FaceTranslator.get_slice_algorithm(cube.front, cube.up, (1, 1))
        # result.algorithms[0] = M[2]  # M slice at column 2 brings U content to F
        len(result.algorithms) == 1  # Adjacent faces have 1 solution

        result = Face2FaceTranslator.get_slice_algorithm(cube.front, cube.back, (1, 1))
        len(result.algorithms) == 2  # Opposite faces have 2 solutions (M or E)
    """
    algorithms: list[Alg]
    source_face_name: FaceName
    dest_face_name: FaceName
    coord: tuple[int, int]


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
            return (row, col)
        case TransformType.ROT_90_CW:
            return (inv(col), row)
        case TransformType.ROT_90_CCW:
            return (col, inv(row))
        case TransformType.ROT_180:
            return (inv(row), inv(col))


def _derive_whole_cube_alg(source: FaceName, dest: FaceName) -> Alg:
    """
    Derive the whole-cube algorithm that brings dest to source's screen position.

    Uses rotation cycles to compute the minimal algorithm dynamically.

    The cycles are ordered so each base_alg application moves content from
    cycle[i] to cycle[i+1]. To move dest to source's position:
    - We need (dest_idx + steps) % 4 == src_idx
    - Therefore: steps = (src_idx - dest_idx) % 4
    """
    whole_cube_alg: Alg
    for cycle, whole_cube_alg in [(_X_CYCLE, Algs.X), (_Y_CYCLE, Algs.Y), (_Z_CYCLE, Algs.Z)]:
        if source in cycle and dest in cycle:
            src_idx = cycle.index(source)
            dst_idx = cycle.index(dest)
            # Steps needed to move dest to source position
            steps = (src_idx - dst_idx) % 4
            if steps == 0:
                # source == dest (shouldn't happen, but handle gracefully)
                return Algs.no_op()
            elif steps == 1:
                return whole_cube_alg
            elif steps == 2:
                return whole_cube_alg * 2
            elif steps == 3:
                return whole_cube_alg.prime

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
        whole_cube_alg = _derive_whole_cube_alg(source_name, dest_name)

        # Get the transformation type from the empirically-derived table
        transform_type = _TRANSFORMATION_TABLE[(source_name, dest_name)]

        # Apply the transformation using center grid size
        dest_coord = _apply_transform(coord, transform_type, n_slices)

        # Find shared edge (None if faces are opposite)
        shared_edge = Face2FaceTranslator._find_shared_edge(source_face, dest_face)

        # Compute slice algorithms
        slice_algorithms = Face2FaceTranslator._compute_slice_algorithms(
            source_name, dest_name, coord, n_slices
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
    def get_slice_algorithm(
        source_face: Face,
        dest_face: Face,
        coord: tuple[int, int]
    ) -> SliceAlgorithmResult:
        """
        Get slice algorithm(s) that bring content from dest_face to source_face at coord.

        This is a convenience wrapper around translate() that returns just the slice info.

        Args:
            source_face: The face where we want the content to arrive
            dest_face: The face where the content currently is
            coord: (row, col) position on source_face (0-indexed)

        Returns:
            SliceAlgorithmResult with:
            - 1 algorithm for adjacent faces (single path)
            - 2 algorithms for opposite faces (two possible paths)

        Raises:
            ValueError: If source_face == dest_face
            ValueError: If coord is out of bounds

        Example::

            result = Face2FaceTranslator.get_slice_algorithm(cube.front, cube.up, (1, 1))
            result.algorithms[0].algorithm.play(cube)  # Brings U content to F at (1,1)
        """
        if source_face is dest_face:
            raise ValueError("Cannot get slice algorithm from a face to itself")

        # Delegate to translate() and extract slice algorithms
        result = Face2FaceTranslator.translate(source_face, dest_face, coord)

        return SliceAlgorithmResult(
            algorithms=result.slice_algorithms,
            source_face_name=source_face.name,
            dest_face_name=dest_face.name,
            coord=coord,
        )

    @staticmethod
    def _compute_slice_algorithms(
        source_name: FaceName,
        dest_name: FaceName,
        coord: tuple[int, int],
        n_slices: int
    ) -> list[Alg]:
        """
        Compute slice algorithm(s) that bring content from dest to source at coord.

        All slice algorithms use the SAME dest_coord as the whole-cube algorithm.
        The slice index is calculated based on which slice passes through the
        source coordinate position.

        GEOMETRIC CONSTRAINTS:
        - E slice preserves rows: E can only work if source row == dest row
        - M slice preserves columns: M can only work if source col == dest col (for faces in cycle)
        - For opposite faces with ROT_180: only M works when row changes, only E works when col changes
        - For odd n_slices at center: both row and col are preserved, so both M and E work

        Returns:
            List of Alg objects (M, E, or S slice algorithms)
        """
        row, col = coord
        algorithms: list[Alg] = []

        # Compute dest_coord to check geometric constraints
        transform_type = _TRANSFORMATION_TABLE[(source_name, dest_name)]
        dest_coord = _apply_transform(coord, transform_type, n_slices)
        dest_row, dest_col = dest_coord

        # Each tuple: (cycle, slice_name, base_alg, opposite_direction)
        all_cycles: list[tuple[list[FaceName], SliceName, SliceAlg, bool]] = [
            (_X_CYCLE, SliceName.M, Algs.M, True),   # M opposite to X
            (_Y_CYCLE, SliceName.E, Algs.E, True),   # E opposite to Y
            (_Z_CYCLE, SliceName.S, Algs.S, False),  # S same as Z
        ]

        for cycle, slice_name, base_slice_alg, opposite_direction in all_cycles:
            if source_name in cycle and dest_name in cycle:
                # GEOMETRIC CONSTRAINT CHECKS:
                #
                # E slice preserves rows - can only work if source row == dest row
                # This is critical for opposite faces (F↔B, L↔R) with even n_slices
                if slice_name == SliceName.E and row != dest_row:
                    continue  # E cannot bring dest content to different row

                # S slice has column inversion between L and R
                # S[i] affects: L col = n_slices - i, R col = i - 1
                # These match only when i = (n_slices + 1) / 2, which requires odd n_slices
                # For even n_slices at non-symmetric positions, S cannot work
                if slice_name == SliceName.S:
                    source_slice_idx = Face2FaceTranslator._get_slice_index(
                        source_name, slice_name, coord, n_slices
                    )
                    dest_slice_idx = Face2FaceTranslator._get_slice_index(
                        dest_name, slice_name, dest_coord, n_slices
                    )
                    if source_slice_idx != dest_slice_idx:
                        continue  # S cannot align source and dest at different slice indices

                # Get slice index from source coord
                source_slice_index = Face2FaceTranslator._get_slice_index(
                    source_name, slice_name, coord, n_slices
                )

                # This cycle connects source and dest
                src_idx = cycle.index(source_name)
                dst_idx = cycle.index(dest_name)

                # Steps needed to move dest content to source position
                if opposite_direction:
                    steps = (dst_idx - src_idx) % 4
                else:
                    steps = (src_idx - dst_idx) % 4

                if steps == 0:
                    continue

                # Create the slice algorithm with proper direction
                slice_alg = base_slice_alg[source_slice_index]
                final_alg: Alg
                if steps == 1:
                    final_alg = slice_alg
                elif steps == 2:
                    final_alg = slice_alg * 2
                else:  # steps == 3
                    final_alg = slice_alg.prime

                algorithms.append(final_alg)

        return algorithms

    @staticmethod
    def _get_slice_index(
        face_name: FaceName,
        slice_name: SliceName,
        coord: tuple[int, int],
        n_slices: int
    ) -> int:
        """
        Determine which slice index corresponds to the coordinate on the given face.

        The slice index depends on:
        - Which slice type (M, E, S) - each rotates around a different axis
        - Which face - determines how the coordinate maps to the slice axis
        - The coordinate (row, col)

        Args:
            face_name: The face where the coordinate is defined
            slice_name: Which slice type (M, E, S)
            coord: (row, col) on the face
            n_slices: Number of slices (center grid size)

        Returns:
            1-based slice index
        """
        row, col = coord

        # M slice: rotates around L-R axis (affects columns on F, U, D, B faces)
        # E slice: rotates around U-D axis (affects rows on F, L, R, B faces)
        # S slice: rotates around F-B axis (affects L, U, R, D faces)

        match slice_name:
            case SliceName.M:
                # M affects D, F, U, B
                # M[1] is the layer closest to L, M[n_slices] is closest to R
                # Must account for how each face's column direction aligns with L-R axis
                if face_name == FaceName.B:
                    # B's R points toward L: col=0 is closest to R
                    return n_slices - col
                else:  # D, F, U
                    # These faces have col=0 closest to L
                    return col + 1

            case SliceName.E:
                # E affects R, F, L, B
                # E[1] is the layer closest to D, E[n_slices] is closest to U
                # Unlike M, E does NOT invert on B (row stays consistent across all faces)
                return row + 1

            case SliceName.S:
                # S affects L, U, R, D
                # S[1] is the layer closest to F, S[n_slices] is closest to B
                # Must account for how each face's coordinate system aligns with F-B axis
                if face_name == FaceName.U:
                    # U's T points toward B: row=0 is closest to F
                    return row + 1
                elif face_name == FaceName.D:
                    # D's T points toward F: row=0 is closest to B
                    return n_slices - row
                elif face_name == FaceName.L:
                    # L's R points toward F: col=n_slices-1 is closest to F
                    return n_slices - col
                else:  # R
                    # R's R points toward B: col=0 is closest to F
                    return col + 1

            case _:
                raise ValueError(f"Unknown slice name: {slice_name}")

