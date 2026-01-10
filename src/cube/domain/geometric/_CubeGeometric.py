"""
_CubeGeometric - Size-dependent cube geometry implementation.

This class implements the CubeGeometric protocol, providing coordinate
calculations that require knowledge of cube size (n_slices).

See GEOMETRY_LAYERS.md for the two-layer architecture:
- Layout layer (CubeLayout): size-independent topology
- Geometric layer (CubeGeometric): size-dependent coordinates

Usage:
    cube = Cube(5)
    walking_info = cube.geometric.create_walking_info(SliceName.M)
    positions = list(cube.geometric.iterate_orthogonal_face_center_pieces(...))
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator

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
    from cube.domain.geometric.Face2FaceTranslator import TransformType


class _CubeGeometric:
    """
    Size-dependent cube geometry calculations.

    This class implements the CubeGeometric protocol. It holds a reference
    to a Cube instance and provides methods that require n_slices for
    coordinate calculations.

    Attributes:
        _cube: The cube instance this geometry belongs to

    See Also:
        CubeGeometric: The protocol this class implements
        CubeLayout: Size-independent layout queries (different layer)
        GEOMETRY_LAYERS.md: Architecture documentation
    """

    def __init__(self, cube: "Cube") -> None:
        """
        Create a CubeGeometric for the given cube.

        Args:
            cube: The cube instance (provides n_slices and face objects)
        """
        self._cube = cube

    @property
    def n_slices(self) -> int:
        """Get the cube's n_slices (cube_size - 2)."""
        return self._cube.n_slices

    # =========================================================================
    # CubeGeometric Protocol Implementation
    # =========================================================================

    def derive_transform_type(
        self,
        source: FaceName,
        target: FaceName,
    ) -> "TransformType | None":
        """
        Derive the TransformType for a (source, target) face pair.

        Delegates to CubeLayout.derive_transform_type() since the transform
        type itself is size-independent (only the coordinate values change).

        Args:
            source: The face where content originates
            target: The face where content arrives

        Returns:
            TransformType or None if faces are same/opposite
        """
        return self._cube.layout.derive_transform_type(source, target)

    def create_walking_info(self, slice_name: SliceName) -> CubeWalkingInfo:
        """
        cluade: fuck he promise tomoe it to move cube layout
        Create walking info by traversing the 4 faces of a slice.

        Walks through all 4 faces, tracking where the reference point
        (slice_index=0, slot=0) lands on each face. Returns face_infos
        in CONTENT FLOW order (direction content moves during rotation).

        Slice rotation reference faces:
        - M rotates like L: F → U → B → D
        - E rotates like D: R → B → L → F
        - S rotates like F: U → R → D → L

        Args:
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            CubeWalkingInfo with reference points and transform functions
        """
        cube = self._cube
        n_slices = cube.n_slices

        def inv(x: int) -> int:
            return n_slices - 1 - x

        # Derive starting face and edge from rotation face
        from cube.domain.geometric.slice_layout import _SliceLayout
        slice_layout = _SliceLayout(slice_name)
        rotation_face_name = slice_layout.get_face_name()
        rotation_face = cube.face(rotation_face_name)

        # Get edges in clockwise order around the rotation face
        rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        cycle_faces_ordered = [edge.get_other_face(rotation_face) for edge in rotation_edges]

        # Pick first two consecutive faces (random starting point in the cycle)
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
        shared_with_rotating: Edge = current_face.get_shared_edge(rotation_face)

        if current_face.is_bottom_or_top(current_edge):
            # Vertical slice - check if left edge aligns with rotation face
            if current_face.edge_left is not shared_with_rotating:
                current_index = inv(current_index)
        else:
            # Horizontal slice - check if bottom edge aligns with rotation face
            if current_face.edge_bottom is not shared_with_rotating:
                current_index = inv(current_index)

        # DEBUG logging
        _log = cube.sp.logger
        _dbg = cube.config.solver_debug
        if _log.is_debug(_dbg):
            _log.debug(_dbg, f"\n=== {slice_name.name} slice ===")
            _log.debug(_dbg, f"Rotation face: {rotation_face_name.name}")
            _log.debug(_dbg, f"Cycle faces: {[f.name.name for f in cycle_faces_ordered]}")
            _log.debug(_dbg, f"First two faces: {first_face.name.name}, {second_face.name.name}")
            _log.debug(_dbg, f"Shared edge = Starting edge: {current_edge.name}")
            _log.debug(_dbg, f"Starting face: {current_face.name.name}")
            _log.debug(_dbg, f"Starting slice index: {current_index}, {slot}")

        face_infos: list[FaceWalkingInfo] = []

        # Point computation functions - 8 combinations of (horizontal, slot_inverted, index_inverted)
        def _compute_h_si_ii(si: int, sl: int) -> Point:
            return (inv(sl), inv(si))

        def _compute_h_si(si: int, sl: int) -> Point:
            return (inv(sl), si)

        def _compute_h_ii(si: int, sl: int) -> Point:
            return (sl, inv(si))

        def _compute_h(si: int, sl: int) -> Point:
            return (sl, si)

        def _compute_v_si_ii(si: int, sl: int) -> Point:
            return (inv(si), inv(sl))

        def _compute_v_si(si: int, sl: int) -> Point:
            return (si, inv(sl))

        def _compute_v_ii(si: int, sl: int) -> Point:
            return (inv(si), sl)

        def _compute_v(si: int, sl: int) -> Point:
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

            # DEBUG logging
            if _log.is_debug(_dbg):
                if current_edge == current_face.edge_top:
                    edge_pos = "top"
                elif current_edge == current_face.edge_bottom:
                    edge_pos = "bottom"
                elif current_edge == current_face.edge_left:
                    edge_pos = "left"
                elif current_edge == current_face.edge_right:
                    edge_pos = "right"
                else:
                    edge_pos = "???"
                _log.debug(_dbg, f"7. Iteration {iteration}: face={current_face.name.name}, "
                          f"edge={current_edge.name} (position={edge_pos}), "
                          f"is_horizontal={is_horizontal}, is_slot_inverted={is_slot_inverted}, "
                          f"is_index_inverted={is_index_inverted}, current_index={current_index}, "
                          f"slot={slot}, reference_point={reference_point}")

            # Select precomputed point function based on edge properties
            if is_horizontal and is_slot_inverted and is_index_inverted:
                compute = _compute_h_si_ii
            elif is_horizontal and is_slot_inverted and not is_index_inverted:
                compute = _compute_h_si
            elif is_horizontal and not is_slot_inverted and is_index_inverted:
                compute = _compute_h_ii
            elif is_horizontal and not is_slot_inverted and not is_index_inverted:
                compute = _compute_h
            elif not is_horizontal and is_slot_inverted and is_index_inverted:
                compute = _compute_v_si_ii
            elif not is_horizontal and is_slot_inverted and not is_index_inverted:
                compute = _compute_v_si
            elif not is_horizontal and not is_slot_inverted and is_index_inverted:
                compute = _compute_v_ii
            else:
                compute = _compute_v

            face_infos.append(FaceWalkingInfo(
                face=current_face,
                edge=current_edge,
                reference_point=reference_point,
                n_slices=n_slices,
                _compute=compute
            ))

            # Move to next face (except after the 4th)
            if len(face_infos) < 4:
                next_face = current_edge.get_other_face(current_face)
                next_edge: Edge = current_edge.opposite(next_face)

                if _log.is_debug(_dbg):
                    _log.debug(_dbg, f"   -> {current_edge.name} leads to {next_face.name.name}, "
                              f"opposite on {next_face.name.name} is {next_edge.name}")

                next_slice_index = current_edge.get_slice_index_from_ltr_index(
                    current_face, current_index
                )
                current_index = current_edge.get_ltr_index_from_slice_index(
                    next_face, next_slice_index
                )
                current_edge = next_edge
                current_face = next_face

        return CubeWalkingInfo(
            slice_name=slice_name,
            rotation_face=rotation_face_name,
            n_slices=n_slices,
            face_infos=tuple(face_infos)
        )

    def iterate_orthogonal_face_center_pieces(
        self,
        layer1_face: "Face",
        side_face: "Face",
        layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """
        Yield (row, col) positions on side_face for the given layer slice.

        A "layer slice" is a horizontal layer parallel to layer1_face (L1).
        Layer slice 0 is the one closest to L1.

        Args:
            layer1_face: The Layer 1 face (base layer)
            side_face: A face orthogonal to layer1_face
            layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

        Yields:
            (row, col) in LTR coordinates on side_face

        Raises:
            ValueError: if side_face is not orthogonal to layer1_face
        """
        cube = self._cube
        l1_name = layer1_face.name
        side_name = side_face.name

        if not cube.layout.is_adjacent(l1_name, side_name):
            raise ValueError(f"{side_name} is not adjacent to {l1_name}")

        n_slices = cube.n_slices

        # claude:more hard coded why hwy why , dont you under stand the mission in HARDCODED_ANALYSIS.md

        # Determine which slice type (M/E/S) is parallel to L1
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
        if l1_name == reference_face:
            physical_slice_index = layer_slice_index
        else:
            physical_slice_index = n_slices - 1 - layer_slice_index

        # Does this slice cut rows or columns on side_face?
        slice_layout = cube.layout.get_slice(slice_name)
        cut_type = slice_layout.does_slice_cut_rows_or_columns(side_name)

        # Does slice index align with face LTR coordinates?
        starts_with_face = self._does_slice_of_face_start_with_face(slice_name, side_name)

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

    def translate_target_from_source(
        self,
        source_face: "Face",
        target_face: "Face",
        source_coord: tuple[int, int],
        slice_name: SliceName,
    ) -> FUnitRotation:
        """
        Compute the unit rotation from source_face to target_face.

        Args:
            source_face: The face where content originates
            target_face: The face where content will appear
            source_coord: (row, col) position on source_face
            slice_name: Which slice (M, E, S) connects the faces

        Returns:
            FUnitRotation that transforms source coordinates to target

        Raises:
            ValueError: If source_face == target_face
            ValueError: If source_coord is out of bounds
        """
        if source_face is target_face:
            raise ValueError("Cannot translate from a face to itself")

        n_slices = source_face.center.n_slices
        row, col = source_coord
        if not (0 <= row < n_slices and 0 <= col < n_slices):
            raise ValueError(f"Coordinate {source_coord} out of bounds (n_slices={n_slices})")

        walk_info = self.create_walking_info(slice_name)
        return walk_info.get_transform(source_face, target_face)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _does_slice_of_face_start_with_face(slice_name: SliceName, face_name: FaceName) -> bool:
        """

        claude: yet another method you promise me to move to cube layout and is not docu,netd in HARDCODED_ANALYSIS.md
        Check if slice index 0 aligns with the face's natural coordinate origin.

        Each slice (M, E, S) has indices 0 to n_slices-1. Slice index 0 is always
        closest to the "reference face" for that slice type:
            - M[0] closest to L (M rotates like L)
            - E[0] closest to D (E rotates like D)
            - S[0] closest to F (S rotates like F)

        Returns:
            True  → slice[0] aligns with face's row/col 0 (natural start)
            False → slice[0] aligns with face's row/col (n_slices-1) (inverted)
        """
        if slice_name == SliceName.S:
            if face_name in [FaceName.L, FaceName.D]:
                return False  # S[1] is on L[last]
        elif slice_name == SliceName.M:
            if face_name in [FaceName.B]:
                return False

        return True

    @staticmethod
    def get_slice_for_faces(source: FaceName, target: FaceName) -> SliceName | None:
        """
        claude: is this method still needed ? whay ?
        Find which slice connects two faces.

        Derives slice faces on demand from _SLICE_ROTATION_FACE + _ADJACENT.

        Returns None if faces are the same or no slice connects them.

        Note: For opposite faces, this returns only the FIRST matching slice.
        Use get_all_slices_for_faces() to get ALL connecting slices.
        """
        from cube.domain.geometric.cube_layout import _SLICE_ROTATION_FACE, _ADJACENT

        # Iterate in SliceName enum order (S, M, E)
        # claude: more hadrd coded that need to rmoved all inforamtion is in cube layout
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            slice_faces = _ADJACENT[rotation_face]
            if source in slice_faces and target in slice_faces:
                return slice_name
        return None

    @staticmethod
    def get_all_slices_for_faces(source: FaceName, target: FaceName) -> list[SliceName]:
        """

        claude: this method belong to layout it doest depended on cube size !!!! read the ruls, you lied to me see HARDCODED_ANALYSIS.md
        Find ALL slices that connect two faces.

        For adjacent faces: returns 1 slice
        For opposite faces: returns 2 slices

        Returns empty list if faces are the same.
        """
        from cube.domain.geometric.cube_layout import _SLICE_ROTATION_FACE, _ADJACENT

        if source == target:
            return []

        result: list[SliceName] = []
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            slice_faces = _ADJACENT[rotation_face]
            if source in slice_faces and target in slice_faces:
                result.append(slice_name)
        return result


__all__ = ['_CubeGeometric']
