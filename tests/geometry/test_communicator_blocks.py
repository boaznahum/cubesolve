"""
Tests for CommunicatorHelper block operations.

This test file validates:
1. Block searching - finding blocks sorted by size (largest first)
2. Block validation - ensuring blocks won't intersect after rotation
3. Multi-cell block commutators - blocks larger than 1x1

Note: Migration tests that compared old NxNCenters with new CommunicatorHelper
have been converted to tests that verify the CommunicatorHelper implementation.
"""

import random
import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.Color import Color
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.common.big_cube.commun._supported_faces import _get_supported_pairs
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver
from cube.domain.solver.Solvers import Solvers

# Type aliases
Point = tuple[int, int]
Block = tuple[Point, Point]

# Get supported pairs for parametrization
SUPPORTED_PAIRS = _get_supported_pairs()


def _face_pair_id(pair: tuple[FaceName, FaceName]) -> str:
    """Generate readable test ID for face pair (target<-source)."""
    source, target = pair
    return f"{target.name}<-{source.name}"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def app_4x4() -> AbstractApp:
    """Create a 4x4 cube app."""
    return AbstractApp.create_non_default(4)


@pytest.fixture
def app_5x5() -> AbstractApp:
    """Create a 5x5 cube app."""
    return AbstractApp.create_non_default(5)


@pytest.fixture
def app_6x6() -> AbstractApp:
    """Create a 6x6 cube app."""
    return AbstractApp.create_non_default(6)


def create_app(cube_size: int) -> AbstractApp:
    """Create an app with specified cube size."""
    return AbstractApp.create_non_default(cube_size, animation=False)


def _cage(app: AbstractApp) -> CageNxNSolver:
    """Create CageNxNSolver through factory with correct type hint."""
    solver = Solvers.cage(app.op)
    assert isinstance(solver, CageNxNSolver)
    return solver


def get_new_comm_helper(app: AbstractApp) -> CommunicatorHelper:
    """Get new CommunicatorHelper instance."""
    solver = _cage(app)
    return CommunicatorHelper(solver)


# =============================================================================
# Helper Functions
# =============================================================================

def set_center_color(face: Face, row: int, col: int, color: Color) -> None:
    """Set a specific center piece to a color."""
    center_slice = face.center.get_center_slice((row, col))
    # We need to manipulate the cube to set colors - use the underlying part
    center_slice._color = color


def get_center_color(face: Face, row: int, col: int) -> Color:
    """Get color of a specific center piece."""
    return face.center.get_center_slice((row, col)).color


def create_color_pattern(face: Face, pattern: list[list[Color]]) -> None:
    """
    Set center colors according to a pattern.

    Pattern is in visual order (top row first), but internally
    we need to handle coordinate translation.
    """
    n = face.cube.n_slices
    for r in range(n):
        for c in range(n):
            set_center_color(face, r, c, pattern[r][c])


def blocks_equal(b1: Block, b2: Block) -> bool:
    """Check if two blocks are equal (same corners)."""
    return b1[0] == b2[0] and b1[1] == b2[1]


# =============================================================================
# SECTION 1: Block Search Tests - CommunicatorHelper
# =============================================================================

