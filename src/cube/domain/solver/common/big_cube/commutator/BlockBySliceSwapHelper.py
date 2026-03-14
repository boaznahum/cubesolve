"""
Block-by-Slice Swap Helper for NxN Big Cubes.

Simpler alternative to CommutatorHelper: swaps a target block with a source block
by using a single slice conjugation: slice → face_rotate → slice'.

Unlike the commutator (which performs a 3-cycle), this algorithm swaps ALL content
on the affected slices. This means 3 blocks on the target face (prefix, main, suffix)
each swap with their corresponding block on the source face — 6 blocks in total.

Coordinate system: Uses the same index coordinates as CommutatorHelper.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Tuple

from cube.domain.algs import Algs, Alg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.geometric.Face2FaceTranslator import (
    Face2FaceTranslator,
    FaceTranslationResult,
    SliceAlgorithmResult,
)
from cube.domain.geometric.block import Block
from cube.domain.geometric.geometry_types import CLGColRow, Point
from cube.domain.geometric.geometry_utils import inv
from cube.domain.model import FaceName, Cube
from cube.domain.model.Face import Face
from cube.domain.model.SliceName import SliceName
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider


@dataclass(frozen=True)
class SliceSwapResult:
    """Result of a slice swap operation.

    Contains all 6 blocks (3 on target, 3 on source) and the algorithm.

    The target face strip (full column or row on affected slices) splits into:
    - prefix_block: above/before the target block (may be None)
    - target_block: the main block being swapped
    - suffix_block: below/after the target block (may be None)

    Each has a corresponding block on the source face.
    """
    slice_name: SliceName
    algorithm: Alg
    rotation_type: int  # 1 (90° CW), -1 (90° CCW), or 2 (180°)

    # Target face blocks
    target_prefix_block: Block | None
    target_block: Block
    target_suffix_block: Block | None

    # Source face blocks (natural positions before any source setup)
    source_prefix_block: Block | None
    source_block: Block
    source_suffix_block: Block | None


class BlockBySliceSwapHelper(SolverHelper):
    """Helper for block-by-slice swap algorithm on NxN cubes.

    Swaps a target block with content from a source face using:
        slice_alg → target_face_rotation → slice_alg' (inverse)

    This swaps ALL content on the affected slices, creating 3 pairs of
    swapped blocks (prefix, main, suffix).
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "BSH")

    @property
    def n_slices(self) -> int:
        return self.cube.n_slices

    def is_valid_for_swap(self, target_block: Block) -> bool:
        """Check if a target block can be swapped (no self-intersection).

        A block is valid if at least one rotation (90° CW or 180°)
        doesn't cause the block to overlap with itself on the slice-cut axis.

        For the slice swap, we need the block not to overlap with its rotated
        image on the axis perpendicular to the slices.

        Note: 90° CCW is provably equivalent to 90° CW for self-intersection:
        if CW overlaps on both axes, CCW must also overlap on both axes.
        """
        n = self.n_slices
        block = target_block.normalize

        for rot_n in [1, 2]:
            rotated = block.rotate_clockwise(n, rot_n % 4)
            # Check if rows don't overlap (for vertical slice case)
            r1, r2 = block.start.row, block.end.row
            rr1, rr2 = rotated.start.row, rotated.end.row
            rows_ok = rr1 > r2 or rr2 < r1

            # Check if columns don't overlap (for horizontal slice case)
            c1, c2 = block.start.col, block.end.col
            rc1, rc2 = rotated.start.col, rotated.end.col
            cols_ok = rc1 > c2 or rc2 < c1

            if rows_ok or cols_ok:
                return True

        return False

    def get_all_combinations(
        self,
        source_face: Face,
        target_face: Face,
        target_block: Block,
    ) -> list[SliceSwapResult]:
        """Return all valid slice swap combinations (dry run).

        Tries all 4 combinations (H/V slice × 180° rotation) for the given
        source/target face pair and target block.

        The 4 combinations come from:
        - Direct slice + 180° rotation (no setup)
        - Setup 90° CW + 180° rotation (converts H↔V strip direction)

        When the slice is horizontal on the target face, a 90° CW setup of the
        target face effectively converts it to a vertical strip, and vice versa.

        Returns:
            List of SliceSwapResult with geometry computed but not executed.
        """
        results: list[SliceSwapResult] = []
        target_block = target_block.normalize

        # Get translation results from Face2FaceTranslator
        trans_results = Face2FaceTranslator.translate_source_from_target(
            target_face, source_face, target_block.start
        )

        for trans_result in trans_results:
            slice_name = trans_result.slice_algorithm.whole_slice_alg.slice_name
            slice_n = trans_result.slice_algorithm.n  # direction multiplier

            # Try all 4 combinations: 2 rotation types × 2 setup options
            for setup_rotation in [0, 1]:  # 0=no setup, 1=90° CW setup
                for rotation_type in [2]:  # 180° — clean 3-pair swap
                    result = self._try_combination(
                        source_face, target_face, target_block,
                        slice_name, slice_n, rotation_type, trans_result,
                        setup_rotation=setup_rotation,
                    )
                    if result is not None:
                        results.append(result)

        return results

    def execute_swap(
        self,
        source_face: Face,
        target_face: Face,
        target_block: Block,
        rotation_type: int | None = None,
        dry_run: bool = False,
        preserve_state: bool = True,
    ) -> SliceSwapResult:
        """Execute a slice swap operation.

        Args:
            source_face: Source face (where content comes from)
            target_face: Target face (where content goes to)
            target_block: Block on target face to swap
            rotation_type: 1 (90° CW), -1 (90° CCW), or 2 (180°).
                          If None, auto-selects best option.
            dry_run: If True, compute geometry only (no moves)
            preserve_state: If True, undo any setup rotations

        Returns:
            SliceSwapResult with all 6 blocks and algorithm
        """
        target_block = target_block.normalize

        if rotation_type is None:
            # Auto-select: get first valid combination
            combinations = self.get_all_combinations(source_face, target_face, target_block)
            if not combinations:
                raise ValueError(
                    f"No valid slice swap combination for block {target_block} "
                    f"from {source_face.name} to {target_face.name}"
                )
            result = combinations[0]
        else:
            # Use specified rotation — try with and without setup
            trans_results = Face2FaceTranslator.translate_source_from_target(
                target_face, source_face, target_block.start
            )
            result = None
            for trans_result in trans_results:
                slice_name = trans_result.slice_algorithm.whole_slice_alg.slice_name
                slice_n = trans_result.slice_algorithm.n
                for setup_rotation in [0, 1]:
                    result = self._try_combination(
                        source_face, target_face, target_block,
                        slice_name, slice_n, rotation_type, trans_result,
                        setup_rotation=setup_rotation,
                    )
                    if result is not None:
                        break
                if result is not None:
                    break
            if result is None:
                raise ValueError(
                    f"Rotation type {rotation_type} is not valid for block {target_block}"
                )

        if not dry_run:
            self._execute_algorithm(result, source_face, target_face)

        return result

    def _try_combination(
        self,
        source_face: Face,
        target_face: Face,
        target_block: Block,
        slice_name: SliceName,
        slice_n: int,
        rotation_type: int,
        trans_result: FaceTranslationResult,
        setup_rotation: int = 0,
    ) -> SliceSwapResult | None:
        """Try a specific slice + rotation combination.

        Args:
            setup_rotation: 0 = no setup, 1 = 90° CW pre-rotation of target face.
                           A setup converts a horizontal strip to vertical and vice versa.

        Returns SliceSwapResult if valid, None if self-intersection.
        """
        n = self.n_slices
        cube = self.cube

        # Get the slice layout to determine orientation on target face
        slice_layout = cube.layout.get_slice(slice_name)
        cuts_rows = slice_layout.does_slice_cut_rows_or_columns(target_face.name) == CLGColRow.ROW

        # Apply setup rotation to get the effective block position
        if setup_rotation:
            effective_block = target_block.rotate_clockwise(n, setup_rotation)
        else:
            effective_block = target_block

        # Rotate the effective block by the face rotation
        rot_n = rotation_type % 4  # Normalize: 2 stays 2, 1 stays 1, -1 becomes 3
        rotated_block = effective_block.rotate_clockwise(n, rot_n)

        # Check self-intersection on the slice-cut axis
        if cuts_rows:
            # Slice cuts rows (vertical on face), so we check column overlap
            t_range = (effective_block.start.col, effective_block.end.col)
            r_range = (rotated_block.start.col, rotated_block.end.col)
        else:
            # Slice cuts columns (horizontal on face), so we check row overlap
            t_range = (effective_block.start.row, effective_block.end.row)
            r_range = (rotated_block.start.row, rotated_block.end.row)

        if _1d_intersect(t_range, r_range):
            return None  # Self-intersection

        # For the swap to work, the rotated block must span the same number of
        # slices as the original. A 90° rotation of a rectangular block swaps
        # dimensions, changing the slice count — reject in that case.
        if cuts_rows:
            orig_slice_count = abs(effective_block.end.col - effective_block.start.col) + 1
            rot_slice_count = abs(rotated_block.end.col - rotated_block.start.col) + 1
        else:
            orig_slice_count = abs(effective_block.end.row - effective_block.start.row) + 1
            rot_slice_count = abs(rotated_block.end.row - rotated_block.start.row) + 1

        if orig_slice_count != rot_slice_count:
            return None  # Dimension mismatch after rotation

        # Compute all 6 blocks in SETUP coordinates (effective block positions)
        target_prefix, target_suffix = self._compute_strip_blocks(
            effective_block, n, cuts_rows
        )

        # Compute source blocks by rotating each target block, then translating
        # to source face
        rotated_main = rotated_block  # already computed above
        rotated_prefix = (
            target_prefix.rotate_clockwise(n, rot_n)
            if target_prefix is not None else None
        )
        rotated_suffix = (
            target_suffix.rotate_clockwise(n, rot_n)
            if target_suffix is not None else None
        )

        # Translate rotated blocks to source face
        source_block = self._translate_block_to_source(
            target_face, source_face, rotated_main, slice_name
        )
        source_prefix = (
            self._translate_block_to_source(target_face, source_face, rotated_prefix, slice_name)
            if rotated_prefix is not None else None
        )
        source_suffix = (
            self._translate_block_to_source(target_face, source_face, rotated_suffix, slice_name)
            if rotated_suffix is not None else None
        )

        # Convert target blocks from setup coordinates back to original coordinates
        if setup_rotation:
            inv_setup = (4 - setup_rotation) % 4  # Inverse: 1 → 3 (90° CCW)
            orig_target_block = target_block  # Already in original coords
            orig_target_prefix = (
                target_prefix.rotate_clockwise(n, inv_setup)
                if target_prefix is not None else None
            )
            orig_target_suffix = (
                target_suffix.rotate_clockwise(n, inv_setup)
                if target_suffix is not None else None
            )
        else:
            orig_target_block = target_block
            orig_target_prefix = target_prefix
            orig_target_suffix = target_suffix

        # Build the algorithm
        algorithm = self._build_algorithm(
            source_face, target_face, effective_block, rotated_block,
            slice_name, slice_n, rotation_type, cuts_rows,
            setup_rotation=setup_rotation,
        )

        return SliceSwapResult(
            slice_name=slice_name,
            algorithm=algorithm,
            rotation_type=rotation_type,
            target_prefix_block=orig_target_prefix,
            target_block=orig_target_block,
            target_suffix_block=orig_target_suffix,
            source_prefix_block=source_prefix,
            source_block=source_block,
            source_suffix_block=source_suffix,
        )

    @staticmethod
    def _compute_strip_blocks(
        block: Block, n: int, cuts_rows: bool
    ) -> tuple[Block | None, Block | None]:
        """Compute prefix and suffix blocks for a strip around the given block.

        The strip spans the full range perpendicular to the slice direction.
        """
        if cuts_rows:
            # Vertical strip: full rows, at block's columns
            t_r1, t_r2 = block.start.row, block.end.row
            c1, c2 = block.start.col, block.end.col

            prefix = (
                Block(Point(0, c1), Point(t_r1 - 1, c2))
                if t_r1 > 0 else None
            )
            suffix = (
                Block(Point(t_r2 + 1, c1), Point(n - 1, c2))
                if t_r2 < n - 1 else None
            )
        else:
            # Horizontal strip: full columns, at block's rows
            t_c1, t_c2 = block.start.col, block.end.col
            r1, r2 = block.start.row, block.end.row

            prefix = (
                Block(Point(r1, 0), Point(r2, t_c1 - 1))
                if t_c1 > 0 else None
            )
            suffix = (
                Block(Point(r1, t_c2 + 1), Point(r2, n - 1))
                if t_c2 < n - 1 else None
            )

        return prefix, suffix

    def _translate_block_to_source(
        self,
        target_face: Face,
        source_face: Face,
        block: Block,
        slice_name: SliceName,
    ) -> Block:
        """Translate a block from target face coordinates to source face coordinates.

        Uses translate_source_from_target to find where content at the target
        position originates from on the source face.
        """
        # Translate start corner
        results_start = Face2FaceTranslator.translate_source_from_target(
            target_face, source_face, block.start
        )
        # Find result matching our slice
        start_result = None
        for r in results_start:
            if r.slice_algorithm.whole_slice_alg.slice_name == slice_name:
                start_result = r
                break
        assert start_result is not None, (
            f"No matching slice {slice_name} for start {block.start}"
        )
        source_start = Point(*start_result.slice_algorithm.source_coord)

        # Translate end corner (same slice)
        if block.start == block.end:
            source_end = source_start
        else:
            results_end = Face2FaceTranslator.translate_source_from_target(
                target_face, source_face, block.end
            )
            end_result = None
            for r in results_end:
                if r.slice_algorithm.whole_slice_alg.slice_name == slice_name:
                    end_result = r
                    break
            assert end_result is not None, (
                f"No matching slice {slice_name} for end {block.end}"
            )
            source_end = Point(*end_result.slice_algorithm.source_coord)

        return Block(source_start, source_end).normalize

    def _build_algorithm(
        self,
        source_face: Face,
        target_face: Face,
        target_block: Block,
        rotated_block: Block,
        slice_name: SliceName,
        slice_n: int,
        rotation_type: int,
        cuts_rows: bool,
        setup_rotation: int = 0,
    ) -> Alg:
        """Build the slice swap algorithm.

        Without setup: slice → face_rotate → slice'
        With setup:    face_setup → slice → face_rotate → slice' → face_setup'
        """
        cube = self.cube

        # Get the base slice algorithm
        base_slice_alg = Algs.of_slice(slice_name)

        # Build slice sub-algorithm covering the ROTATED target block's slice range
        slice_alg = self._get_slice_alg(
            base_slice_alg, rotated_block, target_face.name, cuts_rows
        ) * slice_n

        # Face rotation
        face_rotate = Algs.of_face(target_face.name) * rotation_type

        if setup_rotation:
            # Setup: pre-rotate target face
            face_setup = Algs.of_face(target_face.name) * setup_rotation
            return Algs.seq_alg(None,
                face_setup,
                slice_alg,
                face_rotate,
                slice_alg.prime,
                face_setup.prime,
            )
        else:
            # No setup: slice → rotate → slice'
            return Algs.seq_alg(None,
                slice_alg,
                face_rotate,
                slice_alg.prime,
            )

    def _get_slice_alg(
        self,
        base_slice_alg: SliceAlg,
        target_block: Block,
        on_face: FaceName,
        cuts_rows: bool,
    ) -> SliceAlg:
        """Get the slice sub-algorithm covering the target block's range.

        For vertical slices (cuts_rows=True): uses the block's column range
        For horizontal slices (cuts_rows=False): uses the block's row range
        """
        cube = self.cube
        slice_name = base_slice_alg.slice_name
        slice_layout = cube.layout.get_slice(slice_name)

        if cuts_rows:
            # Extract columns
            v1 = target_block.start.col
            v2 = target_block.end.col
        else:
            # Extract rows
            v1 = target_block.start.row
            v2 = target_block.end.row

        # Invert if slice indexing doesn't match face coordinate order
        if not slice_layout.does_slice_of_face_start_with_face(on_face):
            v1 = inv(self.n_slices, v1)
            v2 = inv(self.n_slices, v2)

        if v1 > v2:
            v1, v2 = v2, v1

        # SliceAlg uses 1-based indexing
        return base_slice_alg[v1 + 1:v2 + 1]

    def _execute_algorithm(
        self,
        result: SliceSwapResult,
        source_face: Face,
        target_face: Face,
    ) -> None:
        """Execute the slice swap algorithm on the cube."""
        self.op.play(result.algorithm)


