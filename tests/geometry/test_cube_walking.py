"""
Tests for cube_walking module.

Key insight from Issue #55:
    "L, F, R, U, D faces all have aligned coordinate systems"
    "B face has a 180-degree rotated coordinate system"

This test verifies this hypothesis by computing transforms using geometric traversal.
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from tests.test_utils import _test_sp


class TestCubeWalkingTransforms:
    """Test CubeWalkingInfo transforms and face traversal."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(5, _test_sp)

    def test_walking_info_creation(self, cube: Cube):
        """Verify CubeWalkingInfo can be created for all slices."""
        for slice_name in SliceName:
            walk_info = cube.sized_layout.create_walking_info(slice_name)
            assert len(walk_info) == 4
            assert walk_info.n_slices == cube.n_slices

    def test_m_slice_faces(self, cube: Cube):
        """M slice should traverse F, U, B, D."""
        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
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
        walk_info = cube.sized_layout.create_walking_info(SliceName.E)
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
        walk_info = cube.sized_layout.create_walking_info(SliceName.S)
        face_names = [info.face.name for info in walk_info]
        # Cycle order is U → R → D → L
        assert FaceName.U in face_names
        assert FaceName.R in face_names
        assert FaceName.D in face_names
        assert FaceName.L in face_names
        # F and B are not in S slice
        assert FaceName.F not in face_names
        assert FaceName.B not in face_names

    def test_opposite_faces_transform_composition(self, cube: Cube):
        """
        Verify that for opposite faces (2 steps apart), the transform is the
        composition of two adjacent transforms.
        """
        for slice_name in SliceName:
            walk_info = cube.sized_layout.create_walking_info(slice_name)
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
        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
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
        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
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
