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

### 3. NEW DISCOVERY: Edge Orientation Bug (2026-02-09 - ACTIVE)

**Status:** Root cause identified

**Findings from debug output (seed_0-size_4):**

After L1 edge solving completes:
- L1 color: WHITE
- L1 face: L (left face)
- 4 edges contain WHITE: FL, LU, RD, BL
- **Only 3 edges on L1 face**: FL, LU, BL (RD is at wrong position!)
- **Only 1 edge has correct orientation**: LU

**Edge details:**
```
FL: e1=(WHITE@F), e2=(RED@L)     - WHITE on F side, not L ❌
LU: e1=(GREEN@U), e2=(WHITE@L)   - WHITE on L side ✓
RD: e1=(BLUE@D), e2=(WHITE@R)    - Not even on L1 face!
BL: e1=(ORANGE@L), e2=(WHITE@B)  - ORANGE on L, WHITE on B ❌
```

**Analysis:**
1. **Wrong positions**: Edge RD should be at DL, but it's at RD
2. **Wrong orientations**: FL and BL have WHITE on the WRONG side of the edge
3. Shadow cube correctly reflects this broken state - it's not a shadow bug!

**Root cause:** `NxNEdges.solve_face_edges()` pairs edges correctly (all slices have same colors) but:
1. Places edges at WRONG positions (RD instead of DL)
2. Places edges with WRONG orientation (WHITE on opposite side)

**The fix for shadow cube remapping was WRONG** - we don't need remapping at all! The shadow cube correctly reflects the big cube state. The bug is in edge solving, not shadow creation.

## Next Steps

1. **Fix edge placement in `NxNEdges.solve_face_edges()`:**
   - Ensure all 4 edges with L1 color are placed on the L1 face
   - Currently only 3 edges on L1 face, one is at wrong position

2. **Fix edge orientation in `NxNEdges._do_edge()`:**
   - Ensure L1 color is on the L1 FACE SIDE of the edge
   - Currently FL and BL have L1 color on opposite side

3. **Remove remapping code:**
   - Revert `with_remapped_edges_by_sticker_colors()` - not needed!
   - Keep `with_fixed_non_3x3_edges()` - this is correct

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
