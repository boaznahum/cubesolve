# Tracker Indicators Feature (WIP)

**Status:** Work in Progress - Basic implementation complete, second scramble crash FIXED, shadow faces issue pending

## Overview

Small filled circle indicators that appear on center slices marked as tracker anchors (even cubes like 4x4, 6x6). The indicator shows the tracker's **assigned color** (not the current sticker color), helping visualize which center is the reference point for each face.

## Implementation

### Files Modified

1. **`_modern_gl_cell.py`**
   - Added constants:
     - `_TRACKER_INDICATOR_RADIUS_FACTOR = 0.25` (25% of cell size)
     - `_TRACKER_INDICATOR_HEIGHT = 0.10` (height offset)
     - `_TRACKER_INDICATOR_OUTLINE_WIDTH = 0.15` (black outline width)
     - `_TRACKER_INDICATOR_OUTLINE_COLOR = (0.0, 0.0, 0.0)` (black)
     - `_TRACKER_KEY_PREFIX = "_nxn_centers_track:"` (for parsing tracker keys)

   - Added `get_tracker_color() -> Color | None`:
     - Detects if cell is a tracked center by checking `c_attributes` for tracker keys
     - Parses the Color enum from the key suffix
     - Key format: `"_nxn_centers_track:Color.WHITE1"`

   - Added `generate_tracker_indicator_vertices(dest: list[float])`:
     - Generates a small filled circle with black outline
     - Uses tracker's assigned color directly (NOT complementary)
     - Reuses `_generate_3d_ring()` with `inner_radius=0` for filled circle

2. **`_modern_gl_board.py`**
   - Added calls to `cell.generate_tracker_indicator_vertices(marker_verts)` after marker generation
   - Both static and animated paths

### How It Works

1. When `FaceTracker.by_center_piece()` creates a tracker, it stores a key in `PartEdge.c_attributes`:
   ```python
   key = "_nxn_centers_track:" + str(_slice.color) + str(unique_id)
   edge.c_attributes[key] = True
   ```

2. During rendering, `get_tracker_color()` checks for these keys and parses the color

3. `generate_tracker_indicator_vertices()` creates a 3D cylinder (filled circle with black outline)

4. The indicator moves with the piece during rotation (stored in `c_attributes`)

5. Indicator is removed when tracker is cleaned up (`remove_face_track_slices()` deletes keys)

## Known Issues

### 1. Shadow Faces Don't Show Indicators

**Status:** Not investigated yet

Shadow faces (L, D, B rendered at offset positions) don't display tracker indicators. Main faces work correctly. The shadow faces use the same `_generate_face_verts()` function, so they should work. Need to investigate why they don't.

### 2. Second Scramble Causes Crash (FIXED)

**Status:** FIXED - Removed persistent tracker holder from solver

When running a second scramble after solving, the solver crashed with:
```
InternalSWError: Can't find face with pred <function FaceTracker.by_center_piece.<locals>._face_pred>
```

This was NOT caused by the indicator feature - it was a pre-existing bug in the tracker system.

**Root cause:** Solver held a persistent `_tracker_holder` that became stale after cube reset.

**Solution:** Removed the persistent tracker holder entirely. Now `status` and `_solve_impl`
each create a fresh `FacesTrackerHolder` using a context manager:
```python
with FacesTrackerHolder(self) as th:
    # use th for all operations
```

This design is safer - no stale references possible. We rely on the tracker majority
algorithm being deterministic (see issue #51 for potential concerns).

## TODO

- [x] Fix second scramble crash bug (blocking) - DONE: Fresh trackers per entry point
- [ ] Investigate shadow faces issue
- [ ] Move constants to ConfigProtocol for runtime configurability
- [ ] Add toggle to enable/disable tracker indicators
- [ ] Consider adding indicators for edge trackers too

## Testing

To test the feature:
1. Run GUI with 4x4 cube
2. Scramble once (key 0)
3. Start LBL-Direct solver
4. Look for small colored circles on center pieces (should have black outlines)

---

# Second Scramble Crash Bug

## Symptom

After scrambling and solving once, running a second scramble causes:
```
File ".../LayerByLayerNxNSolver.py", line 118, in status
    layer1_done = self._is_layer1_solved(th)
...
InternalSWError: Can't find face with pred <function FaceTracker.by_center_piece.<locals>._face_pred>
```

## Root Cause (Hypothesis)

1. First scramble + solve creates trackers with predicates that reference marked center slices
2. Second scramble resets cube and clears all `c_attributes` (including tracker marks)
3. Solver still holds reference to old `FacesTrackerHolder` with old trackers
4. When `status` property is accessed, it tries to use old trackers
5. Tracker predicates can't find their marked centers (keys were cleared)
6. `find_face()` fails because no face matches the predicate

## Call Stack

```
LayerByLayerNxNSolver.status
  -> _is_layer1_solved(th)
    -> _is_layer1_centers_solved(th)
      -> _get_layer1_tracker(th).face
        -> FaceTracker._tracker()  [the predicate]
          -> find_face(_face_pred)
            -> CRASH: predicate returns False for all faces
```

## Key Files

- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py`
- `src/cube/domain/solver/common/big_cube/_FaceTracker.py`
- `src/cube/domain/solver/common/big_cube/FacesTrackerHolder.py`

## Solution (IMPLEMENTED)

The fix was implemented in `LayerByLayerNxNSolver`:

1. Removed `_tracker_holder` field from `__slots__`
2. Removed `tracker_holder` property and `cleanup_trackers()` method
3. Wrapped `status` property with `with FacesTrackerHolder(self) as th:`
4. Wrapped `_solve_impl` method with `with FacesTrackerHolder(self) as th:`

Key insight: Solvers should NOT hold persistent tracker holders - they become stale on cube reset.
Instead, create fresh trackers at each entry point (`status`, `_solve_impl`) using context managers.

**Design decision:** We rely on the tracker majority algorithm being deterministic.
If issue #51 (tracker majority bug) is real, fresh trackers might give inconsistent
face→color assignments across calls.

**Files Modified:**
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py`
- `tests/solvers/test_lbl_big_cube_solver.py`
- `tests/solvers/test_tracker_majority_bug.py`
