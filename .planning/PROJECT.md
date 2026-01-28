# Big-LBL L3 Edge Fix

## What This Is

Fix the Layer 3 edge solving in the big-lbl (Layer-by-Layer) NxN cube solver. Currently, when solving L3 edges, the solver incorrectly modifies already-solved edges (L1 and middle layer edges). The fix ensures L3 edge solving only affects L3 edges.

## Core Value

L3 edge solving must NOT touch any non-L3 edges. Period.

## Requirements

### Validated

- ✓ Big-LBL solver exists and works for L1, middle slices, L3 centers — existing
- ✓ NxNEdges.solve_face_edges() pairs edges by color — existing
- ✓ Test infrastructure exists for solvers — existing

### Active

- [ ] Test script that reproduces the L3 edge bug (5x5, seed "0")
- [ ] Guard assertions that fail immediately when non-L3 edge is modified
- [ ] Fix L3 edge solving to preserve L1 and middle layer edges
- [ ] Works for any NxN cube (5x5, 6x6, 7x7, etc.)

### Out of Scope

- Changing the overall big-lbl approach — just fixing L3 edges
- L3 corners — separate solving step, not part of this fix
- Performance optimization — correctness first
- Beginner/reducer solver — different approach, not affected

## Context

**The bug:** `_solve_layer3_edges()` calls `_nxn_edges.solve_face_edges()` which uses algorithms designed for the reducer approach. These algorithms (like `R F' U R' F` and E-slice moves) don't preserve lower layers.

**Key files:**
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` — main solver
- `src/cube/domain/solver/common/big_cube/NxNEdges.py` — edge pairing logic
- `src/cube/domain/solver/direct/lbl/_LBLSlices.py` — middle slice solving

**Reproduction:** 5x5 cube with seed "0" scramble, solve up to L3 centers, then L3 edges breaks other edges.

**Constraint:** For L3 in LBL, moves must either:
- Only use U-face moves
- Use algorithms that restore other layers after temporary disruption
- Use top-slice-only moves

## Constraints

- **Existing code:** Must work within existing NxNEdges structure (fix, not rewrite)
- **Compatibility:** Must work for all NxN cubes (odd and even)
- **Testing:** Must have reproducible test case

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fix existing solve_face_edges vs new class | User preference + code is "almost there" | — Pending |
| Guard assertions approach | Pinpoint exact move causing issue | — Pending |

---
*Last updated: 2025-01-28 after initialization*
