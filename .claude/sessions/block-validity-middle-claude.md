# Session Summary: Block Validity — "Doesn't Cross the Middle" Rule

**Date:** 2026-03-13
**Branch:** `claude/block-slice-swap-algorithm-R6Pml`
**Status:** IN PROGRESS

## Insight

A block is valid for swap if it **doesn't cross the middle in at least one direction**.

- If a block stays entirely in one half (row or col), then its 180°-rotated
  image lands in the other half — no overlap — valid.
- If it crosses the middle in BOTH directions, every rotation overlaps — invalid.

### Half boundaries (precise math)

For 180° rotation, range `[a, b]` must not overlap `[n-1-b, n-1-a]`:
- **lower_max** = `(n-2) // 2` — last row/col of lower half
- **upper_min** = `(n+1) // 2` — first row/col of upper half
- Even n: halves touch (`lower_max + 1 == upper_min`)
- Odd n: middle row/col excluded from both halves (gap at `n//2`)

### Edge cases (odd cubes)

- Center cell `(mid, mid)` — on the middle in both directions — always invalid
- Middle row/col points — only valid in the perpendicular direction's half

## Implemented Building Blocks

### 1. `get_largest_blocks_containing_point(n, point)`
Returns the maximal half-face blocks (from the 4 possible) that **contain** the point.
- Even cubes: every point in exactly 2 blocks
- Odd cubes: middle row/col → 1 block; center → 0 blocks
- Test: `TestLargestBlocksContainingPoint` (12 tests)

### 2. `get_largest_blocks_from_point(n, point)`
Returns the largest valid blocks with `(r,c)` as **bottom-left corner**, extending
UP (smaller rows) and RIGHT (larger cols):
- Row-safe: rows constrained to half, cols `c..n-1`
- Col-safe: cols constrained to half, rows `0..r`
- Deduplicates when both produce the same block
- Test: `TestLargestBlocksFromPoint` (17 tests)

## Next Steps

- Nuclear test: use these building blocks in the full swap validation
