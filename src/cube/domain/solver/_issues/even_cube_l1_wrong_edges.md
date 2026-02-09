# Even Cube L1 Wrong Edges Issue

**Status:** ACTIVE BUG
**Date:** 2026-02-09
**Branch:** big-lbl-even-opus_2

## Summary

On 4x4 even cubes, after solving L1 (centers + edges + corners), the L1 face has **wrong edges**:
- 2 edges belong to the L1 color (e.g., WHITE)
- 2 edges belong to different colors (wrong!)

The edges themselves are **paired** (all slices have same colors), but they're on the **wrong face**.

## Root Cause Analysis

### 1. Shadow Cube Orientation Bug (FIXED)

**Location:** `src/cube/domain/model/Cube3x3Colors.py:177-188`

**Problem:** When replacing non-3x3 edges with valid color-pairs during shadow cube creation, colors were assigned with arbitrary orientation:

```python
# BEFORE (BUG):
color_pair = available_pairs.pop()  # frozenset is unordered!
colors_list = list(color_pair)      # Random order!
new_edge_colors = EdgeColors({
    f1: colors_list[0],              # ❌ Arbitrary!
    f2: colors_list[1]               # ❌ Might be backwards!
})
```

**Fix (commit f67798ad):** Assign colors based on reference layout:

```python
# AFTER (FIXED):
ref_color_f1 = reference_layout[f1]
ref_color_f2 = reference_layout[f2]
if {ref_color_f1, ref_color_f2} == color_pair:
    new_edge_colors = EdgeColors({f1: ref_color_f1, f2: ref_color_f2})
else:
    colors_list = sorted(list(color_pair), key=lambda c: c.value)
    new_edge_colors = EdgeColors({f1: colors_list[0], f2: colors_list[1]})
```

### 2. Edge Orientation Detection Bug (ACTIVE)

**Location:** `src/cube/domain/solver/common/big_cube/NxNEdges.py:680-746`

**Problem:** `_determine_ordered_color_for_required_color()` returns wrong orientation.

**Evidence from debug output:**
```
DEBUG: Working on edge FL ... color (ORANGE, WHITE)
```

This means solver wants ORANGE on face F and WHITE on other face. But L1 is WHITE face, so we should have `(WHITE, ORANGE)` not `(ORANGE, WHITE)`!

**Current logic:**
```python
def _determine_ordered_color_for_required_color(self, face, edge, required_color):
    # ... find other_color ...

    # Count orientations
    n_required_on_face = 0
    n_required_on_other = 0

    for i in range(edge.n_slices):
        _slice = edge.get_slice(i)
        ordered = self._get_slice_ordered_color(face, _slice)
        face_color, other_face_color = ordered

        if face_color == required_color:
            n_required_on_face += 1
        elif other_face_color == required_color:
            n_required_on_other += 1

    if n_required_on_face > 0:
        return (required_color, other_color)  # ✅ Correct
    else:
        return (other_color, required_color)  # ❌ Wrong!
```

**Hypothesis:** The counting logic is finding `n_required_on_face = 0`, causing it to return the wrong orientation `(other_color, required_color)`.

**Possible causes:**
1. The `face` parameter passed to `_determine_ordered_color_for_required_color()` is not the correct L1 face
2. The `_get_slice_ordered_color()` method is returning colors in wrong order
3. The edge slices are in an unexpected state after shadow cube operations

## Test Results

**Test:** `tests_wip/big_lbl/test_big_lbl_even.py::test_big_lbl_even_l1_only[seed_0-size_4]`

**Before fix f67798ad:** Test PASSED (false positive - wrong edges but check didn't detect)
**After fix f67798ad:** Test FAILS (correct - exposes the real bug)

## Call Stack

```
LayerByLayerNxNSolver._solve_layer1_edges()
  └─> NxNEdges.solve_face_edges(face_tracker, required_color=WHITE)
      └─> _do_edge(edge, required_color=WHITE)
          └─> _determine_ordered_color_for_required_color(face, edge, WHITE)
              └─> Returns (ORANGE, WHITE) instead of (WHITE, ORANGE) ❌
```

## Related Files

| File | Role | Status |
|------|------|--------|
| `src/cube/domain/model/Cube3x3Colors.py` | Shadow cube creation | ✅ Fixed orientation bug |
| `src/cube/domain/solver/common/big_cube/NxNEdges.py` | Edge solving | ❌ Active bug in orientation detection |
| `src/cube/domain/solver/common/big_cube/ShadowCubeHelper.py` | Shadow cube helper | Uses fixed method |
| `tests_wip/big_lbl/test_big_lbl_even.py` | Test cases | Now properly failing |

## Previous Fixes (This Session)

1. ✅ Shadow cube non-3x3 edge support (commit 03cad3d2)
2. ✅ NxNEdges respects required_color parameter (commit 2a3eac1f)
3. ✅ Fix orientation logic flip (commit 1d2ab968)
4. ✅ Fix edge detection to check all slices (commit f6c0922f, 732dfaa5)
5. ✅ Handle scrambled edges with multiple color-pairs (commit 0942dac0)
6. ✅ Fix L2 face mismatch (commit 70fa3b3b)
7. ✅ Fix shadow cube edge orientation (commit f67798ad)

## Next Steps

1. **Debug `_determine_ordered_color_for_required_color()`:**
   - Add debug logging to show `n_required_on_face` and `n_required_on_other` counts
   - Check what `face` parameter is being passed
   - Verify `_get_slice_ordered_color()` returns correct order

2. **Verify face parameter:**
   - Check if `face` in `_determine_ordered_color_for_required_color()` is actually the L1 WHITE face
   - Or if it's been rotated to a different position

3. **Add unit tests:**
   - Test `_determine_ordered_color_for_required_color()` in isolation
   - Test with known edge configurations

## Debug Commands

```bash
# Run L1-only test with full debug output
CUBE_DEBUG_ALL=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest \
  tests_wip/big_lbl/test_big_lbl_even.py::TestBigLBLEven::test_big_lbl_even_l1_only[seed_0-size_4] \
  -v -s -n 0

# Run full test (includes L2, L3)
CUBE_DEBUG_ALL=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest \
  tests_wip/big_lbl/test_big_lbl_even.py::TestBigLBLEven::test_big_lbl_even[seed_0-size_4] \
  -v -s -n 0
```

## Visual Verification

```bash
# Run GUI with scramble seed 0
python -m cube.main_pyglet
# In GUI: scramble seed 0, solve L1
# Expected: 2 WHITE edges, 2 wrong color edges on WHITE face
```

## Commits

- 03cad3d2 - Add shadow cube support for non-3x3 edges in even cubes
- 2a3eac1f - Fix NxNEdges to respect required color in solve_face_edges()
- 1d2ab968 - Fix orientation logic in _determine_ordered_color_for_required_color
- f6c0922f - Fix edge detection to check all slices, not just representative
- 732dfaa5 - Fix line 87 to also use _edge_contains_color for initial edge search
- 0942dac0 - Handle scrambled edges with multiple color-pairs across slices
- 70fa3b3b - Fix face mismatch in L2 edge solving
- f67798ad - Fix shadow cube edge orientation bug (exposed the real issue)
- 7955e90d - Add L1-only test for even cube debugging
