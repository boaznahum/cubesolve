"""
Tests for CommunicatorHelper.

This test module validates the coordinate transformation and commutator
utilities for NxN big cubes. It uses a 7x7 cube as the primary test case.

The CommunicatorHelper provides the mathematical foundation for the
block commutator algorithm: [M', F, M', F', M, F, M, F']

See Also
--------
- docs/communicator-helper.md : Development tracking document
- src/cube/domain/solver/common/big_cube/CommunicatorHelper.py : The helper class
"""

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.solver.common.big_cube.CommunicatorHelper import (
    CommunicatorHelper,
    Point,
)
from tests.test_utils import _test_sp


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def cube_7x7() -> Cube:
    """Create a 7x7 cube for testing."""
    return Cube(7, sp=_test_sp)


@pytest.fixture
def cube_5x5() -> Cube:
    """Create a 5x5 cube for testing."""
    return Cube(5, sp=_test_sp)


@pytest.fixture
def cube_4x4() -> Cube:
    """Create a 4x4 cube for testing (even cube)."""
    return Cube(4, sp=_test_sp)


@pytest.fixture
def helper_7x7(cube_7x7: Cube) -> CommunicatorHelper:
    """Create a helper for a 7x7 cube."""
    return CommunicatorHelper(cube_7x7)


@pytest.fixture
def helper_5x5(cube_5x5: Cube) -> CommunicatorHelper:
    """Create a helper for a 5x5 cube."""
    return CommunicatorHelper(cube_5x5)


@pytest.fixture
def helper_4x4(cube_4x4: Cube) -> CommunicatorHelper:
    """Create a helper for a 4x4 cube."""
    return CommunicatorHelper(cube_4x4)


# =============================================================================
# Test: Basic Properties
# =============================================================================

class TestBasicProperties:
    """Test basic helper properties."""

    def test_n_slices_7x7(self, helper_7x7: CommunicatorHelper):
        """7x7 cube has 5 center slices per dimension."""
        assert helper_7x7.n_slices == 5

    def test_n_slices_5x5(self, helper_5x5: CommunicatorHelper):
        """5x5 cube has 3 center slices per dimension."""
        assert helper_5x5.n_slices == 3

    def test_n_slices_4x4(self, helper_4x4: CommunicatorHelper):
        """4x4 cube has 2 center slices per dimension."""
        assert helper_4x4.n_slices == 2

    def test_cube_reference(self, cube_7x7: Cube, helper_7x7: CommunicatorHelper):
        """Helper maintains reference to cube."""
        assert helper_7x7.cube is cube_7x7


# =============================================================================
# Test: inv() Function
# =============================================================================

class TestInv:
    """Test the inv() index inversion function."""

    def test_inv_endpoints_7x7(self, helper_7x7: CommunicatorHelper):
        """Test inv() on endpoints for 7x7 (n_slices=5)."""
        assert helper_7x7.inv(0) == 4
        assert helper_7x7.inv(4) == 0

    def test_inv_middle_7x7(self, helper_7x7: CommunicatorHelper):
        """Test inv() on middle index for odd cube."""
        # Middle index stays at middle
        assert helper_7x7.inv(2) == 2

    def test_inv_self_inverse(self, helper_7x7: CommunicatorHelper):
        """inv(inv(i)) == i (self-inverse property)."""
        for i in range(helper_7x7.n_slices):
            assert helper_7x7.inv(helper_7x7.inv(i)) == i

    def test_inv_all_values_5x5(self, helper_5x5: CommunicatorHelper):
        """Test all inv() values for 5x5 cube."""
        # n_slices = 3: inv maps 0↔2, 1↔1
        assert helper_5x5.inv(0) == 2
        assert helper_5x5.inv(1) == 1
        assert helper_5x5.inv(2) == 0

    def test_inv_even_cube_4x4(self, helper_4x4: CommunicatorHelper):
        """Test inv() for even cube (no middle)."""
        # n_slices = 2: inv maps 0↔1
        assert helper_4x4.inv(0) == 1
        assert helper_4x4.inv(1) == 0


# =============================================================================
# Test: Point Rotation
# =============================================================================

