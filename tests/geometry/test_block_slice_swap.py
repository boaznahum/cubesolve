"""
Tests for BlockBySliceSwapHelper.

Test structure:
- For each cube size (5x5, 6x6, 7x7)
- For a representative set of face pairs
- For target blocks at various positions
- Place unique markers on all 6 blocks (3 target, 3 source)
- Execute the slice swap
- Verify ALL 6 markers moved to the correct positions:
  - Target blocks → corresponding source block positions
  - Source blocks → corresponding target block positions
- Verify cube state preserved (edges/corners in position)

The slice swap swaps ALL content on the affected slices, not just the target block.
This means 3 blocks on target face (prefix, main, suffix) each swap with their
corresponding block on the source face, giving 6 blocks total.
"""

import uuid

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.geometric.block import Block
from cube.domain.geometric.geometry_types import Point
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Face import Face
from cube.domain.solver.common.big_cube.commutator.BlockBySliceSwapHelper import (
    BlockBySliceSwapHelper,
    SliceSwapResult,
    get_largest_blocks_containing_point,
)
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver
from cube.domain.solver.Solvers import Solvers


# =============================================================================
# Helpers
# =============================================================================

def _cage(app: AbstractApp) -> CageNxNSolver:
    """Create CageNxNSolver through factory."""
    solver = Solvers.cage(app.op)
    assert isinstance(solver, CageNxNSolver)
    return solver


def _create_helper(app: AbstractApp) -> BlockBySliceSwapHelper:
    """Create a BlockBySliceSwapHelper instance."""
    solver = _cage(app)
    return BlockBySliceSwapHelper(solver)


def _place_block_markers(
    face: Face,
    block: Block | None,
    marker_key: str,
    label: str,
) -> dict[Point, str]:
    """Place unique markers on every cell in a block.

    Returns:
        Dict mapping each cell Point to its marker value.
    """
    if block is None:
        return {}

    markers: dict[Point, str] = {}
    for idx, cell in enumerate(block.cells):
        value = f"{label}_{idx}"
        piece = face.center.get_center_slice(cell).edge
        piece.moveable_attributes[marker_key] = value
        markers[cell] = value
    return markers


def _read_block_markers(
    face: Face,
    block: Block | None,
    marker_key: str,
) -> dict[Point, str | None]:
    """Read marker values from every cell in a block.

    Returns:
        Dict mapping each cell Point to its marker value (or None if absent).
    """
    if block is None:
        return {}

    result: dict[Point, str | None] = {}
    for cell in block.cells:
        piece = face.center.get_center_slice(cell).edge
        result[cell] = piece.moveable_attributes.get(marker_key)
    return result


# =============================================================================
# Tests
# =============================================================================

# =============================================================================
# Block generators (must be before test case generation)
# =============================================================================

def _get_test_blocks(n: int) -> list[Block]:
    """Generate representative test blocks for an n×n center grid."""
    blocks = []
    blocks.append(Block(Point(0, 0), Point(0, 0)))
    blocks.append(Block(Point(n - 1, n - 1), Point(n - 1, n - 1)))
    blocks.append(Block(Point(0, n - 1), Point(0, n - 1)))
    if n >= 3:
        blocks.append(Block(Point(1, 0), Point(1, 0)))
        blocks.append(Block(Point(0, 0), Point(1, 0)))
        blocks.append(Block(Point(0, 0), Point(0, 1)))
    if n >= 5:
        blocks.append(Block(Point(0, 0), Point(1, 1)))
        blocks.append(Block(Point(1, 1), Point(2, 2)))
    return blocks


