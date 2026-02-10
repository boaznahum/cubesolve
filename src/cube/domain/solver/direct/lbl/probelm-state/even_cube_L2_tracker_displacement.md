# Even Cube L2 Slices: Tracker Displacement Bug

## Date: 2026-02-10 | Status: FIXED

---

## 1. Background: Why Even Cubes Need Trackers

On odd cubes (3x3, 5x5, 7x7), each face has a physically fixed center piece.
The face's color is simply the color of that center piece. No tracking needed.

On even cubes (4x4, 6x6, 8x8), there is **no fixed center piece**. The face's
"color" must be determined by some other mechanism. The solver uses
`FacesTrackerHolder`, which:

1. Uses majority voting + BOY constraint to determine which color belongs to
   which face
2. **Marks** one specific center slice per face with a unique key in
   `moveable_attributes`
3. Provides `get_face_color(face_name)` that searches all faces for the marked
   slice to determine which face "owns" that color

```
Odd cube (5x5):                    Even cube (4x4):
┌───────────────┐                  ┌────────────┐
│  . . . . .    │                  │  . . . .   │
│  . . . . .    │                  │  . [M] .   │  ← M = marked center slice
│  . . X . .    │ ← X = fixed     │  . . . .   │    (tracking key in attrs)
│  . . . . .    │    center        │  . . . .   │
│  . . . . .    │                  │            │
└───────────────┘                  └────────────┘
face.color = X.color               face.color = tracker finds M → returns color
```

The `Cube.with_faces_color_provider(th)` context manager overrides
`face.color` for ALL faces to use the tracker's `get_face_color()` instead of
the default center-piece lookup. This makes `edge.match_faces` (which checks
`edge.color == edge.face.color`) work correctly with tracker-defined colors.

### Tracker Types

```
FaceTracker (abstract)
    │
    ├── SimpleFaceTracker    # Predicate-based: "find face opposite to X"
    │                        # Used for: odd cubes, opposite faces, f5
    │                        # face property: evaluates predicate against all faces
    │                        # No center slice marked → no displacement possible
    │
    └── MarkedFaceTracker    # Key-based: marks a specific center slice
                             # Used for: even cube primary trackers
                             # face property: searches ALL faces for the marked slice
                             # Displacement: mark follows the physical piece when moved
```

---

## 2. The Problem: Tracker Marks Follow Physical Pieces

When a slice rotation occurs, center pieces move from one face to another.
If a **marked** center slice is in the rotated slice, the mark moves with it.

```
Before E-slice rotation:              After E-slice rotation:

  ┌───┐                                 ┌───┐
  │ U │                                 │ U │
  ├───┼───┬───┬───┐                     ├───┼───┬───┬───┐
  │ L │[F]│ R │ B │  ← [F] has mark    │ L │ F │[R]│ B │  ← mark moved to R!
  ├───┼───┴───┴───┘                     ├───┼───┴───┴───┘
  │ D │                                 │ D │
  └───┘                                 └───┘

  get_face_color(F) → WHITE ✓          get_face_color(F) → KeyError! ✗
  get_face_color(R) → RED ✓            get_face_color(R) → could be WHITE or RED
                                         (two marks on same face!)
```

This displacement happens in TWO places during L2 slice solving:

### 2a. Query-Mode Displacement (in `_find_best_pre_alignment`)

```python
def _find_best_pre_alignment(self, face_row, l1_white_tracker, th):
    # Try rotations 1, 2, 3 to find best pre-alignment
    with self.op.with_query_restore_state():     # ← temporary rotations
        for n_rotations in range(1, 4):
            self.play(slice_alg)                  # ← moves tracker marks!
            count = sum(... if e.match_faces ...) # ← match_faces calls face.color
                                                  #    → get_face_color() → KeyError!
```

The query rotations are temporary (undone on context exit), but during the
query, `match_faces` does a live tracker lookup that fails.

### 2b. Real Pre-Alignment Displacement (in `_solve_slice_row`)

```python
def _solve_slice_row(self, face_row, th, l1_white_tracker):
    best_rotations = self._find_best_pre_alignment(...)

    if best_rotations > 0:
        self.play(slice_alg * best_rotations)   # ← REAL rotation, permanent!
                                                 #    tracker marks displaced!

    self._solve_row_core(face_row, th, ...)     # ← uses displaced trackers!
        # → mark_slices_and_v_mark_if_solved()  #    calls match_faces → KeyError!
        # → preserve_physical_faces()           #    sanity check → BOY assertion!
```

After the real pre-alignment rotation, all subsequent operations use the
displaced tracker mapping, causing cascading failures.

---

## 3. Why This Bug Was Non-Deterministic

The tracker factory (`_factory.py`) uses `set.pop()` and `set` iteration to
determine face-color assignments:

```python
def _track_two_last_simple(self, ...):
    remaining_colors = {c for c in all_colors if c not in assigned}
    remaining_faces = {f for f in all_faces if f not in assigned}
    color = remaining_colors.pop()    # ← ORDER DEPENDS ON HASH SEED!
    face = remaining_faces.pop()      # ← ORDER DEPENDS ON HASH SEED!
```

Python randomizes hash seeds by default (`PYTHONHASHSEED`). Different seeds
produce different (but valid BOY) face-color assignments. Some assignments
place the tracker mark on a center slice that happens to be in the rotated
E-slice; others don't.