def get_largest_blocks_containing_point(n: int, point: Point) -> list[Block]:
    """Return the largest valid blocks that contain the given point.

    Returns those of the 4 maximal half-face blocks that contain (r,c),
    sorted by size descending.

    The 4 maximal half-face blocks (based on the "doesn't cross the middle" rule):
        1. Bottom half, full width: Block((0,0), (lower_max, n-1))
        2. Top half, full width:    Block((upper_min, 0), (n-1, n-1))
        3. Left half, full height:  Block((0,0), (n-1, lower_max))
        4. Right half, full height: Block((0, upper_min), (n-1, n-1))

    For even n: every point is in exactly 2 blocks.
    For odd n: middle row/col points may have only 1, and
    the center point (mid, mid) has none.
    """
    lower_max = (n - 2) // 2  # last row/col of lower half
    upper_min = (n + 1) // 2  # first row/col of upper half
    r, c = point.row, point.col

    candidates: list[Block] = []

    # Bottom half (rows 0..lower_max), full width
    if r <= lower_max:
        candidates.append(Block(Point(0, 0), Point(lower_max, n - 1)))

    # Top half (rows upper_min..n-1), full width
    if r >= upper_min:
        candidates.append(Block(Point(upper_min, 0), Point(n - 1, n - 1)))

    # Left half (cols 0..lower_max), full height
    if c <= lower_max:
        candidates.append(Block(Point(0, 0), Point(n - 1, lower_max)))

    # Right half (cols upper_min..n-1), full height
    if c >= upper_min:
        candidates.append(Block(Point(0, upper_min), Point(n - 1, n - 1)))

    # Sort by size descending
    candidates.sort(key=lambda b: b.size, reverse=True)

    return candidates