def _get_full_slice_blocks(n: int) -> list[Block]:
    """Generate all full-slice blocks that have valid swap combinations.

    Uses BlockBySliceSwapHelper to determine which blocks are valid,
    rather than hardcoding geometric rules in the test.

    For each width w from 1 to n-1:
    - Vertical: n rows × w cols at each column position
    - Horizontal: w rows × n cols at each row position

    Only includes blocks that have at least one valid combination
    (checked against F←U as representative pair).
    """
    from cube.domain.solver.common.big_cube.commutator.BlockBySliceSwapHelper import (
        BlockBySliceSwapHelper,
    )

    # Use a real cube to check validity via geometry (not hardcoded rules)
    app = AbstractApp.create_app(n + 2)
    cube = app.cube
    solver = Solvers.cage(app.op)
    helper = BlockBySliceSwapHelper(solver)

    blocks = []

    for w in range(1, n):
        for c in range(n - w + 1):
            block = Block(Point(0, c), Point(n - 1, c + w - 1))
            if helper.is_valid_for_swap(block):
                blocks.append(block)

        for r in range(n - w + 1):
            block = Block(Point(r, 0), Point(r + w - 1, n - 1))
            if helper.is_valid_for_swap(block):
                blocks.append(block)

    return blocks


# All 30 source/target face pair combinations (6 faces × 5 sources each)
_ALL_FACES = [FaceName.F, FaceName.B, FaceName.U, FaceName.D, FaceName.L, FaceName.R]
_FACE_PAIRS = [
    (source, target)
    for target in _ALL_FACES
    for source in _ALL_FACES
    if source != target
]


def _face_pair_id(pair: tuple[FaceName, FaceName]) -> str:
    source, target = pair
    return f"{target.name}<-{source.name}"


