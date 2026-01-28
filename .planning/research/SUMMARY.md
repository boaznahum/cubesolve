# Research Summary: L3 Edge Fix for Big-LBL

## Key Findings

### The Problem
`_solve_layer3_edges()` calls `NxNEdges.solve_face_edges()` which:
1. Uses `bring_edge_to_front_right_preserve_front_left` - contains **D turns** that destroy L1
2. Uses `rf` algorithm (`R F' U R' F`) - destroys **middle edge wings**
3. Uses **E-slice** moves - disturbs middle edges at specific depths

### The Solution Already Exists
`_LBLNxNEdges.py` has the correct commutator pattern that preserves lower layers:

**Right-side insertion (FR target):**
```
U  R  U'  M[k]'  U  R'  U'  M[k]
```

**Left-side insertion (FL target):**
```
U'  L'  U  M[k]'  U'  L  U  M[k]
```

Why it works:
- R and R' cancel (net-zero effect on FR/BR middle edges)
- M[k] and M[k]' cancel (net-zero effect on L1 edges)
- Only U rotations remain free

### Safe vs Unsafe Moves

| Move | L1 Edges | Middle Edges | Use for L3? |
|------|----------|--------------|-------------|
| U | SAFE | SAFE | YES (free) |
| D | DESTROYS | SAFE | NEVER |
| R, L | SAFE | CONDITIONAL | Only with R'/L' |
| F, B | DESTROYS DF/DB | CONDITIONAL | Avoid |
| M[i] | DESTROYS | SAFE | Only with M[i]' |
| E[i] | SAFE | DESTROYS | NEVER for L3 |

### Fix Strategy

**Option A (Recommended):** Make `solve_face_edges` aware of preservation mode
- Add flag: `preserve_lower_layers=False`
- When True, use `_LBLNxNEdges`-style commutators instead of `rf`

**Option B:** Create dedicated L3 edge solver
- New method `solve_l3_face_edges()` that only uses safe moves
- Reuses the FL/FR commutator from `_LBLNxNEdges`

**Option C (Quick path):** Re-solve middle after L3 edges
- Like parity handling - accept destruction then re-solve
- More moves but simpler code change

## Files to Modify

| File | Change |
|------|--------|
| `NxNEdges.py` | Add L3-safe mode or new method |
| `LayerByLayerNxNSolver.py` | Call L3-safe method |
| `_LBLNxNEdges.py` | Reference for correct commutators |

## Test Script Requirements

1. Create 5x5 cube with seed "0" scramble
2. Solve L1 + middle slices + L3 centers
3. Snapshot all non-L3 edges
4. Run L3 edge solving
5. Assert non-L3 edges unchanged

## Guard Assertions

Add after each move in L3 edge solving:
```python
assert self._verify_lower_layers_intact(snapshot), \
    f"Move {move} disturbed lower layers"
```
