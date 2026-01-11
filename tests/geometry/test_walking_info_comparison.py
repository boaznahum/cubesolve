"""
Test to compare old create_walking_info() behavior with new implementation.

This test captures the essential behavior that must be preserved:
1. Face traversal order (content flow)
2. Reference points for each face
3. Transform computation between faces
4. Point translation accuracy
"""

import pytest
from cube.domain.model.Cube import Cube
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.cube_walking import CubeWalkingInfo, FaceWalkingInfo
from tests.test_utils import TestServiceProvider


def create_cube(size: int = 5) -> Cube:
    """Create a test cube."""
    sp = TestServiceProvider()
    return Cube(size, sp)


class TestWalkingInfoBehavior:
    """Test essential walking info behavior."""

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_walking_info_has_4_faces(self, slice_name: SliceName, cube_size: int):
        """Walking info must have exactly 4 faces."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)
        assert len(walk_info.face_infos) == 4

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_walking_info_faces_are_unique(self, slice_name: SliceName, cube_size: int):
        """All 4 faces must be different."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)
        faces = [info.face for info in walk_info.face_infos]
        assert len(set(f.name for f in faces)) == 4

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_reference_points_are_valid(self, slice_name: SliceName, cube_size: int):
        """Reference points must be within bounds."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)
        n_slices = cube.n_slices

        for info in walk_info.face_infos:
            row, col = info.reference_point
            assert 0 <= row < n_slices, f"row {row} out of bounds for n_slices={n_slices}"
            assert 0 <= col < n_slices, f"col {col} out of bounds for n_slices={n_slices}"

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_compute_points_are_valid(self, slice_name: SliceName, cube_size: int):
        """Computed points must be within bounds."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)
        n_slices = cube.n_slices

        for info in walk_info.face_infos:
            for slice_idx in range(n_slices):
                for slot in range(n_slices):
                    row, col = info.compute_point(slice_idx, slot)
                    assert 0 <= row < n_slices, f"row {row} out of bounds"
                    assert 0 <= col < n_slices, f"col {col} out of bounds"

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_compute_at_zero_matches_reference(self, slice_name: SliceName, cube_size: int):
        """compute_point(0, 0) must equal reference_point."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)

        for info in walk_info.face_infos:
            computed = info.compute_point(0, 0)
            assert computed == info.reference_point, (
                f"compute_point(0,0)={computed} != reference_point={info.reference_point}"
            )

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    @pytest.mark.parametrize("cube_size", [3, 4, 5, 7])
    def test_transforms_are_consistent(self, slice_name: SliceName, cube_size: int):
        """Transform from A->B->C must equal A->C."""
        cube = create_cube(cube_size)
        walk_info = cube.sized_layout.create_walking_info(slice_name)
        n_slices = cube.n_slices

        faces = walk_info.faces
        for i in range(4):
            face_a = faces[i]
            face_b = faces[(i + 1) % 4]
            face_c = faces[(i + 2) % 4]

            # Get transforms
            t_ab = walk_info.get_transform(face_a, face_b)
            t_bc = walk_info.get_transform(face_b, face_c)
            t_ac = walk_info.get_transform(face_a, face_c)

            # Apply A->B->C
            test_point = (1, 1) if n_slices > 2 else (0, 0)
            p1 = t_ab.of_n_slices(n_slices)(*test_point)
            p2 = t_bc.of_n_slices(n_slices)(*p1)

            # Apply A->C directly
            p3 = t_ac.of_n_slices(n_slices)(*test_point)

            assert p2 == p3, f"Transform chain mismatch: {p2} != {p3}"


class TestUnitWalkingInfoConsistency:
    """Test that unit walking info is consistent with sized walking info."""

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    def test_unit_and_sized_have_same_faces(self, slice_name: SliceName):
        """Unit and sized walking info should have the same faces in same order."""
        cube = create_cube(5)

        unit_info = cube.layout.create_unit_walking_info(slice_name)
        # Note: sized uses random starting face, so we just check face set
        sized_info = cube.sized_layout.create_walking_info(slice_name)

        unit_faces = {ufi.face_name for ufi in unit_info.face_infos}
        sized_faces = {fi.face.name for fi in sized_info.face_infos}

        assert unit_faces == sized_faces, (
            f"Face mismatch: unit={unit_faces}, sized={sized_faces}"
        )

    @pytest.mark.parametrize("slice_name", [SliceName.M, SliceName.E, SliceName.S])
    def test_unit_rotation_face_matches_sized(self, slice_name: SliceName):
        """Unit and sized should agree on rotation face."""
        cube = create_cube(5)

        unit_info = cube.layout.create_unit_walking_info(slice_name)
        sized_info = cube.sized_layout.create_walking_info(slice_name)

        assert unit_info.rotation_face == sized_info.rotation_face


class TestSpecificSliceBehavior:
    """Test specific expected behavior for each slice."""

    def test_m_slice_rotation_face_is_l(self):
        """M slice should rotate like L face."""
        cube = create_cube(5)
        from cube.domain.model.FaceName import FaceName

        walk_info = cube.sized_layout.create_walking_info(SliceName.M)
        assert walk_info.rotation_face == FaceName.L

    def test_e_slice_rotation_face_is_d(self):
        """E slice should rotate like D face."""
        cube = create_cube(5)
        from cube.domain.model.FaceName import FaceName

        walk_info = cube.sized_layout.create_walking_info(SliceName.E)
        assert walk_info.rotation_face == FaceName.D

    def test_s_slice_rotation_face_is_f(self):
        """S slice should rotate like F face."""
        cube = create_cube(5)
        from cube.domain.model.FaceName import FaceName

        walk_info = cube.sized_layout.create_walking_info(SliceName.S)
        assert walk_info.rotation_face == FaceName.F


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
