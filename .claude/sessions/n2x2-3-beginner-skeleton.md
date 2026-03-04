# Session: n2x2-3 — 2x2 Beginner Solver Skeleton + Model De-cheating

Branch: `claude/implement-2x2-cube-mi7lb`
Date: 2026-03-04
Parent session: `n2x2-1` (initial 2x2 support), `n2x2-2` (IDA* solver)

---

## Overview

This session had two main thrusts:

1. **Remove "cheating" from the 2x2 domain model** — replace silent fallbacks
   (that pretend empty parts are fine) with hard assertions that explode if
   anyone tries to use 2x2 parts as if they were 3x3 parts.
2. **Create the 2x2 beginner solver skeleton** — separate the IDA* solver
   (renamed `_2x2_ida_optimal`) from a new `_2x2_beginner` solver package
   with stub implementations of L1, L3Orient, and L3Permute.

---

## What We Did — Commit by Commit

### Commit 1: `d70a19b` — Remove virtual center colors from 2x2

**Problem:** The 2x2 model had a `_virtual_color` system on `Center` objects.
When the cube was rotated (whole-cube M/E/S moves), `Slice._rotate_virtual_center_colors()`
would cycle these virtual colors so `face.color` would track correctly. This was
a complex, fragile mechanism maintaining mutable state on objects that don't
physically exist on a 2x2 cube.

**What changed:**
- **`Center.py`**: Removed `_virtual_color` field entirely. `center.color` now
  returns `Color.UNCOLORED` for 2x2 (a new sentinel value).
- **`Color.py`**: Added `Color.UNCOLORED = "N/A"` sentinel with gray RGB fallback.
- **`Slice.py`**: Deleted the entire `_rotate_virtual_center_colors()` method
  (~30 lines) and its `_VIRTUAL_COLOR_CYCLES` dict. The `rotate()` method now
  simply returns early for 2x2 (`n_slices == 0`) with no side effects.
- **`Face.py`**: `create_part()` uses `self._original_color` instead of
  `self.color` (which would be `UNCOLORED` on 2x2). `Face.solved` now checks
  corners-only for 2x2 **first** (before the `is3x3` gate), comparing corner
  sticker colors against each other rather than against `face.color`.
- **`Center.clone()`**: No longer copies `_virtual_color`.

**Design decision:** A 2x2 has no physical centers. Instead of faking them with
mutable virtual state, `face.color` for 2x2 now uses `face.original_color`
(the fixed manufacturing color). The solver and `Face.solved` use corner
stickers directly.

### Commit 2: `90feb5c` — Add Color.UNCOLORED, fix Face.solved

Small follow-up ensuring `Face.solved` doesn't depend on `face.color` for 2x2.
The 2x2 solved check compares all 4 corner stickers on a face to each other:
```python
c = self._corners[0].f_color(self)
return all(corner.f_color(self) == c for corner in self._corners[1:])
```

### Commit 3: `4187ad8` — Face.solved: check corners first, skip is3x3 gate

Moved the 2x2 check **above** the `is3x3` gate in `Face.solved`. Previously
the 2x2 path was below `if not self.is3x3: return False`, but `is3x3` is
meaningless for 2x2 faces. Now the order is:
1. If 2x2 (`n_slices == 0`): check corners only
2. If not reduced (`not is3x3`): return False
3. Normal 3x3+ check with edges and centers

### Commit 4: `6849833` — Replace silent 2x2 cheats with assertions

**This is the big "anti-cheating" commit.** The problem: the n2x2-1 session
added `if not self._slices: return True/frozenset()/()` guards throughout
`Part.py`, `Center.py`, etc. These silently pretended empty parts were fine,
which meant bugs could hide — code calling `position_id` on an empty Edge
would get `frozenset()` instead of crashing, masking the real problem.

**What changed — assertions replacing silent fallbacks:**

| File | Method | Before (cheat) | After (assertion) |
|------|--------|-----------------|-------------------|
| `Part.py` | `match_faces()` | `return True` for empty parts | `assert rep_edges` — crash if called on 2x2 empty part |
| `Part.py` | `position_id` | `return frozenset()` for empty parts | `assert rep_edges` — crash if called |
| `Part.py` | `colors_id` | `return frozenset()` for empty parts | `assert rep_edges` — crash if called |
| `Center.py` | `is3x3` | `return True` for no slices | `assert self._slices` — crash if called |