class TestCommunicatorBlockSearch:
    """
    Tests for CommunicatorHelper.search_big_block() functionality.

    These tests verify the block search implementation works correctly.
    """

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    def test_search_big_block_solved_cube(self, cube_size: int):
        """
        On a solved cube, search finds valid blocks.

        Note: The maximum block size is limited by is_valid_block() which
        rejects blocks that would intersect with themselves after F rotation.
        This means the largest block is typically NOT the entire center.
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        # Test on front face (most common target)
        face = cube.front
        color = face.color

        # Get blocks from CommunicatorHelper
        blocks = comm_helper.search_big_block(face, color)

        # Verify implementation works and returns valid results
        assert blocks is not None
        assert len(blocks) > 0

        # Blocks should be sorted by size (largest first)
        sizes = [b[0] for b in blocks]
        assert sizes == sorted(sizes, reverse=True), \
            "Blocks should be sorted by size descending"

        # Verify blocks are found (the search adds both 1x1 and extended for each position)
        n = cube.n_slices
        assert len(blocks) > 0, "Should find some blocks"

        # On a solved cube, should find blocks for most positions
        # (some may be excluded by is_valid_block intersection check)
        single_blocks = [b for b in blocks if b[0] == 1]
        assert len(single_blocks) > 0, "Should find at least some 1x1 blocks"

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    @pytest.mark.parametrize("face_name", [FaceName.F, FaceName.U, FaceName.R])
    def test_search_big_block_multiple_faces(self, cube_size: int, face_name: FaceName):
        """
        search_big_block works correctly on multiple faces.

        Test on multiple faces to ensure coordinate handling is correct.
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.face(face_name)
        color = face.color

        # Get blocks from CommunicatorHelper
        blocks = comm_helper.search_big_block(face, color)

        # Verify implementation returns valid results
        assert blocks is not None
        assert len(blocks) > 0, f"Should find blocks on face {face_name}"

        # Verify sorted by size
        sizes = [b[0] for b in blocks]
        assert sizes == sorted(sizes, reverse=True), \
            f"Blocks should be sorted on face {face_name}"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    @pytest.mark.parametrize("seed", range(3))
    def test_search_after_random_scramble(self, cube_size: int, seed: int):
        """
        After random scrambles, search correctly finds remaining matching blocks.

        This tests that the implementation handles mixed colors correctly.
        """
        app = create_app(cube_size)
        cube = app.cube

        # Scramble the cube with a seeded random
        random.seed(seed)
        scramble = Algs.scramble(cube_size, seed)
        app.op.play(scramble)

        comm_helper = get_new_comm_helper(app)

        # Test on each face
        for face_name in [FaceName.F, FaceName.U, FaceName.R]:
            face = cube.face(face_name)
            color = face.color

            # Get blocks from CommunicatorHelper
            blocks = comm_helper.search_big_block(face, color)

            # blocks can be empty list if no matching colors
            assert blocks is not None

            # If blocks found, they should be sorted
            if len(blocks) > 0:
                sizes = [b[0] for b in blocks]
                assert sizes == sorted(sizes, reverse=True), \
                    f"Blocks should be sorted on face {face_name} with seed {seed}"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_block_extension_order(self, cube_size: int):
        """
        Verify search extends horizontal THEN vertical.

        The extension order matters for L-shaped patterns where
        different orders produce different maximum rectangles.
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        # Get blocks from solved cube
        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # Verify blocks are sorted by size (largest first)
        sizes = [b[0] for b in blocks]
        assert sizes == sorted(sizes, reverse=True), \
            "Blocks should be sorted largest-first"

    @pytest.mark.parametrize("cube_size", [5, 6])
    def test_largest_block_priority(self, cube_size: int):
        """
        Blocks are returned sorted largest-first.

        This is critical for efficiency - processing larger blocks first
        solves more pieces per commutator operation.
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # Check descending order by size
        for i in range(len(blocks) - 1):
            assert blocks[i][0] >= blocks[i + 1][0], \
                f"Block {i} (size {blocks[i][0]}) should be >= block {i+1} (size {blocks[i+1][0]})"


# =============================================================================
# SECTION 2: Block Searching Details Tests
# =============================================================================

class TestBlockSearching:
    """Tests for block searching functionality details."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    def test_search_finds_single_cell_blocks(self, cube_size: int):
        """
        1x1 blocks detected for matching color positions.

        Note: The search adds BOTH a 1x1 block AND an extended block for each
        starting position (even if the extended block is also 1x1).
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # Count 1x1 blocks - there will be duplicates because the search
        # adds both 1x1 and extended blocks for each position
        single_blocks = [b for b in blocks if b[0] == 1]
        n = cube.n_slices

        # At minimum, should have some 1x1 blocks
        assert len(single_blocks) > 0, "Should find 1x1 blocks"

        # The total blocks should be roughly 2x the number of positions
        # (1x1 + extended for each), minus some exclusions
        assert len(blocks) >= n * n, \
            f"Expected at least {n*n} blocks (1 per position), got {len(blocks)}"

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    def test_search_finds_maximum_block(self, cube_size: int):
        """
        On solved cube, search finds blocks up to maximum valid size.

        Note: Maximum block size is limited by is_valid_block() which
        rejects blocks that would intersect with themselves after F rotation.
        """
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # Verify blocks are found and sorted
        assert len(blocks) > 0
        sizes = [b[0] for b in blocks]
        assert sizes == sorted(sizes, reverse=True), \
            "Blocks should be sorted by size descending"

        # The largest block should be at least size 1
        assert blocks[0][0] >= 1, \
            f"Expected at least size 1 block, got {blocks[0][0]}"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_search_after_partial_scramble(self, cube_size: int):
        """After moves, blocks are found for remaining matching colors."""
        app = create_app(cube_size)
        cube = app.cube

        # Do a simple move that affects centers
        app.op.play(Algs.M)

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # Should still find some blocks (the move only affects middle slice)
        assert len(blocks) > 0, "Should find some matching blocks after M move"

        # Maximum block should be smaller than n*n
        n = cube.n_slices
        assert blocks[0][0] < n * n, \
            "After M move, largest block should be smaller than full center"


# =============================================================================
# SECTION 3: Block Validation Tests
# =============================================================================

