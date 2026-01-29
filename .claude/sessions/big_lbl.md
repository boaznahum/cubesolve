# Big-LBL L3 Edges Fix - Session Notes

## Task Summary

**Goal:** Implement L3 edge pairing in big-lbl solver using new approach based on `_LBLNxNEdges` patterns.

**Scope:**
- L3 edges only (not corners)
- Edges just need to be paired (position flexible)
- Must NOT disturb L1 or middle layer edges

## Solution Architecture

### New Helper Class

Create `_LBLL3Edges.py` in `src/cube/domain/solver/direct/lbl/`:
- Initially a copy of `_LBLNxNEdges`
- Later: extract common methods to `_common.py`

### Method Contract (Default Invariant)

Every method returns cube to known state:
- L3 on front
- Below L3 intact

Unless explicitly stated otherwise or method's purpose is to change state.

### Main Method Structure

```python
def do_l3_edges(faces_tracker):
    bring_l3_to_front()

    MAX_ITERATIONS = 10
    n_iteration = 0

    while True:
        n_iteration += 1
        if n_iteration > MAX_ITERATIONS:
            raise InternalSWError("Maximum iterations reached")

        for _ in range(4):  # rotate around front face
            self._logger.tab(lambda: ...)
            solve_left_edge()  # always works on LEFT
            rotate_cube_around_front_center()

        if no_increase_in_solved_l3_edges:
            break
```

### solve_left_edge() Structure

```python
def solve_left_edge():
    for left_edge_slice_index in range(n_slices):
        # delegate to method that handles one slice
        solve_left_edge_slice(left_edge_slice_index)
```

### solve_left_edge_slice() Logic

```python
def solve_left_edge_slice(slice_index):
    # 1. If wing already solved → skip

    # 2. Find source wings matching this target:
    #    - required_indexes = [i, inv(i)]  (for middle wing on odd cube, inv(i) == i)
    #    - match: s.index in required_indexes AND s.colors_id == target.position_id
    #    - DON'T check is_slice_marked_solve yet (more filtering comes later)

    # 3. Filter: Check if source is usable without rotation
    #    - ti = target index, si = source index
    #    - If source wing color on front == L3 color:
    #        → usable if ti == si
    #    - Else (wrong orientation, needs flip):
    #        → usable if ti == inv(si)

    # 4. Handle based on source position (FL, FR, FU, FD)
```

### Source Position Cases

Source wing can be on one of four edges of front face:

| Case | Source Edge | Status |
|------|-------------|--------|
| FR → FL | Right | DEFINED (see below) |
| FU → FL | Top | TODO |
| FD → FL | Bottom | TODO |
| FL → FL | Left (same as target) | TODO |

## Case 1: FR → FL (Right to Left)

### Key Components

**FD Edge:** The "helper" edge (front-down) - moved to BU to protect it.

**Right CM:** 3-cycle FU → FR → BU → FU
**(Right CM)':** Reverse 3-cycle FU → BU → FR → FU (so FR → FU!)

**Left CM:** 3-cycle FU → FL → BU → FU

**Stack:** Track scaffolding moves for rollback (NOT the CMs - those do actual work)

### Algorithm (CORRECTED - uses (Right CM)')

```
STACK: []

1. SETUP: Bring FD to BU
   STACK: [setup_alg]

2. (RIGHT CM)': Reverse cycle FR → FU
   - FU → BU
   - BU → FR
   - FR → FU  ← Source moves here!
   (no stack - this is work)

3. CHECK ORIENTATION + FLIP if needed
   STACK: [setup_alg, flip_alg] (if flipped)

4. LEFT CM: FU → FL
   - Source (FU) → FL ✓ DONE!
   (no stack - this is work)

5. ROLLBACK (reverse order):
   - Undo flip_alg.prime (if flipped)
   - Undo setup_alg.prime
```

### Orientation Check (after step 3)

After source is on FU, check orientation:

```
IF source color on front == L3 color:
   - Correct orientation
   - ti == si required
   - Proceed to Left CM

ELSE (wrong orientation):
   - ti == inv(si) required
   - FLIP source first, then Left CM
```

### Flip Algorithm (source on FU, preserve FL)

```
1. U' U'  → FU → BU
2. B'     → BU → RB
3. R'     → RB → RU
4. U      → RU → FU (now flipped!)

Path: FU → BU → RB → RU → FU
All steps go on stack, undo with .prime
```

### Full FR → FL with Flip

```
STACK: []

Setup:     FB → BU                    (stack)
Right CM:  FR → BU                    (work)
U rotate:  BU → FU                    (stack)

CHECK orientation - needs flip:
   U' U'                              (stack)
   B'                                 (stack)
   R'                                 (stack)
   U                                  (stack)

Left CM:   FU → FL                    (work) ✓

Rollback:  Undo all stack in reverse:
   U', R, B, U U, U_rotate_undo, setup_undo
```