class TestRotation:
    """Test clockwise and counter-clockwise point rotation."""

    def test_rotate_clockwise_corner(self, helper_5x5: CommunicatorHelper):
        """Test clockwise rotation of corner points."""
        # (0,0) → (2,0) → (2,2) → (0,2) → (0,0)
        assert helper_5x5.rotate_point_clockwise((0, 0)) == (2, 0)
        assert helper_5x5.rotate_point_clockwise((2, 0)) == (2, 2)
        assert helper_5x5.rotate_point_clockwise((2, 2)) == (0, 2)
        assert helper_5x5.rotate_point_clockwise((0, 2)) == (0, 0)

    def test_rotate_counterclockwise_corner(self, helper_5x5: CommunicatorHelper):
        """Test counter-clockwise rotation of corner points."""
        # (0,0) → (0,2) → (2,2) → (2,0) → (0,0)
        assert helper_5x5.rotate_point_counterclockwise((0, 0)) == (0, 2)
        assert helper_5x5.rotate_point_counterclockwise((0, 2)) == (2, 2)
        assert helper_5x5.rotate_point_counterclockwise((2, 2)) == (2, 0)
        assert helper_5x5.rotate_point_counterclockwise((2, 0)) == (0, 0)

    def test_rotate_full_circle(self, helper_7x7: CommunicatorHelper):
        """4 rotations return to original position."""
        original = (1, 3)
        rotated = helper_7x7.rotate_point_clockwise(original, n=4)
        assert rotated == original

    def test_rotate_n_times(self, helper_5x5: CommunicatorHelper):
        """Test n parameter for multiple rotations."""
        # 2 clockwise rotations = 180°
        assert helper_5x5.rotate_point_clockwise((0, 0), n=2) == (2, 2)
        # 3 clockwise rotations = 270° = 1 counter-clockwise
        assert helper_5x5.rotate_point_clockwise((0, 0), n=3) == (0, 2)

    def test_clockwise_counterclockwise_inverse(self, helper_7x7: CommunicatorHelper):
        """Clockwise then counter-clockwise returns to original."""
        original = (2, 4)
        rotated = helper_7x7.rotate_point_clockwise(original)
        back = helper_7x7.rotate_point_counterclockwise(rotated)
        assert back == original

    def test_center_stays_fixed(self, helper_5x5: CommunicatorHelper):
        """Center point of odd cube stays fixed under rotation."""
        center = (1, 1)  # Center of 3x3 grid
        assert helper_5x5.rotate_point_clockwise(center) == center
        assert helper_5x5.rotate_point_counterclockwise(center) == center


# =============================================================================
# Test: Source/Target Mapping
# =============================================================================

class TestSourceTargetMapping:
    """Test coordinate mapping between Front, Up, and Back faces."""

    def test_up_face_same_coords(self, helper_5x5: CommunicatorHelper):
        """Up face has same coordinates as Front."""
        for r in range(3):
            for c in range(3):
                point = (r, c)
                assert helper_5x5.point_on_source(is_back=False, rc=point) == point
                assert helper_5x5.point_on_target(source_is_back=False, rc=point) == point

    def test_back_face_mirrored(self, helper_5x5: CommunicatorHelper):
        """Back face is mirrored in both axes."""
        # (0,0) on front → (2,2) on back
        assert helper_5x5.point_on_source(is_back=True, rc=(0, 0)) == (2, 2)
        assert helper_5x5.point_on_source(is_back=True, rc=(0, 2)) == (2, 0)
        assert helper_5x5.point_on_source(is_back=True, rc=(2, 0)) == (0, 2)
        assert helper_5x5.point_on_source(is_back=True, rc=(2, 2)) == (0, 0)

    def test_back_center_stays(self, helper_5x5: CommunicatorHelper):
        """Center of back face maps to center."""
        center = (1, 1)
        assert helper_5x5.point_on_source(is_back=True, rc=center) == center

    def test_source_target_inverse(self, helper_7x7: CommunicatorHelper):
        """point_on_source and point_on_target are inverses."""
        for r in range(5):
            for c in range(5):
                point = (r, c)
                # For back face
                on_source = helper_7x7.point_on_source(is_back=True, rc=point)
                back_to_target = helper_7x7.point_on_target(source_is_back=True, rc=on_source)
                assert back_to_target == point

    def test_block_on_source(self, helper_5x5: CommunicatorHelper):
        """Test block coordinate conversion."""
        block = helper_5x5.block_on_source(is_back=True, rc1=(0, 0), rc2=(1, 1))
        assert block == ((2, 2), (1, 1))


