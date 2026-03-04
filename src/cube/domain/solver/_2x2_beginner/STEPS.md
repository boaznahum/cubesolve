# 2x2 Beginner Solver — Implementation Steps

## Overview

A human-style layer-by-layer solver for the 2x2 Rubik's cube.
The 2x2 has only corners (no edges, no centers), so the beginner method
simplifies to two layers with three phases.

Convention: **white on bottom, yellow on top**.

---

## Phase 1: First Layer (L1) — 4 Bottom Corners

**Goal:** All 4 corners on the bottom layer are in correct position
with white stickers facing down.

### Algorithm

For each of the 4 bottom corners (FRD, FLD, BRD, BLD):

1. **Locate** the target corner piece (by its 3 colors).

2. **If the corner is already in the correct position with correct orientation:**
   skip it.

3. **If the corner is in the bottom layer but wrong position or orientation:**
   extract it to the top layer first using `R U R'` (adjust face as needed),
   then proceed to step 4.

4. **Corner is in the top layer:**
   - Rotate U to bring the corner above its target slot.
   - Use one of three insertion triggers depending on orientation:
     - **White faces right:** `R U R'`
     - **White faces front:** `F' U' F`
     - **White faces up:** `R U2 R' U' R U R'` (double trigger)

### Key details

- We fix the D face as the reference. The solver should orient the cube
  so white is on the bottom before starting.
- After solving one corner, the solver moves to the next target slot
  by rotating the whole cube (Y rotations) to keep the current target
  at the front-right-down position.

---

## Phase 2: Last Layer Orient (L3 Orient) — Yellow on Top

**Goal:** All 4 top-layer corners have yellow stickers facing up.
(Positions may still be wrong — that's Phase 3.)

### Algorithm — Sune Method

1. **Count** how many top-layer corners have yellow on top:
   - **4:** Already oriented — skip.
   - **0, 1, or 2:** Continue.

2. **Position** the cube so a corner with yellow NOT on top is at
   the front-right-up (URF) position.

3. **Apply Sune:** `R U R' U R U2 R'`

4. **Repeat** from step 1 (at most 3 iterations needed).

### Why this works

Sune twists the URF corner clockwise and adjusts the other three corners'
orientations. Repeatedly applying it with correct setup rotations cycles
through all orientation cases.

---

## Phase 3: Last Layer Permute (L3 Permute) — Final Positions

**Goal:** All 4 top-layer corners are swapped into their correct positions.
(After Phase 2, they all have yellow on top but may be in wrong slots.)

### Algorithm — 3-Corner Cycle

1. **Check** each top corner: is it in the correct position?
   (A corner is correct when its colors match the two adjacent face colors
   and yellow.)

2. **If all 4 correct:** Done!

3. **If exactly 1 correct corner:**
   - Hold the correct corner at UFL (front-left-up).
   - Apply: `R U' L' U R' U' L U`
   - This cycles the other 3 corners (URF → UBR → ULB).
   - After one or two applications, all corners are in place.

4. **If 0 correct corners:**
   - Apply the algorithm once from any angle.
   - Now at least 1 corner will be correct — go to step 3.

---

## Solve Step Mapping

| SolveStep | Phases Executed          |
|-----------|--------------------------|
| L1        | Phase 1                  |
| L3 / ALL  | Phase 1 + Phase 2 + Phase 3 |

---

## Implementation Checklist

- [ ] **_L1.py** — `L1.is_solved` and `L1.solve()`
  - [ ] Locate target corner by colors
  - [ ] Check if corner is in correct position/orientation
  - [ ] Extract from bottom layer if misplaced
  - [ ] Position above target slot via U rotations
  - [ ] Insert with correct trigger based on white sticker orientation
  - [ ] Rotate to next target slot

- [ ] **_L3Orient.py** — `L3Orient.is_solved` and `L3Orient.solve()`
  - [ ] Count yellow-on-top corners
  - [ ] Position cube for Sune setup
  - [ ] Apply Sune algorithm
  - [ ] Loop until all 4 oriented

- [ ] **_L3Permute.py** — `L3Permute.is_solved` and `L3Permute.solve()`
  - [ ] Check which corners are in correct positions
  - [ ] Hold correct corner at UFL
  - [ ] Apply 3-corner cycle algorithm
  - [ ] Loop until all 4 in place
