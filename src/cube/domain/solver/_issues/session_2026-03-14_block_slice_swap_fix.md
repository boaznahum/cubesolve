# Session Summary: Block-by-Slice Swap — get_largest_blocks_from_point Fix

**Date:** 2026-03-14
**Branch:** `claude/block-slice-swap-algorithm-R6Pml`
**Status:** ✅ COMPLETED

## Problem Statement

`get_largest_blocks_from_point` was not discovering all valid blocks.
On a 4×4 grid (cube_size=6), the algorithm failed to find the 4 vertical 4×1
and 4 horizontal 1×4 full-column/full-row blocks.

**Root Cause:** The function used an inverted coordinate convention.
It extended blocks toward row 0 (downward) instead of toward larger rows (upward).
With row 0 as bottom-left, "extending up" means increasing row numbers.

## What Was Fixed

### `get_largest_blocks_from_point` (BlockBySliceSwapHelper.py)

**Before (broken):** Blocks extended from `(r,c)` down to row 0:
- Row-safe: `Block(Point(0, c), Point(r, n-1))`
- Col-safe: `Block(Point(0, c), Point(r, lower_max))`

**After (correct):** Blocks extend from `(r,c)` upward to the half boundary:
- Row-safe: `Block(Point(r, c), Point(lower_max, n-1))` or `Block(Point(r, c), Point(n-1, n-1))`
- Col-safe: `Block(Point(r, c), Point(n-1, lower_max))` or `Block(Point(r, c), Point(n-1, n-1))`

The point `(r,c)` is always `block.start` (bottom-left corner), and blocks grow
toward `(n-1, n-1)` (top-right).

### Tests (test_block_slice_swap.py)

Updated assertions to match the start-anchored convention:
- `block.end.row == r` → `block.start.row == r`
- `iter_sub_blocks` tests: anchored at start, end varies

## Verification

### 4×4 grid (cube_size=6)

All **4 vertical 4×1** and **4 horizontal 1×4** blocks discovered:

```
Vertical:  (0,0)->(3,0)  (0,1)->(3,1)  (0,2)->(3,2)  (0,3)->(3,3)
Horizontal: (0,0)->(0,3)  (1,0)->(1,3)  (2,0)->(2,3)  (3,0)->(3,3)
```

### 6×6 grid (cube_size=8) — Full Distribution

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

## Discovery Chain

```
get_largest_blocks_from_point(n, point)  →  up to 2 largest valid blocks
    ↓
iter_sub_blocks(block)  →  all sub-blocks anchored at start, biggest first
    ↓
is_valid_for_swap(block)  →  check no self-intersection under rotation
```

## All Tests Pass

1241 tests passed (test_block_slice_swap.py), including nuclear swap tests
for cube sizes 4–7.
