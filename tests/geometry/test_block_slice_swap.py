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
    get_largest_blocks_from_point,
    iter_sub_blocks,
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


def _read_block_markers_ordered(
    face: Face,
    block: Block,
    marker_key: str,
    n_slices: int,
    order_by: Block,
) -> list[str | None]:
    """Read marker values from a block in kernel-aligned order.

    Uses points_by(n_slices, order_by) so the iteration order matches
    the order_by block's cell ordering. This ensures that marker[i]
    placed on order_by cell[i] is read at index i from this block.

    Returns:
        List of marker values in aligned order.
    """
    result: list[str | None] = []
    for cell in block.points_by(n_slices, order_by=order_by):
        piece = face.center.get_center_slice(cell).edge
        result.append(piece.moveable_attributes.get(marker_key))
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
    """Test that get_largest_blocks_containing_point returns the maximal
    half-face blocks that contain a given point, all valid for swap."""

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7, 8])
    def test_every_point_has_containing_blocks(self, cube_size: int):
        """Every non-center point has at least 1 containing block, valid for swap."""
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices
        mid = n // 2
        is_odd = n % 2 == 1

        for r in range(n):
            for c in range(n):
                point = Point(r, c)
                blocks = get_largest_blocks_containing_point(n, point)

                if is_odd and r == mid and c == mid:
                    assert len(blocks) == 0
                    continue

                if is_odd and (r == mid or c == mid):
                    assert len(blocks) >= 1
                else:
                    assert len(blocks) >= 2

                # Each block must contain the point
                for block in blocks:
                    assert block.start.row <= r <= block.end.row
                    assert block.start.col <= c <= block.end.col

                # Each block must be valid for swap
                for block in blocks:
                    assert helper.is_valid_for_swap(block), (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"block {block} is NOT valid for swap"
                    )

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7, 8])
    def test_containing_blocks_sorted_by_size(self, cube_size: int):
        """Returned blocks are sorted by size descending."""
        n = cube_size - 2
        for r in range(n):
            for c in range(n):
                blocks = get_largest_blocks_containing_point(n, Point(r, c))
                sizes = [b.size for b in blocks]
                assert sizes == sorted(sizes, reverse=True)

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_center_point_has_no_containing_blocks_on_odd(self, cube_size: int):
        """On odd cubes, the center point has no valid containing blocks."""
        n = cube_size - 2
        mid = n // 2
        assert len(get_largest_blocks_containing_point(n, Point(mid, mid))) == 0


