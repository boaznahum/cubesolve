"""
Central API for face-to-face coordinate translation.

This module provides a unified framework for translating coordinates between
faces of the cube, handling:
- Adjacent face navigation (share an edge)
- Opposite face navigation (no shared edge)
- Axis exchange (ROW ↔ COLUMN)
- Physical alignment preservation

See: docs/design2/issue-face-to-face-navigation-framework.md
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Edge import Edge
    from .Face import Face


class Axis(Enum):
    """Represents whether a slice is a ROW or COLUMN on a face."""
    ROW = auto()
    COLUMN = auto()


class EdgePosition(Enum):
    """Position of an edge on a face."""
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()


class RotationDirection(Enum):
    """Direction of rotation."""
    CW = auto()   # Clockwise
    CCW = auto()  # Counter-clockwise


@dataclass
class FaceTranslationResult:
    """
    Result of translating a coordinate between faces.

    Contains all information needed to understand and execute the translation:
    - The destination coordinate
    - Navigation information (shared edge, adjacency)
    - Rotation information (which face, direction, count)
    - Axis information (whether ROW↔COLUMN swap occurred)
    - LTR translation details
    """

    # The destination coordinate
    dest_coord: tuple[int, int]  # (row, col) on dest_face

    # Navigation information
    shared_edge: "Edge | None"    # None if non-adjacent (opposite faces)
    is_adjacent: bool             # True if faces share an edge

    # Rotation to reach destination
    rotation_face: "Face"         # Which face's rotation moves the piece
    rotation_direction: RotationDirection  # CW or CCW
    rotation_count: int           # Number of 90° turns (1, 2, or 3)

    # Reverse path
    reverse_direction: RotationDirection   # Direction to go back
    reverse_rotation_face: "Face"          # Face to rotate to go back

    # Axis information
    axis_exchange: bool           # True if ROW↔COLUMN swap occurred
    source_axis: Axis             # ROW or COLUMN on source
    dest_axis: Axis               # ROW or COLUMN on destination

    # Edge position on each face
    source_edge_position: EdgePosition  # TOP/BOTTOM/LEFT/RIGHT on source
    dest_edge_position: EdgePosition    # TOP/BOTTOM/LEFT/RIGHT on dest

    # LTR translation details
    source_ltr: int               # LTR index on source edge
    dest_ltr: int                 # LTR index on dest edge


@dataclass
class FaceCoordinate:
    """A coordinate on a specific face."""
    face: "Face"
    row: int
    col: int


class FaceCoordinateTranslator:
    """
    Central API for translating coordinates between faces.

    This is the ONE place that handles:
    - Adjacent face navigation (share an edge)
    - Non-adjacent face navigation (opposite faces)
    - Coordinate transformation with axis exchange
    - Rotation direction to reach destination

    The Axis Rule:
    - Horizontal edge (top/bottom) → ltr selects COLUMN
    - Vertical edge (left/right) → ltr selects ROW

    Example:
        translator = FaceCoordinateTranslator()
        result = translator.translate_coordinate(
            cube.front, cube.up, (1, 1), cube_size=3
        )
        print(f"Coordinate on U: {result.dest_coord}")
        print(f"Axis exchange: {result.axis_exchange}")
    """

    def __init__(self, cube: "Cube" = None):  # type: ignore  # noqa: F821
        """
        Initialize the translator.

        Args:
            cube: Optional cube instance for accessing faces
        """
        self._cube = cube

    def translate_coordinate(
        self,
        source_face: "Face",
        dest_face: "Face",
        source_coord: tuple[int, int],
        cube_size: int
    ) -> FaceTranslationResult:
        """
        Translate a coordinate from source_face to dest_face.

        Args:
            source_face: The face where the piece currently is
            dest_face: The face where we want to find the piece
            source_coord: (row, col) position on source_face
            cube_size: Size of cube (3 for 3x3, 5 for 5x5, etc.)

        Returns:
            FaceTranslationResult with all translation details

        Raises:
            ValueError: If source and dest are the same face
        """
        if source_face == dest_face:
            raise ValueError("Source and destination faces cannot be the same")

        # Check if faces are adjacent or opposite
        shared_edge = self._find_shared_edge(source_face, dest_face)

        if shared_edge is not None:
            return self._translate_adjacent(
                source_face, dest_face, source_coord, cube_size, shared_edge
            )
        else:
            return self._translate_opposite(
                source_face, dest_face, source_coord, cube_size
            )

    def _find_shared_edge(
        self,
        face1: "Face",
        face2: "Face"
    ) -> "Edge | None":
        """
        Find the edge shared by two faces, if any.

        Returns:
            The shared Edge, or None if faces are opposite (not adjacent)
        """
        for edge in face1.edges:
            if face2.is_edge(edge):
                return edge
        return None

    def _get_edge_position(
        self,
        face: "Face",
        edge: "Edge"
    ) -> EdgePosition:
        """
        Determine the position of an edge on a face.

        Returns:
            EdgePosition (TOP, BOTTOM, LEFT, or RIGHT)
        """
        if edge is face.edge_top:
            return EdgePosition.TOP
        elif edge is face.edge_bottom:
            return EdgePosition.BOTTOM
        elif edge is face.edge_left:
            return EdgePosition.LEFT
        elif edge is face.edge_right:
            return EdgePosition.RIGHT
        else:
            raise ValueError(f"Edge {edge} is not on face {face}")

    def _get_axis_from_edge_position(self, pos: EdgePosition) -> Axis:
        """
        Apply the Axis Rule:
        - Horizontal edge (TOP/BOTTOM) → COLUMN
        - Vertical edge (LEFT/RIGHT) → ROW
        """
        if pos in (EdgePosition.TOP, EdgePosition.BOTTOM):
            return Axis.COLUMN
        else:
            return Axis.ROW

    def _translate_adjacent(
        self,
        source: "Face",
        dest: "Face",
        coord: tuple[int, int],
        cube_size: int,
        shared_edge: "Edge"
    ) -> FaceTranslationResult:
        """
        Translate coordinate between adjacent faces (share an edge).

        Algorithm:
        1. Determine edge position on each face (TOP/BOTTOM/LEFT/RIGHT)
        2. Apply axis rule to determine ROW vs COLUMN
        3. Extract ltr coordinate from source
        4. Translate through edge (handles same_direction flag)
        5. Build destination coordinate
        """
        # Get edge positions
        source_edge_pos = self._get_edge_position(source, shared_edge)
        dest_edge_pos = self._get_edge_position(dest, shared_edge)

        # Apply axis rule
        source_axis = self._get_axis_from_edge_position(source_edge_pos)
        dest_axis = self._get_axis_from_edge_position(dest_edge_pos)

        row, col = coord
        n = cube_size

        # Extract the ltr coordinate along the edge from source
        source_ltr = self._extract_ltr_from_coord(
            coord, source_edge_pos, source_axis, n
        )

        # Translate through edge (handles same_direction inversion)
        edge_index = shared_edge.get_slice_index_from_ltr_index(source, source_ltr)
        dest_ltr = shared_edge.get_ltr_index_from_slice_index(dest, edge_index)

        # Extract the perpendicular coordinate (distance from edge)
        perp_distance = self._extract_perpendicular_distance(
            coord, source_edge_pos, n
        )

        # Build destination coordinate
        dest_coord = self._build_dest_coord(
            dest_ltr, perp_distance, dest_edge_pos, dest_axis, n
        )

        # Determine rotation face and direction
        rotation_face, rotation_dir = self._determine_rotation(
            source, dest, source_edge_pos
        )

        return FaceTranslationResult(
            dest_coord=dest_coord,
            shared_edge=shared_edge,
            is_adjacent=True,
            rotation_face=rotation_face,
            rotation_direction=rotation_dir,
            rotation_count=1,
            reverse_direction=RotationDirection.CCW if rotation_dir == RotationDirection.CW else RotationDirection.CW,
            reverse_rotation_face=rotation_face,
            axis_exchange=(source_axis != dest_axis),
            source_axis=source_axis,
            dest_axis=dest_axis,
            source_edge_position=source_edge_pos,
            dest_edge_position=dest_edge_pos,
            source_ltr=source_ltr,
            dest_ltr=dest_ltr,
        )

    def _extract_ltr_from_coord(
        self,
        coord: tuple[int, int],
        edge_pos: EdgePosition,
        axis: Axis,
        n: int
    ) -> int:
        """
        Extract the ltr coordinate (along the edge) from a full coordinate.

        For horizontal edges (TOP/BOTTOM): ltr = column index
        For vertical edges (LEFT/RIGHT): ltr = row index
        """
        row, col = coord

        if axis == Axis.COLUMN:
            # Horizontal edge - ltr is the column
            return col
        else:
            # Vertical edge - ltr is the row
            return row

    def _extract_perpendicular_distance(
        self,
        coord: tuple[int, int],
        edge_pos: EdgePosition,
        n: int
    ) -> int:
        """
        Extract the perpendicular distance from the edge.

        This is how far the coordinate is from the shared edge.
        """
        row, col = coord

        match edge_pos:
            case EdgePosition.TOP:
                return n - 1 - row  # Distance from top (row 0)
            case EdgePosition.BOTTOM:
                return row  # Distance from bottom (row n-1)
            case EdgePosition.LEFT:
                return col  # Distance from left (col 0)
            case EdgePosition.RIGHT:
                return n - 1 - col  # Distance from right (col n-1)

    def _build_dest_coord(
        self,
        dest_ltr: int,
        perp_distance: int,
        dest_edge_pos: EdgePosition,
        dest_axis: Axis,
        n: int
    ) -> tuple[int, int]:
        """
        Build the destination coordinate from ltr and perpendicular distance.

        The perpendicular distance from source edge becomes the perpendicular
        distance from the destination edge.
        """
        match dest_edge_pos:
            case EdgePosition.TOP:
                # Coming in from top edge
                row = perp_distance
                col = dest_ltr
            case EdgePosition.BOTTOM:
                # Coming in from bottom edge
                row = n - 1 - perp_distance
                col = dest_ltr
            case EdgePosition.LEFT:
                # Coming in from left edge
                row = dest_ltr
                col = perp_distance
            case EdgePosition.RIGHT:
                # Coming in from right edge
                row = dest_ltr
                col = n - 1 - perp_distance

        return (row, col)

    def _determine_rotation(
        self,
        source: "Face",
        dest: "Face",
        source_edge_pos: EdgePosition
    ) -> tuple["Face", RotationDirection]:
        """
        Determine which face to rotate and in which direction.

        The rotation face is the face perpendicular to the edge that
        when rotated moves pieces from source to dest.
        """
        # For now, return source as rotation face with CW direction
        # This needs to be refined based on actual cube geometry
        # TODO: Implement proper rotation face determination
        return (source, RotationDirection.CW)

    def _translate_opposite(
        self,
        source: "Face",
        dest: "Face",
        coord: tuple[int, int],
        cube_size: int
    ) -> FaceTranslationResult:
        """
        Translate coordinate between opposite faces (no shared edge).

        Algorithm:
        1. Find an intermediate face adjacent to both
        2. Translate source → intermediate
        3. Translate intermediate → dest
        4. Combine transformations
        """
        # Find intermediate face
        intermediate = self._find_intermediate_face(source, dest)

        # Two-step translation
        step1 = self.translate_coordinate(source, intermediate, coord, cube_size)
        step2 = self.translate_coordinate(intermediate, dest, step1.dest_coord, cube_size)

        return FaceTranslationResult(
            dest_coord=step2.dest_coord,
            shared_edge=None,
            is_adjacent=False,
            rotation_face=step1.rotation_face,  # First rotation face
            rotation_direction=step1.rotation_direction,
            rotation_count=2,
            reverse_direction=step2.reverse_direction,
            reverse_rotation_face=step2.reverse_rotation_face,
            axis_exchange=(step1.axis_exchange != step2.axis_exchange),  # XOR
            source_axis=step1.source_axis,
            dest_axis=step2.dest_axis,
            source_edge_position=step1.source_edge_position,
            dest_edge_position=step2.dest_edge_position,
            source_ltr=step1.source_ltr,
            dest_ltr=step2.dest_ltr,
        )

    def _find_intermediate_face(
        self,
        source: "Face",
        dest: "Face"
    ) -> "Face":
        """
        Find a face that is adjacent to both source and dest.

        For opposite faces, there are always 4 such faces.
        Returns the first one found.
        """
        for edge in source.edges:
            adjacent_to_source = edge.get_other_face(source)
            if self._find_shared_edge(adjacent_to_source, dest) is not None:
                return adjacent_to_source

        raise ValueError(f"No intermediate face found between {source} and {dest}")

    def get_slice_path(
        self,
        start_face: "Face",
        coord: tuple[int, int],
        cube_size: int,
        num_faces: int = 4
    ) -> list[FaceCoordinate]:
        """
        Get the complete path a slice takes through multiple faces.

        Starting from a coordinate on start_face, follows the slice
        through adjacent faces in rotation order.

        Args:
            start_face: Face to start from
            coord: Starting coordinate
            cube_size: Size of cube
            num_faces: Number of faces to traverse (default 4 for full rotation)

        Returns:
            List of FaceCoordinate for each face in the path
        """
        path = [FaceCoordinate(start_face, coord[0], coord[1])]

        current_face = start_face
        current_coord = coord

        for _ in range(num_faces - 1):
            # Find next face (via edge opposite to entry)
            # This logic depends on slice direction - simplified for now
            # TODO: Implement proper slice path following
            break

        return path