class TestSliceSwapSixBlocks:
    """Test that all 6 blocks swap correctly using marker-based verification."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    @pytest.mark.parametrize("face_pair", _FACE_PAIRS, ids=[_face_pair_id(p) for p in _FACE_PAIRS])
    def test_slice_swap_markers(self, cube_size: int, face_pair: tuple[FaceName, FaceName]):
        """Verify all 6 blocks swap correctly with markers.

        For each valid target block, places markers on all 6 blocks
        (3 on target face, 3 on source face), executes the swap,
        then checks all markers moved to the expected positions.
        """
        source_face_name, target_face_name = face_pair

        app = AbstractApp.create_app(cube_size)
        cube = app.cube
        n = cube.n_slices  # inner slices = cube_size - 2
        helper = _create_helper(app)

        target_face = cube.face(target_face_name)
        source_face = cube.face(source_face_name)

        successes = []
        failures = []

        # Try a few representative target blocks
        test_blocks = _get_test_blocks(n)

        for target_block in test_blocks:
            # Reset cube and recreate helper (reset creates new objects)
            cube.reset()
            helper = _create_helper(app)
            target_face = cube.face(target_face_name)
            source_face = cube.face(source_face_name)

            # Dry run to get all 6 blocks
            results = helper.get_all_combinations(source_face, target_face, target_block)

            if not results:
                continue  # No valid combination for this block

            # Use the first valid combination
            result = results[0]

            # Reset and recreate for clean marker placement
            cube.reset()
            helper = _create_helper(app)
            target_face = cube.face(target_face_name)
            source_face = cube.face(source_face_name)

            # Generate unique marker key for this test
            marker_key = f"bsh_{uuid.uuid4().hex[:8]}"

            # Place markers on all 6 blocks
            # Target face blocks
            t_prefix_markers = _place_block_markers(
                target_face, result.target_prefix_block, marker_key, "tp"
            )
            t_main_markers = _place_block_markers(
                target_face, result.target_block, marker_key, "tm"
            )
            t_suffix_markers = _place_block_markers(
                target_face, result.target_suffix_block, marker_key, "ts"
            )

            # Source face blocks
            s_prefix_markers = _place_block_markers(
                source_face, result.source_prefix_block, marker_key, "sp"
            )
            s_main_markers = _place_block_markers(
                source_face, result.source_block, marker_key, "sm"
            )
            s_suffix_markers = _place_block_markers(
                source_face, result.source_suffix_block, marker_key, "ss"
            )

            # Execute the actual swap (not dry run)
            exec_result = helper.execute_swap(
                source_face, target_face, target_block,
                rotation_type=result.rotation_type,
                dry_run=False,
                preserve_state=True,
            )

            # Verify: target blocks' markers should now be at source positions
            # and source blocks' markers should now be at target positions

            record = {
                "target_block": target_block,
                "rotation": result.rotation_type,
                "slice": result.slice_name,
            }

            ok = True

            def _check_swap(
                label: str,
                src_markers: dict[Point, str],
                dest_face: Face,
                dest_block: Block | None,
            ) -> None:
                """Check that all markers from src ended up in dest_block (set comparison)."""
                nonlocal ok
                if not src_markers or dest_block is None:
                    return
                found = _read_block_markers(dest_face, dest_block, marker_key)
                expected_set = set(src_markers.values())
                found_set = {v for v in found.values() if v is not None}
                if found_set != expected_set:
                    ok = False
                    failures.append({
                        **record, "type": label,
                        "expected": sorted(expected_set),
                        "found": sorted(found_set),
                    })

            # Target blocks should swap to source positions
            _check_swap("tm->sm", t_main_markers, source_face, result.source_block)
            _check_swap("tp->sp", t_prefix_markers, source_face, result.source_prefix_block)
            _check_swap("ts->ss", t_suffix_markers, source_face, result.source_suffix_block)

            # Source blocks should swap to target positions
            _check_swap("sm->tm", s_main_markers, target_face, result.target_block)
            _check_swap("sp->tp", s_prefix_markers, target_face, result.target_prefix_block)
            _check_swap("ss->ts", s_suffix_markers, target_face, result.target_suffix_block)

            if ok:
                successes.append(record)

        if failures:
            msg = (
                f"\nCube {cube_size}x{cube_size}, "
                f"{target_face_name.name}<-{source_face_name.name}\n"
                f"Successes: {len(successes)}, Failures: {len(failures)}\n"
            )
            for f in failures[:10]:
                msg += f"  {f}\n"
            assert False, msg

        # Ensure we actually tested something
        assert len(successes) > 0, (
            f"No valid test blocks found for {cube_size}x{cube_size} "
            f"{target_face_name.name}<-{source_face_name.name}"
        )


# Adjacent faces for each face (used by full-slice block tests)
_ADJACENT: dict[FaceName, tuple[FaceName, ...]] = {}


def _get_adjacent(face: FaceName) -> tuple[FaceName, ...]:
    """Lazily compute and cache adjacent faces."""
    if face not in _ADJACENT:
        app = AbstractApp.create_app(4)
        _ADJACENT[face] = app.cube.layout.get_adjacent_faces(face)
    return _ADJACENT[face]


def _full_slice_test_cases() -> list[tuple[int, FaceName, FaceName, Block]]:
    """Generate all (cube_size, target, source, block) for full-slice tests.

    30 face pairs (6 targets × 5 sources) per cube size.
    """
    cases = []
    for cube_size in [4, 5, 6, 7]:
        n = cube_size - 2  # n_slices
        blocks = _get_full_slice_blocks(n)
        for target_fn in _ALL_FACES:
            for source_fn in _ALL_FACES:
                if source_fn == target_fn:
                    continue
                for block in blocks:
                    cases.append((cube_size, target_fn, source_fn, block))
    return cases


_FULL_SLICE_CASES = _full_slice_test_cases()


def _full_slice_id(case: tuple[int, FaceName, FaceName, Block]) -> str:
    cube_size, target, source, block = case
    br, bc = block.start.row, block.start.col
    er, ec = block.end.row, block.end.col
    return f"{cube_size}-{target.name}<-{source.name}-({br},{bc})-({er},{ec})"


class TestFullSliceBlocks:
    """Test all full-slice blocks: n vertical + n horizontal strips.

    Each strip is tested against each of its 4 adjacent source faces.
    Every combination must produce a valid swap — none can be skipped.
    """

    @pytest.mark.parametrize("case", _FULL_SLICE_CASES,
                             ids=[_full_slice_id(c) for c in _FULL_SLICE_CASES])
    def test_full_slice_swap(self, case: tuple[int, FaceName, FaceName, Block]):
        """Single full-slice block swap with marker verification."""
        cube_size, target_face_name, source_face_name, target_block = case

        app = AbstractApp.create_app(cube_size)
        cube = app.cube
        helper = _create_helper(app)
        target_face = cube.face(target_face_name)
        source_face = cube.face(source_face_name)

        # Must find at least one valid combination
        results = helper.get_all_combinations(source_face, target_face, target_block)
        assert results, (
            f"No valid combination for {cube_size}x{cube_size} "
            f"{target_face_name.name}<-{source_face_name.name} block={target_block}"
        )

        result = results[0]

        # Reset and verify with markers
        cube.reset()
        helper = _create_helper(app)
        target_face = cube.face(target_face_name)
        source_face = cube.face(source_face_name)

        marker_key = f"fs_{uuid.uuid4().hex[:8]}"

        t_prefix_markers = _place_block_markers(
            target_face, result.target_prefix_block, marker_key, "tp"
        )
        t_main_markers = _place_block_markers(
            target_face, result.target_block, marker_key, "tm"
        )
        t_suffix_markers = _place_block_markers(
            target_face, result.target_suffix_block, marker_key, "ts"
        )
        s_prefix_markers = _place_block_markers(
            source_face, result.source_prefix_block, marker_key, "sp"
        )
        s_main_markers = _place_block_markers(
            source_face, result.source_block, marker_key, "sm"
        )
        s_suffix_markers = _place_block_markers(
            source_face, result.source_suffix_block, marker_key, "ss"
        )

        helper.execute_swap(
            source_face, target_face, target_block,
            rotation_type=result.rotation_type,
            dry_run=False,
            preserve_state=True,
        )

        failures = []

        def _check(label, src_markers, dest_face, dest_block):
            if not src_markers or dest_block is None:
                return
            found = _read_block_markers(dest_face, dest_block, marker_key)
            expected_set = set(src_markers.values())
            found_set = {v for v in found.values() if v is not None}
            if found_set != expected_set:
                failures.append(
                    f"{label}: expected={sorted(expected_set)} "
                    f"found={sorted(found_set)}"
                )

        _check("tm->sm", t_main_markers, source_face, result.source_block)
        _check("tp->sp", t_prefix_markers, source_face, result.source_prefix_block)
        _check("ts->ss", t_suffix_markers, source_face, result.source_suffix_block)
        _check("sm->tm", s_main_markers, target_face, result.target_block)
        _check("sp->tp", s_prefix_markers, target_face, result.target_prefix_block)
        _check("ss->ts", s_suffix_markers, target_face, result.target_suffix_block)

        assert not failures, (
            f"Swap verification failed for {cube_size}x{cube_size} "
            f"{target_face_name.name}<-{source_face_name.name} "
            f"block={target_block}:\n" + "\n".join(failures)
        )


class TestSliceSwapValid:
    """Test that validity checking works correctly."""

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_center_block_invalid_for_odd(self, cube_size: int):
        """On odd cubes, the center cell cannot be swapped (invariant under rotation)."""

        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices
        mid = n // 2

        # Center single cell
        center_block = Block(Point(mid, mid), Point(mid, mid))
        assert not helper.is_valid_for_swap(center_block)

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_corner_blocks_valid(self, cube_size: int):
        """Corner 1x1 blocks should be valid (they don't self-intersect after 180°)."""
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)

        # Top-left corner of center grid
        corner_block = Block(Point(0, 0), Point(0, 0))
        assert helper.is_valid_for_swap(corner_block)


