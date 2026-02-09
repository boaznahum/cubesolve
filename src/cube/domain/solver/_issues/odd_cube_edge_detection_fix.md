# Fix: Odd Cube Edge Detection in solve_face_edges()

**Date:** 2026-02-10
**Branch:** `big-lbl-even-opus_2`
**Status:** ✅ FIXED
**Breaking Commit:** `2a3eac1f` - "Fix NxNEdges to respect required color in solve_face_edges()"

## Problem Statement

After fixing even cube L1 edge solving (commit `2a3eac1f`), odd cube (5x5, 7x7) tests started failing with:
```
AssertionError: Expected 4 edges with WHITE, found 7/8/11
```

The error occurred in `NxNEdges.solve_face_edges()` at line 94-95.

## Root Cause Analysis

### Breaking Change in Commit 2a3eac1f

The commit added `required_color` parameter to `_do_edge()` to fix even cube edge pairing. However, it introduced TWO bugs for odd cubes:

### Bug 1: _edge_contains_color() Checking All Slices

**Location:** `NxNEdges._edge_contains_color()` (lines 598-601)

**Old code:**
```python
@staticmethod
def _edge_contains_color(edge: Edge, color: Color) -> bool:
    for i in range(edge.n_slices):
        if color in edge.get_slice(i).colors_id:
            return True
    return False
```

**Problem:** Checks ALL slices on the edge to see if any contain the target color.

**Why this is wrong for odd cubes:**
- On odd cubes (3x3, 5x5, 7x7), the **middle slice** defines the edge's identity (`edge.colors_id`)
- After scrambling, OTHER slices may temporarily have different colors until they're paired
- By checking all slices, the code found edges where:
  - Middle slice has WHITE (✓ correct WHITE edge)
  - OR any other slice happens to have WHITE (✗ wrong - just a scrambled slice)
- This caused finding 7-11 edges with WHITE instead of the correct 4

**Example on 5x5 after scramble:**
- Edge at FL position: middle slice has {WHITE, RED} → This IS a WHITE edge
- Edge at FR position: middle slice has {RED, BLUE}, but slice 1 has {WHITE, GREEN} → NOT a WHITE edge, just has a scrambled white slice

### Bug 2: Using required_color for Odd Cubes

**Location:** `NxNEdges.solve_face_edges()` (line 124)

**Old code:**
```python
self._do_edge(edge, required_color=target_color)
```

**Problem:** Passes `required_color` for both even AND odd cubes.

**Why this is wrong for odd cubes:**
- On odd cubes, the middle slice ALREADY defines the edge's colors and orientation
- The `_determine_ordered_color_for_required_color()` method would return `(required_color, other_color)`
- But the middle slice might have the colors in the opposite orientation: `(other_color, required_color)`
- When `_fix_all_slices_on_edge()` tried to fix the middle slice orientation, it failed with `InternalSWError()` at line 272
- This is because **you can't change the middle slice orientation on an odd cube** - it defines what the edge IS

## The Fix

### Fix 1: Check Only Middle Slice for Odd Cubes

**File:** `src/cube/domain/solver/common/big_cube/NxNEdges.py`

**Modified `_edge_contains_color()` method:**
```python
@staticmethod
def _edge_contains_color(edge: Edge, color: Color) -> bool:
    """Check if this edge contains the given color.

    For odd cubes (3x3, 5x5, 7x7):
        Only check the middle/representative slice (edge.colors_id).
        The middle slice defines the edge's identity.

    For even cubes (4x4, 6x6, 8x8):
        Check ALL slices. During scrambling, slices can have different
        color-pairs, so we need to check if any slice contains the target color.
    """
    # Odd cube: Only check representative slice (middle slice)
    if edge.n_slices % 2 == 1:
        return color in edge.colors_id

    # Even cube: Check all slices
    for i in range(edge.n_slices):
        if color in edge.get_slice(i).colors_id:
            return True
    return False
```

### Fix 2: Only Use required_color for Even Cubes

**File:** `src/cube/domain/solver/common/big_cube/NxNEdges.py`

**Modified `solve_face_edges()` method (lines 122-127):**
```python
# Solve one edge
edge = unsolved[0]
# For even cubes: specify required_color to force correct orientation
# For odd cubes: use auto-detection (None) because middle slice defines identity
required_color_param = target_color if self.cube.is_even else None
self._do_edge(edge, required_color=required_color_param)
```

## Why This Works

### For Odd Cubes:
1. `_edge_contains_color()` checks only the middle slice to identify edges
2. Correctly finds exactly 4 edges containing the target color
3. `_do_edge()` gets `required_color=None` and auto-detects from middle slice
4. No attempt to change middle slice orientation - respects the edge's identity

### For Even Cubes:
1. `_edge_contains_color()` checks all slices (correct - slices can differ)
2. `_do_edge()` gets `required_color=target_color` to force correct orientation
3. `_determine_ordered_color_for_required_color()` returns desired orientation
4. All slices are fixed to have the target color in the correct orientation

## Test Results

**Before fix:**
- Odd cube LBL-Big tests: 0/4 passing (all failed with "Expected 4 edges with WHITE, found 7/8/11")
- Even cube L1 tests: 50/50 passing ✓

**After fix:**
- Odd cube tests (3x3, 5x5, all solvers): 40/40 passing ✓
- Even cube L1 tests (4x4-12x12): 50/50 passing ✓
- Even cube general tests (4x4, 8x8, all solvers): 32/32 passing ✓

## Key Insights

1. **Middle slice is authoritative for odd cubes** - The middle slice defines what an edge IS, not just what colors it currently has
2. **required_color is for even cubes only** - Odd cubes must use auto-detection because the middle slice is immutable
3. **Edge identity vs edge state** - For odd cubes, edge identity (middle slice) is separate from edge state (are other slices paired?)
4. **Test coverage matters** - The breaking commit passed all tests at the time because odd cube LBL-Big tests were in a separate test suite

## Files Modified

| File | Changes |
|------|---------|
| `src/cube/domain/solver/common/big_cube/NxNEdges.py` | Modified `_edge_contains_color()` to check only middle slice for odd cubes<br>Modified `solve_face_edges()` to only pass `required_color` for even cubes |
| `src/cube/domain/solver/_issues/odd_cube_edge_detection_fix.md` | This document |

## Related Issues

- Original even cube L1 fix: Session `session_2026-02-09_even_cube_l1_fix.md`
- Breaking commit: `2a3eac1f` - Tagged as `breaks-odd-cube-tests`
- Git bisect identified the breaking commit from known good commit `0540313a`

## Credits

Fix implemented by Claude Sonnet 4.5 after user identified odd cube test failures and requested git bisect investigation.
