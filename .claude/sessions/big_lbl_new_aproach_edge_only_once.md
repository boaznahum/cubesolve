# Session Summary: Big LBL Edge Solving Bug Fix

**Branch:** `big_lbl_new_aproach_edge_only_once`
**Date:** 2026-01-26

## Overview

Working on fixing bugs in the LayerByLayerNxNSolver (LBL_BIG solver) for solving big cubes layer-by-layer.

---

## Bug 1: Center Slices Solving Wrong Rows (FIXED & COMMITTED)

**Status:** ✅ Fixed in commit `8b86e0b6`

### Problem
When `NUMBER_OF_SLICES_TO_SOLVE=1`, solver still solved ALL center rows.

### Root Cause
1. `_is_center_slice()` returns bool, but code checked `is not None` (always True)
2. `_try_remove_all_pieces_from_target_face_and_other_faces` operated on target face at rotated positions

---

## Bug 2: Edge Solving Non-Deterministic Order (FIXED, UNCOMMITTED)

**Status:** ✅ Fixed, 41 tests now pass

### Problem
Edge solving failed inconsistently because face processing order depended on when `FacesTrackerHolder` was created.

### Root Cause
`_get_side_face_trackers()` returned faces in arbitrary order from `th.trackers`.

### Fix
Added sorting by color name in `_common.py`:
```python
return sorted(side_trackers, key=lambda t: t.color.name)
```

---

## Bug 3: Source Wing Orientation Issue (PARTIALLY FIXED)

**Status:** 🔄 In Progress - 41/42 tests pass, 1 test fails due to missing flip logic

### Current State

After reverting incorrect changes, 41/42 tests pass:
```bash
CUBE_QUIET_ALL=1 .venv/Scripts/python.exe -m pytest tests_wip/big_lbl/test_lbl_big_cube_solver.py::TestLBLBigCubeSolver::test_lbl_slices_ctr -v --tb=no
# Result: 41 passed, 1 failed (seed_7-7-size_5)
```

### The Failing Test

`seed_7-7-size_5` fails with:
```
Wing FR[0][ORANGE, GREEN]⬅️[GREEN, ORANGE] is not solved
```

This is an **orientation issue**: FR[0] has the correct colors (ORANGE, GREEN) but they're swapped:
- F-sticker = ORANGE (should be GREEN)
- R-sticker = GREEN (should be ORANGE)

### Root Cause Analysis

**The original `_bring_source_wing_to_top()` has NO orientation checking or flip logic.** It simply:
1. Brings source edge to FL or FR
2. Moves source to FU via communicator
3. Rotates cube to bring target face to front

In most cases (41/42 tests), the source happens to have correct orientation. But in `seed_7-7-size_5`, the source has wrong orientation and there's no logic to fix it.

### Important Discovery - The Orientation CHECK is CORRECT

The check at line 397:
```python
if untracked_source_wing.get_face_edge(cube.up).color != target_face.color:
    # proceed with comm
```

This logic is **CORRECT** and should NOT be changed:
- `u_sticker != target_color` means F-sticker = target_color (since wing has exactly 2 colors)
- After FU→FL comm: FL F-sticker = FU U-sticker
- So if FU U-sticker != target_color, then FU F-sticker = target_color
- After comm: FL F-sticker = FU U-sticker ≠ target_color... wait, this is backwards

Actually, let me re-analyze:
- FL needs: F-sticker = target_color (front color)
- FU→FL comm swaps: U-sticker→F-sticker, F-sticker→L-sticker
- So for FL F-sticker = target_color, we need FU U-sticker = target_color
- Check should be: `u_sticker == target_color` for correct orientation

**BUT the original code uses `u_sticker != target_color` and 41/42 tests pass!**

This suggests either:
1. My trace analysis is wrong
2. Or the algorithm compensates for the "backwards" check elsewhere

### Failed Fix Attempt

I tried changing line 397 from `!=` to `==` thinking the check was inverted. **This broke all 42 tests!** The original logic is somehow correct (or compensated for elsewhere).

### Correct Fix Needed

The fix should ADD orientation flip logic to `_bring_source_wing_to_top()`:
1. After bringing source to FU, check if orientation is correct
2. If wrong, flip by: FU → FL/FR (via comm) → Y rotation → FR/FL → FU (via opposite side comm)
3. The opposite path produces opposite orientation

### Key Constraint

The flip changes the FU index: FU[j] → FU[inv(j)]. This affects which target can be solved:
- FU[j] can solve FL[inv(j)] or FR[j]
- After flip: FU[inv(j)] can solve FL[j] or FR[inv(j)]

If the flip would make the source incompatible with the target, we need to either:
- Skip the flip and find a different source
- Solve a different compatible target first

---

## Files Changed (Uncommitted)

1. `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py`
   - Removed unused `and_` import

2. `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py`
   - Removed unused imports
   - WIP: orientation fix in `_bring_source_wing_to_top()`

3. `src/cube/domain/solver/direct/lbl/_common.py`
   - Added sorting to `_get_side_face_trackers()`

---

## Test Status

- **PASSED:** 41
- **FAILED:** 1 (`seed_7-7-size_5` - orientation bug)

---

## Debug Files

- `tests_wip/big_lbl/debug_edge_bug9.py` - Reproduces seed 7, size 5 failure
- `tests_wip/big_lbl/debug_both_faces.py` - Traces orientation checks
- `tests_wip/big_lbl/debug_flip.py` - Traces flip attempts
- `tests_wip/big_lbl/debug_edge_selected_sources.py` - Shows source selection
