# Session: NxNCenters Use New Sweep Helper

**Date:** 2026-03-14
**Branch:** `nxnceters_use_new_sweep_helper`
**Status:** IN PROGRESS

## Goal

Simplify `NxNCenters._swap_slice` and complete slice logic by using `BlockBySliceSwapHelper.execute_swap()` instead of manual coordinate computation.

## What Was Done

### Replaced `_do_complete_slices` with grade-based algorithm

Old approach:
- `_do_complete_slices` → `_do_one_complete_slice` → `_do_one_complete_slice_imp` → `_swap_slice`
- Manual coordinate computation, F' setup, source alignment, M-slice algorithm
- Only compared matching indices between source and target

New approach:
- Single `_do_complete_slices` with grade-based search
- Groups all slice blocks into g4 groups (4 rotationally-equivalent slices)
- For each (ts, ss) pair: computes grade = solved_after - solved_before
- Considers BOTH target and source face colors for grading
- Picks globally best swap, executes via `BlockBySliceSwapHelper.execute_swap()`
- Repeats until no swap with grade > 1

### Removed methods
- `_swap_slice` — replaced by `BlockBySliceSwapHelper.execute_swap()`
- `_do_one_complete_slice` — absorbed into new `_do_complete_slices`
- `_do_one_complete_slice_imp` — absorbed into new `_do_complete_slices`
- `_search_slices_on_face` — replaced by g4 group enumeration
- `_point_on_target` — no longer needed (BSH handles coordinates)
- `_get_slice_m_alg` — no longer needed (BSH builds algorithms)
- `_CompleteSlice` dataclass — replaced by `Block`

### Added methods
- `_compute_swap_grade()` — grades a (ts, ss) pair
- `_generate_g4_groups()` — generates g4 groups of full-slice blocks
- `_get_face_color()` — gets face's target color from tracker

### Removed imports
- `from cube.domain import algs` (unused after _swap_slice removal)
- `AnnWhat` (unused)
- `CenterSlice` (unused)
- `dataclass` (unused)

## Key Design Decisions

- Grade considers BOTH faces: `(target_ok_after + source_ok_after) - (target_ok_before + source_ok_before)`
- Grade threshold > 1 (at least 2 pieces net improvement)
- Safety assert: max iterations = nn^2
- `undo_target_setup` and `undo_source_setup` controlled by `self._preserve_cage`
- Still restricted to UP/BACK sources (caller limitation), nuclear branch has all-faces support

## Next Steps

- [ ] Run solver tests to verify correctness
- [ ] Fix any test failures
- [ ] Run all 5 checks before committing

## References

- Nuclear branch: `origin/nxncenters-support-all-faces` for future all-faces support
- BlockBySliceSwapHelper: `src/cube/domain/solver/common/big_cube/commutator/BlockBySliceSwapHelper.py`
- Design doc: `src/cube/domain/solver/common/big_cube/commutator/block_by_slice_swap_helper.md`
