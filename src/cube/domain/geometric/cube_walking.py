"""
Cube Walking - Data structures for traversing cube faces along a slice.

This module provides data structures that capture the traversal of 4 faces
that a slice (M, E, or S) passes through.

Related: Issue #55 - Replace hard-coded lookup tables with mathematical derivation

================================================================================
SLOT CONSISTENCY PRINCIPLE
================================================================================

When walking along a slice through 4 faces, the KEY insight is:

    If you travel along the slice keeping the same SLOT number,
    you reach corresponding positions on each face.

This is NOT about a specific point (0,0). Rather:
- Pick any slot number (0, 1, 2, ...)
- Follow that slot through all 4 faces
- The positions you visit are "corresponding" positions

Diagram - M slice, slot 0 (leftmost position on each face):

    ┌─────────┐
    │ Front   │     slot 0 is at (0, slice_idx) - bottom edge
    │    ↑    │
    └────┼────┘
         │
    ┌────┼────┐
    │    ↑    │     slot 0 is at (0, slice_idx) - bottom edge
    │ Up      │
    └────┼────┘
         │
    ┌────┼────┐
    │    ↓    │     slot 0 is at (n-1, slice_idx) - TOP edge (inverted!)
    │ Back    │
    └─────────┘

The reference_point stored in FaceWalkingInfo captures where slot=0, slice_index=0
lands on each face. From any two reference points, we derive the rotation transform.

================================================================================
CYCLE ORDER AND ROTATION FACE RELATIONSHIP
================================================================================

Each slice passes through exactly 4 faces in a cycle:
- M slice: cycles through F, U, B, D (parallel to L and R)
- E slice: cycles through R, B, L, F (parallel to U and D)
- S slice: cycles through U, R, D, L (parallel to F and B)

The cycle order is fixed, but the starting face is an implementation detail.
Only the RELATIVE order of faces in the cycle matters for transforms.

IMPORTANT: The cycle order matches the CONTENT FLOW during slice rotation.

Each slice rotates like a specific face (its "rotation face"):
- M rotates like L (clockwise facing L): content flows F → U → B → D
- E rotates like D (clockwise facing D): content flows R → B → L → F
- S rotates like F (clockwise facing F): content flows U → R → D → L

This relationship is fundamental:
1. The face_infos tuple stores faces in content flow order
2. The rotation face is available via SliceLayout.get_face_name()
3. When rotating the slice, content at face[i] moves to face[(i+1) % 4]

See also:
- SliceLayout.get_face_name() for the rotation face
- Slice.py module docstring for detailed slice traversal diagrams

================================================================================
USAGE
================================================================================

# Create walking info ONCE (can be cached)
walk_info = create_walking_info(cube, SliceName.M)

# Get transform between any two faces
transform = walk_info.get_transform(face_f, face_u)

# Apply transform to translate points
new_point = walk_info.translate_point(source_face, target_face, point)

================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Iterator

from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.geometric.types import Point

if TYPE_CHECKING:
    from cube.domain.model.Edge import Edge
    from cube.domain.model.Face import Face
    from cube.domain.model.FaceName import FaceName
    from cube.domain.model.SliceName import SliceName


# Type alias for the point computation function
PointComputer = Callable[[int, int], Point]  # (slice_index, slot) -> Point

UnitPointComputer = Callable[[int , # n slices
                              int,  # row
                              int   # col
                              ], Point]  # (slice_index, slot) -> Point


@dataclass(frozen=True)
class FaceWalkingInfo:
    """
    Information about one face in a slice traversal.

    This captures where slot=0, slice_index=0 lands on this face (reference_point),
    and provides a precomputed function to compute any point efficiently.

    Attributes:
        face: The Face object
        edge: The "entry edge" - the edge shared with the PREVIOUS face in the cycle.
              This is NOT just any edge - it's specifically the edge through which
              the slice enters this face from the previous face in traversal order.

              For M slice (F→U→B→D), using edge.opposite() to traverse:
              - Front: edge_bottom (starting edge, shared with Down)
              - Up: edge shared with Front (Up's bottom edge)
              - Back: edge shared with Up (Back's top edge)
              - Down: edge shared with Back (Down's top edge)

              This edge determines:
              1. Whether slice cuts rows or columns (horizontal vs vertical edge)
              2. Whether slot indices are inverted (top/right edges invert)
              3. The local slice_index translation from the previous face
        reference_point: Where (slice_index=0, slot=0) lands on this face
        n_slices: Total number of slices
        _compute: Precomputed function (slice_index, slot) -> Point
                  All decisions (edge type, inversions) are baked in at construction.

    The reference_point is used to derive transforms between faces.
    The _compute function is used to get any point efficiently.
    """

    face: "Face"
    edge: "Edge"
    reference_point: Point
    n_slices: int  # boaz:why itis needed per face ?
    _compute: PointComputer = field(compare=False)  # Don't compare functions

    def compute_point(self, slice_index: int, slot: int) -> Point:
        """
        Compute (row, col) for a given slice_index and slot position.

        This uses the precomputed function - no runtime decisions.

        Args:
            slice_index: Which slice (0 to n_slices-1)
            slot: Position along the slice (0 to n_slices-1)

        Returns:
            (row, col) in LTR coordinates on this face
        """
        return self._compute(slice_index, slot)

    def iterate_points(self, slice_index: int) -> Iterator[Point]:
        """
        Iterate over all (row, col) positions along a slice on this face.

        Args:
            slice_index: Which slice

        Yields:
            (row, col) for slot 0, 1, ..., n_slices-1
        """
        for slot in range(self.n_slices):
            yield self._compute(slice_index, slot)

@dataclass(frozen=True)
class FaceWalkingInfoUnit:
    """
    Information about one face in a slice traversal.

    This captures where slot=0, slice_index=0 lands on this face (reference_point),
    and provides a precomputed function to compute any point efficiently.

    Attributes:
        face: The Face object
        edge: The "entry edge" - the edge shared with the PREVIOUS face in the cycle.
              This is NOT just any edge - it's specifically the edge through which
              the slice enters this face from the previous face in traversal order.

              For M slice (F→U→B→D), using edge.opposite() to traverse:
              - Front: edge_bottom (starting edge, shared with Down)
              - Up: edge shared with Front (Up's bottom edge)
              - Back: edge shared with Up (Back's top edge)
              - Down: edge shared with Back (Down's top edge)

              This edge determines:
              1. Whether slice cuts rows or columns (horizontal vs vertical edge)
              2. Whether slot indices are inverted (top/right edges invert)
              3. The local slice_index translation from the previous face
        reference_point: Where (slice_index=0, slot=0) lands on this face
        n_slices: Total number of slices
        _compute: Precomputed function (slice_index, slot) -> Point
                  All decisions (edge type, inversions) are baked in at construction.

    The reference_point is used to derive transforms between faces.
    The _compute function is used to get any point efficiently.
    """

    face: "Face"  # todo CubeLayout must not expose objects from face cube !!! store names
    edge: "Edge"  # todo CubeLayout must not expose objects from face cube !!! store names
    reference_point: Point
    n_slices: int
    _compute: UnitPointComputer = field(compare=False)  # Don't compare functions


    def get_reference_point(self, actual_n_slices: int):
        """
        get refrenc epoint after extend to n_slices
        :param actual_n_slices:
        :param n_slices:
        :return:
        """

        # we assume reference point is on the edge of the slice
        r = self.reference_point[0]

        if r > 0:
            assert r == self.n_slices - 1
            r_actual = actual_n_slices -1
        else:
            r_actual = 0

        c = self.reference_point[1]

        if c > 0:
            assert c == self.n_slices -1
            c_actual = actual_n_slices - 1
        else:
            c_actual = 0

        return r_actual, c_actual


    def get_compute(self, n_slices_actual: int) -> PointComputer:

        return lambda r, c: self._compute(n_slices_actual, r, c)





@dataclass(frozen=True)
class CubeWalkingInfo:
    """
    Complete information about walking a slice through all 4 faces.

    The face_infos are stored in CONTENT FLOW order - the order content moves
    during a positive (clockwise) rotation of the slice's rotation_face.

    Face Order (Content Flow):
        - M slice (rotation_face=L): F → U → B → D
        - E slice (rotation_face=D): R → B → L → F
        - S slice (rotation_face=F): U → R → D → L

    Attributes:
        slice_name: Which slice (M, E, or S)
        rotation_face: The face this slice rotates like (M→L, E→D, S→F)
        n_slices: Total number of slices (cube_size - 2)
        face_infos: Tuple of 4 FaceWalkingInfo in content flow order

    Usage:
        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
        transform = walk_info.get_transform(face_f, face_u)
        new_point = walk_info.translate_point(face_f, face_u, (row, col))
    """

    slice_name: "SliceName"
    rotation_face: "FaceName"
    n_slices: int
    face_infos: tuple[FaceWalkingInfo, ...]

    def __post_init__(self):
        """Validate that we have exactly 4 faces."""
        if len(self.face_infos) != 4:
            raise ValueError(f"CubeWalkingInfo requires exactly 4 faces, got {len(self.face_infos)}")

    def __iter__(self) -> Iterator[FaceWalkingInfo]:
        """Iterate over face infos in cycle order."""
        return iter(self.face_infos)

    def __len__(self) -> int:
        """Return number of faces (always 4)."""
        return len(self.face_infos)

    def __getitem__(self, index: int) -> FaceWalkingInfo:
        """Get face info by cycle index (0-3)."""
        return self.face_infos[index]

    def get_face_info(self, face: "Face") -> FaceWalkingInfo:
        """
        Look up FaceWalkingInfo by Face object.

        Raises:
            KeyError: If face is not in this traversal
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
        """Get tuple of faces in cycle order."""
        return tuple(info.face for info in self.face_infos)

    def get_transform(self, source_face: "Face", target_face: "Face") -> FUnitRotation:
        """
        Get the unit rotation transform from source_face to target_face.

        The transform is derived from the reference points on both faces.

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
        point: Point
    ) -> Point:
        """
        Translate a point from source_face to target_face.

        Args:
            source_face: The face the point is on
            target_face: The face to translate to
            point: (row, col) on source_face

        Returns:
            (row, col) on target_face in LTR coordinates
        """
        transform = self.get_transform(source_face, target_face)
        return transform.of_n_slices(self.n_slices)(*point)

@dataclass(frozen=True)
class CubeWalkingInfoUnit:
    """
    Complete information about walking a slice through all 4 faces.

    The face_infos are stored in CONTENT FLOW order - the order content moves
    during a positive (clockwise) rotation of the slice's rotation_face.

    Face Order (Content Flow):
        - M slice (rotation_face=L): F → U → B → D
        - E slice (rotation_face=D): R → B → L → F
        - S slice (rotation_face=F): U → R → D → L

    Attributes:
        slice_name: Which slice (M, E, or S)
        rotation_face: The face this slice rotates like (M→L, E→D, S→F)
        n_slices: Total number of slices (cube_size - 2)
        face_infos: Tuple of 4 FaceWalkingInfo in content flow order

    Usage:
        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
        transform = walk_info.get_transform(face_f, face_u)
        new_point = walk_info.translate_point(face_f, face_u, (row, col))
    """

    slice_name: "SliceName"
    rotation_face: "FaceName"
    n_slices: int
    face_infos: tuple[FaceWalkingInfoUnit, ...]

    def __post_init__(self):
        """Validate that we have exactly 4 faces."""
        if len(self.face_infos) != 4:
            raise ValueError(f"CubeWalkingInfo requires exactly 4 faces, got {len(self.face_infos)}")

    def __iter__(self) -> Iterator[FaceWalkingInfoUnit]:
        """Iterate over face infos in cycle order."""
        return iter(self.face_infos)

    def __len__(self) -> int:
        """Return number of faces (always 4)."""
        return len(self.face_infos)

    def __getitem__(self, index: int) -> FaceWalkingInfoUnit:
        """Get face info by cycle index (0-3)."""
        return self.face_infos[index]

    def get_face_info(self, face: "Face") -> FaceWalkingInfoUnit:
        """
        Look up FaceWalkingInfo by Face object.

        Raises:
            KeyError: If face is not in this traversal
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
        """Get tuple of faces in cycle order."""
        return tuple(info.face for info in self.face_infos)

    def get_transform(self, source_face: "Face", target_face: "Face") -> FUnitRotation:
        """
        Get the unit rotation transform from source_face to target_face.

        The transform is derived from the reference points on both faces.

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
        point: Point
    ) -> Point:
        """
        Translate a point from source_face to target_face.

        Args:
            source_face: The face the point is on
            target_face: The face to translate to
            point: (row, col) on source_face

        Returns:
            (row, col) on target_face in LTR coordinates
        """
        transform = self.get_transform(source_face, target_face)
        return transform.of_n_slices(self.n_slices)(*point)