def get_largest_blocks_from_point(n: int, point: Point) -> list[Block]:
    """Return the largest valid blocks with (r,c) as bottom-left corner.

    Given point (r,c), extends UP (smaller rows) and RIGHT (larger cols)
    as far as possible while staying valid (not crossing the middle in at
    least one direction after 180° rotation).

    Face coordinate system: left-top-right (row 0 is top, col 0 is left).

    For 180° rotation, the range [a, b] must not overlap with [n-1-b, n-1-a]:
        lower half boundary: lower_max = (n-2) // 2
        upper half boundary: upper_min = (n+1) // 2

    Returns up to 2 blocks with (r,c) at bottom-left:
        1. Row-safe: rows constrained to the half containing r, cols c..n-1
        2. Col-safe: cols constrained to the half containing c, rows 0..r

    Sorted by size descending.
    On odd cubes, if r or c is on the middle row/col, that direction yields
    no block. The center point (mid, mid) returns empty.
    """
    lower_max = (n - 2) // 2  # last row/col of lower half
    upper_min = (n + 1) // 2  # first row/col of upper half
    r, c = point.row, point.col

    candidates: list[Block] = []

    # Row-safe block: rows stay within half, cols extend right to n-1
    if r <= lower_max:
        # r is in lower half → rows 0..r, cols c..n-1
        candidates.append(Block(Point(0, c), Point(r, n - 1)))
    elif r >= upper_min:
        # r is in upper half → rows upper_min..r, cols c..n-1
        candidates.append(Block(Point(upper_min, c), Point(r, n - 1)))
    # else: r is on the middle (odd cube) — no row-safe block

    # Col-safe block: cols stay within half, rows extend up to 0
    if c <= lower_max:
        # c is in left half → rows 0..r, cols c..lower_max
        candidates.append(Block(Point(0, c), Point(r, lower_max)))
    elif c >= upper_min:
        # c is in right half → rows 0..r, cols c..n-1
        candidates.append(Block(Point(0, c), Point(r, n - 1)))
    # else: c is on the middle (odd cube) — no col-safe block

    # Deduplicate (both may produce the same block, e.g. when r <= lower_max and c >= upper_min)
    seen: set[tuple[int, int, int, int]] = set()
    unique: list[Block] = []
    for b in candidates:
        key = (b.start.row, b.start.col, b.end.row, b.end.col)
        if key not in seen:
            seen.add(key)
            unique.append(b)

    # Sort by size descending
    unique.sort(key=lambda b: b.size, reverse=True)

    return unique