**Philosophy:** If code calls `position_id` on a 2x2 Edge (which has no slices),
that's a **bug in the caller**, not something to silently handle. The assertion
makes the bug visible immediately.

**What's still "soft" (not converted to assertions):**
- `Part.__init__` — still handles empty slices gracefully (sets `_cube` from pre-assigned field)
- `Part.finish_init()` — still sets `_fixed_id = frozenset()` for empty parts
- `Part.has_slices` — still exists as a query property
- `Edge.__init__` — still sets up references for empty edges
- `Center.color` — returns `Color.UNCOLORED` (not an assertion, since GUI may query it)
- `Center.face` — returns `_face_ref` for empty centers (valid usage)

### Commit 5: `c06dff1` — Rename _2x2 → _2x2_ida_optimal, add _2x2_beginner skeleton

**Reorganization:**
- Renamed `src/cube/domain/solver/_2x2/` → `src/cube/domain/solver/_2x2_ida_optimal/`
- All internal imports updated (`_precomputed`, `cube_to_coordinates`, etc.)
- `Solver2x2` stays in `_2x2_ida_optimal/Solver2x2.py`

**New package:** `src/cube/domain/solver/_2x2_beginner/`
- `Solver2x2Beginner.py` — Main solver class, extends `BaseSolver`
  - 3 phases: `_l1` (L1), `_l3_orient` (L3Orient), `_l3_permute` (L3Permute)
  - Supports `SolveStep.L1` and `SolveStep.L3` (= L1 + L3Orient + L3Permute)
  - Has `status` property showing current progress
- `_L1.py` — First layer solver (stub: `raise NotImplementedError`)
- `_L3Orient.py` — Last layer orient (stub: `raise NotImplementedError`)
- `_L3Permute.py` — Last layer permute (stub: `raise NotImplementedError`)
- `STEPS.md` — Detailed algorithm documentation for all 3 phases

**SolverName changes:**
- Added `TWO_BY_TWO_BEGINNER` with `implemented=False` (skeleton only)
- Added `TWO_BY_TWO_IDA` with `user_visible=False` (internal, used for delegation)
- All 3x3+ solvers no longer have `skip_2x2` — instead `Solvers.by_name()`
  handles size routing centrally

**Solvers.py routing:**
```python
if op.cube.size == 2:
    if solver_id is SolverName.TWO_BY_TWO_BEGINNER:
        return cls.two_by_two_beginner(op)
    return cls.two_by_two_ida(op, display_as=solver_id)
```

---

## Investigation: Is Solver Recreation After Resize "Cheating"?

**Concern raised:** If the cube is resized from 3x3 to 2x2, does the solver
become stale? The `size == 2` check in `Solvers.by_name()` runs at construction
time — what if someone resizes the cube after the solver exists?

**Finding: NOT cheating.** The resize flow is:

1. Resize command (`SizeInc`/`SizeDec`/`SetSize`) calls `ctx.app.reset(new_size)`
2. `app.reset()` does:
   ```python
   self.cube.reset(cube_size)          # recreate cube with new size
   self.op.reset()                     # reset operator
   self._slv = Solvers.default(self.op) # NEW solver for new cube
   ```
3. The old solver is discarded. The new solver sees the current cube size.

**However**, `AbstractSolver.__init__` captures `self._cube = op.cube` at
construction time. If someone held a reference to the old solver object and
called `.solve()` after a resize, it would operate on the old cube. But since
`app.reset()` replaces `self._slv` entirely, no stale references exist in the
normal code path.

**Potential test to verify:** Create solver → resize cube → call old solver.
This would fail because the old solver's `self._cube` still points to the
pre-resize cube (which has been `.reset()` to the new size). The solver's
internal state would be inconsistent.

---

## Current State of the Codebase

### What Works
- **IDA* 2x2 solver** (`_2x2_ida_optimal`): Fully functional, optimal solutions
  in ≤11 moves, 1000/1000 random seeds pass
