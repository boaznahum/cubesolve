"""
Test that slice index formula is correctly derived from geometry.

The formula is derived dynamically using:
1. does_slice_cut_rows_or_columns() - determines ROW vs COL
2. does_slice_of_face_start_with_face() - determines direct vs inverted

This validates the formula against walking info (ground truth).
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.slice_layout import CLGColRow
from tests.test_utils import _test_sp

# Import the formula derivation and computation functions
from cube.domain.geometric.Face2FaceTranslator import (
    _SliceIndexFormula,
    _derive_slice_index_formula,
    _compute_slice_index,
)


# Test parameters - comprehensive coverage
CUBE_SIZES = [3, 4, 5, 7]  # Various cube sizes


class TestSliceIndexDerivation:
    """Validate that slice index formula derivation works correctly."""

    @pytest.fixture
    def cube(self) -> Cube:
        return Cube(3, _test_sp)

    def test_all_slice_face_combinations_have_formula(self, cube: Cube) -> None:
        """
        Verify formula can be derived for all valid slice-face combinations.

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
                # Should not raise - formula should be derivable
                formula = _derive_slice_index_formula(layout, slice_name, face_name)
                assert formula in (
                    _SliceIndexFormula.ROW,
                    _SliceIndexFormula.COL,
                    _SliceIndexFormula.INV_ROW,
                    _SliceIndexFormula.INV_COL,
                ), f"Invalid formula for {slice_name.name} on {face_name.name}: {formula}"

    def test_formula_consistency_across_cube_sizes(self) -> None:
        """
        Verify formula is the same for all cube sizes (size-independent topology).
        """
        formulas_by_size: dict[int, dict[tuple[SliceName, FaceName], str]] = {}

        for size in CUBE_SIZES:
            cube = Cube(size, _test_sp)
            layout = cube.layout
            formulas_by_size[size] = {}

            for slice_name in SliceName:
                slice_layout = layout.get_slice(slice_name)
                rotation_face = slice_layout.get_face_name()
                opposite_face = layout.opposite(rotation_face)

                affected_faces = [f for f in FaceName if f not in (rotation_face, opposite_face)]
                for face_name in affected_faces:
                    formula = _derive_slice_index_formula(layout, slice_name, face_name)
                    formulas_by_size[size][(slice_name, face_name)] = formula

        # Compare all sizes against size 3 (base case)
        base_formulas = formulas_by_size[3]
        for size in CUBE_SIZES[1:]:
            for key, formula in formulas_by_size[size].items():
                assert formula == base_formulas[key], (
                    f"Formula mismatch for {key} between size 3 and {size}: "
                    f"{base_formulas[key]} vs {formula}"
                )


class TestSliceIndexAgainstWalkingInfo:
    """
    Validate slice index formula against walking info (ground truth).

    This tests the inverse relationship:
    - Walking info: (slice_index, slot) -> (row, col)
    - Formula: (row, col) -> slice_index

    Testing across all cube sizes, slices, faces, and coordinates.
    """

    @pytest.mark.parametrize("cube_size", CUBE_SIZES)
    def test_slice_index_is_inverse_of_walking_info(self, cube_size: int) -> None:
        """
        Verify: walking_info.compute_point(idx, slot) gives point,
                formula(point) gives idx back.

        For each cube size, slice, face, and slice_index:
        1. Get point from walking info for this slice_index
        2. Compute slice_index back using the formula
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

                    # Formula returns 1-based slice index
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

        This confirms the formula correctly extracts the relevant coordinate
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
