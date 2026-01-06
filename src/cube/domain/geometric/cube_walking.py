"""
Cube Walking - Data structures for traversing cube faces along a slice.

This module provides data structures that capture the traversal of 4 faces
that a slice (M, E, or S) passes through. The key insight is tracking where
a "virtual point (0,0)" lands on each face during the walk.

Related: Issue #55 - Replace hard-coded lookup tables with mathematical derivation

================================================================================
VIRTUAL POINT CONCEPT
================================================================================

The "virtual point (0,0)" is a reference point used to determine the coordinate
transformation between faces in a slice traversal.

We start from a reference edge on the first face with coordinates:
- slice_index = 0 (which slice)
- slot = 0 (position along the slice)

These map to (row, col) = (0, 0) on the first face (for bottom/left edge).
As we walk through faces, we track where this virtual (0,0) lands on each face.

From any two reference points, we can derive the rotation transform
(CW0=identity, CW1=90°, CW2=180°, CW3=270°) using FUnitRotation.of().

================================================================================
TRAVERSAL ORDER BY SLICE
================================================================================

Each slice passes through exactly 4 faces:
- M slice: F → U → B → D (parallel to L and R)
- E slice: R → B → L → F (parallel to U and D)
- S slice: U → R → D → L (parallel to F and B)

The starting face and edge for each slice:
- M: Front face, bottom edge
- E: Right face, left edge
- S: Up face, left edge

================================================================================
USAGE
================================================================================

# Create walking info ONCE (can be cached)
walk_info = CubeWalkingInfo.create(cube, SliceName.M)

# Get transform between any two faces
transform = walk_info.get_transform(face_f, face_u)

# Apply transform to translate points
sized_transform = transform.of_n_slices(n_slices)
new_row, new_col = sized_transform(row, col)

# Or use the convenience method
new_point = walk_info.translate_point(source_face, target_face, row, col)

================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.geometric.types import Point

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.cube_slice import SliceName
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face


@dataclass(frozen=True)
class FaceWalkingInfo:
    """
    Information about one face in a slice traversal.

    This captures where the virtual point (0,0) lands on this face,
    which is used to derive the rotation transform to/from other faces.

    It also stores enough information to compute points for ANY slice_index,
    not just slice_index=0. This allows the walking info to be cached and
    reused for all slice indices.

    Attributes:
        face: The Face object
        edge: The reference edge used during the walk (determines orientation)
        reference_point: Where virtual (0,0) lands on this face in LTR coordinates.
                        This is the key data for computing transforms.
        local_slice_index: The translated slice_index for virtual (0,0) on this face.
                          If 0, slice indices are NOT inverted. If n_slices-1, they ARE inverted.
        n_slices: Total number of slices (for inversion calculations)

    The reference_point depends on:
    - Edge type (top/bottom = horizontal, left/right = vertical)
    - Edge side (top/right edges invert the slot coordinate)

    Computing points for arbitrary slice_index:
    - Use get_local_slice_index() to translate from start slice_index to this face's index
    - Use compute_point() to get (row, col) for any (slice_index, slot)

    Example:
        For M slice starting at Front/bottom edge:
        - Front: reference_point = (0, 0), local_slice_index = 0
        - Up:    reference_point = (0, 0), local_slice_index = 0
        - Back:  reference_point = (2, 0), local_slice_index = 0 (but slot inverted)
        - Down:  reference_point = (2, 0), local_slice_index = 0 (but slot inverted)
    """

    face: "Face"
    edge: "Edge"
    reference_point: Point
    local_slice_index: int
    n_slices: int

    @property
    def is_horizontal_edge(self) -> bool:
        """True if edge is top or bottom (slice cuts columns)."""
        return self.face.is_bottom_or_top(self.edge)

    @property
    def is_slot_inverted(self) -> bool:
        """True if slot coordinate is inverted (top or right edge)."""
        if self.is_horizontal_edge:
            return self.face.is_top_edge(self.edge)
        else:
            return self.face.is_right_edge(self.edge)

    @property
    def is_index_inverted(self) -> bool:
        """True if slice_index is inverted relative to start face."""
        # If local_slice_index for virtual 0 is non-zero, the index is inverted
        return self.local_slice_index != 0

    def _inv(self, x: int) -> int:
        """Invert index: n_slices - 1 - x."""
        return self.n_slices - 1 - x

    def get_local_slice_index(self, start_slice_index: int) -> int:
        """
        Convert a starting slice_index to this face's local slice index.

        Args:
            start_slice_index: The slice index on the first face (0 to n_slices-1)

        Returns:
            The corresponding slice index on this face
        """
        if self.is_index_inverted:
            return self._inv(start_slice_index)
        return start_slice_index

    def compute_point(self, start_slice_index: int, slot: int) -> Point:
        """
        Compute (row, col) for a given slice_index and slot position.

        This is the key method for computing points on this face for any
        slice_index, using the cached edge orientation information.

        Args:
            start_slice_index: The slice index on the FIRST face (0 to n_slices-1)
            slot: Position along the slice (0 to n_slices-1)

        Returns:
            (row, col) in LTR coordinates on this face

        The mapping depends on edge type:
        - Horizontal edge (top/bottom): slice cuts columns
          - Bottom: (slot, local_index)
          - Top: (inv(slot), local_index)
        - Vertical edge (left/right): slice cuts rows
          - Left: (local_index, slot)
          - Right: (local_index, inv(slot))
        """
        local_index = self.get_local_slice_index(start_slice_index)
        slot_value = self._inv(slot) if self.is_slot_inverted else slot

        if self.is_horizontal_edge:
            # Slice cuts columns - slot varies row
            return (slot_value, local_index)
        else:
            # Slice cuts rows - slot varies column
            return (local_index, slot_value)

    def iterate_points(self, start_slice_index: int) -> Iterator[Point]:
        """
        Iterate over all (row, col) positions along a slice on this face.

        Args:
            start_slice_index: The slice index on the FIRST face

        Yields:
            (row, col) for slot 0, 1, ..., n_slices-1
        """
        for slot in range(self.n_slices):
            yield self.compute_point(start_slice_index, slot)


@dataclass(frozen=True)
class CubeWalkingInfo:
    """
    Complete information about walking a slice through all 4 faces.

    This captures the traversal of a slice (M, E, or S) through the 4 faces
    it passes through. The face_infos are stored in traversal order AND
    can be looked up by Face object.

    The key data is the reference_point on each face - where virtual (0,0)
    lands. From any two reference points, we can derive the rotation
    transform between those faces.

    Attributes:
        slice_name: Which slice (M, E, or S)
        n_slices: Total number of slices (cube_size - 2), for sized transforms
        face_infos: Tuple of 4 FaceWalkingInfo in traversal order

    Traversal order by slice:
        M: Front → Up → Back → Down
        E: Right → Back → Left → Front
        S: Up → Right → Down → Left

    Usage:
        # Create once, cache for reuse
        walk_info = CubeWalkingInfo.create(cube, SliceName.M)

        # Get unit transform between faces
        transform = walk_info.get_transform(face_f, face_u)

        # Translate a point from one face to another
        new_point = walk_info.translate_point(face_f, face_u, row, col)
    """

    slice_name: "SliceName"
    n_slices: int
    face_infos: tuple[FaceWalkingInfo, ...]

    def __post_init__(self):
        """Validate that we have exactly 4 faces."""
        if len(self.face_infos) != 4:
            raise ValueError(f"CubeWalkingInfo requires exactly 4 faces, got {len(self.face_infos)}")

    def __iter__(self) -> Iterator[FaceWalkingInfo]:
        """Iterate over face infos in traversal order."""
        return iter(self.face_infos)

    def __len__(self) -> int:
        """Return number of faces (always 4)."""
        return len(self.face_infos)

    def __getitem__(self, index: int) -> FaceWalkingInfo:
        """Get face info by traversal index (0-3)."""
        return self.face_infos[index]

    def get_face_info(self, face: "Face") -> FaceWalkingInfo:
        """
        Look up FaceWalkingInfo by Face object.

        Args:
            face: The Face to look up

        Returns:
            FaceWalkingInfo for that face

        Raises:
            KeyError: If face is not in this traversal (e.g., parallel face)
        """
        for info in self.face_infos:
            if info.face is face:
                return info
        raise KeyError(f"Face {face.name} is not in this slice traversal")

    def has_face(self, face: "Face") -> bool:
        """Check if a face is part of this slice traversal."""
        return any(info.face is face for info in self.face_infos)

    @property
    def faces(self) -> tuple["Face", ...]:
        """Get tuple of faces in traversal order."""
        return tuple(info.face for info in self.face_infos)

    def get_transform(self, source_face: "Face", target_face: "Face") -> FUnitRotation:
        """
        Get the unit rotation transform from source_face to target_face.

        The transform is derived from the reference points on both faces.
        Given a point (r, c) on source_face, the corresponding point on
        target_face is: transform.of_n_slices(n_slices)(r, c)

        Args:
            source_face: The face to transform FROM
            target_face: The face to transform TO

        Returns:
            FUnitRotation that transforms coordinates from source to target

        Raises:
            KeyError: If either face is not in this traversal
        """
        source_info = self.get_face_info(source_face)
        target_info = self.get_face_info(target_face)

        return FUnitRotation.of(
            self.n_slices,
            source_info.reference_point,
            target_info.reference_point
        )

    def translate_point(
        self,
        source_face: "Face",
        target_face: "Face",
        row: int,
        col: int
    ) -> Point:
        """
        Translate a point from source_face to target_face.

        Convenience method that gets the transform and applies it.

        Args:
            source_face: The face the point is on
            target_face: The face to translate to
            row: Row coordinate on source_face (LTR)
            col: Column coordinate on source_face (LTR)

        Returns:
            (row, col) on target_face in LTR coordinates
        """
        transform = self.get_transform(source_face, target_face)
        return transform.of_n_slices(self.n_slices)(row, col)

    @staticmethod
    def create(cube: "Cube", slice_name: "SliceName") -> "CubeWalkingInfo":
        """
        Create walking info by traversing the 4 faces of a slice.

        This walks through all 4 faces starting from a reference edge,
        tracking where the virtual point (0,0) lands on each face.

        The walk uses:
        - slice_index = 0 (first slice)
        - slot = 0 (first position along slice)

        These map to reference_point on each face based on edge type.

        Args:
            cube: The cube instance
            slice_name: Which slice (M, E, S) to traverse

        Returns:
            CubeWalkingInfo with reference points for all 4 faces
        """
        from cube.domain.model.cube_slice import SliceName

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

        # Virtual point coordinates
        current_index: int = 0  # which slice
        slot: int = 0  # position along slice

        face_infos: list[FaceWalkingInfo] = []

        for _ in range(4):
            # Compute reference_point based on edge type
            if current_face.is_bottom_or_top(current_edge):
                # Horizontal edge: slice cuts columns
                if current_face.is_top_edge(current_edge):
                    reference_point: Point = (inv(slot), current_index)
                else:  # bottom edge
                    reference_point = (slot, current_index)
            else:
                # Vertical edge: slice cuts rows
                if current_face.is_right_edge(current_edge):
                    reference_point = (current_index, inv(slot))
                else:  # left edge
                    reference_point = (current_index, slot)

            face_infos.append(FaceWalkingInfo(
                face=current_face,
                edge=current_edge,
                reference_point=reference_point,
                local_slice_index=current_index,
                n_slices=n_slices
            ))

            # Move to next face (except after the 4th)
            if len(face_infos) < 4:
                next_edge = current_edge.opposite(current_face)
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
