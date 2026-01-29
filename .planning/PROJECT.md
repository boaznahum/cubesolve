# Big-LBL L3 Edges

## What This Is

Implement L3 edge pairing in the big-lbl (Layer-by-Layer) NxN cube solver. The solver pairs edge wings on the last layer (L3) without disturbing already-solved L1 and middle layer edges. This uses commutator-based algorithms that create 3-cycles of edge wings.

## Core Value

L3 edge pairing must NOT touch any L1 or middle layer edges. Period.

## Requirements

### Validated

- ✓ Big-LBL solver exists and works for L1, middle slices, L3 centers — existing
- ✓ Left/Right CM algorithms exist in `_LBLNxNEdges` — existing
- ✓ Test infrastructure exists for solvers — existing

### Active

- [ ] New helper class `_LBLL3Edges.py` based on `_LBLNxNEdges`
- [ ] Main loop: rotate cube 4x, solve left edge each time, repeat until no progress
- [ ] Source matching: find wings by colors and index (i or inv(i))
- [ ] Orientation check: determine if flip needed based on color position
- [ ] Case FR→FL: right CM + U rotation + left CM
- [ ] Case FU→FL: protect BU + left CM
- [ ] Case FD→FL: F + (left CM)' + F'
- [ ] Case FL→FL: left CM x2 + flip + left CM
- [ ] Flip algorithm for FU (preserves FL): U'² B' R' U
- [ ] Flip algorithm for FL (TBD)
- [ ] Setup returns Alg for `.prime` undo pattern
- [ ] Integration with `LayerByLayerNxNSolver._solve_layer3_edges()`
- [ ] Works for any NxN cube (5x5, 6x6, 7x7, etc.)

### Out of Scope

- L3 corners — separate solving step
- Performance optimization — correctness first
- Changing overall big-lbl approach — just adding L3 edges
- Reducer solver — different approach

## Context

**Key insight:** The left/right CM algorithms are 3-cycles (FU→FL→BU or FU→FR→BU) that preserve lower layers because:
- M[k] and M[k]' cancel (no net L1 effect)
- R/L and R'/L' cancel (no net middle effect)

**FB edge:** The "helper" edge not involved in FL/FR/FU operations. Used as sacrificial edge for BU protection.

**Key files:**
- `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py` — existing edge helper (source for patterns)
- `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py` — NEW helper to create
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` — main solver

## Constraints

- **Pattern:** Methods return Alg for undo via `.prime` operator
- **Contract:** All methods return cube to known state (L3 front, below intact) unless explicitly stated
- **Compatibility:** Must work for all NxN cubes (odd and even)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| New class vs fix existing | Clean implementation, user preference | — Pending |
| Methods return Alg | Cleaner undo pattern than manual stack | — Pending |
| FB as helper edge | Only L3 edge not in FL/FR/FU operations | — Pending |

---
*Last updated: 2025-01-29 after initialization*
