# Even Cube L1→L2 Tracker Mapping Divergence

## Date: 2026-02-10 | Status: RESOLVED (detection + restart)

---

## 1. The Problem

On even cubes, `FacesTrackerHolder` determines face→color mapping via majority
voting + BOY constraint at creation time. When L1 solving completes and L2
starts, the original tracker's mapping may **diverge** from what a fresh
tracker would compute, causing L2 to see incorrect face colors.

Observed: seed 124826159, size 4 cube:
```
Original tracker after L1: F:BLUE, R:ORANGE, B:GREEN, L:RED
Fresh tracker after L1:    F:ORANGE, R:GREEN, B:RED, L:BLUE
```
Both agree on WHITE/YELLOW faces. Side face colors differ — a different
(but valid) BOY arrangement.

---

## 2. Root Cause: NOT Mark Displacement

### What Does NOT Cause the Divergence

**NxNEdges' slice rotations** — paired (E → rf → E'), centers always restored:
```python
# NxNEdges._fix_all_slices_on_edge:
self.op.play(slice_alg)       # E[i]
self.op.play(self.rf)          # face turns
self.op.play(slice_alg.prime)  # E'[i] — cancels out ✓
```

**NxNCenters' commutators** — all wrapped in `preserve_physical_faces()`:
```python
# NxNCenters._block_commutator:
with tracker_holder.preserve_physical_faces():
    self._execute_commutator(...)  # marks restored after each commutator ✓
```

**Shadow cube / DualOperator** — only uses outer face turns (F, R, U...), these
don't move center slices between faces.

### What DOES Cause It

**NxNCenters changes the center piece distribution** — that's its job!

Empirical trace (seed 124826159, PYTHONHASHSEED=0):
```
AFTER SCRAMBLE:
  Original: {F:BLUE, B:GREEN, L:ORANGE, R:RED, D:WHITE, U:YELLOW}
  Fresh:    {F:BLUE, B:GREEN, L:ORANGE, R:RED, D:WHITE, U:YELLOW}
  Match: YES ✓

AFTER L1 CENTERS:     ← divergence starts here!
  Original: {L:BLUE, R:GREEN, D:ORANGE, U:RED, F:WHITE, B:YELLOW}
  Fresh:    {F:WHITE, B:YELLOW, R:RED, L:ORANGE, D:GREEN, U:BLUE}
  Match: NO ✗
```

The original tracker's marks are NOT displaced — they correctly followed the
cube rotation (NxNCenters moved L1 face from D to F). But the **side face
center distribution changed** as NxNCenters moved white centers to L1 and
deposited non-white centers on side faces.

A fresh tracker does new majority voting on the changed distribution and may
pick a **different valid BOY arrangement** for the side faces.

### Why Side Face Assignments Diverge

On a 4x4, each side face has 4 center pieces (2×2). After L1 centers are
solved, the white centers moved to L1, and non-white centers were redistributed.

Example:
```
Before L1: Face F has [orange, orange, white, green] → majority: orange
After L1:  Face F has [orange, orange, blue, green]  → majority: orange (ok)

Before L1: Face R has [red, green, blue, red]        → no clear majority
After L1:  Face R has [red, green, green, red]       → tie: red or green
```

When majority is tied or near-tied, the tracker factory's BOY-constraint
resolution picks differently based on the specific piece positions.
Different PYTHONHASHSEED values can also cause different tiebreaking
(via `set.pop()` ordering in the factory).

---

## 3. The Solution: Detection + Restart

### Why This Is Correct

Since the divergence comes from the cube state changing (NxNCenters doing its
job), we can't prevent it. We **detect** it at the L1→L2 boundary and restart
with a fresh tracker that reflects the post-L1 reality.

```python
# LayerByLayerNxNSolver._solve_l2_slices():
if face_trackers.is_even_cube:
    with FacesTrackerHolder(self) as fresh_th:
        if face_trackers.face_colors != fresh_th.face_colors:
            raise SolverFaceColorsChangedNeedRestartException()
```

### How It Works

1. **First iteration:** L1 solves with original tracker. Center distribution
   changes. Tracker mapping becomes stale.
2. **Detection:** At L2 entry, compare original vs fresh tracker. If different →
   raise exception.
3. **Second iteration:** `_solve_impl` catches exception, retries. L1 already
   solved (no-op). Fresh tracker reflects post-L1 state. L2 proceeds correctly.

### Why Fresh Tracker Is Correct After L1

After L1:
- L1 face has all white centers → clear majority → unambiguous
- L1 corners are placed → corner stickers indicate correct side face colors
- Fresh tracker's majority voting picks up these signals

---

## 4. L2 Commutator Protection (Separate Concern)

L2 slice solving has its OWN center-displacement issue (E2E commutators in edge
solver, pre-alignment rotations). These are handled by individual wrapping:

| Operation | Protection | Mechanism |
|-----------|-----------|-----------|
| Center block commutators | `_preserve_trackers()` | `th.preserve_physical_faces()` |
| E2E commutators | `outer_th.preserve_physical_faces()` | Passed via `outer_th` param |
| Pre-alignment rotations | `th.preserve_physical_faces()` | In `_solve_slice_row` |
| Query-mode rotations | `th.frozen_face_colors()` | Snapshot in `_find_best_pre_alignment` |

These are cage-preserving operations (no cube rotations), so
`preserve_physical_faces()` works correctly for them.

---

## 5. Rejected Approaches and Why

| Approach | Why It Fails |
|----------|-------------|
| Wrap L1 in `preserve_physical_faces()` | L1 rotates cube → face names change meaning after rotation |
| Wrap NxNEdges' slice ops | Slice rotations cancel out (E then E') — not the cause |
| Pass outer_th to NxNEdges | Not needed — slices cancel, no drift from NxNEdges |
| Prevent NxNCenters from changing distribution | Impossible — that's its job |

---

## 6. Remaining Issues

### L3 Edge Solver (Unprotected E2E Commutators)

`_LBLL3Edges` has 4 E2E commutator calls not wrapped in `preserve_physical_faces()`.
These are cage-preserving and DO displace centers. May need wrapping if L3 cross
solving fails on even cubes.

### Edge Solver Index Mismatch (Pre-existing)

E2E commutator can only swap wings at matching slice indices. Multi-pass retry
loop in `_solve_row_core` mitigates this (up to 4 passes), but edge cases remain.

### Non-Deterministic Tracker Factory

`set.pop()` in tracker factory causes different (but valid) face-color assignments
per PYTHONHASHSEED. The detection + restart approach handles all seeds correctly.
