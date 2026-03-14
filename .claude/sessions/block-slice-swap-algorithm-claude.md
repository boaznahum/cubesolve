# Session Summary: Block-by-Slice Swap Algorithm

**Date:** 2026-03-13
**Branch:** `claude/block-slice-swap-algorithm-R6Pml`
**Status:** IN PROGRESS

## What Was Built

Designed and implemented the **Block-by-Slice Swap** algorithm — a simpler
alternative to the commutator for moving blocks between faces on big NxN cubes.

### Core Algorithm

**Formula**: `slice → face_rotate(180°) → slice'`

With optional setup: `face_setup(90°) → slice → face_rotate(180°) → slice' → face_setup'`

Unlike the commutator (which performs a 3-cycle), this swaps **ALL content**
on the affected slices — **6 blocks total** (3 on target face, 3 on source face):
prefix, main, suffix on each.

### Implementation

**File**: `src/cube/domain/solver/common/big_cube/commutator/BlockBySliceSwapHelper.py`

Key methods:
- `is_valid_for_swap(block)` — self-intersection check
- `get_all_combinations(source, target, block)` — all 4 combo attempts
- `execute_swap(...)` — the actual swap, computing all 6 blocks + algorithm

### Test Coverage

**File**: `tests/geometry/test_block_slice_swap.py`

- 6-block marker verification across all 30 face pair combinations
- Full-slice blocks: 576 individual test cases
- Center cell invariant on odd cubes
- Dry run mode verification

## Key Insights

### 1. Four Combinations via Setup Rotation

Each face pair has ONE natural slice (H or V on the target face). A 90° CW
setup rotation of the target face converts H↔V, doubling the options.
Combined with slice direction → **4 combinations** per face pair.

### 2. 90° CCW is Redundant for Self-Intersection

**Proved and removed** (commit `bda5819`): If CW overlaps on both axes,
CCW must also overlap on both axes. Only need to check CW and 180°.

### 3. Center Cell Invariant

On odd cubes, `(n//2, n//2)` maps to itself under all rotations — always invalid.

### 4. "Doesn't Cross the Middle" Rule

**User's insight**: A block is valid if it **doesn't cross the middle in at
least one direction**.

Why this works:
- Block entirely in one half (row or col) → 180° rotation sends it to other half → no overlap → valid
- Block crosses the middle in BOTH directions → every rotation overlaps → invalid
- This is a simpler geometric equivalent of the rotation-based self-intersection check

**Half boundaries (precise math):**
For 180° rotation, range `[a, b]` must not overlap `[n-1-b, n-1-a]`:
- `lower_max = (n-2) // 2` — last row/col of lower half
- `upper_min = (n+1) // 2` — first row/col of upper half
- Even n: halves touch (`lower_max + 1 == upper_min`)
- Odd n: middle row/col excluded from both halves (gap at `n//2`)

### 5. Building Block Functions

**`get_largest_blocks_containing_point(n, point)`**
Returns the maximal half-face blocks (from the 4 possible) that **contain** the point.
- Even cubes: every point in exactly 2 blocks
- Odd cubes: middle row/col → 1 block; center → 0 blocks
- Test: `TestLargestBlocksContainingPoint`

**`get_largest_blocks_from_point(n, point)`**
Returns the largest valid blocks with `(r,c)` as **bottom-left corner**, extending
UP (smaller rows) and RIGHT (larger cols):
- Row-safe: rows constrained to half, cols `c..n-1`
- Col-safe: cols constrained to half, rows `0..r`
- Deduplicates when both produce the same block
- Test: `TestLargestBlocksFromPoint`

## Commits (oldest → newest)

