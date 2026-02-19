"""
SizedCubeLayout Protocol - Size-dependent cube geometry calculations.

Unlike CubeLayout/SliceLayout which answer pure geometric questions independent
of cube size (e.g., "which faces are adjacent?", "does slice cut rows or columns?"),
SizedCubeLayout methods require knowledge of cube size (n_slices) for coordinate
calculations.

Key difference:
    - CubeLayout: "Is F adjacent to U?" → Yes (always, for any cube size)
    - SizedCubeLayout: "What's the reference point for slice M on face F?" → (0, 0) for 3x3, but depends on n_slices

Usage:
    cube = Cube(5)

    # Size-independent (via layout):
    cube.layout.is_adjacent(FaceName.F, FaceName.U)

    # Size-dependent (via sized_layout):
    cube.sized_layout.create_walking_info(SliceName.M)

See Also:
    - CubeLayout: Size-independent face/edge relationships
    - SliceLayout: Size-independent slice/face relationships
    - _SizedCubeLayout: Private implementation of this protocol
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol

from cube.domain.geometric.geometry_types import FaceOrthogonalEdgesInfo

if TYPE_CHECKING:
    from cube.domain.geometric.cube_walking import CubeWalkingInfo
    from cube.domain.geometric.FRotation import FUnitRotation
    from cube.domain.model._elements import EdgePosition
    from cube.domain.model._part import EdgeName
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face
    from cube.domain.model.PartSlice import EdgeWing
    from cube.domain.model.Slice import Slice
    from cube.domain.model.SliceName import SliceName


class SizedCubeLayout(Protocol):
    """
    Protocol for cube geometry calculations that depend on cube size.

    These methods require knowledge of n_slices (cube_size - 2) for coordinate
    calculations. An instance of SizedCubeLayout is stored in each Cube and
    accessed via cube.sized_layout.

    Methods:
        create_walking_info: Get slice traversal info for all 4 faces
        iterate_orthogonal_face_center_pieces: Yield positions for a layer slice
        translate_target_from_source: Get unit rotation between faces
    """

    def reset(self):
        ...

    def get_slice(self, slice_name: SliceName) -> "Slice":
        """
        Get the Slice object for the given slice name.

        Args:
            slice_name: Which slice to get (M, E, or S)

        Returns:
            The Slice object from the underlying cube
        """
        ...

    def create_walking_info(self, slice_name: "SliceName") -> "CubeWalkingInfo":
        """
        Create walking info by traversing the 4 faces of a slice.

        Walks through all 4 faces, tracking where the reference point
        (slice_index=0, slot=0) lands on each face.

        Args:
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            CubeWalkingInfo with reference points and transform functions
        """
        ...

    def iterate_orthogonal_face_center_pieces(
        self,
        layer1_face: "Face",
        side_face: "Face",
        layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """
        Yield (row, col) positions on side_face for the given layer slice.

        Args:
            layer1_face: The Layer 1 face (base layer)
            side_face: A face orthogonal to layer1_face
            layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

        Yields:
            (row, col) in LTR coordinates on side_face
        """
        ...

    def translate_target_from_source(
        self,
        source_face: "Face",
        target_face: "Face",
        source_coord: tuple[int, int],
        slice_name: "SliceName",
    ) -> "FUnitRotation":
        """
        Compute the unit rotation from source_face to target_face.

        Args:
            source_face: The face where content originates
            target_face: The face where content will appear
            source_coord: (row, col) position on source_face
            slice_name: Which slice (M, E, S) connects the faces

        Returns:
            FUnitRotation that transforms source coordinates to target
        """
        ...

    def get_orthogonal_index_by_distance_from_face(
            self,
            face: "Face",
            base_face: "Face",
            row_distance_from_base: int
    ) -> FaceOrthogonalEdgesInfo:
        """
        Find row/column index and orthogonal edges based on distance from a reference face.

        This method is essential for layer-by-layer solving where we process rows/columns
        of a face starting from the layer closest to a solved layer (e.g., L1/white face).

        Concept - Row Distance from Base Face:
        ======================================
        The `row_distance_from_base` is NOT a row index in the face's LTR system.
        It represents the distance from the shared edge with base_face:
        - Distance 0 = row/column closest to base_face (touching the shared edge)
        - Distance 1 = next row/column away from base_face
        - Distance n-1 = row/column furthest from base_face (touching opposite edge)

        This abstraction is orientation-independent: regardless of which face is the
        base_face, distance 0 always means "closest to base_face".

        Visual Examples (5x5 cube, looking at Front face from outside):
        ================================================================

        Case 1: base_face = Down (L1 at bottom)
        ----------------------------------------
        Note: LTR coordinate system has row 0 at BOTTOM, row n-1 at TOP

                    ┌─────────────────────────┐
                    │  row 4  (distance 4)    │  ← furthest from Down (top in LTR)
                    ├─────────────────────────┤
                    │  row 3  (distance 3)    │
            Left    ├─────────────────────────┤    Right
            Edge    │  row 2  (distance 2)    │    Edge
                    ├─────────────────────────┤
                    │  row 1  (distance 1)    │
                    ├─────────────────────────┤
                    │  row 0  (distance 0)    │  ← closest to Down (bottom in LTR)
                    └─────────────────────────┘
                              Down (base_face)

            row_distance_from_base=0 → returns (row=0, edge_left, edge_right, ...)
            row_distance_from_base=2 → returns (row=2, edge_left, edge_right, ...)

        Case 2: base_face = Up (L1 at top)
        -----------------------------------
                              Up (base_face)
                    ┌─────────────────────────┐
                    │  row 4  (distance 0)    │  ← closest to Up (top in LTR)
                    ├─────────────────────────┤
                    │  row 3  (distance 1)    │
            Left    ├─────────────────────────┤    Right
            Edge    │  row 2  (distance 2)    │    Edge
                    ├─────────────────────────┤
                    │  row 1  (distance 3)    │
                    ├─────────────────────────┤
                    │  row 0  (distance 4)    │  ← furthest from Up (bottom in LTR)
                    └─────────────────────────┘
                              Down

            row_distance_from_base=0 → returns (row=4, edge_left, edge_right, ...)
            row_distance_from_base=2 → returns (row=2, edge_left, edge_right, ...)

        Case 3: base_face = Left (horizontal solving)
        ----------------------------------------------
                    ┌───┬───┬───┬───┬───┐
                    │   │   │   │   │   │  col0 col1 col2 col3 col4
                    │   │   │   │   │   │   ↑    ↑    ↑    ↑    ↑
            Left    │   │   │   │   │   │  d=0  d=1  d=2  d=3  d=4
          (base)    │   │   │   │   │   │
                    │   │   │   │   │   │
                    └───┴───┴───┴───┴───┘
                          Top Edge
                          Bottom Edge

            row_distance_from_base=0 → returns (col=0, edge_top, edge_bottom, ...)
            row_distance_from_base=2 → returns (col=2, edge_top, edge_bottom, ...)

        Case 4: base_face = Right
        --------------------------
                    ┌───┬───┬───┬───┬───┐
                    │   │   │   │   │   │  col0 col1 col2 col3 col4
                    │   │   │   │   │   │   ↑    ↑    ↑    ↑    ↑
                    │   │   │   │   │   │  d=4  d=3  d=2  d=1  d=0
                    │   │   │   │   │   │                        Right
                    │   │   │   │   │   │                       (base)
                    └───┴───┴───┴───┴───┘

            row_distance_from_base=0 → returns (col=4, edge_top, edge_bottom, ...)
            row_distance_from_base=2 → returns (col=2, edge_top, edge_bottom, ...)

        Return Values:
        ==============
        Returns an FaceOrthogonalEdgesInfo dataclass with:
        - row_or_col (int): The row or column index in face's LTR coordinate system
           - Row index if base_face is above/below (shared edge is horizontal)
           - Column index if base_face is left/right (shared edge is vertical)

        - edge_one (Edge): First orthogonal edge (perpendicular to shared edge)
           - Left edge if base is top/bottom
           - Top edge if base is left/right

        - edge_two (Edge): Second orthogonal edge (perpendicular to shared edge)
           - Right edge if base is top/bottom
           - Bottom edge if base is left/right

        - index_on_edge_one (int): Index in edge_one's internal coordinate system
           (use edge.get_slice(index) to access the actual slice)

        - index_on_edge_two (int): Index in edge_two's internal coordinate system

        The edge indices are computed using get_edge_slice_index_from_face_ltr_index(),
        which translates the face's LTR row/column to each edge's internal system.

        Args:
            face: The face to get row/column information from
            base_face: The reference face (must share an edge with face)
            row_distance_from_base: Distance from base_face (0 = closest, n-1 = furthest)

        Returns:
            FaceOrthogonalEdgesInfo with row/col index, edges, and edge indices

        Raises:
            ValueError: If face and base_face don't share an edge (are opposite faces)
            ValueError: If row_distance_from_base is out of range [0, n_slices-1]

        Example:
            # Solving Front face row by row, starting from Down (L1)
            for distance in range(cube.n_slices):
                row, left_edge, right_edge, left_idx, right_idx = (
                    cube.sized_layout.get_orthogonal_index_by_distance_from_face(
                        cube.front, cube.down, distance
                    )
                )
                # Process row on front face, with access to edge slices
                # left_edge.get_slice(left_idx) and right_edge.get_slice(right_idx)
                # correspond to the same horizontal row on the front face
        """
        ...

    @staticmethod
    def sorted_edge_key(a: "EdgePosition", b: "EdgePosition") -> tuple["EdgePosition", "EdgePosition"]:
        """Create a canonical sorted key for edge pairs (avoids duplicate entries)."""
        ...

    def map_wing_face_ltr_index_by_name(self, from_edge_name: "EdgeName",
                                        to_edge_name: "EdgeName", face_ltr_index: int) -> int:
        """
        Map wing LTR index from one edge to another on the same face.

        The wing ltr index is the ltr index on the face, not the wing index.

        Both edges must be on the same face. For non-adjacent edges,
        chains through intermediate edges.

        Args:
            from_edge_name: Source edge (e.g., EdgeName.FL, FU, FR, FD)
            to_edge_name: Target edge (e.g., EdgeName.FL, FU, FR, FD)
            face_ltr_index: LTR index on source edge

        Returns:
            Corresponding LTR index on target edge
        """
        ...

    def map_wing_face_ltr_index_by_edge_position(self, from_position: "EdgePosition",
                                                  to_position: "EdgePosition", index: int) -> int:
        """
        Map wing LTR index from one edge position to another on the same face.

        The wing ltr index is the ltr index on the face, not the wing index.

        Both edges must be on the same face. For non-adjacent edges,
        chains through intermediate edges.

        Args:
            from_position: Source edge position (EdgePosition.LEFT, TOP, RIGHT, BOTTOM)
            to_position: Target edge position
            index: LTR index on source edge

        Returns:
            Corresponding LTR index on target edge
        """
        ...

    def map_wing_index_by_name(self, from_edge_name: "EdgeName",
                               to_edge_name: "EdgeName", wing_index: int) -> int:
        """
        Map wing internal index from one edge to another on the same face.

        Given the internal wing index on the source edge, returns the corresponding
        internal wing index on the target edge, assuming the source edge is rotated
        into the target edge position.

        Both edges must share a common face.

        Args:
            from_edge_name: Source edge name (e.g., EdgeName.FL, FU, FR, FD)
            to_edge_name: Target edge name
            wing_index: Internal wing index on source edge (0-based)

        Returns:
            Corresponding internal wing index on target edge
        """
        ...

    def map_wing_index_by_wing(self, from_wing: "EdgeWing", to_edge: "Edge") -> int:
        """
        Map wing internal index from a wing to another edge on the same face.

        Convenience method that extracts edge names from the wing and edge objects.

        Args:
            from_wing: Source wing
            to_edge: Target edge (must share a face with from_wing's edge)

        Returns:
            Corresponding internal wing index on target edge
        """
        ...

    def map_wing_index_to_edge_name(self, from_wing: "EdgeWing", to_edge_name: "EdgeName") -> int:
        """
        Map wing internal index from a wing to another edge by name.

        Convenience method that extracts edge name from the wing object.

        Args:
            from_wing: Source wing
            to_edge_name: Target edge name

        Returns:
            Corresponding internal wing index on target edge
        """
        ...
