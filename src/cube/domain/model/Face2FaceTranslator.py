"""
Face2FaceTranslator - Central API for face-to-face coordinate translation.

Documentation: docs/face-coordinate-system/Face2FaceTranslator.md

Replaces scattered methods in Edge.py, Face.py, and Slice.py:
- Edge.get_slice_index_from_ltr_index()
- Edge.get_ltr_index_from_slice_index()
- Face.is_bottom_or_top() for axis detection
- Slice navigation logic

DEFINITION (Viewer Perspective):
    A coordinate (row, col) on Face A translates to (row', col') on Face B if:
    1. Mark (row, col) on Face A
    2. Apply whole-cube rotation that brings A to B's position
    3. The marker now appears at (row', col') on the face that is now at B's position

    The transformation accounts for how face coordinate systems align after rotation.

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

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge

from cube.domain.model.FaceName import FaceName


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
                   After applying whole_cube_alg, a marker at dest_coord will
                   appear at the original coord's screen position.

        whole_cube_alg: Algorithm (X/Y/Z moves) that brings dest_face to source_face's
                       screen position. Execute this to verify the translation visually.

        shared_edge: Edge connecting source and dest faces.
                    - Not None: faces are adjacent (share this edge)
                    - None: faces are opposite (F↔B, U↔D, L↔R)

    Example:
        >>> result = translator.translate(cube.front, cube.up, (1, 2))
        >>> # result.dest_coord = (1, 2)  # same for viewer-perspective definition
        >>> # result.whole_cube_alg = "X'"  # brings U to F's position
        >>> # result.shared_edge is not None  # F and U are adjacent
    """

    dest_coord: tuple[int, int]
    whole_cube_alg: Alg
    shared_edge: Edge | None

    @property
    def is_adjacent(self) -> bool:
        """True if faces share an edge, False if opposite."""
        return self.shared_edge is not None


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

        Example:
            >>> result = Face2FaceTranslator.translate(cube.front, cube.right, (1, 2))
            >>> print(result.dest_coord)  # Position on R face after F->R translation
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

        return FaceTranslationResult(
            dest_coord=dest_coord,
            whole_cube_alg=whole_cube_alg,
            shared_edge=shared_edge,
        )

    @staticmethod
    def _find_shared_edge(face1: Face, face2: Face) -> Edge | None:
        """
        Find the edge shared by two faces, or None if they're opposite.

        Returns:
            The shared Edge if faces are adjacent, None if opposite
        """
        for edge in [face1.edge_top, face1.edge_bottom, face1.edge_left, face1.edge_right]:
            other_face = edge.get_other_face(face1)
            if other_face is face2:
                return edge
        return None

