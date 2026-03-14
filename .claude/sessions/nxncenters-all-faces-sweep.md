# Session: NxNCenters All Faces Sweep

**Date:** 2026-03-14
**Branch:** `nxncenters-all-faces-sweep`
**Status:** COMPLETE - deployed to dev v1.65

## Goal

1. Replace `_swap_slice` with `BlockBySliceSwapHelper.execute_swap()`
2. New grade-based algorithm for finding best slice swaps
3. Merge nuclear branch (`origin/nxncenters-support-all-faces`) for all-faces support
4. Replace `CenterBlockStatistics` with typed `SolverStatistics` system

## What Was Done

### 1. Grade-Based Complete Slice Algorithm

Replaced the old `_swap_slice` pipeline with a grade-based search:
- Generate all full-slice blocks (nn columns + nn rows, skip middle on odd)
- Precompute natural sources via BSH dry_run
- For each target slice x 4 source rotations: grade = solved_after - solved_before
- Both faces' colors considered for grading
- Pick best (grade > 1), execute, repeat until no improvement
- Safety assert at nn^2 iterations

### 2. All Faces Support (Nuclear Branch Merge)

- Merged `origin/nxncenters-support-all-faces`
- Removed `source_is_up_or_back` / `source_on_m_axis` restriction
- `_do_complete_slices` now called for ALL source faces
- Removed disabling line: `if True: self._OPTIMIZE = False`

### 3. SolverStatistics with Typed Keys

New `SolverStatistics` system replacing `CenterBlockStatistics`:
- `TopicKey[T]` — generic typed key, `get_topic(key)` returns `T`
- `StatsTopic` — abstract base with merge, format_lines, reset, is_empty
- `BlockSizeTopic` — tracks block sizes (replaces old dict)
- `SliceSwapTopic` — tracks swap count, pieces, grade histogram
- Updated 14 files across solver hierarchy

### Removed Methods (from NxNCenters)
- `_swap_slice`, `_do_one_complete_slice`, `_do_one_complete_slice_imp`
- `_search_slices_on_face`, `_point_on_target`, `_get_slice_m_alg`
- `_CompleteSlice` dataclass, `_swap_entire_face_odd_cube`, `_preserve_trackers`

### Added Methods (to NxNCenters)
- `_do_complete_slices` (rewritten with grade loop)
- `_compute_swap_grade`, `_generate_all_slice_blocks`, `_get_face_color`

## Test Results
- 7893 solver tests passed, 0 failed
- 11509 non-GUI tests passed (4 webgl timeouts unrelated)
- Slice swaps verified: sizes 5-8 all fire 5-9 swaps per solve

## Commits
- `66575a37` WIP: New grade-based complete slice algorithm
- `14762b5e` Merge nuclear branch + grade-based slice swaps + SolverStatistics

## Key Files
- `src/cube/domain/solver/common/SolverStatistics.py` — new typed stats system
- `src/cube/domain/solver/common/big_cube/NxNCenters.py` — main changes
- `src/cube/domain/solver/common/big_cube/commutator/BlockBySliceSwapHelper.py` — used for swaps

## References
- Nuclear branch: `origin/nxncenters-support-all-faces`
- Design doc: `src/cube/domain/solver/common/big_cube/commutator/block_by_slice_swap_helper.md`
