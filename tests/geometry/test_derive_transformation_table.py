"""
Test derivation of _TRANSFORMATION_TABLE from slice geometry.

This test verifies that we can derive the transformation table dynamically
using CubeWalkingInfo instead of relying on the hardcoded table.

Issue #55: Replace hard-coded lookup tables with mathematical derivation
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.Face2FaceTranslator import (
    TransformType,
    _TRANSFORMATION_TABLE,
)
from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry
from cube.domain.geometric.cube_walking import CubeWalkingInfo
from cube.domain.geometric.FRotation import FUnitRotation
from tests.test_utils import _test_sp


# Mapping from FUnitRotation to TransformType
_UNIT_TO_TRANSFORM: dict[int, TransformType] = {
    0: TransformType.IDENTITY,
    1: TransformType.ROT_90_CW,
    2: TransformType.ROT_180,
    3: TransformType.ROT_90_CCW,
}


def _get_slice_for_faces(source: FaceName, target: FaceName) -> SliceName | None:
    """
    Find which slice connects two faces.

    Returns None if faces are the same or opposite (no single slice connects them).
    """
    # Slice -> faces it affects
    slice_faces = {
        SliceName.M: {FaceName.F, FaceName.U, FaceName.B, FaceName.D},
        SliceName.E: {FaceName.F, FaceName.R, FaceName.B, FaceName.L},
        SliceName.S: {FaceName.U, FaceName.R, FaceName.D, FaceName.L},
    }

    for slice_name, faces in slice_faces.items():
        if source in faces and target in faces:
            return slice_name

    return None


def _unit_rotation_to_transform(unit: FUnitRotation) -> TransformType:
    """Convert FUnitRotation to TransformType."""
    return _UNIT_TO_TRANSFORM[unit._n_rotation % 4]


def _invert_transform(transform: TransformType) -> TransformType:
    """Invert a transform (for opposite rotation directions)."""
    # CW0 stays CW0, CW1 becomes CW3, CW2 stays CW2, CW3 becomes CW1
    inversion = {
        TransformType.IDENTITY: TransformType.IDENTITY,
        TransformType.ROT_90_CW: TransformType.ROT_90_CCW,
        TransformType.ROT_180: TransformType.ROT_180,
        TransformType.ROT_90_CCW: TransformType.ROT_90_CW,
    }
    return inversion[transform]


def _get_axis_rotation_face(slice_name: SliceName) -> FaceName:
    """
    Get the face that the corresponding axis rotation uses.

    X rotates around R, Y rotates around U, Z rotates around F.
    """
    return {
        SliceName.M: FaceName.R,  # X axis
        SliceName.E: FaceName.U,  # Y axis
        SliceName.S: FaceName.F,  # Z axis
    }[slice_name]


def _get_slice_rotation_face(slice_name: SliceName) -> FaceName:
    """
    Get the face that defines the slice's rotation direction.

    M rotates like L, E rotates like D, S rotates like F.
    """
    return {
        SliceName.M: FaceName.L,
        SliceName.E: FaceName.D,
        SliceName.S: FaceName.F,
    }[slice_name]


def _are_opposite_faces(f1: FaceName, f2: FaceName) -> bool:
    """Check if two faces are opposite."""
    opposites = {
        FaceName.F: FaceName.B, FaceName.B: FaceName.F,
        FaceName.U: FaceName.D, FaceName.D: FaceName.U,
        FaceName.L: FaceName.R, FaceName.R: FaceName.L,
    }
    return opposites.get(f1) == f2


def derive_transform_type(
    cube: Cube,
    source: FaceName,
    target: FaceName,
) -> TransformType | None:
    """
    Derive the TransformType for a (source, target) face pair.

    This function computes how coordinates transform when content moves from
    source face to target face via a whole-cube rotation (X, Y, or Z).

    Args:
        cube: A Cube instance (needed to access face objects and walking info)
        source: The face where content originates (e.g., FaceName.F)
        target: The face where content arrives (e.g., FaceName.U)

    Returns:
        TransformType indicating how (row, col) coordinates change:
        - IDENTITY: (r, c) → (r, c) - no change
        - ROT_90_CW: (r, c) → (inv(c), r) - 90° clockwise
        - ROT_90_CCW: (r, c) → (c, inv(r)) - 90° counter-clockwise
        - ROT_180: (r, c) → (inv(r), inv(c)) - 180° rotation
        - None: if faces are same or opposite (no direct connection)

    Example:
        derive_transform_type(cube, FaceName.F, FaceName.U)
        → TransformType.IDENTITY (F→U via X keeps coordinates)

        derive_transform_type(cube, FaceName.D, FaceName.L)
        → TransformType.ROT_90_CW (D→L via Z rotates 90° CW)

    GEOMETRIC ASSUMPTION: Opposite faces rotate in opposite directions.
    See: Face2FaceTranslator.py comment block for details.
    """
    if source == target:
        return None

    # Find which slice connects them
    slice_name = _get_slice_for_faces(source, target)
    if slice_name is None:
        return None  # Opposite faces - no single slice

    # Get walking info for this slice
    walking_info: CubeWalkingInfo = _CubeLayoutGeometry.create_walking_info(cube, slice_name)

    # Get faces from cube
    source_face = cube.face(source)
    target_face = cube.face(target)

    # Get the transform from walking info
    unit_rotation = walking_info.get_transform(source_face, target_face)
    transform = _unit_rotation_to_transform(unit_rotation)

    # Check if we need to invert due to opposite rotation faces
    slice_rot_face = _get_slice_rotation_face(slice_name)
    axis_rot_face = _get_axis_rotation_face(slice_name)

    if _are_opposite_faces(slice_rot_face, axis_rot_face):
        transform = _invert_transform(transform)

    return transform


class TestDeriveTransformationTable:
    """Test that we can derive the transformation table from geometry."""

    @pytest.fixture
    def cube(self) -> Cube:
        """Create a test cube."""
        return Cube(5, sp=_test_sp)

    def test_derive_all_entries(self, cube: Cube):
        """
        Compare derived transforms against the hardcoded table.

        This test verifies that our derivation algorithm produces
        the same results as the empirically-derived table.
        """
        mismatches: list[str] = []
        matches = 0

        for (source, target), expected in _TRANSFORMATION_TABLE.items():
            derived = derive_transform_type(cube, source, target)

            if derived is None:
                mismatches.append(
                    f"({source.name}, {target.name}): Expected {expected.name}, got None"
                )
            elif derived != expected:
                mismatches.append(
                    f"({source.name}, {target.name}): Expected {expected.name}, got {derived.name}"
                )
            else:
                matches += 1

        # Report results
        print(f"\nMatches: {matches}/{len(_TRANSFORMATION_TABLE)}")
        if mismatches:
            print("Mismatches:")
            for m in mismatches:
                print(f"  {m}")

        assert not mismatches, f"Found {len(mismatches)} mismatches:\n" + "\n".join(mismatches)

    def test_derive_single_entry_debug(self, cube: Cube):
        """Debug test for a single entry - useful for investigating mismatches."""
        source, target = FaceName.F, FaceName.U
        expected = _TRANSFORMATION_TABLE.get((source, target))
        derived = derive_transform_type(cube, source, target)

        print(f"\n({source.name}, {target.name}):")
        print(f"  Expected: {expected}")
        print(f"  Derived:  {derived}")

        assert derived == expected
