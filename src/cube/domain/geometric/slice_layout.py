from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.domain.model.FaceName import FaceName
    from cube.domain.model.SliceName import SliceName
    from cube.domain.geometric.cube_layout import CubeLayout
    from cube.domain.geometric.cube_walking import CubeWalkingInfoUnit


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()


class SliceLayout(Protocol):
    """
    Holds all the geometry related to a slice.

    Each slice (M, E, S) has properties like:
    - Which face defines its rotation direction
    - How it cuts faces (rows vs columns)
    - Whether its indices align with face coordinates
    """

    def get_face_name(self) -> FaceName:
        """
        Return the face that defines the positive rotation direction for this slice.

        This is the face that the slice rotates "over" - when the slice rotates,
        it moves content in the same direction as rotating I think that face clockwise
        (viewed from outside the cube looking at that face).

        In terms of the LTR coordinate system (see docs/face-coordinate-system/):
        - Clockwise rotation moves content: T→R→(-T)→(-R)→T
        - Content flows from the T (top/bottom) direction toward the R (left/right) direction

        Returns:
            M slice → L face (middle layer between L and R, rotates like L)
            E slice → D face (middle layer between U and D, rotates like D)
            S slice → F face (middle layer between F and B, rotates like F)

        See also:
            - WholeCubeAlg.get_face_name() for whole-cube rotation equivalent
            - docs/face-coordinate-system/face-slice-rotation.md
        """
        ...

    def does_slice_cut_rows_or_columns(self, face_name: FaceName) -> CLGColRow:
        """
        Determine whether this slice cuts rows or columns on the given face.

        Derived from slice geometry: checks if the exit edge (to next face in cycle)
        is horizontal or vertical on this face.

        - Horizontal exit edge (top/bottom) → slice goes vertically → cuts rows
        - Vertical exit edge (left/right) → slice goes horizontally → cuts columns

        Args:
            face_name: The face to check.

        Returns:
            CLGColRow.ROW if slice cuts rows (forms vertical strips on face)
            CLGColRow.COL if slice cuts columns (forms horizontal strips on face)

        See also:
            is_horizontal_on_face() - alias that returns bool
        """
        ...

    def is_horizontal_on_face(self, face_name: FaceName) -> bool:
        """
        Check if slice forms horizontal strips (rows) on the given face.

        This is an alias for does_slice_cut_rows_or_columns that returns a bool:
        - True = slice forms horizontal strips = cuts columns = CLGColRow.COL
        - False = slice forms vertical strips = cuts rows = CLGColRow.ROW

        Args:
            face_name: The face to check.

        Returns:
            True if slice is horizontal on this face (cuts columns)
            False if slice is vertical on this face (cuts rows)
        """
        ...

    def does_slice_of_face_start_with_face(self, face_name: FaceName) -> bool:
        """
        Check if slice index 0 aligns with the face's natural coordinate origin.

        Each slice (M, E, S) has indices 0 to n_slices-1. Slice index 0 is always
        closest to the "reference face" for that slice type:
            - M[0] closest to L (M rotates like L)
            - E[0] closest to D (E rotates like D)
            - S[0] closest to F (S rotates like F)

        This method answers: when iterating slice indices on a given face,
        does index 0 correspond to row/col 0, or to row/col (n_slices-1)?

        Args:
            face_name: The face to check alignment on.

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
        ...

    def create_walking_info_unit(self) -> "CubeWalkingInfoUnit":
        """
        Create SIZE-INDEPENDENT walking info for this slice.

        This method computes the topological structure of walking through the 4 faces
        that this slice passes through. The result uses a fake n_slices value (1234)
        to capture the TOPOLOGY without binding to any specific cube size.

        The returned CubeWalkingInfoUnit can be converted to any actual cube size
        using FaceWalkingInfoUnit.get_reference_point() and get_compute().

        WHY SIZE-INDEPENDENT?
        =====================
        - The faces a slice passes through don't change with cube size
        - The edges connecting those faces don't change
        - Whether coordinates are inverted on each face doesn't change
        - Only the actual coordinate VALUES change (0..n_slices-1)

        By computing this once and caching it, we avoid recomputing the same
        topology for every cube size.

        Returns:
            CubeWalkingInfoUnit with:
            - face_infos: 4 FaceWalkingInfoUnit in content flow order
            - Each FaceWalkingInfoUnit has a compute function: (n_slices, r, c) -> Point

        See Also:
            - UNIT_WALKING_INFO.md for detailed architecture documentation
            - SizedCubeLayout.create_walking_info() which converts to actual size
        """
        ...


class _SliceLayout(SliceLayout):

    def __init__(self, slice_name: "SliceName", layout: "CubeLayout | None" = None):
        self._slice_name = slice_name
        self._layout: "CubeLayout | None" = layout

    def get_face_name(self) -> "FaceName":
        """
        Return the face that defines the positive rotation direction for this slice.

        Uses CubeLayout.get_slice_rotation_face() method.
        """
        if self._layout is None:
            raise RuntimeError(
                "Cannot get_face_name without layout reference. "
                "Use layout.get_slice_rotation_face() directly."
            )
        return self._layout.get_slice_rotation_face(self._slice_name)

    def does_slice_cut_rows_or_columns(self, face_name: "FaceName") -> CLGColRow:
        """
        Determine whether this slice cuts rows or columns on the given face.

        Derived from first principles (Issue #55):
        - The slice is parallel to its rotation face and its opposite face
        - If these "axis faces" are the left/right neighbors of target face → vertical → cuts rows
        - If these "axis faces" are the top/bottom neighbors → horizontal → cuts columns

        Args:
            face_name: The face to check.

        Returns:
            CLGColRow.ROW if slice cuts rows (forms vertical strips on face)
            CLGColRow.COL if slice cuts columns (forms horizontal strips on face)

        See also:
            is_horizontal_on_face() - alias returning bool
        """
        if self._layout is None:
            raise RuntimeError(
                "Cannot derive does_slice_cut_rows_or_columns without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> CLGColRow:
            from cube.domain.model.Cube import Cube
            from cube.domain.model.Face import Face

            # Get the rotation face for this slice (M→L, E→D, S→F)
            rotation_face_name = self.get_face_name()

            # Access the internal 3x3 cube to check face edge relationships
            assert self._layout is not None  # Already checked above
            internal_cube: Cube = self._layout._cube
            face: Face = internal_cube.face(face_name)

            # Get the left and right neighbors of the target face
            left_neighbor: FaceName = face.edge_left.get_other_face(face).name
            right_neighbor: FaceName = face.edge_right.get_other_face(face).name

            # If the slice's rotation face is a left/right neighbor,
            # the slice is vertical on this face (cuts rows)
            if rotation_face_name in (left_neighbor, right_neighbor):
                return CLGColRow.ROW
            else:
                return CLGColRow.COL

        # Use cache manager from layout
        cache_key = ("SliceLayout.does_slice_cut_rows_or_columns", self._slice_name, face_name)
        cache = self._layout.cache_manager.get(cache_key, CLGColRow)
        return cache.compute(compute)

    def is_horizontal_on_face(self, face_name: "FaceName") -> bool:
        """
        Check if slice forms horizontal strips (rows) on the given face.

        This is an alias for does_slice_cut_rows_or_columns that returns a bool:
        - True = slice forms horizontal strips = cuts columns = CLGColRow.COL
        - False = slice forms vertical strips = cuts rows = CLGColRow.ROW

        Args:
            face_name: The face to check.

        Returns:
            True if slice is horizontal on this face (cuts columns)
            False if slice is vertical on this face (cuts rows)
        """
        return self.does_slice_cut_rows_or_columns(face_name) == CLGColRow.COL

    def does_slice_of_face_start_with_face(self, face_name: "FaceName") -> bool:
        """
        Check if slice index 0 aligns with the face's natural coordinate origin.

        Each slice (M, E, S) has indices 0 to n_slices-1. Slice index 0 is always
        closest to the "reference face" for that slice type:
            - M[0] closest to L (M rotates like L)
            - E[0] closest to D (E rotates like D)
            - S[0] closest to F (S rotates like F)

        This is a size-independent topology question derived from:
        - The slice's rotation face (from _SLICE_ROTATION_FACE)
        - The face's position relative to that rotation face

        Returns:
            True  → slice[0] aligns with face's row/col 0 (natural start)
            False → slice[0] aligns with face's row/col (n_slices-1) (inverted)
        """
        if self._layout is None:
            raise RuntimeError(
                "Cannot derive does_slice_of_face_start_with_face without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> bool:
            from cube.domain.model.Cube import Cube
            from cube.domain.model.Face import Face

            # Get the rotation face (slice[0] is closest to it)
            rotation_face_name = self.get_face_name()

            # Use internal 3x3 cube to check edge relationships
            assert self._layout is not None
            internal_cube: Cube = self._layout._cube
            face: Face = internal_cube.face(face_name)
            rotation_face: Face = internal_cube.face(rotation_face_name)

            # Find which edge of 'face' connects to rotation_face
            shared_edge = face.get_shared_edge(rotation_face)
            if shared_edge is None:
                # face_name is not adjacent to rotation face (shouldn't happen in slice cycle)
                return True

            # If rotation face is on the left or bottom edge of this face,
            # then slice[0] aligns with row/col 0 (True)
            # If rotation face is on the right or top edge,
            # then slice[0] aligns with row/col (n-1) (False)
            if shared_edge is face.edge_left or shared_edge is face.edge_bottom:
                return True
            else:
                return False

        # Use cache manager from layout
        cache_key = ("SliceLayout.does_slice_of_face_start_with_face", self._slice_name, face_name)
        cache = self._layout.cache_manager.get(cache_key, bool)
        return cache.compute(compute)

    def create_walking_info_unit(self) -> "CubeWalkingInfoUnit":
        """
        Create SIZE-INDEPENDENT walking info for this slice.

        See SliceLayout protocol docstring for full documentation.
        """
        import random
        from cube.domain.geometric.cube_walking import CubeWalkingInfoUnit, FaceWalkingInfoUnit
        from cube.domain.geometric.types import Point
        from cube.domain.model.Edge import Edge
        from cube.domain.model.Face import Face

        if self._layout is None:
            raise RuntimeError(
                "Cannot create walking info unit without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> CubeWalkingInfoUnit:
            assert self._layout is not None
            internal_3x3 = self._layout._cube
            slice_name = self._slice_name
            fake_n_slices = 1234  # Arbitrary large value - see UNIT_WALKING_INFO.md

            def inv(x: int) -> int:
                return fake_n_slices - 1 - x

            # Derive starting face and edge from rotation face
            rotation_face_name = self.get_face_name()
            rotation_face = internal_3x3.face(rotation_face_name)

            # Get edges in clockwise order around the rotation face
            rotation_edges = internal_3x3.layout.get_face_edge_rotation_cw(rotation_face)
            cycle_faces_ordered = [edge.get_other_face(rotation_face) for edge in rotation_edges]

            # Pick first two consecutive faces (random starting point in the cycle)
            # INTENTIONALLY RANDOM: The user chose this to expose potential bugs.
            # The walking algorithm must NOT depend on which face we start from.
            # If tests fail non-deterministically, it reveals hidden assumptions.
            fidx = random.randint(0, 3)
            first_face = cycle_faces_ordered[fidx]
            second_face = cycle_faces_ordered[(fidx + 1) % 4]

            # Find shared edge between first two faces - this IS the starting edge
            shared_edge: Edge | None = first_face.get_shared_edge(second_face)
            assert shared_edge is not None, f"No shared edge between {first_face.name} and {second_face.name}"

            current_face: Face = first_face
            current_edge: Edge = shared_edge

            # Virtual point coordinates for reference
            current_index: int = 0  # which slice
            slot: int = 0  # position along slice

            # Determine if current_index needs to be inverted based on alignment with rotation face
            if not self.does_slice_of_face_start_with_face(current_face.name):
                current_index = inv(current_index)

            face_infos: list[FaceWalkingInfoUnit] = []

            def actual_inv(actual_n_slices: int, si: int) -> int:
                return actual_n_slices - 1 - si

            # Point computation functions - 8 combinations of (horizontal, slot_inverted, index_inverted)
            def _compute_h_si_ii(actual_n_slices: int, si: int, sl: int) -> Point:
                return (actual_inv(actual_n_slices, sl), actual_inv(actual_n_slices, si))

            def _compute_h_si(actual_n_slices: int, si: int, sl: int) -> Point:
                return (actual_inv(actual_n_slices, sl), si)

            def _compute_h_ii(actual_n_slices: int, si: int, sl: int) -> Point:
                return (sl, actual_inv(actual_n_slices, si))

            def _compute_h(actual_n_slices: int, si: int, sl: int) -> Point:
                return (sl, si)

            def _compute_v_si_ii(actual_n_slices: int, si: int, sl: int) -> Point:
                return (actual_inv(actual_n_slices, si), actual_inv(actual_n_slices, sl))

            def _compute_v_si(actual_n_slices: int, si: int, sl: int) -> Point:
                return (si, actual_inv(actual_n_slices, sl))

            def _compute_v_ii(actual_n_slices: int, si: int, sl: int) -> Point:
                return (actual_inv(actual_n_slices, si), sl)

            def _compute_v(actual_n_slices: int, si: int, sl: int) -> Point:
                return (si, sl)

            for iteration in range(4):
                # Determine edge properties
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

                # Select precomputed point function based on edge properties
                if is_horizontal and is_slot_inverted and is_index_inverted:
                    compute_fn = _compute_h_si_ii
                elif is_horizontal and is_slot_inverted and not is_index_inverted:
                    compute_fn = _compute_h_si
                elif is_horizontal and not is_slot_inverted and is_index_inverted:
                    compute_fn = _compute_h_ii
                elif is_horizontal and not is_slot_inverted and not is_index_inverted:
                    compute_fn = _compute_h
                elif not is_horizontal and is_slot_inverted and is_index_inverted:
                    compute_fn = _compute_v_si_ii
                elif not is_horizontal and is_slot_inverted and not is_index_inverted:
                    compute_fn = _compute_v_si
                elif not is_horizontal and not is_slot_inverted and is_index_inverted:
                    compute_fn = _compute_v_ii
                else:
                    compute_fn = _compute_v

                face_infos.append(FaceWalkingInfoUnit(
                    face_name=current_face.name,
                    edge_name=current_edge.name,
                    reference_point=reference_point,
                    n_slices=fake_n_slices,
                    _compute=compute_fn
                ))

                # Move to next face (except after the 4th)
                if len(face_infos) < 4:
                    next_face = current_edge.get_other_face(current_face)
                    next_edge: Edge = current_edge.opposite(next_face)

                    next_slice_index = current_edge.get_slice_index_from_ltr_index_arbitrary_n_slices(
                        fake_n_slices,
                        current_face, current_index
                    )
                    current_index = current_edge.get_ltr_index_from_slice_index_arbitrary_n_slices(
                        fake_n_slices,
                        next_face, next_slice_index
                    )
                    current_edge = next_edge
                    current_face = next_face

            return CubeWalkingInfoUnit(
                slice_name=slice_name,
                rotation_face=rotation_face_name,
                n_slices=fake_n_slices,
                face_infos=tuple(face_infos)
            )

        # Use cache manager from layout - cache by slice_name only (size-independent!)
        cache_key = ("SliceLayout.create_walking_info_unit", self._slice_name)
        cache = self._layout.cache_manager.get(cache_key, CubeWalkingInfoUnit)
        return cache.compute(compute)
