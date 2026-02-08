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

**Why it broke things — Root Cause Analysis:**

The fundamental problem is the difference between how `SimpleFaceTracker` and
`MarkedFaceTracker` find their face:

**SimpleFaceTracker (original, face 5):**
- `face` property calls `cube.cqr.find_face(self._pred)` every time
- The predicate re-evaluates: "which of the remaining 2 faces, when assigned
  this color, creates a valid BOY layout?"
- It reads the CURRENT positions of faces 1-4 trackers dynamically
- Cube rotations, commutators, any operation — the predicate adapts because
  it recalculates from scratch each time
- **Self-healing:** Even if the cube state changes dramatically, the predicate
  always finds the correct face by checking the BOY constraint

**MarkedFaceTracker (attempted, face 5):**
- `face` property searches ALL faces for the slice containing `self._key`
  in `moveable_attributes`
- It follows a PHYSICAL center slice piece
- When commutators move center pieces between faces, the marked slice moves
  with the piece — potentially to the WRONG face
- **Fragile for face 5:** Unlike faces 1-4 where we mark a slice of the
  CORRECT majority color (likely to be placed back on its face during solving),
  face 5's color is assigned by BOY constraint, not majority. The marked
  slice might be of a completely different color and move unpredictably.

**Why faces 1-4 work with MarkedFaceTracker but face 5 doesn't:**
- Faces 1-4: Selected by MAJORITY color — the marked slice's color matches
  the face's target color. During solving, that slice is actively being
  collected TO this face, so the marker stays stable.
- Face 5: Selected by BOY CONSTRAINT — the target color may be a MINORITY
  on the face. `_create_tracker_on_face` falls back to marking ANY available
  slice. This arbitrary slice has no affinity to the face and drifts away
  during commutators.

**The deeper issue:** `_factory.py` is shared infrastructure used by ALL solvers
(Cage, Beginner, LBL). Changing face 5 tracking from a self-healing predicate
to a fragile physical marker broke every even-cube solver, not just LBL.

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

2. **Face 5/6 tracking — keep predicate approach:** The `SimpleFaceTracker` with
   `_create_f5_pred` is the correct design for face 5 because:
   - The BOY predicate is self-healing (re-evaluates from current state)
   - It doesn't depend on any physical piece staying in place
   - It works for ALL solvers, not just LBL

   If `_create_f5_pred` has bugs for even cubes, fix the predicate logic itself
   rather than switching to `MarkedFaceTracker`. The predicate approach is
   architecturally sound — `MarkedFaceTracker` is fundamentally wrong for face 5
   because BOY-assigned colors have no majority affinity to their face.
