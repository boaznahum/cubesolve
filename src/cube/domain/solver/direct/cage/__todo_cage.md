# Cage Solver TODO

## Current Focus: Edge Solving (Phase 1a)

### Status: DONE - Reusing NxNEdges

Edge solving is implemented by reusing `NxNEdges` from the beginner solver.

Key insight: `NxNEdges` determines edge colors from the edge itself (middle slice for odd cubes, majority for even), NOT from centers. This means it works perfectly for cage method where centers are unsolved.

### Implementation
```python
self._nxn_edges = NxNEdges(self, advanced_edge_parity=False)

def _solve_edges(self) -> bool:
    return self._nxn_edges.solve()
```

### Parity Handling
Edge parity is handled INSIDE `NxNEdges.solve()`:
1. Solves 11 edges via `_do_first_11()`
2. If 1 edge left unsolved -> parity detected
3. Calls `_do_last_edge_parity()` to fix
4. Re-solves remaining edges
5. Returns True if parity was detected/fixed

### TODO: advanced_edge_parity Flag
Currently using `advanced_edge_parity=False` (M-slice algorithm).
Consider switching to `True` (R/L-slice algorithm) which:
- Preserves edge pairing better
- May be better for cage method where we want clean edges

### Checklist
- [x] Basic solver structure with BaseSolver
- [x] State inspection methods (_are_edges_solved)
- [x] Edge solving algorithm (reuses NxNEdges)
- [x] Edge parity handling (via NxNEdges)
- [ ] Evaluate advanced_edge_parity=True

## Next Steps

### Phase 1b: Corner Solving
- [ ] Implement corner positioning
- [ ] Implement corner orientation
- [ ] Can reuse 3x3 corner algorithms (L1Corners, L3Corners)

### Phase 2: Center Solving
- [ ] Implement center solving with commutators
- [ ] Must use only commutators that preserve edges