def iter_sub_blocks(block: Block) -> Iterator[Block]:
    """Yield all sub-blocks anchored at block.start, biggest to smallest.

    Given Block(start=(r1,c1), end=(r2,c2)), yields all
    Block((r1,c1), (r,c)) for r1 <= r <= r2, c1 <= c <= c2.

    Biggest = full block (r1,c1,r2,c2), smallest = single cell (r1,c1,r1,c1).

    Iteration order: outer loop shrinks the bigger dimension first.
    - If width >= height: outer loop on cols (c2 down to c1),
      inner loop on rows (r2 down to r1).
    - If height > width: outer loop on rows (r2 down to r1),
      inner loop on cols (c2 down to c1).
    """
    r1, c1 = block.start.row, block.start.col
    r2, c2 = block.end.row, block.end.col
    height = r2 - r1 + 1
    width = c2 - c1 + 1

    if width >= height:
        # Wider or square: shrink cols first (outer), then rows (inner)
        for c in range(c2, c1 - 1, -1):
            for r in range(r2, r1 - 1, -1):
                yield Block(Point(r1, c1), Point(r, c))
    else:
        # Taller: shrink rows first (outer), then cols (inner)
        for r in range(r2, r1 - 1, -1):
            for c in range(c2, c1 - 1, -1):
                yield Block(Point(r1, c1), Point(r, c))


def _1d_intersect(range_1: tuple[int, int], range_2: tuple[int, int]) -> bool:
    """Check if two 1D ranges intersect."""
    x1, x2 = range_1
    x3, x4 = range_2
    if x1 > x2:
        x1, x2 = x2, x1
    if x3 > x4:
        x3, x4 = x4, x3
    return not (x3 > x2 or x4 < x1)
