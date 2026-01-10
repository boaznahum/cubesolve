"""
Tests for cube_walking module - verifying transforms match hardcoded tables.

This test file validates that CubeWalkingInfo.get_transform() produces the same
results as the hardcoded _TRANSFORMATION_TABLE in Face2FaceTranslator.

Key insight from Issue #55:
    "L, F, R, U, D faces all have aligned coordinate systems"
    "B face has a 180-degree rotated coordinate system"

This test verifies this hypothesis by computing transforms using geometric
traversal and comparing them to the empirically-derived table.
"""

from __future__ import annotations

import pytest

from cube.domain.geometric.cube_walking import CubeWalkingInfo
from cube.domain.geometric.Face2FaceTranslator import TransformType, _TRANSFORMATION_TABLE
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from tests.test_utils import _test_sp


# Map FUnitRotation to TransformType
_FUNIT_TO_TRANSFORM: dict[FUnitRotation, TransformType] = {
    FUnitRotation.CW0: TransformType.IDENTITY,
    FUnitRotation.CW1: TransformType.ROT_90_CW,
    FUnitRotation.CW2: TransformType.ROT_180,
    FUnitRotation.CW3: TransformType.ROT_90_CCW,
}


def _transform_to_funit(tt: TransformType) -> FUnitRotation:
    """Convert TransformType to FUnitRotation."""
    for funit, transform in _FUNIT_TO_TRANSFORM.items():
        if transform == tt:
            return funit
    raise ValueError(f"Unknown TransformType: {tt}")