```
PYTHONHASHSEED=0:  Tracker mark at position (0,0) → NOT in E[1] slice → PASS
PYTHONHASHSEED=1:  Tracker mark at position (1,0) → IN E[1] slice    → FAIL
PYTHONHASHSEED=42: Tracker mark at position (0,1) → IN E[1] slice    → FAIL
```

This also explains why test ordering appeared to matter: running other tests
changed memory allocation patterns, which changed object addresses, which
changed hash values, which changed set iteration order.

---

## 4. The Fix

Two complementary mechanisms, each addressing one displacement scenario:

### 4a. Frozen Face Colors (for query-mode displacement)

**File:** `FacesTrackerHolder.py`

Added `frozen_face_colors()` context manager that snapshots the face-color
mapping. When frozen, `get_face_color()` and `get_face_colors()` return the
snapshot instead of doing live tracker searches.

```python
@contextmanager
def frozen_face_colors(self):
    frozen = self.get_face_colors().copy()   # snapshot current mapping
    self._frozen_colors = frozen
    try:
        yield frozen
    finally:
        self._frozen_colors = None

def get_face_color(self, face_name):
    if self._frozen_colors is not None:       # frozen? use snapshot
        return self._frozen_colors[face_name]
    # ... normal live tracker search ...
```

**Used in** `_find_best_pre_alignment`:
```python
with th.frozen_face_colors():                 # snapshot before query
    with self.op.with_query_restore_state():
        for n_rotations in range(1, 4):
            self.play(slice_alg)              # marks displaced, but...
            count = sum(... if e.match_faces) # match_faces uses frozen colors ✓
```

### 4b. Preserve Physical Faces (for real pre-alignment displacement)

**File:** `_LBLSlices.py`

Wrapped the real pre-alignment rotation in `th.preserve_physical_faces()`.
This context manager (already existed for commutator operations):

1. **Saves** each tracker's current face name
2. Allows the rotation to happen (pieces move permanently)
3. **Restores** each tracker mark to its original face

```python
if best_rotations > 0:
    with th.preserve_physical_faces():        # save tracker positions
        self.play(slice_alg * best_rotations) # pieces move, marks displaced
    # marks restored to original faces ✓

    self._solve_row_core(...)                 # trackers now correct ✓
```

The key insight: the pre-alignment rotation moves **pieces** to better
positions (intended), but the face-color **mapping** should not change.
Face F is still orange, face R is still red, etc. Only the pieces within
those faces moved.

`restore_to_physical_face()` for `MarkedFaceTracker`:
1. Removes the mark from wherever it ended up (wrong face)
2. Finds a center slice on the original face
3. Places a new mark on it

```
Before rotation:     After rotation:      After restore:
F has mark ✓         R has mark ✗         F has mark ✓  (new piece, same face)
                     F has no mark ✗
```

---

## 5. Call Flow Diagram (After Fix)

```
_solve_l2_slices(th)
  └── solve_all_faces_all_rows(th, l1_tracker)
        └── for each row_index:
              └── _solve_slice_row(row_index, th, l1_tracker)
                    │
                    ├── _find_best_pre_alignment(row, l1, th)
                    │     └── with th.frozen_face_colors():        ← FIX 4a
                    │           └── with op.with_query_restore_state():
                    │                 └── play(slice_alg) × 3      (temp, marks displaced)
                    │                     match_faces uses frozen   (safe ✓)
                    │
                    ├── if best_rotations > 0:
                    │     └── with th.preserve_physical_faces():   ← FIX 4b
                    │           └── play(slice_alg × N)            (real, marks displaced)
                    │         marks restored to original faces     (safe ✓)
                    │
                    └── _solve_row_core(row, th, l1)
                          ├── mark_slices_and_v_mark_if_solved()   (trackers correct ✓)
                          └── for each side_face:
                                └── _solve_face_row(l1, face, row, th)
                                      └── centers.solve_single_center_face_row()
                                            └── with th.preserve_physical_faces():
                                                  └── commutator    (existing, already safe)
```

---

## 6. Files Modified

| File | Change |
|------|--------|
| `tracker/FacesTrackerHolder.py` | Added `_frozen_colors` field, `frozen_face_colors()` context manager, frozen checks in `get_face_color()` and `get_face_colors()` |
| `solver/direct/lbl/_LBLSlices.py` | `_find_best_pre_alignment`: added `th` param + `frozen_face_colors()` wrapper. `_solve_slice_row`: wrapped pre-alignment in `preserve_physical_faces()` |

---

## 7. Test Results

```
test_lbl_l2_slices (even cubes 4/6/8, 14 seeds):  14/14 PASS
All L2 solver tests (358 tests):                   358/358 PASS
Verified across PYTHONHASHSEED = 0,1,2,42,100,456,789,999: ALL PASS
```

---

## 8. Related Issues

- **`with_faces_color_provider` stack safety** (fixed in prior session):
  Nested `with_faces_color_provider()` calls didn't save/restore the previous
  provider. Fixed by making `Cube.with_faces_color_provider()` stack-safe.

- **Tracker factory non-determinism** (not fixed, mitigated):
  `set.pop()` in `_track_two_last_simple` and set iteration in
  `_find_face_with_max_colors` produce different face-color assignments
  depending on `PYTHONHASHSEED`. All assignments are valid BOY layouts,
  but some are more "fragile" to slice rotations. The freeze/preserve fix
  handles ALL assignments correctly regardless of hash seed.

- **L3 cross parity** (separate issue, not related):
  `test_big_lbl_even.py` has pre-existing failures at the L3 cross stage
  (`EvenCubeEdgeParityException`). These are unrelated to tracker displacement.