## Dependencies to Implement

1. **`scl.map_wing_index_between_edges(from_edge, to_edge, index)`** - Map wing index from one edge to another on same face

2. **Flip algorithm** - As defined above

3. **Left CM** - Commutator to bring FU → FL

4. **Right CM** - Already exists in `_LBLNxNEdges`

## Case 2: FU → FL (Top to Left)

Source already on FU, but still need protection (left CM is 3-cycle) and maybe flip.

```
STACK: []

1. SETUP: Bring FB to BU
   STACK: [setup_steps]

2. CHECK orientation - if needs flip:
   U' U'                              (stack)
   B'                                 (stack)
   R'                                 (stack)
   U                                  (stack)

3. LEFT CM: FU → FL
   - Source (FU) → FL ✓ DONE!
   (no stack - this is work)

4. ROLLBACK (reverse order):
   - Undo flip steps (if any)
   - Undo setup_steps
```

**Difference from FR → FL:** Skip right CM and U rotation (source already on top).

## Case 3: FD → FL (Bottom to Left)

```
STACK: []

1. F rotation - frees up FD
   - Source (FD) → FL
   - Target wing (FL) → FU
   - FD is now FREE
   STACK: [F]

2. SETUP: Bring FD to BU (FD is now available!)
   STACK: [F, setup_alg]

3. (LEFT CM)': Reverse cycle FL → FU
   - FU → BU (target wing)
   - BU → FL (helper from FD)
   - FL → FU ← Source moves here!
   (no stack - this is work)

4. F' (undo F rotation)
   - Source (FU) → FL ✓ TARGET!
   (pop F from stack, now: [setup_alg])

5. CHECK orientation - if needs flip on FL:
   FLIP FL algorithm (TBD)
   STACK: [setup_alg, flip_fl_alg]

6. ROLLBACK:
   - Undo flip_fl_alg.prime (if flipped)
   - Undo setup_alg.prime
```

## Case 4: FL → FL (Source on Same Edge as Target)

SI is on FL (same edge as target TI), but different wing index.

**Key insight:** If SI is on FL and usable, it must have index `inv(ti)` (can't be `ti` or it would BE the target). From matching check, this means colors didn't match → **flip always required**.

```
STACK: []

1. SETUP: Bring FB to BU
   STACK: [setup_steps]

2. LEFT CM twice
   - First: SI (FL) → BU
   - Second: SI (BU) → FU
   (no stack - this is work)

3. FLIP (always required - no check needed)
   U' U', B', R', U
   STACK: [setup_steps, flip_steps]

4. LEFT CM
   - SI (FU) → FL ✓ TARGET!
   (no stack - this is work)

5. ROLLBACK:
   - Undo flip_steps
   - Undo setup_steps
```

Math: `inv(inv(si)) == ti` confirms indices match after flip.

---

## Complete Algorithm Summary

### All Four Cases: Source → Target (FL)

| Case | Source | Path | Flip Check |
|------|--------|------|------------|
| 1 | FR (right) | FR → BU (right CM) → FU (U rot) → FL (left CM) | Check orientation |
| 2 | FU (top) | FU → FL (left CM) | Check orientation |
| 3 | FD (bottom) | FD → FL (F) → FU ((left CM)') → FL (F') | TBD flip on FL |
| 4 | FL (left) | FL → BU → FU (left CM x2) → FL (left CM) | Always flip |

### Common Elements

1. **Setup:** Always bring FB to BU first (protect BU from CM destruction)
2. **Stack:** Track scaffolding moves for rollback (NOT the CMs)
3. **Rollback:** Undo stack in reverse order after work is done

### Flip Algorithm (source on FU, preserve FL)

```
U' U'  → FU → BU
B'     → BU → RB
R'     → RB → RU
U      → RU → FU (now flipped!)
```
All steps go on stack, undo with `.prime`

### Flip Algorithm for FL (TBD)

Needed for Case 3 (FD → FL) - different from FU flip.

---

## Dependencies to Implement

1. **`scl.map_wing_index_between_edges(from_edge, to_edge, index)`** - Map wing index from one edge to another on same face

2. **Flip algorithm for FU** - Defined above

3. **Flip algorithm for FL** - TBD

4. **Left CM** - Commutator: FU → FL → BU → FU

5. **Right CM** - Already exists in `_LBLNxNEdges`: FU → FR → BU

6. **Stack-based move tracking** - Track scaffolding, undo with `.prime`

---
*Last updated: 2025-01-29*
