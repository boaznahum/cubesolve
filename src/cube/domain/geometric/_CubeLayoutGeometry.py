from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.geometric.slice_layout import CLGColRow
from cube.domain.geometric.types import Point
from cube.domain.model.Edge import Edge
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


class _CubeLayoutGeometry:
    """
    Private implementation of cube geometry calculations.

    This class answers geometric questions about the relationship between
    slices (M, E, S) and faces. It provides the static implementation that
    is exposed through the SliceLayout and CubeLayout protocols.

    Methods are currently hardcoded based on empirical observation. Future
    work (Issue #55) may derive these mathematically from slice traversal
    paths and face coordinate systems.

    See Also:
        - SliceLayout protocol: exposes does_slice_cut_rows_or_columns,
          does_slice_of_face_start_with_face as instance methods
        - CubeLayout protocol: exposes iterate_orthogonal_face_center_pieces
        - GEOMETRY.md: detailed documentation of geometric relationships
    """

    @staticmethod
    def does_slice_cut_rows_or_columns(slice_name: SliceName, face_name: FaceName) -> CLGColRow:

        """
           Slice Traversal (content movement during rotation):
                M: F → U → B → D → F  (vertical cycle, like L rotation)
                E: R → B → L → F → R  (horizontal cycle, like D rotation)
                S: U → R → D → L → U  (around F/B axis, like F rotation)

        """
        # claude what is the Mathematica of this ???
        if slice_name == SliceName.M:
            return CLGColRow.ROW

        elif slice_name == SliceName.E:
            return CLGColRow.COL  # slice cut the column so we check row

        elif slice_name == SliceName.S:

            if face_name in [FaceName.R, FaceName.L]:
                # slice cut the rows so we take columns like in M
                return CLGColRow.ROW
            else:
                return CLGColRow.COL

        raise InternalSWError()

    @staticmethod
    def does_slice_of_face_start_with_face(slice_name: SliceName, face_name: FaceName) -> bool:
        """
        Check if slice index 0 aligns with the face's natural coordinate origin.

        Classification: HARDCODED - empirically determined, could be derived from
        slice traversal paths and face coordinate systems.

        Each slice (M, E, S) has indices 0 to n_slices-1. Slice index 0 is always
        closest to the "reference face" for that slice type:
            - M[0] closest to L (M rotates like L)
            - E[0] closest to D (E rotates like D)
            - S[0] closest to F (S rotates like F)

        This method answers: when iterating slice indices on a given face,
        does index 0 correspond to row/col 0, or to row/col (n_slices-1)?

        Returns:
            True  → slice[0] aligns with face's row/col 0 (natural start)
            False → slice[0] aligns with face's row/col (n_slices-1) (inverted)

        Example: M slice on FRONT face (5x5 cube, n_slices=3)
        ======================================================

            M[0] is closest to L. On FRONT face, L is on the left side.
            Face coordinates: col 0 is on the left.
            So M[0] → col 0. Returns True (aligned).

                    L           R
                    ↓           ↓
                ┌───┬───┬───┐
                │M0 │M1 │M2 │   M[0]=col0, M[1]=col1, M[2]=col2
                ├───┼───┼───┤
                │M0 │M1 │M2 │   Returns True: slice indices align
                ├───┼───┼───┤   with face column indices
                │M0 │M1 │M2 │
                └───┴───┴───┘

        Example: M slice on BACK face (5x5 cube, n_slices=3)
        =====================================================

            M[0] is closest to L. On BACK face, L is on the RIGHT side
            (because we're looking from behind).
            Face coordinates: col 0 is on the left (which is R side of cube).
            So M[0] → col 2 (rightmost). Returns False (inverted).

                    R           L
                    ↓           ↓
                ┌───┬───┬───┐
                │M2 │M1 │M0 │   M[0]=col2, M[1]=col1, M[2]=col0
                ├───┼───┼───┤
                │M2 │M1 │M0 │   Returns False: slice indices are
                ├───┼───┼───┤   inverted relative to face columns
                │M2 │M1 │M0 │
                └───┴───┴───┘

        See also: does_slice_cut_rows_or_columns()
        """
        if slice_name == SliceName.S:

            if face_name in [FaceName.L, FaceName.D]:
                # slice cut the rows so we take columns like in M
                return False  # S[1] is on L[last]
        elif slice_name == SliceName.M:
            if face_name in [FaceName.B]:
                return False

        return True

    # =========================================================================
    # Iterate centers on orthogonal face for a layer slice
    # Classification: COMPUTED (derived from BOY reference)
    # See: GEOMETRY.md for full documentation
    # =========================================================================

    @staticmethod
    def iterate_orthogonal_face_center_pieces(
            cube: "Cube",
            layer1_face: "Face",
            side_face: "Face",
            layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """
        Yield (row, col) positions on side_face for the given layer slice.

        A "layer slice" is a horizontal layer parallel to layer1_face (L1).
        Layer slice 0 is the one closest to L1.

        Args:
            cube: The cube (for n_slices)
            layer1_face: The Layer 1 face (base layer, e.g., white face)
            side_face: A face orthogonal to layer1_face
            layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

        Yields:
            (row, col) in LTR coordinates on side_face

        Raises:
            ValueError: if side_face is not orthogonal to layer1_face

        Example 1: L1=DOWN, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U
                ┌───┬───┬───┐
            row2│   │   │   │  ← layer_slice_index=2 (closest to U)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│ * │ * │ * │  ← layer_slice_index=0 (closest to D=L1)
                └───┴───┴───┘
                      D (L1)

            layer_slice_index=0 yields: (0,0), (0,1), (0,2)

        Example 2: L1=LEFT, side_face=FRONT, 5x5 cube (n_slices=3)
        ==========================================================

            Looking at FRONT face:

                L1        R
                (L)
                ┌───┬───┬───┐
                │ * │   │   │  row2
                ├───┼───┼───┤
                │ * │   │   │  row1
                ├───┼───┼───┤
                │ * │   │   │  row0
                └───┴───┴───┘
                col0 col1 col2

                ↑ layer_slice_index=0 (closest to L=L1)

            layer_slice_index=0 yields: (0,0), (1,0), (2,0)

        Example 3: L1=UP, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U (L1)
                ┌───┬───┬───┐
            row2│ * │ * │ * │  ← layer_slice_index=0 (closest to U=L1)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│   │   │   │  ← layer_slice_index=2 (closest to D)
                └───┴───┴───┘
                      D

            layer_slice_index=0 yields: (2,0), (2,1), (2,2)
        """
        # Validate side_face is adjacent to layer1_face (shares an edge)
        l1_name = layer1_face.name
        side_name = side_face.name

        if not cube.layout.is_adjacent(l1_name, side_name):
            raise ValueError(f"{side_name} is not adjacent to {l1_name}")

        n_slices = cube.n_slices

        # Determine which slice type (M/E/S) is parallel to L1
        # and which face is the reference (slice index 0 is closest to reference)
        if l1_name in [FaceName.U, FaceName.D]:
            slice_name = SliceName.E
            reference_face = FaceName.D  # E[0] closest to D
        elif l1_name in [FaceName.L, FaceName.R]:
            slice_name = SliceName.M
            reference_face = FaceName.L  # M[0] closest to L
        else:  # F or B
            slice_name = SliceName.S
            reference_face = FaceName.F  # S[0] closest to F

        # Convert layer_slice_index to physical slice index
        # If L1 == reference, layer_slice 0 = physical slice 0
        # If L1 == opposite of reference, indices are inverted
        if l1_name == reference_face:
            physical_slice_index = layer_slice_index
        else:
            physical_slice_index = n_slices - 1 - layer_slice_index

        # Does this slice cut rows or columns on side_face?
        # ROW → slice cuts rows → forms a COLUMN on face → fixed col, iterate rows
        # COL → slice cuts cols → forms a ROW on face → fixed row, iterate cols
        cut_type = _CubeLayoutGeometry.does_slice_cut_rows_or_columns(slice_name, side_name)

        # Does slice index align with face LTR coordinates?
        starts_with_face = _CubeLayoutGeometry.does_slice_of_face_start_with_face(slice_name, side_name)

        # Convert physical_slice_index to row/column index on face
        if starts_with_face:
            face_index = physical_slice_index
        else:
            face_index = n_slices - 1 - physical_slice_index

        # Yield positions
        if cut_type == CLGColRow.ROW:
            # Slice cuts rows → forms a column → fixed col, iterate rows
            for row in range(n_slices):
                yield row, face_index
        else:
            # Slice cuts cols → forms a row → fixed row, iterate cols
            for col in range(n_slices):
                yield face_index, col

    @staticmethod
    def translate_target_from_source(
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            slice_name: SliceName
    ) -> FUnitRotation:
        """
        Compute the unit rotation that transforms coordinates from source_face to target_face.

        Given a slice that connects source_face and target_face, this method computes
        the FUnitRotation that, when applied to a coordinate on source_face, gives
        the corresponding coordinate on target_face.

        Args:
            source_face: The face where content originates
            target_face: The face where content will appear
            source_coord: (row, col) position on source_face (used for bounds validation)
            slice_name: Which slice (M, E, S) connects the faces

        Returns:
            FUnitRotation that transforms source coordinates to target coordinates.
            Apply with: unit.of_cube(cube)(*source_coord) to get (target_row, target_col)

        Raises:
            ValueError: If source_face == target_face
            ValueError: If source_coord is out of bounds

        Example::

            # Get the rotation from Right to Front via E slice
            unit = _CubeLayoutGeometry.translate_target_from_source(
                cube.right, cube.front, (1, 2), SliceName.E
            )
            # Apply to get actual target coordinate
            target_coord = unit.of_cube(cube)(1, 2)
        """
        if source_face is target_face:
            raise ValueError("Cannot translate from a face to itself")

        n_slices = source_face.center.n_slices
        row, col = source_coord
        if not (0 <= row < n_slices and 0 <= col < n_slices):
            raise ValueError(f"Coordinate {source_coord} out of bounds for center grid (n_slices={n_slices})")

        """Derive unit rotation using Slice traversal logic."""
        # Use (0, 0) as reference point
        origin = (0, 0)
        unit_rotation = _CubeLayoutGeometry._translate_via_slice_geometry(
            source_face, target_face, origin, n_slices, slice_name
        )
        return unit_rotation

    @staticmethod
    def _translate_via_slice_geometry(
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            n_slices: int,
            slice_name: SliceName
    ) -> FUnitRotation:
        """
        Derive the unit rotation between two faces using slice traversal geometry.

        Uses _travel_all_faces to compute the reference point (0,0) on all 4 faces
        that the slice passes through, then derives the FUnitRotation that maps
        the source reference point to the target reference point.

        Args:
            source_face: Starting face
            target_face: Destination face
            source_coord: Not used (kept for API compatibility)
            n_slices: Cube size (for FUnitRotation.of)
            slice_name: Which slice connects the faces

        Returns:
            FUnitRotation representing the coordinate transformation
        """

        point_on_faces = _CubeLayoutGeometry._travel_all_faces(source_face.cube, slice_name)

        assert source_face in point_on_faces
        assert target_face in point_on_faces

        point_on_source = point_on_faces[source_face]
        point_on_target = point_on_faces[target_face]

        unit = FUnitRotation.of(n_slices, point_on_source, point_on_target)

        return unit

    @staticmethod
    def _travel_all_faces(
            cube: Cube,
            slice_name: SliceName,
    ) -> dict[Face, Point]:
        """
        Travel through all 4 faces that a slice passes through, computing reference points.

        Starting from a reference edge on the first face, this method walks through
        all 4 faces in the slice's traversal order, computing where the reference
        point (0, 0) lands on each face.

        Slice starting faces and edges:
            M: Front face, bottom edge  (traverses F → U → B → D)
            E: Right face, left edge    (traverses R → B → L → F)
            S: Up face, left edge       (traverses U → R → D → L)

        Args:
            cube: The cube instance
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            dict mapping each Face to its reference Point.
            The reference point is where (row=0, col=0) from the start face
            appears on each face in the traversal.

        ================================================================================
        IMPLEMENTATION DETAILS - TWO COORDINATES TO TRACK
        ================================================================================

        When a slice crosses a face, each point has two components:

        1. current_index: WHICH slice (0, 1, 2, ...)
           - Translates through the shared edge
           - Uses edge.get_slice_index_from_ltr_index() and get_ltr_index_from_slice_index()

        2. slot_along: WHERE on the slice (position 0, 1, 2, ...)
           - Physical position along the slice strip
           - PRESERVED across faces (slot 0 stays slot 0)
           - But mapping to (row, col) depends on edge type

        ================================================================================
        SLOT ORDERING (from Slice._get_slices_by_index)
        ================================================================================

        HORIZONTAL EDGES (top/bottom):
        ┌─────────────────────────────┬─────────────────────────────┐
        │  Bottom edge:               │   Top edge:                 │
        │  slot 0 → (row=0, col=idx)  │   slot 0 → (row=n-1, col=idx)
        │  slot 1 → (row=1, col=idx)  │   slot 1 → (row=n-2, col=idx)
        │                             │                             │
        │  current_index = col        │   current_index = col       │
        │  slot = row                 │   slot = inv(row)           │
        └─────────────────────────────┴─────────────────────────────┘

        VERTICAL EDGES (left/right):
        ┌─────────────────────────────┬─────────────────────────────┐
        │  Left edge:                 │   Right edge:               │
        │  slot 0 → (row=idx, col=0)  │   slot 0 → (row=idx, col=n-1)
        │  slot 1 → (row=idx, col=1)  │   slot 1 → (row=idx, col=n-2)
        │                             │                             │
        │  current_index = row        │   current_index = row       │
        │  slot = col                 │   slot = inv(col)           │
        └─────────────────────────────┴─────────────────────────────┘

        ================================================================================
        EXAMPLE: M slice, F(bottom) → U(bottom)
        ================================================================================

        Source F with edge_bottom:
        ┌───────────────┐
        │   0   1   2   │ col
        │ ┌───┬───┬───┐ │
        │ │   │   │   │ │ row 2
        │ ├───┼───┼───┤ │
        │ │   │ X │   │ │ row 1  ← X at (1, 1)
        │ ├───┼───┼───┤ │
        │ │   │   │   │ │ row 0
        │ └───┴───┴───┘ │
        │     ↑ slice 1 │
        └───────────────┘

        Extract: current_index=1, slot_along=1 (bottom edge)
        Translate current_index through F-U edge
        Reconstruct at U with its edge

        ================================================================================
        """

        n_slices = cube.n_slices

        def inv(x: int) -> int:
            return n_slices - 1 - x

        # we mimic the alg in cube.domain.model.Slice.Slice._get_slices_by_index
        # todo: hard coded
        match slice_name:
            case SliceName.M:  # over L, works
                current_face = cube.front
                current_edge = current_face.edge_bottom

            case SliceName.E:  # over D, works
                current_face = cube.right
                current_edge = current_face.edge_left

            case SliceName.S:  # over F, works
                current_face = cube.up
                current_edge = current_face.edge_left

            case _:
                raise ValueError(f"Unknown slice name: {slice_name}")
        # now find the reference edge of the start face

        # noinspection PyUnboundLocalVariable no it is not
        assert current_face.is_edge(current_edge)

        current_index: int = 0  # arbitrary column or row depends on the Slice
        other_rol_or_col = 0

        point_on_faces: dict[Face, Point] = {}

        for face_index in range(4):  # walking on two faces
            if current_face.is_bottom_or_top(current_edge):
                if current_face.is_top_edge(current_edge):
                    point_on_current_face = (inv(other_rol_or_col), current_index)
                else:
                    point_on_current_face = (other_rol_or_col, current_index)

            else:
                if current_face.is_right_edge(current_edge):
                    point_on_current_face = (current_index, inv(other_rol_or_col))
                else:
                    point_on_current_face = (current_index, other_rol_or_col)

            point_on_faces[current_face] = point_on_current_face

            if face_index < 3:  # PREPARE FOR THE NEXT
                next_edge: Edge = current_edge.opposite(current_face)
                next_face = next_edge.get_other_face(current_face)
                assert next_face.is_edge(next_edge)

                # SLICE COORDINATES are always ltr
                next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
                current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
                current_edge = next_edge
                current_face = next_face

                #assert current_face is target_face

        assert len(point_on_faces) == 4

        return point_on_faces