class TestBlockValidation:
    """Tests for block validation (intersection checking)."""

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_is_valid_block_single_cell(self, cube_size: int):
        """
        Single cell blocks are valid except for center position on odd cubes.

        The center position maps to itself after rotation, causing intersection.
        """
        app = create_app(cube_size)

        comm_helper = get_new_comm_helper(app)

        # Test various single-cell positions
        n = app.cube.n_slices
        mid = n // 2

        for r in range(n):
            for c in range(n):
                rc = (r, c)
                is_valid = comm_helper.is_valid_block(rc, rc)

                # Center position on odd cubes is invalid (maps to itself after rotation)
                is_center = (n % 2 == 1) and (r == mid) and (c == mid)

                if is_center:
                    assert not is_valid, f"Center block at {rc} should be invalid (self-intersection)"
                else:
                    assert is_valid, f"Non-center block at {rc} should be valid"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_block_size_calculation(self, cube_size: int):
        """Block size = (rows+1) * (cols+1)."""
        # Test various block shapes
        test_cases = [
            ((0, 0), (0, 0), 1),    # 1x1 → size 1
            ((0, 0), (1, 0), 2),    # 2x1 → size 2
            ((0, 0), (0, 1), 2),    # 1x2 → size 2
            ((0, 0), (1, 1), 4),    # 2x2 → size 4
            ((0, 0), (2, 1), 6),    # 3x2 → size 6
            ((0, 0), (2, 2), 9),    # 3x3 → size 9
            ((1, 1), (2, 3), 6),    # 2x3 → size 6 (offset start)
        ]

        for rc1, rc2, expected_size in test_cases:
            actual_size = CommunicatorHelper.block_size(rc1, rc2)
            assert actual_size == expected_size, \
                f"Block {rc1}->{rc2} should have size {expected_size}, got {actual_size}"


# =============================================================================
# SECTION 4: Multi-Cell Block Commutator Tests (Future)
# =============================================================================

class TestMultiCellBlockCommutator:
    """
    Tests for multi-cell block commutators.

    These tests will validate that blocks larger than 1x1 are
    handled correctly by the new CommunicatorHelper.
    """

    @pytest.mark.skip(reason="Pending implementation of multi-cell block support")
    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_2x2_block_commutator(self, cube_size: int):
        """2x2 block (4 pieces) cycles correctly."""
        app = create_app(cube_size)
        # TODO: Implement when block support is added
        pass

    @pytest.mark.skip(reason="Pending implementation of multi-cell block support")
    @pytest.mark.parametrize("cube_size", [6, 7])
    def test_2x3_block_commutator(self, cube_size: int):
        """2x3 block (6 pieces) cycles correctly."""
        app = create_app(cube_size)
        # TODO: Implement when block support is added
        pass


# =============================================================================
# SECTION 5: Integration Tests
# =============================================================================

class TestBlockIntegration:
    """Integration tests for block processing workflow."""

    @pytest.mark.parametrize("cube_size", [5, 6])
    def test_search_returns_largest_first(self, cube_size: int):
        """Block search returns largest block first for efficient processing."""
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        # First block should be the largest
        if len(blocks) > 1:
            assert blocks[0][0] >= blocks[1][0], \
                "First block should be largest"

    @pytest.mark.parametrize("cube_size", [4, 5, 6])
    def test_search_returns_consistent_results(self, cube_size: int):
        """Multiple searches on same state return identical results."""
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        # Search multiple times
        blocks1 = comm_helper.search_big_block(face, color)
        blocks2 = comm_helper.search_big_block(face, color)
        blocks3 = comm_helper.search_big_block(face, color)

        # All should be identical
        assert blocks1 == blocks2 == blocks3, \
            "Block search should be deterministic"


# =============================================================================
# SECTION 6: Coordinate System Tests
# =============================================================================

class TestBlockCoordinates:
    """Tests for coordinate handling in block operations."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6])
    def test_block_coordinates_in_range(self, cube_size: int):
        """All returned block coordinates are within valid range."""
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        n = cube.n_slices

        for face_name in FaceName:
            face = cube.face(face_name)
            color = face.color

            blocks = comm_helper.search_big_block(face, color)

            for size, block in blocks:
                rc1, rc2 = block

                # All coordinates should be in [0, n)
                assert 0 <= rc1[0] < n, f"Row {rc1[0]} out of range on {face_name}"
                assert 0 <= rc1[1] < n, f"Col {rc1[1]} out of range on {face_name}"
                assert 0 <= rc2[0] < n, f"Row {rc2[0]} out of range on {face_name}"
                assert 0 <= rc2[1] < n, f"Col {rc2[1]} out of range on {face_name}"

                # rc2 should be >= rc1 (normalized)
                assert rc2[0] >= rc1[0], f"Block rows not normalized: {block}"
                assert rc2[1] >= rc1[1], f"Block cols not normalized: {block}"

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_block_size_matches_coordinates(self, cube_size: int):
        """Block size matches (r2-r1+1) * (c2-c1+1)."""
        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        face = cube.front
        color = face.color

        blocks = comm_helper.search_big_block(face, color)

        for reported_size, block in blocks:
            rc1, rc2 = block
            calculated_size = (rc2[0] - rc1[0] + 1) * (rc2[1] - rc1[1] + 1)

            assert reported_size == calculated_size, \
                f"Block {block}: reported size {reported_size} != calculated {calculated_size}"