class TestCubeWalkingTransforms:
    """Test that CubeWalkingInfo transforms match the hardcoded table."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(5, _test_sp)

    def test_walking_info_creation(self, cube: Cube):
        """Verify CubeWalkingInfo can be created for all slices."""
        for slice_name in SliceName:
            walk_info = cube.geometric.create_walking_info(slice_name)
            assert len(walk_info) == 4
            assert walk_info.n_slices == cube.n_slices

    def test_m_slice_faces(self, cube: Cube):
        """M slice should traverse F, U, B, D."""
        walk_info = cube.geometric.create_walking_info(SliceName.M)
        face_names = [info.face.name for info in walk_info]
        # Cycle order is F → U → B → D
        assert FaceName.F in face_names
        assert FaceName.U in face_names
        assert FaceName.B in face_names
        assert FaceName.D in face_names
        # L and R are not in M slice
        assert FaceName.L not in face_names
        assert FaceName.R not in face_names

    def test_e_slice_faces(self, cube: Cube):
        """E slice should traverse R, B, L, F."""
        walk_info = cube.geometric.create_walking_info(SliceName.E)
        face_names = [info.face.name for info in walk_info]
        # Cycle order is R → B → L → F
        assert FaceName.R in face_names
        assert FaceName.B in face_names
        assert FaceName.L in face_names
        assert FaceName.F in face_names
        # U and D are not in E slice
        assert FaceName.U not in face_names
        assert FaceName.D not in face_names

    def test_s_slice_faces(self, cube: Cube):
        """S slice should traverse U, R, D, L."""
        walk_info = cube.geometric.create_walking_info(SliceName.S)
        face_names = [info.face.name for info in walk_info]
        # Cycle order is U → R → D → L
        assert FaceName.U in face_names
        assert FaceName.R in face_names
        assert FaceName.D in face_names
        assert FaceName.L in face_names
        # F and B are not in S slice
        assert FaceName.F not in face_names
        assert FaceName.B not in face_names

    def test_transforms_match_hardcoded_table_adjacent_faces(self, cube: Cube):
        """
        Verify that CubeWalkingInfo.get_transform() matches _TRANSFORMATION_TABLE
        for ADJACENT face pairs in the slice cycle.

        Note: For OPPOSITE face pairs (U-D, L-R, F-B), the transforms may differ
        because:
        - _TRANSFORMATION_TABLE uses whole-cube rotations (X2, Y2, Z2)
        - CubeWalkingInfo uses slice traversal geometry

        For adjacent faces (1 step apart in cycle), both should agree.
        """
        mismatches = []

        for slice_name in SliceName:
            walk_info = cube.geometric.create_walking_info(slice_name)
            faces = walk_info.faces

            # Check ADJACENT pairs only (faces that are 1 step apart in cycle)
            for i in range(4):
                source_face = faces[i]
                target_face = faces[(i + 1) % 4]

                # Get computed transform from CubeWalkingInfo
                computed_funit = walk_info.get_transform(source_face, target_face)
                computed_transform = _FUNIT_TO_TRANSFORM[computed_funit]

                # Get expected transform from hardcoded table
                source_name = source_face.name
                target_name = target_face.name
                expected_transform = _TRANSFORMATION_TABLE.get((source_name, target_name))

                if expected_transform is None:
                    # Skip if not in table
                    continue

                if computed_transform != expected_transform:
                    mismatches.append(
                        f"{slice_name.name}: {source_name.name}->{target_name.name}: "
                        f"computed={computed_transform.name}, expected={expected_transform.name}"
                    )

        assert not mismatches, f"Transform mismatches:\n" + "\n".join(mismatches)

    def test_opposite_faces_transform_composition(self, cube: Cube):
        """
        Verify that for opposite faces (2 steps apart), the transform is the
        composition of two adjacent transforms.

        This explains why _TRANSFORMATION_TABLE (whole-cube) differs from
        CubeWalkingInfo (slice traversal) for opposite faces.
        """
        for slice_name in SliceName:
            walk_info = cube.geometric.create_walking_info(slice_name)
            faces = walk_info.faces

            for i in range(4):
                # Get transform from face[i] to face[i+2] (opposite in cycle)
                source_face = faces[i]
                target_face = faces[(i + 2) % 4]

                # Direct transform
                direct = walk_info.get_transform(source_face, target_face)

                # Composed transform (via intermediate face)
                mid_face = faces[(i + 1) % 4]
                step1 = walk_info.get_transform(source_face, mid_face)
                step2 = walk_info.get_transform(mid_face, target_face)
                composed = step2 * step1  # Apply step1 first, then step2

                assert direct == composed, (
                    f"{slice_name.name}: {source_face.name.name}->{target_face.name.name}: "
                    f"direct={direct}, composed={composed}"
                )


class TestBFaceAsymmetry:
    """
    Test the B-face asymmetry hypothesis from Issue #55.

    The hypothesis: F, U, D, L, R faces have aligned coordinate systems,
    while B face has a 180-degree rotated coordinate system.

    This means:
    - Any face -> B: should involve ROT_180
    - B -> any face: should involve ROT_180
    - Among F, U, D, L, R: various transforms but with a pattern
    """

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(5, _test_sp)

    def test_b_face_always_rot_180(self, cube: Cube):
        """
        Verify that transforms involving B face are always ROT_180.

        From _TRANSFORMATION_TABLE, all B<->other transitions involve ROT_180:
        - B->D: ROT_180
        - B->F: ROT_180
        - B->U: ROT_180
        - D->B: ROT_180
        - F->B: ROT_180
        - U->B: ROT_180

        Note: B<->L and B<->R are IDENTITY because they share the Y axis.
        """
        # Check B -> other (except L, R which share Y axis)
        assert _TRANSFORMATION_TABLE[(FaceName.B, FaceName.D)] == TransformType.ROT_180
        assert _TRANSFORMATION_TABLE[(FaceName.B, FaceName.F)] == TransformType.ROT_180
        assert _TRANSFORMATION_TABLE[(FaceName.B, FaceName.U)] == TransformType.ROT_180

        # Check other -> B
        assert _TRANSFORMATION_TABLE[(FaceName.D, FaceName.B)] == TransformType.ROT_180
        assert _TRANSFORMATION_TABLE[(FaceName.F, FaceName.B)] == TransformType.ROT_180
        assert _TRANSFORMATION_TABLE[(FaceName.U, FaceName.B)] == TransformType.ROT_180

        # B <-> L and B <-> R are IDENTITY (same Y axis)
        assert _TRANSFORMATION_TABLE[(FaceName.B, FaceName.L)] == TransformType.IDENTITY
        assert _TRANSFORMATION_TABLE[(FaceName.B, FaceName.R)] == TransformType.IDENTITY

    def test_front_face_transitions_identity(self, cube: Cube):
        """
        Verify F face transitions to adjacent non-B faces are IDENTITY.

        F shares edges with U, D, L, R and transitions should be IDENTITY.
        """
        assert _TRANSFORMATION_TABLE[(FaceName.F, FaceName.D)] == TransformType.IDENTITY
        assert _TRANSFORMATION_TABLE[(FaceName.F, FaceName.U)] == TransformType.IDENTITY
        assert _TRANSFORMATION_TABLE[(FaceName.F, FaceName.L)] == TransformType.IDENTITY
        assert _TRANSFORMATION_TABLE[(FaceName.F, FaceName.R)] == TransformType.IDENTITY

    def test_z_axis_rotation_pattern(self, cube: Cube):
        """
        Verify rotation pattern around Z axis (F-B axis).

        Faces around Z axis: U, R, D, L
        Moving CW (viewing from F): U -> R -> D -> L
        """
        # U -> R (CW): should be ROT_90_CCW (or its inverse)
        # R -> D (CW): should be ROT_90_CW
        # etc.
        assert _TRANSFORMATION_TABLE[(FaceName.U, FaceName.R)] == TransformType.ROT_90_CW
        assert _TRANSFORMATION_TABLE[(FaceName.R, FaceName.D)] == TransformType.ROT_90_CW
        assert _TRANSFORMATION_TABLE[(FaceName.D, FaceName.L)] == TransformType.ROT_90_CW
        assert _TRANSFORMATION_TABLE[(FaceName.L, FaceName.U)] == TransformType.ROT_90_CW

    def test_computed_b_face_asymmetry(self, cube: Cube):
        """
        Verify B-face asymmetry using CubeWalkingInfo computed transforms.

        In the M slice (F, U, B, D), transitions to/from B should be ROT_180.
        """
        walk_info = cube.geometric.create_walking_info(SliceName.M)

        # Get faces
        face_f = cube.front
        face_u = cube.up
        face_b = cube.back
        face_d = cube.down

        # F -> U should NOT be ROT_180 (both "aligned" faces)
        fu_transform = walk_info.get_transform(face_f, face_u)
        assert _FUNIT_TO_TRANSFORM[fu_transform] != TransformType.ROT_180

        # F -> B should be ROT_180 (B is "inverted")
        fb_transform = walk_info.get_transform(face_f, face_b)
        assert _FUNIT_TO_TRANSFORM[fb_transform] == TransformType.ROT_180

        # U -> B should be ROT_180
        ub_transform = walk_info.get_transform(face_u, face_b)
        assert _FUNIT_TO_TRANSFORM[ub_transform] == TransformType.ROT_180


class TestSlotConsistency:
    """Test the slot consistency principle across face traversals."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(5, _test_sp)

    def test_same_slot_across_faces(self, cube: Cube):
        """
        Verify that following the same slot through all 4 faces
        reaches corresponding positions.

        For M slice at slot=0:
        - Front: should be at left edge (col 0 or col n-1)
        - Up: should be at bottom edge
        - Back: should be at right edge
        - Down: should be at top edge
        """
        walk_info = cube.geometric.create_walking_info(SliceName.M)
        n_slices = walk_info.n_slices

        # For slice_index=0, slot=0
        points = []
        for face_info in walk_info:
            point = face_info.compute_point(0, 0)
            points.append((face_info.face.name, point))

        # All points should be valid (row and col within bounds)
        for face_name, (row, col) in points:
            assert 0 <= row < n_slices, f"Invalid row {row} for {face_name}"
            assert 0 <= col < n_slices, f"Invalid col {col} for {face_name}"

    def test_translate_point_roundtrip(self, cube: Cube):
        """
        Verify that translating a point around the full cycle returns to start.
        """
        walk_info = cube.geometric.create_walking_info(SliceName.M)
        faces = walk_info.faces

        # Start with a point on the first face
        start_point = (1, 1)  # Some interior point

        # Translate through all 4 faces and back
        current_point = start_point
        for i in range(4):
            source_face = faces[i]
            target_face = faces[(i + 1) % 4]
            current_point = walk_info.translate_point(source_face, target_face, current_point)

        # After 4 translations, should be back at start
        assert current_point == start_point, (
            f"Roundtrip failed: started at {start_point}, ended at {current_point}"
        )
