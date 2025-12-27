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
    1. Place a marker at (row, col) on Face A - note where it appears on screen
    2. Place a marker at (row', col') on Face B
    3. Perform whole cube rotation to bring Face B to Face A's position
    4. The marker at (row', col') now appears at the EXACT SAME screen position
       as (row, col) was originally

    The translated coordinate preserves VISUAL POSITION from the viewer's perspective.

IMPLEMENTATION:
    Uses rotation cycle analysis to derive whole-cube algorithms dynamically.
    Coordinates are identity-transformed (viewer-perspective consistency).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.domain.algs import Algs
from cube.domain.algs.Alg import Alg

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Cube import Cube

from cube.domain.model.FaceName import FaceName


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
# ROTATION CYCLES - Derived from cube geometry
# =============================================================================
#
# Whole cube rotations move faces along these cycles:
#   X: F→U→B→D→F (rotate around R-L axis)
#   Y: F→R→B→L→F (rotate around U-D axis)
#   Z: U→R→D→L→U (rotate around F-B axis)
#
# To bring dest face to source face's position, find which cycle contains
# both faces and count steps from dest to source.

_X_CYCLE: list[FaceName] = [FaceName.F, FaceName.U, FaceName.B, FaceName.D]
_Y_CYCLE: list[FaceName] = [FaceName.F, FaceName.R, FaceName.B, FaceName.L]
_Z_CYCLE: list[FaceName] = [FaceName.U, FaceName.R, FaceName.D, FaceName.L]


def _derive_whole_cube_alg(source: FaceName, dest: FaceName) -> Alg:
    """
    Derive the whole-cube algorithm that brings dest to source's screen position.

    Uses rotation cycles to compute the minimal algorithm dynamically.
    """
    whole_cube_alg:Alg
    for cycle, whole_cube_alg in [(_X_CYCLE, Algs.X), (_Y_CYCLE, Algs.Y), (_Z_CYCLE, Algs.Z)]:
        if source in cycle and dest in cycle:
            src_idx = cycle.index(source)
            dst_idx = cycle.index(dest)
            # Steps from dest to source in positive direction
            steps = (src_idx - dst_idx) % 4
            if steps == 1:
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
            >>> print(result.dest_coord)  # Position on R face
            >>> # Verify: mark both positions, apply Y', both markers align
        """
        if source_face is dest_face:
            raise ValueError("Cannot translate from a face to itself")

        n = source_face.cube.size
        row, col = coord
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError(f"Coordinate {coord} out of bounds for {n}x{n} cube")

        source_name = source_face.name
        dest_name = dest_face.name

        # Derive whole-cube algorithm dynamically from rotation cycles
        whole_cube_alg = _derive_whole_cube_alg(source_name, dest_name)

        # For viewer-perspective definition, coordinates are identical on all faces
        # (the cube's coordinate system is designed this way)
        dest_coord = (row, col)

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

