# Cage Solver TODO

## Current Status

### Phase 1a: Edge Solving - DONE
- Reuses `NxNEdges` from beginner solver
- Edge parity handled inside `NxNEdges.solve()`
- Works for both odd and even cubes

### Phase 1b: Corner Solving - DONE
- Uses **shadow cube approach** for both odd and even cubes:
  1. Build a virtual 3x3 "shadow cube"
  2. Copy corner/edge positions from real cube
  3. Solve the shadow cube with a 3x3 solver
  4. Apply the solution algorithm to the real cube
- **Odd cubes**: Use face center color for face color mapping
- **Even cubes**: Use `FaceTracker` to establish face colors from majority colors
- **Even cube solver**: Uses beginner solver (not CFOP) to avoid parity oscillation

### Phase 2: Center Solving - DONE
- Uses `CageCenters` which wraps `NxNCenters`
- Face color mapping from Phase 1b trackers
- Preserves edges and corners

---

## Even Cube Support - IMPLEMENTED

Even cubes (4x4, 6x6) are now fully supported:

1. **Face color mapping**: Uses `FaceTracker` pattern to establish colors
2. **Shadow cube approach**: Same as odd cubes but with tracked colors
3. **Parity handling**: Uses beginner solver to avoid OLL/PLL parity oscillation

---

## Parity Handling Summary

### Edge Parity (Phase 1a)
Handled INSIDE `NxNEdges.solve()`:
1. Solves 11 edges via `_do_first_11()`
2. If 1 edge left unsolved → parity detected
3. Calls `_do_last_edge_parity()` to fix (M-slice algorithm)
4. Re-solves remaining edges
5. Returns `True` if parity was detected/fixed

### Parity (Phase 1b) - Even Cubes Only
On even cubes, the shadow cube may have "impossible" 3x3 states:

1. **OLL Edge Parity** (`EvenCubeEdgeParityException`): 1 or 3 edges flipped
2. **PLL Corner Parity** (`EvenCubeCornerSwapException`): 2 corners need swap
3. **PLL Edge Swap Parity** (`EvenCubeEdgeSwapParityException`): 2 edges need swap

**Solution**: Use **beginner solver** for even cube shadow cubes.
- CFOP detects these parities and raises exceptions
- The exceptions cause fix → re-pair → new parity oscillation
- Beginner solver handles these states without raising exceptions

---

## TODO: advanced_edge_parity Flag
Currently using `advanced_edge_parity=False` (M-slice algorithm).
Consider switching to `True` (R/L-slice algorithm) which:
- Preserves edge pairing better
- May be better for cage method

---

## TODO: Centralize Animation Handling

**Status:** Fixed for cage solver (uses `with_animation()` wrapper)

**Current approach:** Each solver wraps its logic in `with self._op.with_animation(animation):`
- Works but requires every solver to remember to do this
- Duplicated pattern across all solvers

**Better approach (future):**
- Handle animation at a higher level (command layer or operator)
- So solvers don't need to care about animation parameter
- Single point of control for animation enable/disable

---

## FIXED: CFOP Solver for Odd Cubes

**Status:** FIXED - CFOP now works for odd cubes (5x5, 7x7)

**Solution:** Added `ignore_center_check=True` parameter to `Solvers3x3.by_name()`.
When set, CFOP's F2L uses `Part.match_faces` instead of `Face.solved` for validation.

**Current Configuration:**
- **Odd cubes**: CFOP (configurable via `cage_3x3_solver`)
- **Even cubes**: Beginner (hardcoded to avoid parity oscillation)