```
4fc752e Create block-slice-swap-algorithm
33d59af Update block-slice-swap-algorithm
32b9756 Update block-slice-swap-algorithm
9257265 Update block-slice-swap-algorithm
4a846bc Add BlockBySliceSwapHelper for block-by-slice swap algorithm
8e146fa Support all 4 slice swap combinations via setup rotation
67d2410 Expand slice swap tests to all 30 face pair combinations
106c53b Add even cube sizes (4x4, 6x6) to slice swap tests
980ae40 Remove even cube from odd-only center block test to eliminate skip
0ab3b6b Add full-slice block tests: 2n blocks × 4 adjacent sources per face
9f461bf Skip center strips on odd cubes in full-slice block tests
5aa12c1 Expand full-slice tests to 576 individual test cases
f3884f0 Use all 30 face pairs (not just 4 adjacent) in full-slice tests
85f8e10 Use geometry-based filtering for multi-width full-slice blocks
bda5819 Remove redundant 90° CCW check from is_valid_for_swap
```

## Session 2 (2026-03-14): get_largest_blocks_from_point Fix

**Status:** ✅ COMPLETED

### Problem

`get_largest_blocks_from_point` was not discovering all valid blocks.
On a 4×4 grid (cube_size=6), the algorithm failed to find the 4 vertical 4×1
and 4 horizontal 1×4 full-column/full-row blocks.

**Root Cause:** The function used an inverted coordinate convention.
It extended blocks toward row 0 (downward) instead of toward larger rows (upward).
With row 0 as bottom-left, "extending up" means increasing row numbers.

### What Was Fixed

#### `get_largest_blocks_from_point` (BlockBySliceSwapHelper.py)

**Before (broken):** Blocks extended from `(r,c)` down to row 0:
- Row-safe: `Block(Point(0, c), Point(r, n-1))`
- Col-safe: `Block(Point(0, c), Point(r, lower_max))`

**After (correct):** Blocks extend from `(r,c)` upward to the half boundary:
- Row-safe: `Block(Point(r, c), Point(lower_max, n-1))` or `Block(Point(r, c), Point(n-1, n-1))`
- Col-safe: `Block(Point(r, c), Point(n-1, lower_max))` or `Block(Point(r, c), Point(n-1, n-1))`

The point `(r,c)` is always `block.start` (bottom-left corner), and blocks grow
toward `(n-1, n-1)` (top-right).

#### Tests (test_block_slice_swap.py)

Updated assertions to match the start-anchored convention:
- `block.end.row == r` → `block.start.row == r`
- `iter_sub_blocks` tests: anchored at start, end varies

### Verification

#### 4×4 grid (cube_size=6)

All **4 vertical 4×1** and **4 horizontal 1×4** blocks discovered:

```
Vertical:  (0,0)->(3,0)  (0,1)->(3,1)  (0,2)->(3,2)  (0,3)->(3,3)
Horizontal: (0,0)->(0,3)  (1,0)->(1,3)  (2,0)->(2,3)  (3,0)->(3,3)
```

#### 6×6 grid (cube_size=8) — Full Distribution

360 unique blocks total:

```
 HxW  | Count     HxW  | Count
------+------    ------+------
 1x1  |  36       4x1  |  18
 1x2  |  30       4x2  |  12
 1x3  |  24       4x3  |   6
 1x4  |  18       5x1  |  12
 1x5  |  12       5x2  |   8
 1x6  |   6       5x3  |   4
 2x1  |  30       6x1  |   6
 2x2  |  24       6x2  |   4
 2x3  |  18       6x3  |   2
 2x4  |  12
 2x5  |   8
 2x6  |   4
 3x1  |  24
 3x2  |  18
 3x3  |  12
 3x4  |   6
 3x5  |   4
 3x6  |   2
```

Notable: 6 full vertical columns (6×1) and 6 full horizontal rows (1×6).

### Discovery Chain

```
get_largest_blocks_from_point(n, point)  →  up to 2 largest valid blocks
    ↓
iter_sub_blocks(block)  →  all sub-blocks anchored at start, biggest first
    ↓
is_valid_for_swap(block)  →  check no self-intersection under rotation
```

### All Tests Pass

1241 tests passed (test_block_slice_swap.py), including nuclear swap tests
for cube sizes 4–7.

## Next Steps

- Use block-slice-swap in actual solver strategies
