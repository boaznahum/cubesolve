# L3 Edge Pairing Algorithms for Big Cubes (NxN LBL Solver)

**Domain:** Rubik's cube NxN Layer-by-Layer solver -- L3 (last layer) edge wing pairing
**Researched:** 2026-01-28
**Overall confidence:** MEDIUM-HIGH (codebase patterns HIGH, external algorithms MEDIUM)

---

## Executive Summary

The LBL solver solves layers bottom-to-top. When L3 (last layer, opposite of L1/white face)
edges are being paired, L1 edges, middle-slice edge wings, and all corners are already solved.
The L3 edge pairing phase must NOT disturb any of those.

The current codebase uses `NxNEdges.solve_face_edges()` for L3 -- the same code path as L1 edge
pairing. This is problematic because `solve_face_edges` uses unrestricted whole-cube rotations
(`bring_edge_to_front_left_by_whole_rotate`) and `bring_edge_to_front_right_preserve_front_left`
which can displace pieces on solved layers.

For L3, the only "safe" moves are:
- **U** (the L3 layer itself) -- free to turn
- **Outer face turns of side faces (R, L, F, B)** -- these move middle slices
- **Middle-layer slice turns (M, E)** -- used carefully with undo

The standard approach across the big cube community is **Setup + Commutator + Restore** (conjugate pattern).

---

## 1. The Constraint: What Must Be Preserved

After L1 + middle slices + L3 centers are solved, the state before L3 edge pairing is:

```
                    ┌───────┐
                    │  L3   │  ← L3 face (e.g. Yellow/Up)
                    │ (free)│     Free to turn, edges here are unsolved
                    └───┬───┘
         ┌──────┐  ┌───┴───┐  ┌──────┐
         │ Side │  │ Side  │  │ Side │  ← Side face CENTERS solved
         │edges │  │ edges │  │edges │    Side face EDGE WINGS in middle
         │solved│  │solved │  │solved│    slices: solved
         └──────┘  └───┬───┘  └──────┘
                    ┌───┴───┐
                    │  L1   │  ← L1 face (e.g. White/Down)
                    │ LOCKED│     All edges solved, corners solved
                    └───────┘
```

**Safe moves (do not disturb solved state):**
| Move | Effect | Safe? |
|------|--------|-------|
| U, U', U2 | Rotates L3 layer | YES -- L3 edges are what we're solving |
| D, D' | Rotates L1 layer | NO -- destroys L1 corners/edges |
| R, L, F, B | Outer face turns | CONDITIONAL -- disturbs middle edge wings temporarily |
| M[i], E[i] | Middle slice turns | CONDITIONAL -- same as R/L/F/B for adjacent edge wings |
| y (whole cube) | Reorients cube | YES if D stays locked (conceptual reframe only) |

**The key constraint:** Any R/L/F/B or middle slice move that disturbs a middle-layer edge wing
must be undone before the next edge pairing iteration begins.

---

## 2. Algorithms in the Current Codebase

### 2.1 The FL/FR Edge-to-Edge Commutator (Used for middle slice wings)

**File:** `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py`, lines 387-467
**Method:** `_do_right_or_left_edge_to_edge_communicator`

This is the workhorse algorithm. It moves a wing from Front-Up (FU) edge into
Front-Left (FL) or Front-Right (FR) edge at a specific index.

**For Right edge (FR) target:**
```
U  R  U'  [i]M'  U  R'  U'  [i]M
```

**For Left edge (FL) target:**
```
U'  L'  U  [i]M'  U'  L  U  [i]M
```

Where `[i]M` is the i-th middle slice parallel to M (1-indexed from the face side).

**Why it preserves layers:**
- The sequence is a conjugate: the R/R' (or L/L') and M/M' moves cancel out
- Net effect: only the target wing on FL/FR and the source wing on FU move
- U moves freely rotate L3 layer -- this is the "free" layer
- The M slice move disturbs ONE middle edge wing, but the M' at the end restores it

**Constraint:** The source wing MUST be on the FU edge. If it's elsewhere, setup moves
bring it to FU first (via `_bring_source_wing_to_top`).

### 2.2 Source Setup: Bring Wing to Top (FU Edge)

**File:** `_LBLNxNEdges.py`, lines 371-384
**Method:** `_bring_source_wing_to_top`

