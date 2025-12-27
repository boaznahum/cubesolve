"""
Face2FaceTranslator - Central API for face-to-face coordinate translation.

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
    Phase 1: All 30 face pairs hardcoded (verification rotations + coordinate transforms)
    Phase 2: Derive mathematical formulas
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Cube import Cube

from cube.domain.model.FaceName import FaceName


class Axis(Enum):
    """Axis on a face - ROW (horizontal) or COLUMN (vertical)."""
    ROW = auto()
    COLUMN = auto()


class EdgePosition(Enum):
    """Position of an edge relative to a face."""
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class FaceTranslationResult:
    """
    Result of translating a coordinate from one face to another.

    All information needed to:
    - Know the destination coordinate
    - Understand the translation path
    - Verify correctness via whole-cube rotation test
    """

    # The destination coordinate (row, col) on dest_face
    dest_coord: tuple[int, int]

    # Navigation information
    shared_edge: Edge | None  # None if opposite faces (no shared edge)
    is_adjacent: bool         # True if faces share an edge

    # For verification: which whole-cube rotation brings dest to source position
    # e.g., if source=F, dest=R, then verification_rotation="Y'" brings R to F's position
    verification_rotation: str

    # Axis information (for debugging/understanding)
    source_axis: Axis         # ROW or COLUMN on source face
    dest_axis: Axis           # ROW or COLUMN on destination face
    axis_exchanged: bool      # True if ROW↔COLUMN swap occurred


# =============================================================================
# HARDCODED LOOKUP TABLES
# =============================================================================

# Verification rotations: (source, dest) -> whole-cube algorithm
# The rotation brings dest_face to source_face's position
#
# Whole cube rotations:
#   Y:  F→R, R→B, B→L, L→F  (rotate around U axis, looking from top: CCW)
#   Y': F→L, L→B, B→R, R→F  (rotate around U axis, looking from top: CW)
#   X:  F→U, U→B, B→D, D→F  (rotate around R axis, looking from right: forward)
#   X': F→D, D→B, B→U, U→F  (rotate around R axis, looking from right: backward)
#   Z:  U→R, R→D, D→L, L→U  (rotate around F axis, looking at front: CW)
#   Z': U→L, L→D, D→R, R→U  (rotate around F axis, looking at front: CCW)

_VERIFICATION_ROTATIONS: dict[tuple[FaceName, FaceName], str] = {
    # Source = F (Front)
    (FaceName.F, FaceName.U): "X'",   # U→F after X'
    (FaceName.F, FaceName.R): "Y'",   # R→F after Y'
    (FaceName.F, FaceName.D): "X",    # D→F after X
    (FaceName.F, FaceName.L): "Y",    # L→F after Y
    (FaceName.F, FaceName.B): "Y2",   # B→F after Y2

    # Source = U (Up)
    (FaceName.U, FaceName.F): "X",    # F→U after X
    (FaceName.U, FaceName.R): "Z'",   # R→U after Z'
    (FaceName.U, FaceName.B): "X'",   # B→U after X'
    (FaceName.U, FaceName.L): "Z",    # L→U after Z
    (FaceName.U, FaceName.D): "X2",   # D→U after X2

    # Source = R (Right)
    (FaceName.R, FaceName.F): "Y",    # F→R after Y
    (FaceName.R, FaceName.U): "Z",    # U→R after Z
    (FaceName.R, FaceName.B): "Y'",   # B→R after Y'
    (FaceName.R, FaceName.D): "Z'",   # D→R after Z'
    (FaceName.R, FaceName.L): "Y2",   # L→R after Y2

    # Source = B (Back)
    (FaceName.B, FaceName.U): "X",    # U→B after X
    (FaceName.B, FaceName.R): "Y",    # R→B after Y
    (FaceName.B, FaceName.D): "X'",   # D→B after X'
    (FaceName.B, FaceName.L): "Y'",   # L→B after Y'
    (FaceName.B, FaceName.F): "Y2",   # F→B after Y2

    # Source = D (Down)
    (FaceName.D, FaceName.F): "X'",   # F→D after X'
    (FaceName.D, FaceName.R): "Z",    # R→D after Z
    (FaceName.D, FaceName.B): "X",    # B→D after X
    (FaceName.D, FaceName.L): "Z'",   # L→D after Z'
    (FaceName.D, FaceName.U): "X2",   # U→D after X2

    # Source = L (Left)
    (FaceName.L, FaceName.F): "Y'",   # F→L after Y'
    (FaceName.L, FaceName.U): "Z'",   # U→L after Z'
    (FaceName.L, FaceName.B): "Y",    # B→L after Y
    (FaceName.L, FaceName.D): "Z",    # D→L after Z
    (FaceName.L, FaceName.R): "Y2",   # R→L after Y2
}

# Coordinate transformation functions: (source, dest) -> function(row, col, n) -> (row', col')
# These transform coordinates so that after verification rotation, marker appears at same position
#
# CoordTransform = Callable[[int, int, int], tuple[int, int]]
# Parameters: (row, col, n) where n = cube size
# Returns: (dest_row, dest_col)

def _identity(row: int, col: int, n: int) -> tuple[int, int]:
    """No change - same coordinates."""
    return (row, col)

def _rotate_cw(row: int, col: int, n: int) -> tuple[int, int]:
    """Rotate 90° clockwise: (row, col) → (col, n-1-row)"""
    return (col, n - 1 - row)

def _rotate_ccw(row: int, col: int, n: int) -> tuple[int, int]:
    """Rotate 90° counter-clockwise: (row, col) → (n-1-col, row)"""
    return (n - 1 - col, row)

def _rotate_180(row: int, col: int, n: int) -> tuple[int, int]:
    """Rotate 180°: (row, col) → (n-1-row, n-1-col)"""
    return (n - 1 - row, n - 1 - col)

def _flip_horizontal(row: int, col: int, n: int) -> tuple[int, int]:
    """Flip horizontally: (row, col) → (row, n-1-col)"""
    return (row, n - 1 - col)

def _flip_vertical(row: int, col: int, n: int) -> tuple[int, int]:
    """Flip vertically: (row, col) → (n-1-row, col)"""
    return (n - 1 - row, col)

def _transpose(row: int, col: int, n: int) -> tuple[int, int]:
    """Transpose: (row, col) → (col, row)"""
    return (col, row)

def _anti_transpose(row: int, col: int, n: int) -> tuple[int, int]:
    """Anti-transpose (flip along anti-diagonal): (row, col) → (n-1-col, n-1-row)"""
    return (n - 1 - col, n - 1 - row)


# Coordinate transformations for all 30 face pairs
# TODO: These are placeholders - need to determine correct transformations through testing
_COORD_TRANSFORMS: dict[tuple[FaceName, FaceName], Callable[[int, int, int], tuple[int, int]]] = {
    # Source = F (Front)
    # After X', U comes to F. How do U's coords map to F's view?
    (FaceName.F, FaceName.U): _identity,           # TODO: verify
    (FaceName.F, FaceName.R): _identity,           # TODO: verify
    (FaceName.F, FaceName.D): _identity,           # TODO: verify
    (FaceName.F, FaceName.L): _identity,           # TODO: verify
    (FaceName.F, FaceName.B): _identity,           # TODO: verify

    # Source = U (Up)
    (FaceName.U, FaceName.F): _identity,           # TODO: verify
    (FaceName.U, FaceName.R): _identity,           # TODO: verify
    (FaceName.U, FaceName.B): _identity,           # TODO: verify
    (FaceName.U, FaceName.L): _identity,           # TODO: verify
    (FaceName.U, FaceName.D): _identity,           # TODO: verify

    # Source = R (Right)
    (FaceName.R, FaceName.F): _identity,           # TODO: verify
    (FaceName.R, FaceName.U): _identity,           # TODO: verify
    (FaceName.R, FaceName.B): _identity,           # TODO: verify
    (FaceName.R, FaceName.D): _identity,           # TODO: verify
    (FaceName.R, FaceName.L): _identity,           # TODO: verify

    # Source = B (Back)
    (FaceName.B, FaceName.U): _identity,           # TODO: verify
    (FaceName.B, FaceName.R): _identity,           # TODO: verify
    (FaceName.B, FaceName.D): _identity,           # TODO: verify
    (FaceName.B, FaceName.L): _identity,           # TODO: verify
    (FaceName.B, FaceName.F): _identity,           # TODO: verify

    # Source = D (Down)
    (FaceName.D, FaceName.F): _identity,           # TODO: verify
    (FaceName.D, FaceName.R): _identity,           # TODO: verify
    (FaceName.D, FaceName.B): _identity,           # TODO: verify
    (FaceName.D, FaceName.L): _identity,           # TODO: verify
    (FaceName.D, FaceName.U): _identity,           # TODO: verify

    # Source = L (Left)
    (FaceName.L, FaceName.F): _identity,           # TODO: verify
    (FaceName.L, FaceName.U): _identity,           # TODO: verify
    (FaceName.L, FaceName.B): _identity,           # TODO: verify
    (FaceName.L, FaceName.D): _identity,           # TODO: verify
    (FaceName.L, FaceName.R): _identity,           # TODO: verify
}

# Adjacent face pairs (share an edge)
_ADJACENT_PAIRS: set[tuple[FaceName, FaceName]] = {
    # F adjacent to U, R, D, L
    (FaceName.F, FaceName.U), (FaceName.F, FaceName.R),
    (FaceName.F, FaceName.D), (FaceName.F, FaceName.L),
    # U adjacent to F, R, B, L
    (FaceName.U, FaceName.F), (FaceName.U, FaceName.R),
    (FaceName.U, FaceName.B), (FaceName.U, FaceName.L),
    # R adjacent to F, U, B, D
    (FaceName.R, FaceName.F), (FaceName.R, FaceName.U),
    (FaceName.R, FaceName.B), (FaceName.R, FaceName.D),
    # B adjacent to U, R, D, L
    (FaceName.B, FaceName.U), (FaceName.B, FaceName.R),
    (FaceName.B, FaceName.D), (FaceName.B, FaceName.L),
    # D adjacent to F, R, B, L
    (FaceName.D, FaceName.F), (FaceName.D, FaceName.R),
    (FaceName.D, FaceName.B), (FaceName.D, FaceName.L),
    # L adjacent to F, U, B, D
    (FaceName.L, FaceName.F), (FaceName.L, FaceName.U),
    (FaceName.L, FaceName.B), (FaceName.L, FaceName.D),
}


class Face2FaceTranslator:
    """
    Central API for translating coordinates between cube faces.

    This is the ONE place that handles all face-to-face coordinate operations,
    ensuring consistency with the viewer-perspective definition.

    DEFINITION:
        translate(F, R, (row, col)) → (row', col') means:
        If you mark (row, col) on F and (row', col') on R, then apply Y' (R→F),
        both markers appear at the same screen position.

    IMPLEMENTATION:
        Phase 1: All 30 face pairs hardcoded
        Phase 2: Derive mathematical formulas
    """

    def __init__(self, cube: Cube) -> None:
        """
        Initialize translator with a cube instance.

        Args:
            cube: The cube whose faces we're translating between
        """
        self._cube = cube
        self._n = cube.n  # Cube size (3 for 3x3, etc.)

    def translate(
        self,
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
            >>> translator = FaceCoordinateTranslator(cube)
            >>> result = translator.translate(cube.front, cube.right, (1, 2))
            >>> print(result.dest_coord)  # Position on R face
            >>> # Verify: mark both positions, apply Y', both markers align
        """
        if source_face is dest_face:
            raise ValueError("Cannot translate from a face to itself")

        row, col = coord
        if not (0 <= row < self._n and 0 <= col < self._n):
            raise ValueError(f"Coordinate {coord} out of bounds for {self._n}x{self._n} cube")

        source_name = source_face.name
        dest_name = dest_face.name

        # Get verification rotation from lookup table
        key = (source_name, dest_name)
        verification_rotation = _VERIFICATION_ROTATIONS[key]

        # Get coordinate transformation from lookup table
        transform = _COORD_TRANSFORMS[key]
        dest_coord = transform(row, col, self._n)

        # Determine if faces are adjacent
        is_adjacent = key in _ADJACENT_PAIRS

        # Get shared edge if adjacent
        shared_edge: Edge | None = None
        if is_adjacent:
            shared_edge = self._find_shared_edge(source_face, dest_face)

        # Determine axis info (simplified for now)
        # TODO: Calculate based on edge positions
        source_axis = Axis.ROW
        dest_axis = Axis.ROW
        axis_exchanged = False

        return FaceTranslationResult(
            dest_coord=dest_coord,
            shared_edge=shared_edge,
            is_adjacent=is_adjacent,
            verification_rotation=verification_rotation,
            source_axis=source_axis,
            dest_axis=dest_axis,
            axis_exchanged=axis_exchanged,
        )

    def _find_shared_edge(self, face1: Face, face2: Face) -> Edge | None:
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

    def _get_edge_position(self, face: Face, edge: Edge) -> EdgePosition:
        """Determine the position of an edge relative to a face."""
        if edge is face.edge_top:
            return EdgePosition.TOP
        elif edge is face.edge_bottom:
            return EdgePosition.BOTTOM
        elif edge is face.edge_left:
            return EdgePosition.LEFT
        elif edge is face.edge_right:
            return EdgePosition.RIGHT
        else:
            raise ValueError(f"Edge {edge} is not an edge of face {face}")
