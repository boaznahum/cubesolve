from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Tuple, cast

from cube.domain.exceptions import GeometryError, GeometryErrorCode
from cube.domain.geometric.geometry_types import CLGColRow, CenterToSlice
from cube.domain.model.FaceName import FaceName
from cube.domain.model._elements import EdgePosition
from cube.domain.geometric.geometry_utils import inv
from cube.utils.Cache import CacheManager
from cube.utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from cube.domain.model.SliceName import SliceName
    from cube.domain.geometric._CubeLayout import _CubeLayout
    from cube.domain.geometric.cube_walking import CubeWalkingInfoUnit


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

        !!! same as get_slice_rotation_face  !!!


        See also:
            - WholeCubeAlg.get_face_name() for whole-cube rotation equivalent
            - docs/face-coordinate-system/face-slice-rotation.md
        """
        ...

    def get_slice_rotation_face(self) -> FaceName:
        """Get the face that defines the rotation direction for a slice.

        See CubeLayout.get_slice_rotation_face() for full documentation.

        cluade: this is SliceLayout method, need to resolve and delegate
        """
        return self.get_face_name()

    def get_slice_rotation_faces(self) -> Tuple[FaceName, FaceName]:
        """
        Get the two faces that the slice is parallel to.

        Returns:
            A tuple of (rotation_face, opposite_face):
            - rotation_face: The face that defines the slice's rotation direction
            - opposite_face: The face opposite to rotation_face

            Examples:
                M slice → (L, R) - parallel to L and R, rotates like L
                E slice → (D, U) - parallel to D and U, rotates like D
                S slice → (F, B) - parallel to F and B, rotates like F
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

    def distance_from_face_to_slice_index(self, face_name: FaceName,
                                          distance_from_face: int,
                                          n_slices: int
                                          ) -> int:
        """
        Convert distance from a parallel face to slice index.

        Given a face that is parallel to the slice and a distance from that face,
        return the corresponding 0-based slice index.

        Args:
            face_name: A face parallel to the slice (must be rotation_face or opposite_face)
            distance_from_face: 0-based distance from the face (0 = closest to face)
            n_slices: Total number of inner slices (cube.size - 2)

        Returns:
            0-based slice index in range [0, n_slices-1]

        Example for M slice (parallel to L and R) with n_slices=3:
            - distance_from_face_to_slice_index(L, 0, 3) → 0 (closest to L)
            - distance_from_face_to_slice_index(L, 2, 3) → 2 (farthest from L)
            - distance_from_face_to_slice_index(R, 0, 3) → 2 (closest to R = farthest from L)
            - distance_from_face_to_slice_index(R, 2, 3) → 0 (farthest from R = closest to L)

        Raises:
            GeometryError: If face_name is not parallel to this slice
        """
        ...

    def create_slice_index_computer(self, face_name: FaceName) -> CenterToSlice:
        """
        Create a function that computes slice coordinates from (row, col, n_slices).

        The returned function encapsulates the geometry-derived formula for this
        specific slice and face combination.

        Args:
            face_name: The face to compute formula for

        Returns:
            A function (row, col, n_slices) -> (slice_index, slot)
            Caller typically uses result[0] to get just the slice_index.
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

    def __init__(self, slice_name: "SliceName",
                 layout: "_CubeLayout",
                 sp: IServiceProvider):
        self._slice_name = slice_name
        self._cube_layout: _CubeLayout = layout

        self._cache_manager = CacheManager.create(sp.config)


    def get_face_name(self) -> "FaceName":
        """
        Return the face that defines the positive rotation direction for this slice.

        Uses CubeLayout.get_slice_rotation_face() method.
        """
        if self._cube_layout is None:
            raise RuntimeError(
                "Cannot get_face_name without layout reference. "
                "Use layout.get_slice_rotation_face() directly."
            )
        return self._cube_layout.get_slice_rotation_face(self._slice_name)


    def get_slice_rotation_faces(self) -> Tuple[FaceName, FaceName]:
        """
        Get the two faces that the slice is parallel to.

        Returns:
            A tuple of (rotation_face, opposite_face):
            - rotation_face: The face that defines the slice's rotation direction
            - opposite_face: The face opposite to rotation_face

            Examples:
                M slice → (L, R) - parallel to L and R, rotates like L
                E slice → (D, U) - parallel to D and U, rotates like D
                S slice → (F, B) - parallel to F and B, rotates like F
        """
        rotation_face: FaceName = self.get_slice_rotation_face()
        opposite: FaceName = self._cube_layout.opposite(rotation_face)

        return rotation_face, opposite



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
        if self._cube_layout is None:
            raise RuntimeError(
                "Cannot derive does_slice_cut_rows_or_columns without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> CLGColRow:
            # Get the rotation face for this slice (M→L, E→D, S→F)
            rotation_face_name = self.get_face_name()

            # Get the left and right neighbors of the target face
            assert self._cube_layout is not None  # Already checked above
            left_neighbor: FaceName = self._cube_layout.get_face_neighbor(face_name, EdgePosition.LEFT)
            right_neighbor: FaceName = self._cube_layout.get_face_neighbor(face_name, EdgePosition.RIGHT)

            # If the slice's rotation face is a left/right neighbor,
            # the slice is vertical on this face (cuts rows)
            if rotation_face_name in (left_neighbor, right_neighbor):
                return CLGColRow.ROW
            else:
                return CLGColRow.COL

        # Use cache manager from layout
        cache_key = ("does_slice_cut_rows_or_columns", face_name)
        cache = self._cache_manager.get(cache_key, CLGColRow)
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

        Raises:
            GeometryError: If face_name is parallel to the slice (not cut by it)
        """
        assert self._cube_layout

        def compute() -> bool:
            # Get the rotation face (slice[0] is closest to it)
            rotation_face_name = self.get_face_name()

            # Validate: face must be cut by slice, not parallel to it
            assert self._cube_layout is not None
            parallel_faces = self.get_slice_rotation_faces()
            if face_name in parallel_faces:
                raise GeometryError(
                    GeometryErrorCode.FACE_IS_PARALLEL_TO_SLICE,
                    f"Face {face_name} is parallel to {self._slice_name}, expected a face cut by it"
                )

            # Check which edge position connects face_name to rotation_face
            left_neighbor = self._cube_layout.get_face_neighbor(face_name, EdgePosition.LEFT)
            bottom_neighbor = self._cube_layout.get_face_neighbor(face_name, EdgePosition.BOTTOM)

            # If rotation face is on the left or bottom edge of this face,
            # then slice[0] aligns with row/col 0 (True)
            # If rotation face is on the right or top edge,
            # then slice[0] aligns with row/col (n-1) (False)
            if rotation_face_name in (left_neighbor, bottom_neighbor):
                return True
            else:
                return False

        # Use cache manager from layout
        cache_key = ("does_slice_of_face_start_with_face", face_name)
        cache = self._cache_manager.get(cache_key, bool)
        return cache.compute(compute)

    def distance_from_face_to_slice_index(self, face_name: FaceName,
                                          distance_from_face: int,
                                          n_slices: int
                                          ) -> int:
        """
        Convert distance from a parallel face to slice index.

        Given a face that is parallel to the slice and a distance from that face,
        return the corresponding 0-based slice index.

        Args:
            face_name: A face parallel to the slice (must be rotation_face or opposite_face)
            distance_from_face: 0-based distance from the face (0 = closest to face)
            n_slices: Total number of inner slices (cube.size - 2)

        Returns:
            0-based slice index in range [0, n_slices-1]

        Example for M slice (parallel to L and R) with n_slices=3:
            - distance_from_face_to_slice_index(L, 0, 3) → 0 (closest to L)
            - distance_from_face_to_slice_index(L, 2, 3) → 2 (farthest from L)
            - distance_from_face_to_slice_index(R, 0, 3) → 2 (closest to R = farthest from L)
            - distance_from_face_to_slice_index(R, 2, 3) → 0 (farthest from R = closest to L)

        Raises:
            GeometryError: If face_name is not parallel to this slice
        """
        faces: tuple[FaceName, FaceName] = self.get_slice_rotation_faces()

        if face_name not in faces:
            raise GeometryError(GeometryErrorCode.FACE_NOT_PARALLEL_TO_SLICE, f"Face {face_name} not parallel to {self._slice_name}")



        assert len(faces) == 2

        if face_name == faces[0]:
            return distance_from_face
        else:
            opposite_face = self._cube_layout.opposite(face_name)

            if opposite_face not in faces:
                raise GeometryError(GeometryErrorCode.FACE_NOT_PARALLEL_TO_SLICE,
                                    f"Face {face_name} not parallel to {self._slice_name}")

            return inv(n_slices, distance_from_face)

    def create_slice_index_computer(self, face_name: FaceName) -> CenterToSlice:
        """
        Create a function that computes slice coordinates from (row, col, n_slices).

        The returned function encapsulates the geometry-derived formula for this
        specific slice and face combination.

        Args:
            face_name: The face to compute formula for

        Returns:
            A function (row, col, n_slices) -> (slice_index, slot)
            Caller typically uses result[0] to get just the slice_index.
        """

        def compute() -> CenterToSlice:
            # Get the walking info which has center_to_slice for all 4 faces
            walking_info_unit = self.create_walking_info_unit()

            # Find the face info for this face
            for face_info in walking_info_unit.face_infos:
                if face_info.face_name == face_name:
                    # Return center_to_slice directly: (row, col, n_slices) -> (slice_index, slot)
                    return face_info.center_to_slice

            raise GeometryError(
                GeometryErrorCode.INVALID_FACE,
                f"Face {face_name} is not in the cycle for slice {self._slice_name}"
            )

        # Use cache manager from layout
        cache_key = ("create_slice_index_computer", (face_name,))
        cache = self._cache_manager.get(cache_key, object)  # type: ignore[arg-type]
        #cluade: lets get rid of the cast !!!
        return cast(CenterToSlice, cache.compute(compute))

    def create_walking_info_unit(self) -> "CubeWalkingInfoUnit":
        """
        Create SIZE-INDEPENDENT walking info for this slice.

        See SliceLayout protocol docstring for full documentation.
        """
        import random
        from cube.domain.geometric.cube_walking import CubeWalkingInfoUnit, FaceWalkingInfoUnit
        from cube.domain.model.Edge import Edge
        from cube.domain.model.Face import Face

        if self._cube_layout is None:
            raise RuntimeError(
                "Cannot create walking info unit without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> CubeWalkingInfoUnit:
            assert self._cube_layout is not None
            internal_3x3 = self._cube_layout._cube
            slice_name = self._slice_name

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

            # Determine if current_index needs to be inverted based on alignment with rotation face
            if not self.does_slice_of_face_start_with_face(current_face.name):
                pass

            face_infos: list[FaceWalkingInfoUnit] = []

            from cube.domain.geometric._slice_walking_path import create_walking_info

            for _ in range(4):

                # Get the rotating edge (edge between current_face and rotation_face)
                rotating_edge = current_face.get_shared_edge(rotation_face)
                assert rotating_edge is not None, f"No shared edge between {current_face.name} and {rotation_face.name}"

                # Use centralized logic from _slice_walking_path.py
                # create_walking_info returns size-independent FaceWalkingInfoUnit
                face_info = create_walking_info(
                    face=current_face,
                    entry_edge_position=current_face.get_edge_position(current_edge),
                    rotating_edge_position=current_face.get_edge_position(rotating_edge),
                    face_name=current_face.name,
                    edge_name=current_edge.name,
                )
                face_infos.append(face_info)

                # Move to next face (except after the 4th)
                if len(face_infos) < 4:
                    next_face = current_edge.get_other_face(current_face)
                    next_edge: Edge = current_edge.opposite(next_face)

                    current_edge = next_edge
                    current_face = next_face

            return CubeWalkingInfoUnit(
                slice_name=slice_name,
                rotation_face=rotation_face_name,
                face_infos=tuple(face_infos),
            )

        # Use cache manager from layout - cache by slice_name only (size-independent!)
        cache_key = ("SliceLayout.create_walking_info_unit", self._slice_name)
        cache = self._cube_layout.cache_manager.get(cache_key, CubeWalkingInfoUnit)
        return cache.compute(compute)