Uses `bring_edge_to_front_right_or_left_preserve_down` to get the source wing's parent
edge onto the front face, then uses the FR/FL commutator to flip it up to FU.

**Problem:** `bring_edge_to_front_right_or_left_preserve_down` only handles edges on the
"belt" (FR, FL, BR, BL) via Y rotations. If the source wing is on a D-adjacent or
U-adjacent edge, this approach fails or disturbs D.

### 2.3 The Flip Commutator (NxNEdgesCommon / NxNEdges)

**File:** `src/cube/domain/solver/common/big_cube/NxNEdgesCommon.py`, lines 208-284
**Method:** `_fix_all_slices_on_edge`

For wings already on the target edge but with wrong orientation (flipped):
```
E[indices]  RF  E[indices]'
```
Where `RF = R F' U R' F` (a well-known "sexy move" variant).

This swaps wing pairs on the same edge using the E slice (parallel to D).

**Problem for L3:** The E slice is parallel to D. Turning E moves D-layer edge wings.
In the reduction method this is fine (edges solved last), but in LBL the D-layer edges
are already solved.

---

## 3. Standard Industry Algorithms for L3 Edge Pairing

### 3.1 Setup + Commutator + Restore (Conjugate Pattern)

The universally recommended approach for LBL last-layer edge wing pairing.

**Structure:**
```
[Setup]  [Core Commutator]  [Setup']
   P          [A, B]            P'
```

- **P (Setup):** Position the source wing into a slot the commutator can reach.
  Uses moves that temporarily disturb solved pieces.
- **[A, B] (Core):** A short commutator that cycles 2-3 wings. Typically only
  uses U and one outer face (R or L).
- **P' (Restore):** Exactly undoes Setup, restoring all previously solved pieces.

**Why this works:** The commutator [A,B] only permanently affects pieces it "catches"
in the intersection of A and B moves. The setup P positions the right pieces into
those intersection slots, so after P' restores everything else, only the intended
wings have moved.

### 3.2 Specific L3 Edge Wing Algorithms (from community sources)

