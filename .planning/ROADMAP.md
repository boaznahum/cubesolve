# Roadmap: Big-LBL L3 Edges

**Created:** 2025-01-29
**Phases:** 6
**Requirements:** 27 mapped

## Phase Overview

| # | Phase | Goal | Requirements | Status |
|---|-------|------|--------------|--------|
| 1 | Infrastructure | Create helper class skeleton | INFRA-01..04 | ○ Pending |
| 2 | Main Loop | Implement iteration logic | LOOP-01..05 | ○ Pending |
| 3 | Source Matching | Find and validate source wings | MATCH-01..04, ORIENT-01..03 | ○ Pending |
| 4 | Algorithms | Implement CM and flip algorithms | ALG-01..05 | ○ Pending |
| 5 | Case Handlers | Implement all 4 source position cases | CASE-01..04 | ○ Pending |
| 6 | Integration | Wire into main solver, test | INTEG-01..02 | ○ Pending |

---

## Phase 1: Infrastructure

**Goal:** Create the `_LBLL3Edges` helper class skeleton with proper structure.

**Requirements:** INFRA-01, INFRA-02, INFRA-03, INFRA-04

**Success Criteria:**
1. `_LBLL3Edges.py` exists in `src/cube/domain/solver/direct/lbl/`
2. Class inherits from appropriate base (like `_LBLNxNEdges`)
3. Main entry method accepts `faces_tracker` parameter
4. Logging infrastructure in place

**Deliverables:**
- `_LBLL3Edges.py` with class skeleton

---

## Phase 2: Main Loop

**Goal:** Implement the main iteration logic that rotates cube and solves left edge.

**Requirements:** LOOP-01, LOOP-02, LOOP-03, LOOP-04, LOOP-05

**Success Criteria:**
1. L3 brought to front at start
2. Loop iterates 4 times with cube rotation
3. Each iteration calls `solve_left_edge()` (stub for now)
4. Progress tracked by counting solved L3 edges
5. Max iterations guard prevents infinite loops

**Deliverables:**
- `do_l3_edges()` method
- Progress tracking logic
- Cube rotation around front center

---

## Phase 3: Source Matching

**Goal:** Implement logic to find valid source wings for a target.

**Requirements:** MATCH-01..04, ORIENT-01..03

**Success Criteria:**
1. Already-solved wings skipped
2. Sources found by `colors_id` match
3. Index matching handles i and inv(i)
4. Middle wing on odd cube handled correctly
5. Orientation check determines if flip needed

**Deliverables:**
- `find_matching_sources()` method
- `check_orientation()` method
- Index mapping logic

---

## Phase 4: Algorithms

**Goal:** Implement all the move algorithms (CMs, flips, setup).

**Requirements:** ALG-01..05

**Success Criteria:**
1. Left CM implemented: `U' L' U M[k]' U' L U M[k]`
2. Right CM implemented: `U R U' M[k]' U R' U' M[k]`
3. Flip FU implemented: `U'² B' R' U`
4. Flip FL implemented (TBD algorithm)
5. Protect BU (bring FB to BU) implemented
6. All methods return `Alg` for `.prime` undo

**Deliverables:**
- `left_cm()` method
- `right_cm()` method
- `flip_fu()` method
- `flip_fl()` method
- `protect_bu()` method

---

## Phase 5: Case Handlers

**Goal:** Implement all 4 source position case handlers.

**Requirements:** CASE-01..04

**Success Criteria:**
1. FR→FL: right CM → U rotate → left CM (with setup/rollback)
2. FU→FL: left CM (with setup/rollback)
3. FD→FL: F → (left CM)' → F' (with setup/rollback)
4. FL→FL: left CM x2 → flip → left CM (with setup/rollback)
5. All cases preserve L1 and middle edges

**Deliverables:**
- `handle_fr_to_fl()` method
- `handle_fu_to_fl()` method
- `handle_fd_to_fl()` method
- `handle_fl_to_fl()` method

---

## Phase 6: Integration

**Goal:** Wire into main solver and verify with tests.

**Requirements:** INTEG-01, INTEG-02

**Success Criteria:**
1. `LayerByLayerNxNSolver._solve_layer3_edges()` calls `_LBLL3Edges`
2. Works for 5x5 cube
3. Works for 6x6 cube
4. Works for 7x7 cube
5. L1 and middle edges preserved after L3 edge solving

**Deliverables:**
- Integration in `LayerByLayerNxNSolver.py`
- Test script verifying correctness

---

## Dependencies

```
Phase 1 → Phase 2 → Phase 3 → Phase 5
                  ↘        ↗
                    Phase 4

Phase 5 → Phase 6
```

Phase 4 (Algorithms) can be done in parallel with Phase 3 (Source Matching).
Phase 5 (Case Handlers) requires both Phase 3 and Phase 4.
Phase 6 (Integration) requires Phase 5.

---
*Roadmap created: 2025-01-29*
