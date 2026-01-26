# Session Summary: Big LBL Center Slices Bug Fix

**Branch:** `big_lbl_new_aproach_edge_only_once`
**Date:** 2026-01-26

## Problem

When `NUMBER_OF_SLICES_TO_SOLVE=1` was set in `_lbl_config.py`, the solver was still solving ALL center rows instead of just row 0.

## Root Cause Analysis

Two bugs were found:

### Bug 1: `_iterate_all_tracked_center_slices_index` returning ALL slices

**File:** `src/cube/domain/solver/direct/lbl/_common.py` line 265

**Problem:**
```python
if _is_center_slice(cs) is not None:  # BUG: always True!
```

The function `_is_center_slice()` returns a **bool** (`True`/`False`), not `None`. So the check `is not None` was always `True` for both values, causing ALL 9 center slices to be iterated instead of just the tracked ones.

**Fix:**
```python
if _is_center_slice(cs):  # Just check the boolean value
```

### Bug 2: `_try_remove_all_pieces_from_target_face_and_other_faces` solving wrong rows

**File:** `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py` lines 313-351

**Problem:** The rotation loop was searching ALL faces including the target face. When operating on the target face at rotated positions, it placed pieces at rows 1 and 2 instead of just row 0.

Original code checked `if n == 0 and move_from_target_face_is_target_face: continue` which only skipped the target face at the original position (n=0), but operated on it at rotated positions (n=1,2,3).

**Fix:**
- Keep the rotation loop (needed to find pieces at different positions on OTHER faces)
- ALWAYS skip the target face regardless of rotation:
```python
if move_from_target_face is _target_face_tracker.face:
    continue  # ALWAYS skip target face
```

## Testing

### Before Fix
- 5x5 cube with `NUMBER_OF_SLICES_TO_SOLVE=1`: All 3 rows solved (bug)
- 7x7 cube: Row 2 failed with 23/24 pieces (missing GREEN piece)

### After Fix
- 5x5 cube with `NUMBER_OF_SLICES_TO_SOLVE=1`: Only row 0 solved (correct)
- 7x7 cube with all slices: All 5 rows solved (correct)

## Files Changed

1. `src/cube/domain/solver/direct/lbl/_common.py`
   - Line 265: Fixed boolean check in `_iterate_all_tracked_center_slices_index`

2. `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py`
   - Lines 313-351: Fixed `_try_remove_all_pieces_from_target_face_and_other_faces` to always skip target face

## Commits

- Bug fix commit with tag (to be created)