- **2x2 domain model**: Corners work correctly, `Face.solved` checks corners
  only, virtual center colors removed
- **Solver routing**: `Solvers.by_name()` correctly delegates all 2x2 requests
  to either IDA* or beginner solver
- **Resize safety**: `app.reset()` recreates solver on every resize
- **Assertions**: Empty parts crash loudly if used incorrectly

### What's Incomplete
- **2x2 beginner solver**: All 3 phases (`_L1.py`, `_L3Orient.py`,
  `_L3Permute.py`) are stubs with `raise NotImplementedError`
- `SolverName.TWO_BY_TWO_BEGINNER` has `implemented=False` — cannot be
  selected in the GUI or tests
- Algorithm documentation exists in `STEPS.md` but no code implements it yet

### Known Problems / Design Debt

1. **Scattered `if not self._slices` guards remain** — While the worst "cheats"
   (returning `True`/`frozenset()`) are now assertions, there are still ~10
   places with `if not slices` soft handling in `Part.py`, `Edge.py`, `Center.py`.
   These are necessary for construction but blur the boundary between "valid
   empty part usage" and "bug".

2. **`frozenset()` as `fixed_id`** for empty parts — Multiple empty parts
   (edges, centers) share the same `frozenset()` identity. This is technically
   a hash collision. It works because no solver code should ever look up empty
   parts, but it's fragile.

3. **RuntimeError landmines** — Methods like `Edge.get_other_face_edge()`,
   `Part.get_face_edge()`, `Part.find_face_by_color()` raise `ValueError` for
   2x2. If any future code path calls these on a 2x2 part, it's a runtime crash.

4. **No null object pattern** — The ideal fix would be `EmptyEdge`/`EmptyCenter`
   subclasses that are explicitly no-ops, rather than guards scattered in base
   classes. This was identified in n2x2-1 but not yet implemented.

5. **`face.color` returns `original_color` for 2x2** — This is correct behavior
   (a 2x2 has no reference frame shift) but it's implicit. The `color` property
   on `Face` calls `self._center.color`, which returns `UNCOLORED` for 2x2,
   then... actually `face.color` falls through to `self._center.edg().color`.
   Wait — for 2x2, `Center.color` returns `Color.UNCOLORED`. So `face.color`
   returns `UNCOLORED`. Code that needs the face color must use
   `face.original_color`. This is a trap for future developers.

---

## Files Modified (Full List)

| File | Change |
|------|--------|
| `src/cube/domain/model/Center.py` | Removed `_virtual_color`, `color` returns `UNCOLORED`, `is3x3` is now assertion |
| `src/cube/domain/model/Color.py` | Added `UNCOLORED` sentinel with gray RGB |
| `src/cube/domain/model/Edge.py` | Minor: assertion tightening |
| `src/cube/domain/model/Face.py` | `solved` checks corners-first for 2x2, `create_part` uses `original_color` |
| `src/cube/domain/model/Part.py` | `match_faces`, `position_id`, `colors_id` now assert instead of silently returning |
| `src/cube/domain/model/Slice.py` | Deleted `_rotate_virtual_center_colors()` and `_VIRTUAL_COLOR_CYCLES` |
| `src/cube/domain/solver/SolverName.py` | Added `TWO_BY_TWO_IDA`, `TWO_BY_TWO_BEGINNER` |
| `src/cube/domain/solver/Solvers.py` | Added `two_by_two_ida()`, `two_by_two_beginner()`, size-2 routing in `by_name()` |
| `src/cube/domain/solver/_2x2_ida_optimal/` | Renamed from `_2x2/`, imports updated |
| `src/cube/domain/solver/_2x2_beginner/` | **NEW** — Solver2x2Beginner + 3 stub phases + STEPS.md |

---

## Next Steps

1. **Implement `_L1.py`** — First layer solver (4 bottom corners)
2. **Implement `_L3Orient.py`** — Sune-based orientation
3. **Implement `_L3Permute.py`** — 3-corner cycle permutation
4. **Set `TWO_BY_TWO_BEGINNER.implemented = True`** once all phases work
5. **Write tests** — scramble + solve with beginner solver, verify move count
6. **Consider null object pattern** — `EmptyEdge`/`EmptyCenter` to replace guards
