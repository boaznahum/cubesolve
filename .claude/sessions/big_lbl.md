# Big-LBL L3 Edges Fix - Session Notes

## Task Summary

**Goal:** Implement L3 edge pairing in big-lbl solver using new approach based on `_LBLNxNEdges` patterns.

**Scope:**
- L3 edges only (not corners)
- Edges just need to be paired (position flexible)
- Must NOT disturb L1 or middle layer edges

## Current Status: ~90% Complete

**File:** `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py` - Pyright clean

### What's Done
1. Infrastructure with composition pattern
2. Main loop with 4x rotation and `_count_solved_l3_wings(tracker)`
3. Source matching: `_find_sources_for_target()` returns LIST, asserts non-empty
4. All 4 case handlers with source.tracker()
5. Commutators use `_map_wing_index()` with EdgeName enum
6. Type-safe code: EdgeName enum, bool for same/inv
7. Correct mapping values (verified by chaining FL→FU→FR→FD→FL = same)

### TODO for Next Session
1. **Fix helper name**: Line 31 has wrong name in `super().__init__()`
2. **Add diagrams**: Complete diagrams for Cases 2, 3, 4 (Case 1 done)
3. **Add L3 preservation docs**: Document which methods preserve L3 layer
4. **Integration**: Wire into `LayerByLayerNxNSolver._solve_layer3_edges()`
5. **Testing**: Run actual solver tests

## Key Design Decisions

1. **Source tracking**: Use `source.tracker()` to follow physical piece
2. **Target tracking**: Use `_map_wing_index()` to calculate index after moves
3. **Multiple sources**: `_find_sources_for_target()` returns list (may be 1 or 2)
4. **Assert on no source**: No source = bug, so assert instead of return None
5. **Type safety**: EdgeName enum, bool instead of strings

## Wing Index Mapping

**Verified by chaining: FL→FU→FR→FD→FL returns same index (i → i)**

```python
adjacent_map = {
    # FL ↔ FU: same
    (EdgeName.FL, EdgeName.FU): True,
    (EdgeName.FU, EdgeName.FL): True,
    # FU ↔ FR: inv
    (EdgeName.FU, EdgeName.FR): False,
    (EdgeName.FR, EdgeName.FU): False,
    # FR ↔ FD: same
    (EdgeName.FR, EdgeName.FD): True,
    (EdgeName.FD, EdgeName.FR): True,
    # FD ↔ FL: inv
    (EdgeName.FD, EdgeName.FL): False,
    (EdgeName.FL, EdgeName.FD): False,
}
```

## Commutators Reference

```
LEFT CM:   FU → FL → BU → FU
           Alg: U' L' U M[k]' U' L U M[k]

RIGHT CM:  FU → FR → BU → FU
           Alg: U R U' M[k]' U R' U' M[k]

(LEFT CM)':  FL → FU (reverse)
(RIGHT CM)': FR → FU (reverse)
```

## Case Summary

| Case | Source | Path |
|------|--------|------|
| 1 | FR | FR → FU ((Right CM)') → FL (Left CM) |
| 2 | FU | FU → FL (Left CM) |
| 3 | FD | F → FL → FU ((Left CM)') → F' → FL |
| 4 | FL | FL → BU → FU (Left CM x2) → flip → FL |

## Files

- `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py` - Main implementation
- `.planning/L3_EDGES_DIAGRAMS.md` - Algorithm diagrams

---
*Last updated: 2025-01-30*
