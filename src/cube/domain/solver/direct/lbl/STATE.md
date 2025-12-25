# Layer-by-Layer NxN Solver - State

## Current Status (2025-12-25)

**Working:** Odd cubes (5x5, 7x7, etc.) - Layer 1 complete
**In Progress:** Layer 2 centers design

## Implemented Steps

| Step | Status | Description |
|------|--------|-------------|
| LBL_L1_Ctr | ✅ Working | Layer 1 centers only |
| L1x | ✅ Working | Layer 1 cross (centers + edges paired + edges positioned) |
| LBL_L1 | ✅ Working | Layer 1 complete (centers + edges + corners) |
| LBL_SLICES_CTR | 🔄 WIP | Middle slices centers (placeholder) |

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

---

## Middle Slice Design Progress (2025-12-25)

### Coordinate System Understanding ✅

**Slice indices are 0-based:** `slice_index = 0 to n_slices-1`

| Slice Index | Row Index on Side Faces | Position |
|-------------|------------------------|----------|
| 0 | n_slices - 1 (bottom) | Closest to D |
| 1 | n_slices - 2 | Middle |
| n_slices - 1 | 0 (top) | Closest to U |

**Formula:** `row_index = n_slices - 1 - slice_index`

Example for 5x5 (n=5, n_slices=3):
- slice 0 → row 2 (bottom, closest to D)
- slice 1 → row 1 (middle)
- slice 2 → row 0 (top, closest to U)

### Challenges Identified ✅

1. **Partial Face Solving**: Need `solve_slice_centers()` not `solve_single_face()`
2. **Move Restrictions**: D face cannot rotate after Layer 1 solved
3. **Source Centers**: Must come from U face or unsolved rows on side faces
4. **Face Orientation**: 4 faces to solve simultaneously (the ring)
5. **Even Cube Tracking**: FaceTracker handles this

### Proposed Approach ✅

1. Calculate row index for slice: `row = n_slices - 1 - slice_index`
2. For each side face (F, R, B, L):
   - Check which centers in that row need fixing
   - Find source center (from U or rows above current slice)
   - Use adapted commutator to move piece
3. Solve slices in order: 0, 1, 2, ... n_slices-1 (bottom to top)

### Implemented (2025-12-25)

- [x] Add `SolveStep.LBL_SLICES_CTR` enum value
- [x] Create `_LBLSlices` helper class wrapping NxNCenters + NxNEdges
  - `slice_to_row()` / `row_to_slice()` - coordinate conversion
  - `get_side_face_trackers()` - get 4 side face trackers
  - `is_slice_centers_solved()` - check single slice
  - `count_solved_slice_centers()` - count consecutive solved
  - `solve_slice_centers()` / `solve_all_slice_centers()` - placeholders
- [x] Update `status()` to show "L1:Done|Sl:X/N" format
- [x] Integrate `_LBLSlices` into `LayerByLayerNxNSolver`

### Next Steps

- [ ] Study `NxNCenters._block_communicator()` for adaptation
- [ ] Implement actual solving logic in `_solve_single_slice_centers()`
- [ ] Write tests for slice center solving

---

## TODO - Future Layers

### Middle Slices (0 to n_slices-1) - In Progress
- [x] Understand coordinate mapping (slice_index → row_index)
- [x] Identify challenges
- [x] Document approach in DESIGN.md
- [x] Add SolveStep.LBL_SLICES_CTR enum
- [x] Add placeholder methods and status reporting
- [ ] **Centers**: Implement actual solving logic in `_solve_single_slice_centers()`
- [ ] **Edge wings**: Pair the 4 edge wings at each slice level
- [ ] **Loop**: Solve all slices 0 → n_slices-1

### Last Layer (U face)
- [ ] U-face centers (restricted moves - only U, u available)
- [ ] U-face edges (OLL-style)
- [ ] U-layer corners (PLL-style)
- [ ] Parity handling for even cubes

### General
- [ ] Even cube support: Verify FaceTracker works correctly
- [ ] Performance optimization

## Files

- `LayerByLayerNxNSolver.py` - Main solver
- `_LBLSlices.py` - Helper wrapping NxNCenters + NxNEdges for slice operations
- `DESIGN.md` - Detailed design including Layer 2 planning
- `NxNCenters.solve_single_face()` - Single face center solving
- `NxNEdges.solve_face_edges()` - Face edge solving
- `FacesTrackerHolder` - Manages face trackers
- `_FaceTracker` - Tracks face by color