class TestLargestBlocksContainingPoint:
    """Test that get_largest_blocks_containing_point returns valid blocks."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7, 8])
    def test_every_point_has_largest_blocks(self, cube_size: int):
        """Every non-center point has at least 1 largest block, all valid for swap.

        For even cubes: every point has exactly 2 blocks.
        For odd cubes: middle row/col points may have only 1, and the
        center point (mid, mid) has 0 (it's always invalid).
        """
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices
        mid = n // 2
        is_odd = n % 2 == 1

        for r in range(n):
            for c in range(n):
                point = Point(r, c)
                blocks = get_largest_blocks_containing_point(n, point)

                # On odd cubes, center point has no valid block
                if is_odd and r == mid and c == mid:
                    assert len(blocks) == 0, (
                        f"Center ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected 0 blocks, got {len(blocks)}"
                    )
                    continue

                # Even cubes: always 2. Odd cubes: at least 1 (2 if not on middle row/col)
                if is_odd and (r == mid or c == mid):
                    assert len(blocks) >= 1, (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected >=1 blocks, got {len(blocks)}"
                    )
                else:
                    assert len(blocks) >= 2, (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected >=2 blocks, got {len(blocks)}"
                    )

                # Each block must contain the point
                for block in blocks:
                    assert block.start.row <= r <= block.end.row, (
                        f"Block {block} doesn't contain point ({r},{c}) in rows"
                    )
                    assert block.start.col <= c <= block.end.col, (
                        f"Block {block} doesn't contain point ({r},{c}) in cols"
                    )

                # Each block must be valid for swap
                for block in blocks:
                    assert helper.is_valid_for_swap(block), (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"block {block} is NOT valid for swap"
                    )

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7, 8])
    def test_blocks_sorted_by_size(self, cube_size: int):
        """Returned blocks are sorted by size descending."""
        n = cube_size - 2

        for r in range(n):
            for c in range(n):
                blocks = get_largest_blocks_containing_point(n, Point(r, c))
                sizes = [b.size for b in blocks]
                assert sizes == sorted(sizes, reverse=True), (
                    f"Point ({r},{c}): sizes {sizes} not sorted descending"
                )

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_center_point_has_no_blocks_on_odd(self, cube_size: int):
        """On odd cubes, the center point (mid, mid) has no valid blocks —
        it's on the middle in both directions, so every rotation overlaps."""
        n = cube_size - 2
        mid = n // 2

        blocks = get_largest_blocks_containing_point(n, Point(mid, mid))
        assert len(blocks) == 0

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_middle_row_point_has_one_block_on_odd(self, cube_size: int):
        """On odd cubes, a point on the middle row (but not mid col) has
        exactly 1 valid block (the column-based half)."""
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices
        mid = n // 2

        # Point on middle row, col 0 (in the left half)
        blocks = get_largest_blocks_containing_point(n, Point(mid, 0))
        assert len(blocks) == 1
        assert helper.is_valid_for_swap(blocks[0])


class TestSliceSwapDryRun:
    """Test dry_run mode returns correct geometry without executing."""

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_dry_run_no_cube_change(self, cube_size: int):
        """Dry run should not modify the cube state."""
        app = AbstractApp.create_app(cube_size)
        cube = app.cube
        helper = _create_helper(app)
        n = cube.n_slices

        source_face = cube.face(FaceName.U)
        target_face = cube.face(FaceName.F)

        # Pick a valid block
        target_block = Block(Point(0, 0), Point(0, 0))

        # Record state before
        marker_key = f"test_{uuid.uuid4().hex[:8]}"
        piece = target_face.center.get_center_slice((0, 0)).edge
        piece.moveable_attributes[marker_key] = "before"

        # Dry run
        results = helper.get_all_combinations(source_face, target_face, target_block)
        assert len(results) > 0, "Should have at least one valid combination"

        # Verify cube unchanged
        piece_after = target_face.center.get_center_slice((0, 0)).edge
        assert piece_after.moveable_attributes.get(marker_key) == "before"


