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
2. Main loop with 4x rotation
3. Source matching with `_find_source_for_target()` and `_is_source_usable()`
4. All 4 case handlers implemented with trackers
5. Commutators use `_map_wing_index()` (not hardcoded `cube.inv()`)
6. Flip methods return `Algs.NOOP` instead of `None`
7. Started adding diagrams to case handlers

### TODO for Next Session
1. **Fix helper name**: Line 31 has `super().__init__(slv, "_LBLL3Edges")` - should match actual class name
2. **Add diagrams**: Complete diagrams for Cases 2, 3, 4
3. **Add L3 preservation docs**: Document which methods preserve L3 layer
4. **Integration**: Wire into `LayerByLayerNxNSolver._solve_layer3_edges()`
5. **Testing**: Run actual solver tests

## Key Design Decisions

1. **Source tracking**: Use `source.tracker()` to follow physical piece
2. **Target tracking**: Use `_map_wing_index()` to calculate index after moves
3. **Commutator parameters**: Pass both indices, use `_map_wing_index()` for assertions
4. **No hardcoded `cube.inv()`**: Always use `_map_wing_index()` for index transformations

## Commutators Reference

```
LEFT CM:   FU → FL → BU → FU
           Alg: U' L' U M[k]' U' L U M[k]
           FU[i] → FL[map("FU","FL",i)]

RIGHT CM:  FU → FR → BU → FU
           Alg: U R U' M[k]' U R' U' M[k]
           FU[i] → FR[map("FU","FR",i)]

(LEFT CM)':  FL → FU (reverse)
(RIGHT CM)': FR → FU (reverse)
```

## Wing Index Mapping (User-Verified)

```
FL → FU: same
FU → FL: inv
FL → FD: inv
FD → FL: same
FU → FR: inv
FR → FU: inv
FR → FD: same
FD → FR: inv
```

## Case Summary

| Case | Source | Path |
|------|--------|------|
| 1 | FR | FR → FU ((Right CM)') → FL (Left CM) |
| 2 | FU | FU → FL (Left CM) |
| 3 | FD | F → FL → FU ((Left CM)') → F' → FL |
| 4 | FL | FL → BU → FU (Left CM x2) → flip → FL |

## Files Modified

1. `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py` - Main implementation
2. `.planning/L3_EDGES_DIAGRAMS.md` - Algorithm diagrams
3. `.planning/STATE.md` - Progress tracking

---
*Last updated: 2025-01-29*