**Algorithm 1: 5x5 L2E -- Adjacent Dedge Swap**
```
Rw' U' R' U R' F R F' Rw
```
Source: SpeedCubeDB 5x5 L2E (https://speedcubedb.com/a/5x5/L2E)
Confidence: MEDIUM (fetched from database, notation verified against standard conventions)

This pairs two adjacent edge wings on the U layer by:
1. `Rw'` -- wide R move, moves the inner slice too (setup)
2. `U' R' U R' F R F'` -- the core commutator (sexy move derivative)
3. `Rw` -- restores the wide move

**Why it preserves lower layers:** Only U and R/Rw are used. U is the free layer.
Rw affects one middle slice but is undone by the final Rw. The R turns affect
the FR edge but the algorithm is structured so they cancel in pairs.

**Algorithm 2: Edge Wing Parity (OLL Parity / Last Edge)**
```
r2 B2 U2 l U2 r' U2 r U2 F2 r F2 l' B2 r2
```
Source: KewbzUK 4x4 Parity Guide (https://kewbz.co.uk/blogs/solutions-guides/4x4-parity)
Confidence: MEDIUM

Used when the very last edge has a single wing flipped (parity situation). This
algorithm uses wide moves (r, l) which are inherently safe for middle layers because
they restore via the symmetric structure.

**Algorithm 3: 6x6 Wing Parity (from existing codebase, referenced in NxNEdges.py line 478)**
```
3R' U2 3L F2 3L' F2 3R2 U2 3R U2 3R' U2 F2 3R2 F2
```
Source: https://speedcubedb.com/a/6x6/6x6L2E (cited in code)
Confidence: HIGH (already in codebase, referenced directly)

The `3R` notation means the 3rd layer from R (inner slice). This only affects inner
slices + U layer. F2 moves do NOT affect U or D edge wings.

### 3.3 The "Tredge" Pattern (3x3-like Edge Positioning)

After pairing all wings, the L3 edges behave as a 3x3 edge set. The current code
already handles this via `_solve_layer3_cross` which delegates to a shadow 3x3 solver.
This is the correct approach -- position edges with standard 3x3 last-layer algorithms
after they are paired.

---

## 4. How Other LBL Solvers Handle This Constraint

### 4.1 Reduction Method (Cage solver in this codebase)

The Cage solver (`CageNxNSolver.py`) solves ALL 12 edges first (using `NxNEdges.solve()`),
THEN corners, THEN centers. This means there are NO previously-solved edges to preserve
during edge pairing. It uses `bring_edge_to_front_left_by_whole_rotate` freely.

**Not applicable to LBL** because LBL solves L1 edges before L3.

### 4.2 Layer-by-Layer Methods (Community)

From the SpeedSolving 4x4 LBL thread and BH commutator guides:

1. **Outer-layer-only constraint:** Only turn the unsolved layer (U) and outer faces
   (R, F, L, B). Never turn D or inner slices without immediately undoing them.

2. **Wide moves as safe setup/restore:** Moves like `Rw` (R + inner slice) are safe
   IF the move is later undone by `Rw'`. The inner slice is temporarily displaced
   but restored.

3. **Pre-position then solve:** Rotate U to align source wings near the target,
   then use a short 8-10 move algorithm. Never search globally -- always bring
   the source to a known position first.

4. **L2E (Last Two Edges) as endgame:** When only 2 edges remain, use dedicated
   L2E algorithms rather than the general pairing loop. L2E algorithms are
   specifically designed to pair the final two edges without disturbing anything.

### 4.3 K4 Method (4x4 Specific)

K4 uses a set of ~57 algorithms for the last layer that handle all permutation and
orientation cases simultaneously. These are pre-computed and cover all possible
L3 states. Each algorithm only uses U, R, F, L, B, and wide moves -- never D.

**Applicability:** Too specialized for a general NxN solver. But the principle is sound:
last-layer algorithms should be a closed set that only touches U + outer faces.

---

## 5. Why the Current L3 Edge Solver May Have Issues

The current `_solve_layer3_edges` calls `NxNEdges.solve_face_edges(l3_tracker)` which
delegates to `_do_edge()`. The `_do_edge` method:

1. Calls `bring_edge_to_front_left_by_whole_rotate(edge)` -- this uses whole-cube
   rotations which are fine (conceptual reorientation).
2. Uses `bring_edge_to_front_right_preserve_front_left` -- this uses B, U, D, R
   face turns to position edges. **The D turns here destroy L1 edges.**
3. Uses `_fix_all_slices_on_edge` with E-slice turns. **E turns disturb middle
   layer edges when D is L1.**

**The `solve_face_edges` method was written for L1 (when nothing else is solved).
It is NOT safe for L3 when L1 + middle slices are already solved.**

The `_LBLNxNEdges` class (used for middle slices) has the right approach:
- Uses U as the free layer
- Uses the FL/FR commutator which self-restores M slice moves
- Tracks source wings and brings them to FU before applying the algorithm

**L3 edge pairing should follow the same pattern as `_LBLNxNEdges`, NOT `NxNEdges`.**

---

## 6. Recommended Algorithm Strategy for L3 Edge Pairing

### Phase A: General Pairing (solve N-1 edges)

For each unpaired L3 edge wing:

```
1. Position L1 DOWN (D). L3 is now UP (U).
2. Find source wing (matching colors for target position)
3. If source is on U layer: rotate U to bring source to Front-Up edge
4. If source is on belt (FR/FL/BR/BL edges):
   a. Use Y rotation to bring source edge to Front (preserves D)
   b. Use FL/FR commutator to flip source up to FU:
      - Target is FL: U' L' U M[i]' U' L U M[i]
      - Target is FR: U R U' M[i]' U R' U' M[i]
5. Now source is on FU. Bring target to FL or FR via U rotation.
6. Apply FL/FR commutator to place source into target position:
   - FR target: U R U' M[i]' U R' U' M[i]
   - FL target: U' L' U M[i]' U' L U M[i]
7. Verify source index matches target index (column alignment)
```

**Key invariant:** After each wing placement, all middle-slice edges and L1 edges
remain solved. The M[i] moves self-cancel within each algorithm.

### Phase B: Last Edge (Parity Detection)

If exactly 1 edge remains unpaired after solving all others, this is edge parity.
Use the algorithm already in the codebase (line 478 of NxNEdges.py):

```
For 6x6:  3R' U2 3L F2 3L' F2 3R2 U2 3R U2 3R' U2 F2 3R2 F2
General:  M[i]' U2  (repeated 4x)  then M[i]'
```

The general M-based parity algorithm (already implemented):
```python
for _ in range(4):
    play(M[indices].prime)
    play(U * 2)
play(M[indices].prime)
```

This only uses M slices (parallel to L/R) and U. Safe for L3 because:
- U is the free layer
- M slices are middle layers -- they move side face edge wings but the algorithm
  is structured to restore them (the 4+1 repetition pattern)

**IMPORTANT:** The M-based parity alg does NOT preserve middle edge wings during
execution. It only restores them at the end. This means it must be the LAST operation,
or middle edges must be re-verified afterward.

### Phase C: Position Edges (3x3 OLL)

After all wings are paired, use shadow 3x3 solver for final edge positioning.
This is already implemented in `_solve_layer3_cross()`.

---

## 7. Move Compatibility Matrix

| Move | Disturbs L1 edges | Disturbs L1 corners | Disturbs middle edge wings | Disturbs L3 center | Safe for L3 pairing? |
|------|-------------------|---------------------|---------------------------|--------------------|--------------------|
| U | No | No | No | No | YES (free layer) |
| D | YES | YES | No | No | NO |
| R | No | No | Yes (FR middle) | No | CONDITIONAL (must undo) |
| L | No | No | Yes (FL middle) | No | CONDITIONAL (must undo) |
| F | No | No | Yes (FU/FD middle) | No | CONDITIONAL (must undo) |
| B | No | No | Yes (BU/BD middle) | No | CONDITIONAL (must undo) |
| M[i] | No | No | Yes (specific wing) | No | CONDITIONAL (must undo) |
| E[i] | Yes (if i touches D) | No | Yes | No | DANGEROUS |
| y | No | No | No | No | YES (reorientation) |
| x | Reorients all | Reorients all | Reorients all | Reorients all | Only for reorientation |

---

## 8. Sources

| Source | URL | Confidence |
|--------|-----|------------|
| SpeedCubeDB 5x5 L2E | https://speedcubedb.com/a/5x5/L2E | MEDIUM |
| SpeedCubeDB 6x6 L2E | https://www.speedcubedb.com/a/6x6/6x6L2E | MEDIUM |
| SpeedSolving Edge Pairing Wiki | https://www.speedsolving.com/wiki/index.php/Edge_pairing | MEDIUM |
| SpeedSolving BH Edge Commutators | https://www.speedsolving.com/threads/explanation-of-bh-edge-commutator-types.18673/ | MEDIUM |
| SpeedSolving Commutators for Big Cubes | https://www.speedsolving.com/threads/how-to-commutators-for-big-cubes.697/ | MEDIUM |
| Ruwix Big NxNxN Solution | https://ruwix.com/twisty-puzzles/big-cubes-nxnxn-solution/ | MEDIUM |
| KewbzUK 4x4 Parity Guide | https://kewbz.co.uk/blogs/solutions-guides/4x4-parity | MEDIUM |
| Codebase: _LBLNxNEdges.py | Local -- FL/FR commutator (lines 387-467) | HIGH |
| Codebase: NxNEdgesCommon.py | Local -- edge parity alg (lines 466-494) | HIGH |
| Codebase: LayerByLayerNxNSolver.py | Local -- L3 solve flow (lines 451-461) | HIGH |

---

## 9. Open Questions / Gaps

1. **Index alignment mismatch:** The FL/FR commutator requires source wing index to match
   target wing index (column alignment on front face). What happens when they don't match?
   The current code returns `NOT_SOLVED` and tries the next source. Is there a direct
   swap algorithm for mismatched indices?

2. **E-slice safety for L3:** The `_fix_all_slices_on_edge` method uses E slices which
   are parallel to D. When D is L1, E turns disturb L1 edge wings. This code path should
   NOT be used for L3. Needs investigation into whether `solve_face_edges` triggers this.

3. **Even cube L3 parity:** For 4x4/6x6, edge parity can manifest during L3 pairing.
   The current `solve_face_edges` detects parity only when it's the last edge in the
   WHOLE cube. In LBL, parity could appear when it's the last L3 edge but other edges
   elsewhere are also unsolved. This detection logic may need adjustment.

4. **Performance:** The current approach tries all source wings one at a time. For large
   cubes (7x7+), this could be slow. Pre-sorting sources by position (U-layer first,
   then belt) would reduce unnecessary setup moves.
