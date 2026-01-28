# Code Analysis: NxNEdges L3-Safe Edge Pairing

**Date:** 2026-01-28
**Branch:** big_lbl
**Focus:** Understanding edge pairing algorithm and what breaks when called for L3 (Layer 3 / opposite face)

---

## 1. Current Algorithm Flow

### Entry Point for L3 Edges

```
LayerByLayerNxNSolver._solve_layer3_edges(th)
    → self._nxn_edges.solve_face_edges(l3_tracker)
```

**File:** `LayerByLayerNxNSolver.py` lines 451-461

`solve_face_edges()` is the same method used for L1 edges. It finds all 4 edges containing the target color (by color, not position) and calls `_do_edge()` on each unsolved one. The code was originally written for the "reduction" method where all 12 edges are solved in one pass -- there is no concept of "already solved layers that must be preserved."

### solve_face_edges() Flow

**File:** `NxNEdges.py` lines 65-115

1. Find 4 edges containing target color
2. Loop: while unsolved edges remain for target color:
   a. If this is the LAST unsolved edge in the WHOLE cube -> parity
   b. Otherwise: call `_do_edge(edge)` to pair the edge

### _do_edge() Flow

**File:** `NxNEdges.py` lines 142-185

1. **`bring_edge_to_front_left_by_whole_rotate(edge)`** -- uses Y, X, Z whole-cube rotations to bring the target edge to the front-left position. This does NOT preserve any other edge.
2. Determine the "ordered color" (which color should be on front face vs side face) using the center slice or majority vote (even cubes).
3. Call `_solve_on_front_left()` to pair all slices on this edge.

### _solve_on_front_left() Flow

**File:** `NxNEdges.py` lines 187-206

Two phases:
1. **`_fix_all_slices_on_edge()`** -- Fix slices on the SAME edge that have the right colors but wrong orientation (flipped).
2. **`_fix_all_from_other_edges()`** -- Pull matching slices from OTHER edges into this edge.

### The Core Pairing Mechanism (the "rf commutator")

**Both phases use the same 3-step pattern:**

```
E[slices]          -- move target slice positions to the right edge
rf                 -- swap between front-left and front-right edges
E[slices].prime    -- restore slice positions
```

Where `rf` is defined at **NxNEdges.py line 518-519:**
```python
@property
def rf(self) -> Alg:
    return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F
    # R F' U R' F
```

The E-slice moves specific wing positions out of the front-left edge to front-right. The `rf` commutator swaps content between front-left and front-right. Then E[slices].prime restores.

---

## 2. The `rf` Algorithm: R F' U R' F

### What it does physically

This is a well-known commutator for big cube edge pairing. When the target edge is on front-left and a "helper" edge is on front-right:

```
R  -- rotates right face, moving front-right edge slice to up-right
F' -- rotates front face, affects front-left and front-right
U  -- rotates up face
R' -- undoes R
F  -- undoes F'
```

### Why it is problematic for L3

By the time we solve L3 edges, the following are already solved:
- **L1 face** (Down): centers, edges, corners -- FULLY solved
- **Middle slices**: All edge wings and center slices in correct positions
- **L3 face centers**: Solved

The `rf` commutator uses **R, F, and U face rotations**. These are "outer layer" moves. When L1 is on the Down face:

| Move | Faces affected | Problem |
|------|---------------|---------|
| R | Right face rotation | Moves edge wings on the right edge (middle slice pieces) |
| F' | Front face rotation | Moves edge wings on the front edge (middle slice pieces) |
| U | Up face rotation | Moves the L3 (up) face edges -- but L3 edges are what we are trying to solve, so this might be OK |
| R' | Right face rotation | Same as R |
| F | Front face rotation | Same as F' |

**The critical issue:** R and F rotate outer faces. On a big cube (5x5, 6x6, 7x7), rotating R moves ALL slices of the right edge, including the middle-slice wings that were solved in `_solve_face_rows()`. Similarly F moves all slices of the front edge.

### Concrete example on 5x5 (n_slices=3)

Edge has 3 wing slices (indices 0, 1, 2). Middle slice = index 1.

When we do `R`:
- ALL 3 wings of the FR edge move to UR
- This includes wing[1] which was solved during middle slice solving

When we do `F'`:
- ALL 3 wings of the FL edge move
- Wing[1] on FL was solved

The `E[slices]` moves only move SPECIFIC slice indices, but the `rf` commutator moves the ENTIRE edge (all slices). This destroys solved middle-slice wings.

### What _fix_all_slices_on_edge does that's dangerous

**File:** `NxNEdges.py` lines 208-284

Before applying `rf`, it brings a "helper" edge to front-right:
```python
self.cmn.bring_edge_to_front_right_preserve_front_left(edge_can_destroyed)
```

This uses R, B, U, D, and other face rotations (see `CommonOp.py` lines 314-379). Each of these moves the ENTIRE edge to the front-right position, destroying any solved middle slices on those edges.

### What _fix_all_from_other_edges does that's dangerous

**File:** `NxNEdges.py` lines 286-316

Same pattern:
1. Find a source slice on another edge
2. `bring_edge_to_front_right_preserve_front_left(source_slice.parent)` -- destroys middle slices on edges along the path
3. If orientation is wrong: `self.op.play(self.rf)` -- bare rf with no E-slice protection, destroys ALL slices on FR
4. Then the E-slice + rf + E-slice.prime pairing

---

## 3. Slice Moves (E Slices) Usage

**E slices** are middle-layer rotations parallel to the D face. In this codebase:

```python
Algs.E[[ltr + 1 for ltr in ltrs]]  # Move specific E-slice indices
```

E-slice indexing is 1-based from D. So on a 5x5:
- E[1] = slice closest to D (already solved for L1)
- E[2] = middle slice (solved during face_rows)
- E[3] = slice closest to U (not yet solved when doing L3)

