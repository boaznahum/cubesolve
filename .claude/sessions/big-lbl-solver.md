# Big Cube LBL Solver - Session Notes

## Overview

Layer-by-Layer solver for NxN cubes (4x4, 5x5, etc.) that solves one horizontal layer at a time, unlike the reduction method.

## Current Architecture

```
LayerByLayerNxNSolver (direct/lbl/)
├── _LBLSlices helper
│   ├── NxNCenters2 (block commutators for ring centers)
│   └── NxNEdges (edge wing pairing - reused)
└── ShadowCubeHelper (for Layer 1 corners via shadow 3x3)
```

## What Works (as of 2026-01-12)

| Step | Status | Notes |
|------|--------|-------|
| Layer 1 Centers | Done | Uses NxNCenters.solve_single_face() |
| Layer 1 Edges | Done | Uses NxNEdges.solve_face_edges() |
| Layer 1 Corners | Done | Shadow 3x3 + BeginnerSolver3x3 |
| Slice 0 Centers | WIP | Works but limited to 1 slice |
| Slice 1..n Centers | Not started | Code exists but disabled (line 248) |
| Slice Edges | Not started | Edge wing pairing per slice |
| Last Layer | Not started | Opposite face solving |

## Key Files

- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` - Main solver
- `src/cube/domain/solver/direct/lbl/_LBLSlices.py` - Slice solving helper
- `src/cube/domain/solver/direct/lbl/NxNCenters2.py` - Block commutators

## WIP Limitation (line 248 of _LBLSlices.py)

```python
if True:  # WIP: Only solve first slice for now
    r = range(1)
else:
    r = range(self.n_slices)
```

## Known Issues

1. Slice index depends on cube orientation (commented at line 198-199)
2. `_is_slice_centers_solved` check disabled (line 199)

## Next Steps

- [ ] Enable all slice solving (remove WIP limitation)
- [ ] Fix slice index orientation issue
- [ ] Add slice edge wing pairing
- [ ] Add last layer solving