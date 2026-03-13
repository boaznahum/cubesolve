# Session Summary: Block Validity — "Doesn't Cross the Middle" Rule

**Date:** 2026-03-13
**Branch:** `claude/block-slice-swap-algorithm-R6Pml`
**Status:** IN PROGRESS

## Insight

A block is valid for swap if it **doesn't cross the middle in at least one direction**.

- If a block stays entirely in one half (row or col), then its 180°-rotated
  image lands in the other half — no overlap — valid.
- If it crosses the middle in BOTH directions, every rotation overlaps — invalid.
- This is a simpler geometric equivalent of the current rotation-based
  self-intersection check in `is_valid_for_swap`.

### Edge case

On odd cubes, the center cell `(n//2, n//2)` sits exactly on the middle in
both directions — correctly flagged as invalid.

## Next Steps

- Implement and validate this rule
