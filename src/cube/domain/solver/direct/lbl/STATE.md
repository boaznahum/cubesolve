# Layer-by-Layer NxN Solver - State

## Current Status (2024-12-24)

**Working:** Odd cubes (5x5, 7x7, etc.) - Layer 1 complete

## Implemented Steps

| Step | Status | Description |
|------|--------|-------------|
| LBL_L1_Ctr | ✅ Working | Layer 1 centers only |
| L1x | ✅ Working | Layer 1 cross (centers + edges paired + edges positioned) |
| LBL_L1 | ✅ Working | Layer 1 complete (centers + edges + corners) |

## Architecture

### Layer 1 Solving Flow

1. **Centers** (`_solve_layer1_centers`)
   - Uses `NxNCenters.solve_single_face()` with FaceTracker
   - Solves only the Layer 1 face centers

2. **Edges - Pairing** (`_solve_layer1_edges`)
   - Uses `NxNEdges.solve_face_edges()` with FaceTracker
   - Pairs edge wings (reduces to 3x3)
   - Only targets 4 edges adjacent to Layer 1 face

3. **Edges - Positioning** (`_solve_layer1_cross`)
   - Uses shadow 3x3 cube with `DualOperator`
   - Calls `Solvers3x3.beginner()` with `SolveStep.L1x`
   - Positions edges correctly (cross on Layer 1)

4. **Corners** (`_solve_layer1_corners`)
   - Uses shadow 3x3 cube with `DualOperator`
   - Calls `Solvers3x3.beginner()` with `SolveStep.L1`
   - Solves Layer 1 corners

### Key Design Decisions

- **FaceTracker**: All methods use `FaceTracker` to track Layer 1 face by COLOR (not position)
- **config.first_face_color**: Determines Layer 1 color (default: WHITE)
- **Shadow 3x3**: Used for corner/cross solving via `DualOperator`

## Known Issues

- **#49 CRITICAL**: `CommonOp.white_face` is hardcoded - will break when changing first layer
- **Even cubes**: Not yet tested - edge color detection may need work

## TODO - Future Layers

- [ ] Layer 2 to n-1 (middle slices): centers + edge wings
- [ ] Layer n (opposite face): like Layer 1 but restricted moves
- [ ] Even cube support: verify FaceTracker works correctly
- [ ] Parity handling for partial solves

## Files

- `LayerByLayerNxNSolver.py` - Main solver
- `NxNCenters.solve_single_face()` - Single face center solving
- `NxNEdges.solve_face_edges()` - Face edge solving
- `FacesTrackerHolder` - Manages face trackers
- `_FaceTracker` - Tracks face by color
