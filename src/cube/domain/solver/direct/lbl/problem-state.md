# Even Cube Big LBL Solver - Problem State

## Context

Branch: `big-lbl-even-opus-broken`
Commit that introduced the changes: `d0b3469 Even cube support: FacesColorsProvider + fix _create_f5_pred`

The commit attempted to add even cube (4x4, 6x6, etc.) support to the Big LBL solver.
It broke ALL solvers (not just LBL). We bisected by reverting/disabling individual changes
to isolate what caused regressions in other solvers.

## What Was Reverted / Disabled

### 1. `_track_two_last` in `_factory.py` - REVERTED to original

**What the commit did:** Replaced the dynamic `_create_f5_pred` predicate approach
with a static `_create_tracker_on_face` method. Face 5 was tracked using a
`MarkedFaceTracker` (marking any center slice on the face) instead of a
`SimpleFaceTracker` with a BOY-checking predicate.

**Key differences:**
- Old: `left_two_faces.pop()` (removes from list) + `_create_f5_pred` predicate + `SimpleFaceTracker`
- New: `left_two_faces[0]` / `left_two_faces[1]` (index access) + `_create_tracker_on_face` + `MarkedFaceTracker`

**What was reverted:**
- Restored `_track_two_last` to use `left_two_faces.pop()` and predicate-based `SimpleFaceTracker`
- Restored `_create_f5_pred` method (was deleted in the commit)
- Removed `_create_tracker_on_face` method (new, didn't exist before)
- Removed `FaceName` import (added only for the new code)

**Why it broke things:** The change to face 5/6 tracking affected ALL even cube solvers
(not just LBL), since `_factory.py` is shared tracker infrastructure used by all solvers.

### 2. `Face.set_color_provider` in `Face.py` - Made NO-OP

**What the commit did:** Added `_color_provider` field to `Face` and modified
`Face.color` property to check `_color_provider` first. When set via
`Cube.with_faces_color_provider(th)`, all `face.color` calls would return
tracker-assigned colors instead of reading from the center piece.

**What was disabled:**
- `set_color_provider` body changed to `pass` (no-op)
- The `_color_provider` is never set, so `Face.color` always falls through to `self.center.color`
- All infrastructure remains in place: the protocol `FacesColorsProvider`, the context manager
  `Cube.with_faces_color_provider()`, the `FacesTrackerHolder(FacesColorsProvider)` inheritance

**Why it broke things:** `Face.color` is read by EVERY solver. Overriding it globally
affected all solvers, not just the LBL even solver. The provider mechanism needs to be
scoped more carefully or the trackers need to provide correct colors for ALL solver contexts.

## What Was NOT Reverted (Still Active from the Commit)

These changes remain and did NOT cause regressions in other solvers:

1. **`NxNCenters.py`** - `tracker_holder` param (default `None`) + `_preserve_trackers()` wrapping.
   When `tracker_holder=None` (all non-LBL callers), uses `nullcontext()` - no behavior change.

2. **`_LBLNxNCenters.py`** - `tracker_holder` param + `_preserve_trackers()` wrapping commutators.

3. **`_LBLSlices.py`** - Changed from eager `_centers` to lazy `_last_centers` creation via
   `_create_centers(th)`. Added `get_statistics()` method to handle `None` case.

4. **`LayerByLayerNxNSolver.py`** - `with_faces_color_provider(th)` wrapping (now no-op).
   Passes `tracker_holder=th` to `NxNCenters`. Added `get_statistics()` method.

5. **`FacesTrackerHolder.py`** - Inherits from `FacesColorsProvider` (harmless, adds interface).

6. **`FacesColorsProvider.py`** - New protocol file (unused since provider is no-op).

7. **`Cube.py`** - `with_faces_color_provider()` context manager (calls no-op `set_color_provider`).

## Test Changes

- Removed size 8 from `CUBE_SIZES_ALL` in `conftest.py` (even cubes not ready)
- Fixed `_centers` -> `_last_centers` rename in tests, then moved to `solver.get_statistics()`
- Added `Solver.get_statistics()` base method returning `{}` (default no-op)

## Next Steps for Even Cube Support

To re-enable even cube support, investigate:

1. **Face color provider scoping:** The `FacesColorsProvider` mechanism overrides `Face.color`
   globally. This breaks solvers that rely on the physical center piece color. Consider:
   - Only using provider within LBL solver scope (not globally on Face)
   - Or ensuring provider returns correct colors for all solver contexts

2. **Face 5/6 tracking:** The `_create_tracker_on_face` approach (marking any slice, not
   necessarily matching color) may be needed for even cubes where the target color isn't
   on the face yet. But it changes tracker behavior for ALL solvers. Consider:
   - Making this LBL-specific rather than changing shared `_factory.py`
   - Or ensuring `_create_f5_pred` works correctly for even cubes too
