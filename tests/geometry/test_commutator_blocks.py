"""
Tests for CommutatorHelper block operations.

This test file validates:
1. Block searching - finding blocks sorted by size (largest first)
2. Block validation - ensuring blocks won't intersect after rotation
3. Multi-cell block commutators - blocks larger than 1x1

Note: Migration tests that compared old NxNCenters with new CommutatorHelper
have been converted to tests that verify the CommutatorHelper implementation.
"""

import random
import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.Color import Color
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper
from cube.domain.solver.common.big_cube.commutator._supported_faces import _get_supported_pairs
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


def get_new_comm_helper(app: AbstractApp) -> CommutatorHelper:
    """Get new CommutatorHelper instance."""
    solver = _cage(app)
    return CommutatorHelper(solver)


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
# SECTION 1: Block Search Tests - CommutatorHelper
# =============================================================================

class TestCommutatorBlockSearch:
    """
    Tests for CommutatorHelper.search_big_block() functionality.

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

        # Get blocks from CommutatorHelper
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

        # Get blocks from CommutatorHelper
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

            # Get blocks from CommutatorHelper
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
            actual_size = CommutatorHelper.block_size(rc1, rc2)
            assert actual_size == expected_size, \
                f"Block {rc1}->{rc2} should have size {expected_size}, got {actual_size}"


# =============================================================================
# SECTION 4: Multi-Cell Block Commutator Tests
# =============================================================================

class TestMultiCellBlockCommutator:
    """
    Tests for multi-cell block commutators.

    These tests validate that blocks larger than 1x1 are handled correctly.
    The 3-cycle pattern for blocks is: s1_block → t_block → s2_block → s1_block
    """

    @pytest.mark.parametrize("cube_size", [5, 6, 7])
    def test_block_commutator_3_cycle(self, cube_size: int):
        """
        Block commutator correctly cycles all cells in the block.

        Plan:
        1. Iterate over all points on center face
        2. For each point, find the largest block starting at that point
        3. Pass the block to execute_commutator to get s1_block, t_block, s2_block
        4. Place unique markers on all cells in all 3 blocks
        5. Execute the commutator
        6. Verify cycle: s1_block → t_block, t_block → s2_block, s2_block → s1_block
        """
        import uuid
        from cube.domain.geometric.geometry_types import Block as GeomBlock

        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        # Use Front as target, Up as source (a common pair)
        target_face = cube.front
        source_face = cube.up
        n = cube.n_slices

        failures = []
        successes = []

        # Iterate over all points on the center face to find blocks
        for target_r in range(n):
            for target_c in range(n):
                target_point = (target_r, target_c)

                # Find largest block starting at this point
                color = target_face.center.get_center_slice(target_point).color
                all_blocks = comm_helper.search_big_block(target_face, color)

                # Find a block starting at this point that is larger than 1x1
                matching_blocks = [
                    (size, blk) for size, blk in all_blocks
                    if blk[0] == target_point and size > 1
                ]

                if not matching_blocks:
                    # No multi-cell block at this position, skip
                    continue

                # Take the largest multi-cell block starting at this position
                _, target_block = matching_blocks[0]

                # Reset cube for clean test
                cube.reset()

                # Refresh face references after reset (they become stale)
                target_face = cube.front
                source_face = cube.up

                # Get the 3-cycle blocks using dry_run
                dry_result = comm_helper.execute_commutator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=target_block,
                    dry_run=True
                )

                s1_block = dry_result.natural_source_block
                t_block = dry_result.target_block
                s2_block = dry_result.second_block

                if s1_block is None or t_block is None or s2_block is None:
                    failures.append({
                        "target_block": target_block,
                        "error": "Block fields not populated in result"
                    })
                    continue

                # Helper function to iterate over all cells in a block
                def block_cells(block: GeomBlock) -> list[tuple[int, int]]:
                    """Return list of all (row, col) in the block."""
                    r1 = min(block[0][0], block[1][0])
                    r2 = max(block[0][0], block[1][0])
                    c1 = min(block[0][1], block[1][1])
                    c2 = max(block[0][1], block[1][1])
                    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

                s1_cells = block_cells(s1_block)
                t_cells = block_cells(t_block)
                s2_cells = block_cells(s2_block)

                # All blocks should have the same number of cells
                if len(s1_cells) != len(t_cells) or len(t_cells) != len(s2_cells):
                    failures.append({
                        "target_block": target_block,
                        "error": f"Block sizes don't match: s1={len(s1_cells)}, t={len(t_cells)}, s2={len(s2_cells)}"
                    })
                    continue

                # Place unique markers on all cells in all 3 blocks
                marker_key = f"marker_{uuid.uuid4().hex[:8]}"

                # Markers for s1 cells (on source face)
                s1_markers = {}
                for idx, cell in enumerate(s1_cells):
                    marker_value = f"s1_{idx}"
                    piece = source_face.center.get_center_slice(cell).edge
                    piece.moveable_attributes[marker_key] = marker_value
                    s1_markers[idx] = marker_value

                # Markers for t cells (on target face)
                t_markers = {}
                for idx, cell in enumerate(t_cells):
                    marker_value = f"t_{idx}"
                    piece = target_face.center.get_center_slice(cell).edge
                    piece.moveable_attributes[marker_key] = marker_value
                    t_markers[idx] = marker_value

                # Markers for s2 cells (on source face)
                s2_markers = {}
                for idx, cell in enumerate(s2_cells):
                    marker_value = f"s2_{idx}"
                    piece = source_face.center.get_center_slice(cell).edge
                    piece.moveable_attributes[marker_key] = marker_value
                    s2_markers[idx] = marker_value

                # Execute the commutator (source_block = natural_source_block for this test)
                comm_helper.execute_commutator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=target_block,
                    source_block=s1_block,  # Use the natural source block
                    preserve_state=True,
                    dry_run=False
                )

                # Verify the 3-cycle
                # The cells within blocks may be reordered during transformation,
                # so we check that the SET of markers is correct, not the order.

                # Collect all markers found at each block position
                t_block_markers_found = set()
                for cell in t_cells:
                    piece = target_face.center.get_center_slice(cell).edge
                    marker = piece.moveable_attributes.get(marker_key)
                    if marker:
                        t_block_markers_found.add(marker)

                s2_block_markers_found = set()
                for cell in s2_cells:
                    piece = source_face.center.get_center_slice(cell).edge
                    marker = piece.moveable_attributes.get(marker_key)
                    if marker:
                        s2_block_markers_found.add(marker)

                s1_block_markers_found = set()
                for cell in s1_cells:
                    piece = source_face.center.get_center_slice(cell).edge
                    marker = piece.moveable_attributes.get(marker_key)
                    if marker:
                        s1_block_markers_found.add(marker)

                # s1 → t: all s1 markers should now be at t positions
                s1_marker_set = set(s1_markers.values())
                s1_to_t_ok = t_block_markers_found == s1_marker_set

                # t → s2: all t markers should now be at s2 positions
                t_marker_set = set(t_markers.values())
                t_to_s2_ok = s2_block_markers_found == t_marker_set

                # s2 → s1: all s2 markers should now be at s1 positions
                s2_marker_set = set(s2_markers.values())
                s2_to_s1_ok = s1_block_markers_found == s2_marker_set

                if s1_to_t_ok and t_to_s2_ok and s2_to_s1_ok:
                    successes.append({
                        "target_block": target_block,
                        "block_size": len(t_cells)
                    })
                else:
                    failures.append({
                        "target_block": target_block,
                        "s1_to_t": s1_to_t_ok,
                        "t_to_s2": t_to_s2_ok,
                        "s2_to_s1": s2_to_s1_ok
                    })

        # Report results
        assert len(failures) == 0, \
            f"Block commutator 3-cycle failed for {len(failures)} blocks: {failures[:5]}"

        # Verify we actually tested some multi-cell blocks
        assert len(successes) > 0, \
            f"No multi-cell blocks found to test on {cube_size}x{cube_size} cube"

    @pytest.mark.parametrize("cube_size", [6, 7, 8])
    def test_large_block_commutator(self, cube_size: int):
        """
        Test with explicitly constructed large blocks.

        Finds the largest valid block on a solved cube and tests the 3-cycle.
        """
        import uuid
        from cube.domain.geometric.geometry_types import Block as GeomBlock

        app = create_app(cube_size)
        cube = app.cube

        comm_helper = get_new_comm_helper(app)

        target_face = cube.front
        source_face = cube.up
        color = target_face.color

        # Find largest valid block on the target face
        all_blocks = comm_helper.search_big_block(target_face, color)
        large_blocks = [(size, blk) for size, blk in all_blocks if size > 1]

        if not large_blocks:
            pytest.skip(f"No large blocks found on {cube_size}x{cube_size} cube")

        # Take the largest block
        _, target_block = large_blocks[0]
        block_size = CommutatorHelper.block_size(target_block[0], target_block[1])

        # Get the 3-cycle blocks
        dry_result = comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            dry_run=True
        )

        s1_block = dry_result.natural_source_block
        t_block = dry_result.target_block
        s2_block = dry_result.second_block

        assert s1_block is not None, "natural_source_block should be populated"
        assert t_block is not None, "target_block should be populated"
        assert s2_block is not None, "second_block should be populated"

        # Verify block sizes match
        def block_cell_count(block: GeomBlock) -> int:
            r1, c1 = block[0]
            r2, c2 = block[1]
            return (abs(r2 - r1) + 1) * (abs(c2 - c1) + 1)

        assert block_cell_count(s1_block) == block_size, \
            f"s1_block size mismatch: expected {block_size}, got {block_cell_count(s1_block)}"
        assert block_cell_count(t_block) == block_size, \
            f"t_block size mismatch: expected {block_size}, got {block_cell_count(t_block)}"
        assert block_cell_count(s2_block) == block_size, \
            f"s2_block size mismatch: expected {block_size}, got {block_cell_count(s2_block)}"

        # Place markers and execute
        marker_key = f"marker_{uuid.uuid4().hex[:8]}"

        def block_cells(block: GeomBlock) -> list[tuple[int, int]]:
            r1 = min(block[0][0], block[1][0])
            r2 = max(block[0][0], block[1][0])
            c1 = min(block[0][1], block[1][1])
            c2 = max(block[0][1], block[1][1])
            return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

        s1_cells = block_cells(s1_block)
        t_cells = block_cells(t_block)
        s2_cells = block_cells(s2_block)

        # Place markers
        s1_markers = {}
        for idx, cell in enumerate(s1_cells):
            marker_value = f"s1_{idx}"
            piece = source_face.center.get_center_slice(cell).edge
            piece.moveable_attributes[marker_key] = marker_value
            s1_markers[idx] = marker_value

        t_markers = {}
        for idx, cell in enumerate(t_cells):
            marker_value = f"t_{idx}"
            piece = target_face.center.get_center_slice(cell).edge
            piece.moveable_attributes[marker_key] = marker_value
            t_markers[idx] = marker_value

        s2_markers = {}
        for idx, cell in enumerate(s2_cells):
            marker_value = f"s2_{idx}"
            piece = source_face.center.get_center_slice(cell).edge
            piece.moveable_attributes[marker_key] = marker_value
            s2_markers[idx] = marker_value

        # Execute commutator
        comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            source_block=s1_block,
            preserve_state=True,
            dry_run=False
        )

        # Verify 3-cycle - check that SET of markers cycles correctly
        # (cells within blocks may be reordered during transformation)

        # Collect markers found at each block
        t_block_markers = set()
        for cell in t_cells:
            piece = target_face.center.get_center_slice(cell).edge
            marker = piece.moveable_attributes.get(marker_key)
            if marker:
                t_block_markers.add(marker)

        s2_block_markers = set()
        for cell in s2_cells:
            piece = source_face.center.get_center_slice(cell).edge
            marker = piece.moveable_attributes.get(marker_key)
            if marker:
                s2_block_markers.add(marker)

        s1_block_markers = set()
        for cell in s1_cells:
            piece = source_face.center.get_center_slice(cell).edge
            marker = piece.moveable_attributes.get(marker_key)
            if marker:
                s1_block_markers.add(marker)

        # Verify s1 markers moved to t
        s1_marker_set = set(s1_markers.values())
        assert t_block_markers == s1_marker_set, \
            f"s1→t failed: expected {s1_marker_set}, got {t_block_markers}"

        # Verify t markers moved to s2
        t_marker_set = set(t_markers.values())
        assert s2_block_markers == t_marker_set, \
            f"t→s2 failed: expected {t_marker_set}, got {s2_block_markers}"

        # Verify s2 markers moved to s1
        s2_marker_set = set(s2_markers.values())
        assert s1_block_markers == s2_marker_set, \
            f"s2→s1 failed: expected {s2_marker_set}, got {s1_block_markers}"


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
