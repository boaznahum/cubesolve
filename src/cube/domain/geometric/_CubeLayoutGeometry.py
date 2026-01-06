from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.geometric.cube_walking import CubeWalkingInfo, FaceWalkingInfo
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

        Uses CubeWalkingInfo to compute the reference point on all 4 faces
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
        walk_info = _CubeLayoutGeometry.create_walking_info(source_face.cube, slice_name)
        return walk_info.get_transform(source_face, target_face)

    @staticmethod
    def _travel_all_faces(
            cube: Cube,
            slice_name: SliceName,
    ) -> dict[Face, Point]:
        """
        Travel through all 4 faces that a slice passes through, computing reference points.

        This method delegates to create_walking_info() which performs the actual
        traversal, then converts the result to a dict for backward compatibility.

        Args:
            cube: The cube instance
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            dict mapping each Face to its reference Point.

        See Also:
            CubeWalkingInfo - the underlying data structure
            cube_walking.py - explanation of the slot consistency principle
        """
        walk_info = _CubeLayoutGeometry.create_walking_info(cube, slice_name)
        return {info.face: info.reference_point for info in walk_info}

    @staticmethod
    def create_walking_info(cube: Cube, slice_name: SliceName) -> CubeWalkingInfo:
        """
        Create walking info by traversing the 4 faces of a slice.

        This walks through all 4 faces, tracking where the reference point
        (slice_index=0, slot=0) lands on each face. It also precomputes
        the point computation function for each face for efficiency.

        Args:
            cube: The cube instance
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            CubeWalkingInfo with reference points and precomputed functions
        """
        n_slices = cube.n_slices

        def inv(x: int) -> int:
            return n_slices - 1 - x

        # Get starting face and edge based on slice type
        match slice_name:
            case SliceName.M:
                current_face = cube.front
                current_edge = current_face.edge_bottom
            case SliceName.E:
                current_face = cube.right
                current_edge = current_face.edge_left
            case SliceName.S:
                current_face = cube.up
                current_edge = current_face.edge_left
            case _:
                raise ValueError(f"Unknown slice name: {slice_name}")

        # Virtual point coordinates for reference
        current_index: int = 0  # which slice
        slot: int = 0  # position along slice

        face_infos: list[FaceWalkingInfo] = []

        for _ in range(4):
            # Determine edge properties ONCE
            is_horizontal = current_face.is_bottom_or_top(current_edge)
            is_slot_inverted = (
                current_face.is_top_edge(current_edge) if is_horizontal
                else current_face.is_right_edge(current_edge)
            )
            is_index_inverted = current_index != 0

            # Compute reference_point for (slice_index=0, slot=0)
            if is_horizontal:
                reference_point: Point = (inv(slot) if is_slot_inverted else slot, current_index)
            else:
                reference_point = (current_index, inv(slot) if is_slot_inverted else slot)

            # Create precomputed point function - all decisions baked in
            if is_horizontal and is_slot_inverted and is_index_inverted:
                compute = lambda si, sl, inv=inv: (inv(sl), inv(si))
            elif is_horizontal and is_slot_inverted and not is_index_inverted:
                compute = lambda si, sl, inv=inv: (inv(sl), si)
            elif is_horizontal and not is_slot_inverted and is_index_inverted:
                compute = lambda si, sl, inv=inv: (sl, inv(si))
            elif is_horizontal and not is_slot_inverted and not is_index_inverted:
                compute = lambda si, sl: (sl, si)
            elif not is_horizontal and is_slot_inverted and is_index_inverted:
                compute = lambda si, sl, inv=inv: (inv(si), inv(sl))
            elif not is_horizontal and is_slot_inverted and not is_index_inverted:
                compute = lambda si, sl, inv=inv: (si, inv(sl))
            elif not is_horizontal and not is_slot_inverted and is_index_inverted:
                compute = lambda si, sl, inv=inv: (inv(si), sl)
            else:  # not is_horizontal and not is_slot_inverted and not is_index_inverted
                compute = lambda si, sl: (si, sl)

            face_infos.append(FaceWalkingInfo(
                face=current_face,
                edge=current_edge,
                reference_point=reference_point,
                n_slices=n_slices,
                _compute=compute
            ))

            # Move to next face (except after the 4th)
            if len(face_infos) < 4:
                next_edge: Edge = current_edge.opposite(current_face)
                next_face = next_edge.get_other_face(current_face)

                # Translate slice index through the edge
                next_slice_index = next_edge.get_slice_index_from_ltr_index(
                    current_face, current_index
                )
                current_index = next_edge.get_ltr_index_from_slice_index(
                    next_face, next_slice_index
                )
                current_edge = next_edge
                current_face = next_face

        return CubeWalkingInfo(
            slice_name=slice_name,
            n_slices=n_slices,
            face_infos=tuple(face_infos)
        )
