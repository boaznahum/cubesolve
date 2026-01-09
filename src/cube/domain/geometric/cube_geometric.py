"""
CubeGeometric Protocol - Size-dependent cube geometry calculations.

Unlike CubeLayout/SliceLayout which answer pure geometric questions independent
of cube size (e.g., "which faces are adjacent?", "does slice cut rows or columns?"),
CubeGeometric methods require knowledge of cube size (n_slices) for coordinate
calculations.

Key difference:
    - CubeLayout: "Is F adjacent to U?" → Yes (always, for any cube size)
    - CubeGeometric: "What's the reference point for slice M on face F?" → (0, 0) for 3x3, but depends on n_slices

Usage:
    cube = Cube(5)

    # Size-independent (via layout):
    cube.layout.is_adjacent(FaceName.F, FaceName.U)

    # Size-dependent (via geometric):
    cube.geometric.derive_transform_type(FaceName.F, FaceName.U)
    cube.geometric.create_walking_info(SliceName.M)

See Also:
    - CubeLayout: Size-independent face/edge relationships
    - SliceLayout: Size-independent slice/face relationships
    - _CubeGeometric: Private implementation of this protocol
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol

if TYPE_CHECKING:
    from cube.domain.geometric.cube_walking import CubeWalkingInfo
    from cube.domain.geometric.Face2FaceTranslator import TransformType
    from cube.domain.geometric.FRotation import FUnitRotation
    from cube.domain.model.Face import Face
    from cube.domain.model.FaceName import FaceName
    from cube.domain.model.SliceName import SliceName


class CubeGeometric(Protocol):
    """
    Protocol for cube geometry calculations that depend on cube size.

    These methods require knowledge of n_slices (cube_size - 2) for coordinate
    calculations. An instance of CubeGeometric is stored in each Cube and
    accessed via cube.geometric.

    Methods:
        derive_transform_type: Get coordinate transform between two faces
        create_walking_info: Get slice traversal info for all 4 faces
        iterate_orthogonal_face_center_pieces: Yield positions for a layer slice
        translate_target_from_source: Get unit rotation between faces
    """

    def derive_transform_type(
        self,
        source: "FaceName",
        target: "FaceName",
    ) -> "TransformType | None":
        """
        Derive the TransformType for a (source, target) face pair.

        Computes how coordinates transform when content moves from source face
        to target face via a whole-cube rotation (X, Y, or Z).

        Args:
            source: The face where content originates
            target: The face where content arrives

        Returns:
            TransformType indicating how (row, col) coordinates change:
            - IDENTITY: (r, c) -> (r, c)
            - ROT_90_CW: (r, c) -> (inv(c), r)
            - ROT_90_CCW: (r, c) -> (c, inv(r))
            - ROT_180: (r, c) -> (inv(r), inv(c))
            - None: if faces are same or opposite
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