# =============================================================================
# Test: 2D Range Iteration
# =============================================================================

class TestRange2D:
    """Test 2D block iteration."""

    def test_single_cell(self, helper_5x5: CommunicatorHelper):
        """Single cell block yields one point."""
        points = list(CommunicatorHelper.range_2d((1, 1), (1, 1)))
        assert points == [(1, 1)]

    def test_row_block(self, helper_5x5: CommunicatorHelper):
        """Row block (1x3)."""
        points = list(CommunicatorHelper.range_2d((0, 0), (0, 2)))
        assert points == [(0, 0), (0, 1), (0, 2)]

    def test_column_block(self, helper_5x5: CommunicatorHelper):
        """Column block (3x1)."""
        points = list(CommunicatorHelper.range_2d((0, 1), (2, 1)))
        assert points == [(0, 1), (1, 1), (2, 1)]

    def test_square_block(self, helper_5x5: CommunicatorHelper):
        """Square block (2x2)."""
        points = list(CommunicatorHelper.range_2d((0, 0), (1, 1)))
        assert points == [(0, 0), (0, 1), (1, 0), (1, 1)]

    def test_reversed_corners(self, helper_5x5: CommunicatorHelper):
        """Reversed corners give same result."""
        forward = list(CommunicatorHelper.range_2d((0, 0), (1, 2)))
        backward = list(CommunicatorHelper.range_2d((1, 2), (0, 0)))
        assert forward == backward


# =============================================================================
# Test: Block Size
# =============================================================================

class TestBlockSize:
    """Test block size calculations."""

    def test_single_cell(self):
        """Single cell has size 1."""
        assert CommunicatorHelper.block_size((0, 0), (0, 0)) == 1

    def test_row_size(self):
        """Row block size."""
        assert CommunicatorHelper.block_size((0, 0), (0, 2)) == 3

    def test_column_size(self):
        """Column block size."""
        assert CommunicatorHelper.block_size((0, 0), (2, 0)) == 3

    def test_square_size(self):
        """Square block size."""
        assert CommunicatorHelper.block_size((0, 0), (2, 2)) == 9

    def test_rectangle_size(self):
        """Rectangle block size."""
        assert CommunicatorHelper.block_size((0, 0), (1, 2)) == 6

    def test_dimensions(self):
        """Block dimensions."""
        assert CommunicatorHelper.block_dimensions((0, 0), (2, 1)) == (3, 2)


# =============================================================================
# Test: 1D Range Intersection
# =============================================================================

class TestRangeIntersection:
    """Test 1D range intersection detection."""

    def test_no_overlap(self):
        """Non-overlapping ranges."""
        assert not CommunicatorHelper.ranges_intersect_1d((0, 1), (2, 3))
        assert not CommunicatorHelper.ranges_intersect_1d((2, 3), (0, 1))

    def test_overlap(self):
        """Overlapping ranges."""
        assert CommunicatorHelper.ranges_intersect_1d((0, 2), (1, 3))
        assert CommunicatorHelper.ranges_intersect_1d((1, 3), (0, 2))

    def test_touch(self):
        """Touching ranges (share endpoint)."""
        assert CommunicatorHelper.ranges_intersect_1d((0, 1), (1, 2))

    def test_contained(self):
        """One range contains the other."""
        assert CommunicatorHelper.ranges_intersect_1d((0, 3), (1, 2))
        assert CommunicatorHelper.ranges_intersect_1d((1, 2), (0, 3))

    def test_reversed_ranges(self):
        """Reversed range endpoints still work."""
        assert CommunicatorHelper.ranges_intersect_1d((2, 0), (1, 3))


# =============================================================================
# Test: Symmetric Points
# =============================================================================

