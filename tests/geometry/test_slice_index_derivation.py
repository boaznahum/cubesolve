"""
Test that slice index computation is correctly derived from geometry.

The computation is derived dynamically using:
1. does_slice_cut_rows_or_columns() - determines ROW vs COL
2. does_slice_of_face_start_with_face() - determines direct vs inverted

This validates the computation against walking info (ground truth).
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from tests.test_utils import _test_sp


# Test parameters - comprehensive coverage
CUBE_SIZES = [3, 4, 5, 7]  # Various cube sizes


class TestSliceIndexDerivation:
    """Validate that slice index computation derivation works correctly."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(3, _test_sp)




class TestSliceIndexAgainstWalkingInfo:
    """
    Validate slice index computation against walking info (ground truth).

    This tests the inverse relationship:
    - Walking info: (slice_index, slot) -> (row, col)
    - Computation: (row, col) -> slice_index

    Testing across all cube sizes, slices, faces, and coordinates.
    """

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_slice_index_is_inverse_of_walking_info(self, cube_size: int) -> None:
        """
        Verify: walking_info.compute_point(idx, slot) gives point,
                computation(point) gives idx back.

        For each cube size, slice, face, and slice_index:
        1. Get point from walking info for this slice_index
        2. Compute slice_index back using the function
        3. Verify they match (accounting for 0-based vs 1-based)
        """
        cube = Cube(cube_size, _test_sp)
        n_slices = cube.n_slices

        if n_slices == 0:
            pytest.skip("No inner slices for this cube size")

        for slice_name in SliceName:
            walking_info = cube.sized_layout.create_walking_info(slice_name)

            for face_info in walking_info:
                face_name = face_info.face.name

                # Test all slice indices
                for slice_idx_0based in range(n_slices):
                    # Walking info uses 0-based slice index
                    # Get any point on this slice (slot=0)
                    point = face_info.compute_point(slice_idx_0based, slot=0)
                    row, col = point

                    # Computation returns 0-based slice index
                    computed_0based = cube.sized_layout.get_slice(slice_name).compute_slice_index(
                        face_name, (row, col), n_slices
                    )

                    assert computed_0based == slice_idx_0based, (
                        f"Cube {cube_size}x{cube_size}, {slice_name.name} on {face_name.name}: "
                        f"slice_idx={slice_idx_0based} -> point={point} -> "
                        f"computed={computed_0based} (expected {slice_idx_0based})"
                    )

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_all_points_on_slice_map_to_same_index(self, cube_size: int) -> None:
        """
        Verify all points along a slice (different slots) map to the same slice_index.

        This confirms the computation correctly extracts the relevant coordinate
        (row or col) and ignores the irrelevant one.
        """
        cube = Cube(cube_size, _test_sp)
        n_slices = cube.n_slices

        if n_slices == 0:
            pytest.skip("No inner slices for this cube size")

        for slice_name in SliceName:
            walking_info = cube.sized_layout.create_walking_info(slice_name)

            for face_info in walking_info:
                face_name = face_info.face.name

                for slice_idx_0based in range(n_slices):
                    # Test multiple slots along the same slice
                    for slot in range(n_slices):
                        point = face_info.compute_point(slice_idx_0based, slot)
                        row, col = point

                        computed_0based = cube.sized_layout.get_slice(slice_name).compute_slice_index(
                            cube.layout, face_name, slice_name, (row, col), n_slices
                        )

                        assert computed_0based == slice_idx_0based, (
                            f"Cube {cube_size}, {slice_name.name} on {face_name.name}: "
                            f"slice_idx={slice_idx_0based}, slot={slot} -> point={point} -> "
                            f"computed={computed_0based} (expected {slice_idx_0based})"
                        )