E-slice moves are used to selectively move specific wing positions out of the front-left edge to the front-right edge BEFORE the rf commutator. This is the "selective" part -- only specific indices are moved to FR where they can be swapped.

**E slices are safe for L3** because they rotate parallel to D/U and do not affect the D-face (L1) edges or the U-face (L3) edges. They only affect the 4 orthogonal edges (FL, FR, BL, BR).

The problem is NOT with E-slice moves. The problem is with:
1. The `rf` commutator itself (R, F, U moves)
2. The `bring_edge_to_front_right_preserve_front_left` movements (R, B, U, D moves)

---

## 4. What needs to change for L3-safe solve_face_edges

### Problem Statement

When `solve_face_edges(l3_tracker)` is called to pair L3 edges:
- L1 (Down face) is fully solved -- must not be disturbed
- Middle slices are fully solved -- must not be disturbed
- Only the 4 edges touching the L3 (Up) face are available for manipulation

### The preserved set (cannot be disturbed)

```
D face edges: DF, DR, DB, DL -- solved, must stay
Middle wings: All edge wings at E-slice indices that correspond to solved rows
L3 face center: Solved
```

### What CAN be freely used

```
U face rotations: Rearrange L3 edges freely (they are unsolved)
E-slice moves: Move wing positions between orthogonal edges (FL, FR, BL, BR)
               -- but only indices that are NOT solved middle slices
```

### Approaches to fix

**Approach A: Replace rf with a U-face-only commutator**

Instead of `R F' U R' F`, use an algorithm that only rotates U and E-slices. This would preserve both L1 and all middle slices.

Challenge: The `rf` commutator's purpose is to swap specific wing positions between front-left and front-right edges. Achieving the same swap using only U + E-slice moves is a fundamentally different algorithm.

A candidate: `E[i] U E[i]' U' E[i] U E[i]' U'` style commutator -- but this would need careful design to achieve the exact swap needed.

**Approach B: Selective E-slice isolation**

Before doing `rf`, move ALL solved middle-slice wings out of the affected edges (to a "safe" edge like BL or BR via E-slices), do the rf, then restore them. This is expensive (many E-slice moves) but preserves the existing rf logic.

**Approach C: Restrict movements to U-layer only**

Redesign `_do_edge` so that:
1. Instead of `bring_edge_to_front_left_by_whole_rotate`, use U rotations to bring L3 edges to the target position
2. Instead of `rf`, use a commutator that only touches U and specific E-slice indices
3. Never use R, F, D, B face rotations

This is the cleanest approach but requires the most new code.

**Approach D: Solve L3 edges BEFORE middle slices**

Reorder the solve sequence so L3 edges are paired before middle slices are solved. This avoids the preservation problem entirely.

Challenge: The middle-slice solving (`_solve_face_rows`) may need L3 edges to already be paired, depending on how it works. Need to verify.

**Approach E: Post-solve restoration**

Solve L3 edges using the existing algorithm (which destroys middle slices), then re-solve the middle slices. This is essentially what the parity retry loop does for L1.

Challenge: Middle slice solving is expensive. This adds significant move count.

---

## 5. Key Code References

| Description | File | Line(s) |
|-------------|------|---------|
| solve_face_edges (entry point) | NxNEdges.py | 65-115 |
| _do_edge (main edge solver) | NxNEdges.py | 142-185 |
| _solve_on_front_left | NxNEdges.py | 187-206 |
| _fix_all_slices_on_edge (same-edge flip) | NxNEdges.py | 208-284 |
| _fix_all_from_other_edges (cross-edge pull) | NxNEdges.py | 286-316 |
| _fix_many_from_other_edges_same_order | NxNEdges.py | 318-393 |
| rf commutator definition | NxNEdges.py | 517-519 |
| bring_edge_to_front_left_by_whole_rotate | CommonOp.py | 240-312 |
| bring_edge_to_front_right_preserve_front_left | CommonOp.py | 314-379 |
| _solve_layer3_edges (caller) | LayerByLayerNxNSolver.py | 451-461 |
| _LBLNxNEdges (middle-slice edge solver) | _LBLNxNEdges.py | 1-485 |
| _LBLSlices.solve_all_faces_all_rows | _LBLSlices.py | 206-232 |

---

## 6. Recommendation

**Approach C (U-layer-only commutator)** is the right long-term solution but requires significant algorithm design work.

**Approach E (solve then re-solve middle slices)** is the fastest path to correctness if middle-slice solving is reliable and fast enough. The existing `_solve_face_rows` already handles re-solving, and the parity retry pattern already exists in the codebase (see `big_lbl.md` session notes).

**Approach D (reorder)** is worth investigating as a quick win -- if L3 edge pairing can happen before middle slices without breaking anything.

The session notes in `.claude/sessions/big_lbl.md` document that parity algorithms also destroy L1 edges, and the pattern of "solve, detect destruction, re-solve from earlier stage" is the established pattern in this codebase.

---

## 7. Duplication Note

`NxNEdges.py` and `NxNEdgesCommon.py` contain nearly identical code. The classes `NxNEdges` and `NxNEdgesCommon` have the same `solve_face_edges`, `_do_edge`, `_fix_all_slices_on_edge`, `_fix_all_from_other_edges`, `_fix_many_from_other_edges_same_order`, `_do_last_edge_parity`, and `_do_edge_parity_on_edge` methods. The only difference is method naming (`_get_slice_ordered_color` is static in NxNEdges but `get_slice_ordered_color` is static in NxNEdgesCommon).

This duplication means any L3-safe changes need to be made in whichever class is actually used by the LBL solver. Currently `LayerByLayerNxNSolver` instantiates `NxNEdges` (line 82).
