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

## What Works (as of 2026-02-04)

| Step | Status | Notes |
|------|--------|-------|
| Layer 1 Centers | Done | Uses NxNCenters.solve_single_face() |
| Layer 1 Edges | Done | Uses NxNEdges.solve_face_edges() |
| Layer 1 Corners | Done | Shadow 3x3 + BeginnerSolver3x3 |
| Slice Centers (all) | Done | All slices solving, piece-by-piece |
| Block Search | Disabled | Infrastructure ready, ~3% edge case failures |
| Slice Edges | Not started | Edge wing pairing per slice |
| Last Layer | Not started | Opposite face solving |

## Key Files

- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` - Main solver
- `src/cube/domain/solver/direct/lbl/_LBLSlices.py` - Slice solving helper
- `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py` - Center solving with block commutators
- `src/cube/domain/solver/common/big_cube/commutator/CommutatorHelper.py` - Block commutator implementation

## Block Search Integration (2026-02-04)

### What Was Done

Implemented block search infrastructure in `_LBLNxNCenters.py` to solve multiple center pieces with a single commutator operation. **Currently disabled** pending edge case investigation.

### New Methods Added

| Method | Purpose |
|--------|---------|
| `_block_iter(block)` | Iterate over all cells in a rectangular block |
| `_rotate_block_clockwise(block, n)` | Rotate block coordinates |
| `_source_block_has_color_no_rotation()` | Check source WITHOUT rotation search |
| `_find_target_blocks()` | Find target blocks from tracked positions |
| `_try_blocks_from_target()` | Main entry point for block-based solving |

### Critical Insight: Block Rotation Changes Shape

**Key discovery:** Multi-cell blocks CANNOT be rotated during source search because rotating coordinates changes the block's SHAPE:

```
1x3 horizontal at (1,0), (1,1), (1,2)
        ↓ 90° clockwise rotation
3x1 vertical at (0,1), (1,1), (2,1)
```

The commutator's slice algorithm depends on block shape, so source blocks must be found at their natural position without rotation.

### Current Status

- Infrastructure is implemented and compiles cleanly
- Block search is **disabled** in `_solve_single_center_piece_from_source_face_impl()`
- ~97% of test cases pass when enabled (9 out of ~300 fail)
- Edge cases need investigation before enabling

### To Enable Block Search

In `_LBLNxNCenters.py`, uncomment:
```python
# work_done = self._try_blocks_from_target(
#     color, target_face, source_face.face
# )
```

## Documentation Updated

- `docs/design/commutator.md` - Added "Block Search Integration in LBL Solver" section

## Known Issues

1. **Block search edge cases** - ~3% failure rate when enabled
   - Commutator executes but pieces don't end up with correct colors
   - Investigation needed

## Next Steps

- [ ] Debug remaining 9 failing block search test cases
- [ ] Enable block search after edge cases resolved
- [ ] Add slice edge wing pairing
- [ ] Add last layer solving