class TestSymmetricPoints:
    """Test four-fold rotational symmetry."""

    def test_corner_symmetry(self, helper_5x5: CommunicatorHelper):
        """Corner points have 4 distinct symmetric positions."""
        points = list(helper_5x5.get_four_symmetric_points(0, 0))
        assert len(points) == 4
        # All should be distinct (for corners)
        assert set(points) == {(0, 0), (0, 2), (2, 2), (2, 0)}

    def test_center_symmetry(self, helper_5x5: CommunicatorHelper):
        """Center point maps to itself 4 times."""
        points = list(helper_5x5.get_four_symmetric_points(1, 1))
        assert points == [(1, 1), (1, 1), (1, 1), (1, 1)]

    def test_is_center_point_odd(self, helper_5x5: CommunicatorHelper):
        """Center detection for odd cube."""
        assert helper_5x5.is_center_point(1, 1)
        assert not helper_5x5.is_center_point(0, 0)
        assert not helper_5x5.is_center_point(1, 0)

    def test_is_center_point_even(self, helper_4x4: CommunicatorHelper):
        """Even cubes have no center point."""
        assert not helper_4x4.is_center_point(0, 0)
        assert not helper_4x4.is_center_point(0, 1)
        assert not helper_4x4.is_center_point(1, 0)
        assert not helper_4x4.is_center_point(1, 1)


# =============================================================================
# Test: Visualization
# =============================================================================

class TestVisualization:
    """Test ASCII grid visualization."""

    def test_empty_grid(self, helper_5x5: CommunicatorHelper):
        """Test visualization of empty grid."""
        viz = helper_5x5.visualize_grid()
        assert "┌" in viz
        assert "┘" in viz
        assert "0" in viz  # Row/column numbers

    def test_highlighted_grid(self, helper_5x5: CommunicatorHelper):
        """Test visualization with highlights."""
        viz = helper_5x5.visualize_grid({(0, 0): "A", (2, 2): "B"})
        assert "A" in viz
        assert "B" in viz

    def test_visualization_7x7(self, helper_7x7: CommunicatorHelper):
        """Test larger grid visualization."""
        viz = helper_7x7.visualize_grid({(0, 0): "X", (4, 4): "Y"})
        # Should have 5 columns (0-4)
        assert "4" in viz
        assert "X" in viz
        assert "Y" in viz


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests verifying coordinate system consistency."""

    def test_rotation_preserves_block_size(self, helper_7x7: CommunicatorHelper):
        """Rotating a block preserves its size."""
        rc1 = (0, 1)
        rc2 = (2, 3)
        original_size = CommunicatorHelper.block_size(rc1, rc2)

        # Rotate both corners
        rc1_rot = helper_7x7.rotate_point_clockwise(rc1)
        rc2_rot = helper_7x7.rotate_point_clockwise(rc2)
        rotated_size = CommunicatorHelper.block_size(rc1_rot, rc2_rot)

        assert original_size == rotated_size

    def test_back_mapping_preserves_block_size(self, helper_7x7: CommunicatorHelper):
        """Mapping to back face preserves block size."""
        rc1 = (0, 1)
        rc2 = (2, 3)
        original_size = CommunicatorHelper.block_size(rc1, rc2)

        on_back = helper_7x7.block_on_source(is_back=True, rc1=rc1, rc2=rc2)
        back_size = CommunicatorHelper.block_size(*on_back)

        assert original_size == back_size

    def test_all_points_reachable_by_rotation(self, helper_5x5: CommunicatorHelper):
        """Verify rotation covers all equivalent positions."""
        # For corner (0,0), all 4 corners should be reachable
        points_from_corner = set(helper_5x5.get_four_symmetric_points(0, 0))
        expected_corners = {(0, 0), (0, 2), (2, 0), (2, 2)}
        assert points_from_corner == expected_corners

        # For edge midpoint (0,1), all 4 edge midpoints should be reachable
        points_from_edge = set(helper_5x5.get_four_symmetric_points(0, 1))
        expected_edges = {(0, 1), (1, 0), (1, 2), (2, 1)}
        assert points_from_edge == expected_edges