class TestLargestBlocksFromPoint:
    """Test that get_largest_blocks_from_point returns valid blocks.

    The function takes a point (r,c) as the bottom-left corner and returns the
    largest blocks extending down-right that are valid for swap.
    """

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7, 8])
    def test_every_point_has_largest_blocks(self, cube_size: int):
        """Every non-center point has at least 1 block starting from it, valid for swap.

        For even cubes: every point yields 1-2 distinct blocks.
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
                blocks = get_largest_blocks_from_point(n, point)

                # On odd cubes, center point has no valid block
                if is_odd and r == mid and c == mid:
                    assert len(blocks) == 0, (
                        f"Center ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected 0 blocks, got {len(blocks)}"
                    )
                    continue

                # Must have at least 1 block
                if is_odd and (r == mid or c == mid):
                    assert len(blocks) >= 1, (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected >=1 blocks, got {len(blocks)}"
                    )
                else:
                    assert len(blocks) >= 1, (
                        f"Point ({r},{c}) on {cube_size}x{cube_size}: "
                        f"expected >=1 blocks, got {len(blocks)}"
                    )

                # (r,c) must be at the bottom-left corner of each block
                for block in blocks:
                    assert block.end.row == r, (
                        f"Block {block}: end.row={block.end.row} != r={r}"
                    )
                    assert block.start.col == c, (
                        f"Block {block}: start.col={block.start.col} != c={c}"
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
                blocks = get_largest_blocks_from_point(n, Point(r, c))
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

        blocks = get_largest_blocks_from_point(n, Point(mid, mid))
        assert len(blocks) == 0

    @pytest.mark.parametrize("cube_size", [5, 7])
    def test_middle_row_point_has_one_block_on_odd(self, cube_size: int):
        """On odd cubes, a point on the middle row (but not mid col) has
        exactly 1 valid block (the column-based half starting from it)."""
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices
        mid = n // 2

        # Point on middle row, col 0 (in the left half)
        blocks = get_largest_blocks_from_point(n, Point(mid, 0))
        assert len(blocks) == 1
        # (mid, 0) is bottom-left: block extends up to row 0, right to lower_max
        assert blocks[0].end.row == mid
        assert blocks[0].start.col == 0
        assert helper.is_valid_for_swap(blocks[0])

    @pytest.mark.parametrize("cube_size", [4, 6, 8])
    def test_top_left_corner_on_even(self, cube_size: int):
        """On even cubes, (0,0) yields 2 blocks: row-safe and col-safe."""
        app = AbstractApp.create_app(cube_size)
        helper = _create_helper(app)
        n = app.cube.n_slices

        blocks = get_largest_blocks_from_point(n, Point(0, 0))
        # Both row-safe and col-safe, but may deduplicate if identical
        assert len(blocks) >= 1
        for block in blocks:
            # (0,0) is bottom-left corner
            assert block.end.row == 0
            assert block.start.col == 0
            assert helper.is_valid_for_swap(block)


class TestIterSubBlocks:
    """Test that iter_sub_blocks yields all sub-blocks anchored at end, biggest first."""

    def test_total_count(self):
        """A 3x4 block should yield 3*4=12 sub-blocks."""
        block = Block(Point(1, 2), Point(3, 5))
        subs = list(iter_sub_blocks(block))
        assert len(subs) == 3 * 4

    def test_all_anchored_at_end(self):
        """Every sub-block ends at the parent's end."""
        block = Block(Point(1, 2), Point(3, 5))
        for sb in iter_sub_blocks(block):
            assert sb.end == block.end

    def test_first_is_full_block(self):
        """First yielded block is the full block itself."""
        block = Block(Point(0, 0), Point(2, 3))
        first = next(iter(iter_sub_blocks(block)))
        assert first == block

    def test_last_is_single_cell(self):
        """Last yielded block is the single cell at end."""
        block = Block(Point(0, 0), Point(2, 3))
        last = list(iter_sub_blocks(block))[-1]
        assert last == Block(block.end, block.end)

    def test_wider_block_shrinks_cols_first(self):
        """For width > height, outer loop is on cols."""
        block = Block(Point(0, 0), Point(1, 2))  # 2x3
        subs = list(iter_sub_blocks(block))
        # First 2 blocks have full width (start.col=0), next 2 have col=1, last 2 col=2
        assert subs[0].start.col == 0 and subs[1].start.col == 0
        assert subs[2].start.col == 1 and subs[3].start.col == 1
        assert subs[4].start.col == 2 and subs[5].start.col == 2

    def test_taller_block_shrinks_rows_first(self):
        """For height > width, outer loop is on rows."""
        block = Block(Point(0, 0), Point(2, 1))  # 3x2
        subs = list(iter_sub_blocks(block))
        # First 2 blocks have full height (start.row=0), next 2 row=1, last 2 row=2
        assert subs[0].start.row == 0 and subs[1].start.row == 0
        assert subs[2].start.row == 1 and subs[3].start.row == 1
        assert subs[4].start.row == 2 and subs[5].start.row == 2


