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

# Import the computation functions
from cube.domain.geometric.Face2FaceTranslator import (
    _create_slice_index_computer,
    _compute_slice_index,
)


# Test parameters - comprehensive coverage
CUBE_SIZES = [3, 4, 5, 7]  # Various cube sizes


class TestSliceIndexDerivation:
    """Validate that slice index computation derivation works correctly."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(3, _test_sp)

    def test_all_slice_face_combinations_have_computer(self, cube: Cube) -> None:
        """
        Verify computation function can be created for all valid slice-face combinations.

        Each slice affects exactly 4 faces (not the rotation face or its opposite).
        """
        layout = cube.layout

        for slice_name in SliceName:
            slice_layout = layout.get_slice(slice_name)
            rotation_face = slice_layout.get_face_name()
            opposite_face = layout.opposite(rotation_face)

            # Slice affects all faces except rotation face and its opposite
            affected_faces = [f for f in FaceName if f not in (rotation_face, opposite_face)]
            assert len(affected_faces) == 4, f"Slice {slice_name} should affect exactly 4 faces"

            for face_name in affected_faces:
                # Should not raise - computer should be creatable
                computer = _create_slice_index_computer(layout, slice_name, face_name)
                assert callable(computer), (
                    f"Expected callable for {slice_name.name} on {face_name.name}"
                )
                # Verify it returns valid results
                result = computer(0, 0, 3)
                assert isinstance(result, int), (
                    f"Expected int result for {slice_name.name} on {face_name.name}"
                )
                assert 1 <= result <= 3, (
                    f"Expected result in [1, 3] for {slice_name.name} on {face_name.name}, got {result}"
                )

    def test_computer_consistency_across_cube_sizes(self) -> None:
        """
        Verify the same computer produces correct results for different cube sizes.

        The computer function itself is size-independent - only the n_slices parameter changes.
        """
        # Test that for the same (slice, face) combo, computer gives consistent results
        # when scaled appropriately
        for size in CUBE_SIZES:
            cube = Cube(size, _test_sp)
            layout = cube.layout
            n_slices = cube.n_slices

            if n_slices == 0:
                continue

            for slice_name in SliceName:
                slice_layout = layout.get_slice(slice_name)
                rotation_face = slice_layout.get_face_name()
                opposite_face = layout.opposite(rotation_face)

                affected_faces = [f for f in FaceName if f not in (rotation_face, opposite_face)]
                for face_name in affected_faces:
                    computer = _create_slice_index_computer(layout, slice_name, face_name)

                    # Test first and last slice indices
                    first_result = computer(0, 0, n_slices)
                    assert 1 <= first_result <= n_slices, (
                        f"Size {size}, {slice_name.name} on {face_name.name}: "
                        f"first_result={first_result} not in [1, {n_slices}]"
                    )


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

                    # Computation returns 1-based slice index
                    computed_1based = _compute_slice_index(
                        cube.layout, face_name, slice_name, (row, col), n_slices
                    )

                    # Convert to 0-based for comparison
                    computed_0based = computed_1based - 1

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

                        computed_1based = _compute_slice_index(
                            cube.layout, face_name, slice_name, (row, col), n_slices
                        )
                        computed_0based = computed_1based - 1

                        assert computed_0based == slice_idx_0based, (
                            f"Cube {cube_size}, {slice_name.name} on {face_name.name}: "
                            f"slice_idx={slice_idx_0based}, slot={slot} -> point={point} -> "
                            f"computed={computed_0based} (expected {slice_idx_0based})"
                        )
