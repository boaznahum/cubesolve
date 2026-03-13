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

### 4. "Doesn't Cross the Middle" Rule (NEW — not yet implemented)

**User's insight**: A block is valid if it **doesn't cross the middle in at
least one direction**.

Why this works:
- Block entirely in one half (row or col) → 180° rotation sends it to other half → no overlap → valid
- Block crosses the middle in BOTH directions → every rotation overlaps → invalid
- This is a simpler geometric equivalent of the rotation-based self-intersection check

This is the next thing to implement.

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

## Next Steps

- Implement "doesn't cross the middle" as a simpler validity check
- Use block-slice-swap in actual solver strategies
