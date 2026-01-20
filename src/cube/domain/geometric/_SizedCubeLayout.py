"""
_SizedCubeLayout - Size-dependent cube geometry implementation.

This class implements the SizedCubeLayout protocol, providing coordinate
calculations that require knowledge of cube size (n_slices).

See GEOMETRY_LAYERS.md for the two-layer architecture:
- Layout layer (CubeLayout): size-independent topology
- Sized layout layer (SizedCubeLayout): size-dependent coordinates

Usage:
    cube = Cube(5)
    walking_info = cube.sized_layout.create_walking_info(SliceName.M)
    positions = list(cube.sized_layout.iterate_orthogonal_face_center_pieces(...))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from cube.domain.exceptions.GeometryError import GeometryError, GeometryErrorCode
from cube.domain.geometric.geometry_types import (
    CLGColRow, FaceOrthogonalEdgesInfo, Point, PointComputer, ReversePointComputer
)
from cube.domain.geometric.sized_cube_layout import SizedCubeLayout
from cube.domain.geometric.cube_walking import (
    CubeWalkingInfo, CubeWalkingInfoUnit, FaceWalkingInfo,
)
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.model.Edge import Edge
from cube.domain.model.SliceName import SliceName
from cube.utils.Cache import CacheManager

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.domain.model.Slice import Slice


class _SizedCubeLayout(SizedCubeLayout):
    """
    Size-dependent cube geometry calculations.

    This class implements the SizedCubeLayout protocol. It holds a reference
    to a Cube instance and provides methods that require n_slices for
    coordinate calculations.

    Attributes:
        _cube: The cube instance this geometry belongs to
        _cache_manager: Per-instance CacheManager for this SizedCubeLayout

    IMPORTANT - Cache Architecture:
        This class has its OWN CacheManager (_cache_manager), separate from CubeLayout.cache_manager.

        Why NOT use CubeLayout.cache_manager:
        - CubeLayout is shared across ALL cubes of the same size (singleton per n_slices)
        - _SizedCubeLayout is tied to a SPECIFIC Cube instance
        - CubeWalkingInfo contains Face and Edge objects from a specific cube
        - If we cached in CubeLayout, a cached CubeWalkingInfo would return
          Face/Edge objects from the WRONG cube instance!

        Example of the bug if using layout cache:
            cube1 = Cube(5)
            cube2 = Cube(5)  # Same size, shares CubeLayout with cube1
            info1 = cube1.sized_layout.create_walking_info(M)  # Cached in shared layout
            info2 = cube2.sized_layout.create_walking_info(M)  # Returns cached info1!
            # BUG: info2.face_infos[0].face is cube1's Face, not cube2's!

    See Also:
        SizedCubeLayout: The protocol this class implements
        CubeLayout: Size-independent layout queries (different layer)
        GEOMETRY_LAYERS.md: Architecture documentation
    """

    def __init__(self, cube: "Cube") -> None:
        """
        Create a SizedCubeLayout for the given cube.

        Args:
            cube: The cube instance (provides n_slices and face objects)
        """
        self._cube = cube
        # Per-instance CacheManager - NOT shared with other cubes!
        # See class docstring for why we can't use CubeLayout.cache_manager
        self._cache_manager: CacheManager = CacheManager.create(cube.config)

    def reset(self):
        # must free all objects when new cube is created !!!
        self._cache_manager.clear()


    def get_slice(self, slice_name: SliceName) -> "Slice":
        """
        Get the Slice object for the given slice name.

        Args:
            slice_name: Which slice to get (M, E, or S)

        Returns:
            The Slice object from the underlying cube
        """
        return self._cube.get_slice(slice_name)

    @property
    def n_slices(self) -> int:
        """Get the cube's n_slices (cube_size - 2)."""
        return self._cube.n_slices

    # =========================================================================
    # CubeGeometric Protocol Implementation
    # =========================================================================

    def create_walking_info(self, slice_name: SliceName) -> CubeWalkingInfo:
        """
        Create SIZE-DEPENDENT walking info for this slice on this cube.

        This method:
        1. Gets the size-independent unit walking info from SliceLayout (cached there)
        2. Converts it to actual coordinates for this cube's n_slices
        3. Caches the result in this instance's CacheManager (NOT in layout cache!)

        IMPORTANT: Uses per-instance _cache_manager, NOT CubeLayout.cache_manager!
        See class docstring for why layout cache is invalid here.

        Args:
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            CubeWalkingInfo with actual coordinates for this cube size
        """
        cube: Cube = self._cube
        n_slices = cube.n_slices

        def compute() -> CubeWalkingInfo:
            # Get size-independent unit walking info from SliceLayout (cached there)
            slice_layout = cube.layout.get_slice(slice_name)
            unit: CubeWalkingInfoUnit = slice_layout.create_walking_info_unit()

            sized_faces = []

            for uf in unit.face_infos:
                face: Face = cube.face(uf.face_name)
                edge: Edge = cube.edge(uf.edge_name)
                reference_point: Point = uf.get_reference_point(n_slices)
                compute_fn: PointComputer = uf.get_compute(n_slices)
                compute_reverse_fn: ReversePointComputer = uf.get_compute_reverse(n_slices)

                slice_index_to_entry_edge_slice_index_fn = uf.get_compute_slice_index_to_entry_edge_slice_index(n_slices)

                sized_face_info: FaceWalkingInfo = FaceWalkingInfo(
                    face=face,
                    edge=edge,
                    reference_point=reference_point,
                    n_slices=n_slices,
                    slice_to_center=compute_fn,
                    center_to_slice=compute_reverse_fn,
                    slice_index_to_entry_edge_slice_index_fn=slice_index_to_entry_edge_slice_index_fn
                )

                sized_faces.append(sized_face_info)

            return CubeWalkingInfo(
                slice_name=slice_name,
                rotation_face=unit.rotation_face,
                n_slices=n_slices,
                face_infos=tuple(sized_faces)
            )

        # Cache using per-instance CacheManager (NOT layout cache!)
        cache = self._cache_manager.get(("SizedCubeLayout.create_walking_info", slice_name), CubeWalkingInfo)
        return cache.compute(compute)

    def iterate_orthogonal_face_center_pieces(
        self,
        layer1_face: "Face",
        side_face: "Face",
        layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """

        There is a dpulication with what is done in cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._is_slice_centers_solved
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

        # Determine which slice type (M/E/S) is parallel to L1
        # A slice is parallel to a face if that face is NOT on the slice's axis
        slice_name = cube.layout.get_slice_name_parallel_to_face(l1_name)
        reference_face = cube.layout.get_slice_rotation_face(slice_name)

        # Convert layer_slice_index to physical slice index
        if l1_name == reference_face:
            physical_slice_index = layer_slice_index
        else:
            physical_slice_index = n_slices - 1 - layer_slice_index

        # Does this slice cut rows or columns on side_face?
        slice_layout = cube.layout.get_slice(slice_name)
        cut_type = slice_layout.does_slice_cut_rows_or_columns(side_name)

        # Does slice index align with face LTR coordinates?
        starts_with_face = slice_layout.does_slice_of_face_start_with_face(side_name)

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

    def get_orthogonal_index_by_distance_from_face(
            self,
            face: "Face",
            base_face: "Face",
            row_distance_from_base: int
    ) -> FaceOrthogonalEdgesInfo:
        """
        Find row/column index and orthogonal edges based on distance from a reference face.

        See SizedCubeLayout protocol for full documentation.
        """
        from cube.domain.model._elements import EdgePosition

        n_slices = self.n_slices

        # Validate distance
        if not (0 <= row_distance_from_base < n_slices):
            raise ValueError(
                f"row_distance_from_base={row_distance_from_base} out of range [0, {n_slices - 1}]"
            )

        # Get the shared edge between face and base_face
        shared_edge = face.find_shared_edge(base_face)
        if shared_edge is None:
            raise GeometryError(
                GeometryErrorCode.OPPOSITE_FACES,
                f"{face.name} and {base_face.name} don't share an edge (they are opposite faces)"
            )

        # Get the position of the shared edge on face
        shared_position = shared_edge.get_position_on_face(face)

        # Determine row/col index and orthogonal edges based on shared edge position
        # Note: LTR coordinate system has row 0 at BOTTOM, row n-1 at TOP
        if shared_position == EdgePosition.BOTTOM:
            # base_face is below → distance 0 = bottom row (row 0 in LTR)
            row_or_col = row_distance_from_base
            edge_one = face.edge_left
            edge_two = face.edge_right
        elif shared_position == EdgePosition.TOP:
            # base_face is above → distance 0 = top row (row n-1 in LTR)
            row_or_col = n_slices - 1 - row_distance_from_base
            edge_one = face.edge_left
            edge_two = face.edge_right
        elif shared_position == EdgePosition.LEFT:
            # base_face is to the left → distance 0 = left col (0)
            row_or_col = row_distance_from_base
            edge_one = face.edge_top
            edge_two = face.edge_bottom
        else:  # EdgePosition.RIGHT
            # base_face is to the right → distance 0 = right col (n_slices-1)
            row_or_col = n_slices - 1 - row_distance_from_base
            edge_one = face.edge_top
            edge_two = face.edge_bottom

        # Calculate edge indices using the edge's coordinate translation
        # For horizontal shared edges (TOP/BOTTOM), we use the row index
        # For vertical shared edges (LEFT/RIGHT), we use the column index
        index_on_edge_one = edge_one.get_edge_slice_index_from_face_ltr_index(face, row_or_col)
        index_on_edge_two = edge_two.get_edge_slice_index_from_face_ltr_index(face, row_or_col)

        return FaceOrthogonalEdgesInfo(
            row_or_col=row_or_col,
            edge_one=edge_one,
            edge_two=edge_two,
            index_on_edge_one=index_on_edge_one,
            index_on_edge_two=index_on_edge_two
        )


__all__ = ['_SizedCubeLayout']