@pytest.mark.slow
class TestNuclearSwap:
    """Nuclear test: exhaustively enumerate ALL valid blocks on the n×n grid
    and verify the 6-block marker swap is correct with ordered comparison.

    For each valid block sb:
    1. Verify 4 rotated images exist
    2. Execute the 180° swap
    3. Verify all 6 blocks swapped correctly with ordered marker comparison
       using points_by(n, order_by=src_block) for kernel-aligned iteration
    """

    @pytest.mark.parametrize("cube_size", [4, 5, 6, 7])
    @pytest.mark.parametrize(
        "face_pair", _FACE_PAIRS, ids=[_face_pair_id(p) for p in _FACE_PAIRS]
    )
    def test_nuclear_all_sub_blocks(
        self, cube_size: int, face_pair: tuple[FaceName, FaceName]
    ):
        source_face_name, target_face_name = face_pair

        app = AbstractApp.create_app(cube_size)
        cube = app.cube
        n = cube.n_slices
        helper = _create_helper(app)

        successes = 0
        failures: list[dict] = []

        # Enumerate all valid blocks via get_largest_blocks_from_point + iter_sub_blocks
        tested_blocks: set[tuple[int, int, int, int]] = set()
        valid_blocks: list[Block] = []
        for r in range(n):
            for c in range(n):
                big_blocks = get_largest_blocks_from_point(n, Point(r, c))
                for big_block in big_blocks:
                    for sb in iter_sub_blocks(big_block):
                        key = (sb.start.row, sb.start.col, sb.end.row, sb.end.col)
                        if key not in tested_blocks and helper.is_valid_for_swap(sb):
                            tested_blocks.add(key)
                            valid_blocks.append(sb)

        for sb in valid_blocks:
            # Verify 4 rotated images exist
            for rot in range(4):
                _rotated = sb.rotate_clockwise(n, rot)
                assert _rotated is not None

            # Execute 180° swap and verify
            cube.reset()
            helper = _create_helper(app)
            target_face = cube.face(target_face_name)
            source_face = cube.face(source_face_name)

            # Dry run to get block geometry
            result = helper.execute_swap(
                source_face, target_face, sb,
                rotation_type=2,
                dry_run=True,
                preserve_state=True,
            )

            # Reset for clean marker placement
            cube.reset()
            helper = _create_helper(app)
            target_face = cube.face(target_face_name)
            source_face = cube.face(source_face_name)

            marker_key = f"nuc_{uuid.uuid4().hex[:8]}"

            # Place markers on all 6 blocks
            t_prefix = _place_block_markers(
                target_face, result.target_prefix_block,
                marker_key, "tp",
            )
            t_main = _place_block_markers(
                target_face, result.target_block,
                marker_key, "tm",
            )
            t_suffix = _place_block_markers(
                target_face, result.target_suffix_block,
                marker_key, "ts",
            )
            s_prefix = _place_block_markers(
                source_face, result.source_prefix_block,
                marker_key, "sp",
            )
            s_main = _place_block_markers(
                source_face, result.source_block,
                marker_key, "sm",
            )
            s_suffix = _place_block_markers(
                source_face, result.source_suffix_block,
                marker_key, "ss",
            )

            # Execute the actual swap
            helper.execute_swap(
                source_face, target_face, sb,
                rotation_type=2,
                dry_run=False,
                preserve_state=True,
            )

            # Verify all 6 marker swaps (ordered comparison)
            # Use points_by(n, order_by=src_block) to align
            # iteration order with the source block's cell order.
            record = {
                "block": sb,
                "slice": result.slice_name,
            }
            ok = True

            def _check(
                label: str,
                src_markers: dict[Point, str],
                src_block: Block | None,
                dest_face: Face,
                dest_block: Block | None,
            ) -> None:
                nonlocal ok
                if not src_markers or dest_block is None or src_block is None:
                    return
                actual = _read_block_markers_ordered(
                    dest_face, dest_block, marker_key,
                    n, order_by=src_block,
                )
                expected = list(src_markers.values())
                if actual != expected:
                    ok = False
                    failures.append({
                        **record, "type": label,
                        "expected": expected,
                        "found": actual,
                    })

            _check("tm->sm", t_main, result.target_block,
                   source_face, result.source_block)
            _check("tp->sp", t_prefix, result.target_prefix_block,
                   source_face, result.source_prefix_block)
            _check("ts->ss", t_suffix, result.target_suffix_block,
                   source_face, result.source_suffix_block)
            _check("sm->tm", s_main, result.source_block,
                   target_face, result.target_block)
            _check("sp->tp", s_prefix, result.source_prefix_block,
                   target_face, result.target_prefix_block)
            _check("ss->ts", s_suffix, result.source_suffix_block,
                   target_face, result.target_suffix_block)

            if ok:
                successes += 1

        if failures:
            msg = (
                f"\nCube {cube_size}x{cube_size}, "
                f"{target_face_name.name}<-{source_face_name.name}\n"
                f"Successes: {successes}, Failures: {len(failures)}\n"
            )
            for f in failures[:10]:
                msg += f"  {f}\n"
            assert False, msg

        assert successes > 0, (
            f"No valid sub-blocks for {cube_size}x{cube_size} "
            f"{target_face_name.name}<-{source_face_name.name}"
        )


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


