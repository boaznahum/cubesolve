# Cage Solver TODO

## Current Status

### Phase 1a: Edge Solving - DONE
- Reuses `NxNEdges` from beginner solver
- Edge parity handled inside `NxNEdges.solve()`
- Works for both odd and even cubes

### Phase 1b: Corner Solving - DONE
- Uses `Solvers3x3.by_name(config.cage_3x3_solver)` to solve the "virtual 3x3"
- 3x3 solver choice configurable via `cube.config.cage_3x3_solver` (default: "beginner")
- Access via ConfigProtocol (not `_config` directly) - see `config_protocol.py`
- After edges are paired, 3x3 solver positions corners AND edges correctly
- **ODD CUBES ONLY** - face center defines face color
- **Beginner solver works, CFOP does NOT** (see bug below)

### Phase 2: Center Solving - TODO (NEXT SESSION)
- Need commutators that preserve edges/corners
- Centers remain scrambled after Phase 1b
- See DESIGN.md for commutator approach

---

## LIMITATION: Even Cubes Not Supported

**Problem:** Even cubes (4x4, 6x6) have NO fixed center piece.
- Face color is undefined until we establish it
- 3x3 solver uses `face.center.color` which doesn't work for even cubes
- Would need `FaceTracker` pattern to establish color mapping first

**Future Work:**
1. Before Phase 1b, establish face color mapping for even cubes
2. Use `FaceTracker` from `NxNCenters` as reference
3. Or: solve one center face first to establish reference color

---

## Parity Handling Summary

### Edge Parity (Phase 1a)
Handled INSIDE `NxNEdges.solve()`:
1. Solves 11 edges via `_do_first_11()`
2. If 1 edge left unsolved → parity detected
3. Calls `_do_last_edge_parity()` to fix (M-slice algorithm)
4. Re-solves remaining edges
5. Returns `True` if parity was detected/fixed

### Corner/Edge Parity (Phase 1b)
The 3x3 solver may encounter parity on even cubes:
- `EvenCubeEdgeParityException` - 1 or 3 edges flipped
- `EvenCubeCornerSwapException` - 2 corners in position

Since we only support ODD cubes for now, these shouldn't occur.

---

## TODO: advanced_edge_parity Flag
Currently using `advanced_edge_parity=False` (M-slice algorithm).
Consider switching to `True` (R/L-slice algorithm) which:
- Preserves edge pairing better
- May be better for cage method

---

## BUG: CFOP Solver Fails on Big Cubes with Scrambled Centers

**Status:** Confirmed - CFOP fails, Beginner works

**Symptom:** When using CFOP solver for Phase 1b on 5x5/7x7:
- `F2L.solve()` fails with `assert self.solved()` at line 151
- `self.solved()` calls `_l1_l2_solved()` which checks `wf.solved` (white face)
- `Face.solved` returns `False` because `is3x3=False` (centers scrambled)

**Root Cause:** `Face.solved` (line 377-378) has early return:
```python
def solved(self):
    if not self.is3x3:
        return False  # Always false when centers scrambled!
```

**Why Beginner Works but CFOP Doesn't:**
- Beginner solver doesn't use `Face.solved` in the same way
- CFOP's F2L explicitly checks `face.solved` in its completion assertion

**Fix Options (for future CFOP support):**
1. Modify `Face.solved` to have a `virtual_3x3` mode
2. Add `Face.solved_as_3x3` method that ignores center state
3. Modify CFOP's `_l1_l2_solved()` to use different check for big cubes

**Current Workaround:** Use `CAGE_3X3_SOLVER = "beginner"` (default)
