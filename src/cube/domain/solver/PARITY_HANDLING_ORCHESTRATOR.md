# Parity Error Handling in CubeSolve (NxN Orchestrator)

> **Reference Design**: Old `BeginnerSolver` from commit `378bc87` on branch `claude/learn-project-structure-01WYYtkueCTRzNjpBziMJtBB`
> **See**: `PARITY_HANDLING_BEFORE_ORCHESTRATOR.md` for the original design analysis
> **Current Branch**: `p314` with `src/cube/domain/solver/` structure

This document describes how the `NxNSolverOrchestrator` implements the **same parity handling logic** that was originally in the monolithic `BeginnerSolver`. The design decisions documented in `PARITY_HANDLING_BEFORE_ORCHESTRATOR.md` (based on the old `cube/solver/begginer/beginner_solver.py`) are preserved here.

**Key insight**: The orchestrator is a **refactoring** of the old BeginnerSolver, not a new design. The parity handling logic (why we retry, why corner is fixed immediately, why edge can be fixed anytime) comes directly from the old code.

---

## Table of Contents

1. [Architecture Evolution](#architecture-evolution)
2. [The Orchestrator Pattern](#the-orchestrator-pattern)
3. [Why Parity Still Requires Retries](#why-parity-still-requires-retries)
4. [The Solve Algorithm](#the-solve-algorithm)
5. [Pseudo Code](#pseudo-code)
6. [Edge Parity Handling](#edge-parity-handling)
7. [Corner Parity Handling](#corner-parity-handling)
8. [Why Corner Fix Happens Immediately But Edge Fix Doesn't](#why-corner-fix-happens-immediately-but-edge-fix-doesnt)
9. [Parity Detection for Non-Detecting Solvers](#parity-detection-for-non-detecting-solvers)
10. [Key Files Reference](#key-files-reference)

---

## Architecture Evolution

### Before: Monolithic BeginnerSolver

The original `BeginnerSolver` was a single class handling everything:
- NxN reduction (centers + edges)
- 3x3 layer-by-layer solving
- Parity detection and recovery

```
BeginnerSolver (monolithic)
├── nxn_centers, nxn_edges  (reduction)
├── l1_cross, l1_corners, l2, l3_cross, l3_corners  (3x3 solving)
└── Retry loop for parity handling
```

### After: Orchestrator Pattern

The new design separates concerns:

```
NxNSolverOrchestrator
├── Reducer (ReducerProtocol)
│   └── BeginnerReducer: centers, edges, parity fix algorithms
├── 3x3 Solver (Solver3x3Protocol)
│   └── BeginnerSolver3x3, CFOP3x3, or Kociemba3x3
└── Parity handling retry loop
```

**Benefits:**
- Any reducer can work with any 3x3 solver
- Parity handling in one place (orchestrator)
- Easy testing of reducers and solvers independently
- Clear separation of responsibilities

---

## The Orchestrator Pattern

### Composition over Inheritance

```python
class NxNSolverOrchestrator(AbstractSolver):
    def __init__(self, op, reducer: ReducerProtocol, solver_3x3: Solver3x3Protocol):
        self._reducer = reducer        # Handles NxN → 3x3
        self._solver_3x3 = solver_3x3  # Handles 3x3 solving
```

### Protocol-Based Design

```
ReducerProtocol:
    - reduce() → ReductionResults
    - fix_edge_parity()
    - fix_corner_parity()

Solver3x3Protocol:
    - solve_3x3()
    - can_detect_parity: bool
```

---

## Why Parity Still Requires Retries

The fundamental problem remains the same:

### Edge Parity (Full Even - OLL Parity)

On even cubes, after reduction, ALL slices of an edge might be flipped. This is **undetectable during edge pairing** (no center slice reference).

Detected during L3 Cross when 1 or 3 edges appear flipped.

### Corner Parity (PLL Parity)

On even cubes, exactly 2 corners in position (impossible on 3x3).

Detected during L3 Corners.

### Solution: Exception + Retry

Same approach as before:
1. Try to solve
2. Catch parity exception → fix → re-reduce → retry

---

## The Solve Algorithm

### Location: `src/cube/domain/solver/NxNSolverOrchestrator.py`

```python
def _solve(self, debug: bool, what: SolveStep) -> SolverResults:
    # Step 1: Reduce NxN to 3x3
    self._reducer.reduce(debug)

    # Step 2: Solve as 3x3 with parity handling
    # Retry loop catches parity exceptions
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            self._solver_3x3.solve_3x3(debug, what)
        except EvenCubeEdgeParityException:
            self._reducer.fix_edge_parity()
            self._reducer.reduce(debug)  # Re-reduce after fix
            continue
        except EvenCubeCornerSwapException:
            # May need to call fix_corner_parity() if using parity detector
            self._reducer.reduce(debug)  # Re-reduce after fix
            continue
```

---

## Pseudo Code

```
FUNCTION orchestrator_solve(cube, what=ALL):

    results = new SolverResults()

    IF cube.is_solved:
        RETURN results

    # Parity tracking flags
    edge_parity_detected = FALSE
    corner_parity_detected = FALSE
    partial_edge_parity = FALSE

    # Step 1: Reduce NxN to 3x3
    reduction_results = reducer.reduce()
    partial_edge_parity = reduction_results.partial_edge_parity_detected

    # Step 2: Determine if we need a parity detector
    # Some solvers (like Kociemba) can't detect parity themselves
    is_even_cube = cube.n_slices % 2 == 0
    use_parity_detector = is_even_cube AND NOT solver_3x3.can_detect_parity

    IF use_parity_detector:
        parity_detector = BeginnerSolver3x3()  # Can detect parity via exceptions
    ELSE:
        parity_detector = NULL

    # Step 3: Main retry loop
    FOR attempt IN [1, 2, 3]:

        IF cube.is_solved:
            BREAK

        TRY:
            IF parity_detector IS NOT NULL:
                # Use query mode: detect parity without modifying cube
                # Then let actual solver solve
                WITH query_restore_state():
                    WITH dont_fix_corner_parity():
                        parity_detector.solve_3x3()
                # No exception = no parity, state restored
                solver_3x3.solve_3x3()
            ELSE:
                # Solver can detect parity itself
                solver_3x3.solve_3x3()

        CATCH EvenCubeEdgeParityException:
            IF edge_parity_detected:
                # Already fixed - fall back to known solver
                IF parity_detector:
                    parity_detector.solve_3x3()
                    BREAK
                THROW InternalSWError("Edge parity detected twice!")

            edge_parity_detected = TRUE
            reducer.fix_edge_parity()  # Fix via reducer
            reducer.reduce()           # Re-reduce (fix disturbs edges)
            CONTINUE                   # Retry

        CATCH EvenCubeCornerSwapException:
            IF corner_parity_detected:
                THROW InternalSWError("Corner parity detected twice!")

            corner_parity_detected = TRUE

            # KEY DIFFERENCE FROM OLD DESIGN:
            # If using parity detector (query mode with dont_fix_corner_parity),
            # the corner swap was NOT done by the solver - orchestrator must do it
            IF parity_detector IS NOT NULL:
                reducer.fix_corner_parity()

            reducer.reduce()  # Re-reduce (fix disturbs edges)
            CONTINUE          # Retry

    RETURN results
```

---

## Edge Parity Handling

### Two Different Cases: Odd vs Even Cubes

Edge parity is handled **differently** depending on cube size:

| Cube Type | When Handled | Where Handled | Exception? |
|-----------|--------------|---------------|------------|
| **Odd (5x5, 7x7)** | During reduction | `NxNEdges.solve()` in reducer | No |
| **Even (4x4, 6x6)** | During 3x3 solve | L3Cross → Orchestrator | Yes |

---

## Odd Cube Edge Parity (Handled in Reducer)

### Why Odd Cubes Are Different

On odd cubes, the **center slice of each edge is fixed** - it cannot be flipped. This gives us a reference point during edge pairing:

```
5x5 Edge cross-section:
  [slice 0][slice 1][CENTER][slice 3][slice 4]
                       ↑
            Fixed reference - cannot be flipped
```

### Detection During Edge Pairing

The reducer's `NxNEdges.solve()` detects parity when exactly **1 edge remains unsolved** after pairing 11 edges:

```python
# In BeginnerReducer._nxn_edges.solve()
def solve(self) -> bool:
    self._do_first_11()            # Pair first 11 edges

    if self._is_solved():
        return False               # All 12 paired - no parity

    assert self._left_to_fix == 1   # 1 remaining = PARITY

    self._do_last_edge_parity()     # Fix using simple or advanced algo

    self._do_first_11()             # Re-pair if needed

    return True                     # Signal: parity was fixed
```

### The Two Fix Algorithms

**Controlled by `advanced_edge_parity` flag in reducer construction:**

#### Simple Algorithm (`advanced_edge_parity=False`)

```python
# M-slice based - fast but disturbs edge pairing
for _ in range(4):
    M'[inner_slices] U2
M'[inner_slices]
```

**After fix**: Some edges become unpaired → `_do_first_11()` re-pairs them.

#### Advanced Algorithm (`advanced_edge_parity=True`)

```python
# R/L-slice based - preserves edge pairing
# From https://speedcubedb.com/a/6x6/6x6L2E
Rw' U2 Lw F2 Lw' F2 Rw2 U2 Rw U2 Rw' U2 F2 Rw2 F2
```

**After fix**: Edges remain paired → `_do_first_11()` finds nothing to do.

### Flow in Orchestrator

```
Orchestrator._solve()
    │
    ├─→ reducer.reduce()
    │       │
    │       ├─→ solve_centers()
    │       │
    │       └─→ solve_edges()  ←── ODD CUBE PARITY HANDLED HERE
    │               │
    │               ├─ Pair 11 edges
    │               ├─ If 1 remaining: FIX PARITY (no exception!)
    │               ├─ Re-pair if needed (simple algo)
    │               └─ Return True if parity was fixed
    │
    └─→ solver_3x3.solve_3x3()  ←── Cube is already parity-free
```

**Key point**: Orchestrator never sees odd cube parity - it's fully handled inside the reducer. The `reduce()` method returns `ReductionResults.partial_edge_parity_detected = True` for tracking.

---

## Even Cube Edge Parity (Handled by Orchestrator)

### Why Even Cubes Need Special Handling

On even cubes (4x4, 6x6), there's **no center slice** - all slices can be flipped:

```
4x4 Edge cross-section:
  [slice 0][slice 1][slice 2][slice 3]
         ↑
  No fixed reference - ALL could be flipped!
```

If all slices are flipped identically, the edge **appears paired** during reduction but is actually "wrong" relative to the 3x3 structure.

### Detection in L3Cross

Same as before - L3Cross counts edges matching yellow face:
- If n ∈ {0, 2, 4}: Valid 3x3 state
- If n ∈ {1, 3}: Invalid → `EvenCubeEdgeParityException`

### Fix by Orchestrator

**Orchestrator catches exception and calls:**
```python
self._reducer.fix_edge_parity()  # Flips all inner slices of any edge
self._reducer.reduce(debug)       # Re-reduce (fix disturbs pairing)
```

The fix is **position-independent** - can be done on any edge at any time.

### Flow in Orchestrator

```
Orchestrator._solve()
    │
    ├─→ reducer.reduce()
    │       │
    │       └─→ solve_edges() returns False (no parity detected)
    │           # Even cube full parity is INVISIBLE during pairing!
    │
    └─→ solver_3x3.solve_3x3()
            │
            └─→ L3Cross detects 1 or 3 edges flipped
                    │
                    └─→ Raises EvenCubeEdgeParityException
                            │
    ┌───────────────────────┘
    │
    ▼ (catch in orchestrator)
    reducer.fix_edge_parity()   # Flip all inner slices
    reducer.reduce()            # Re-reduce (edges disturbed)
    RETRY solve_3x3()           # Now parity-free
```

---

## Summary: Edge Parity Handling

| Aspect | Odd Cube | Even Cube |
|--------|----------|-----------|
| **Reference point** | Center slice (fixed) | None |
| **When detected** | During edge pairing | During L3Cross |
| **Who detects** | Reducer (NxNEdges) | 3x3 Solver (L3Cross) |
| **Exception?** | No | Yes (`EvenCubeEdgeParityException`) |
| **Who fixes?** | Reducer (internally) | Orchestrator → Reducer |
| **Re-reduction** | Maybe (simple) / No (advanced) | Always |
| **Algorithm** | Simple OR Advanced (configurable) | Full edge flip only |

---

## Corner Parity Handling

### Detection

Same as before - L3Corners counts corners in position:
- If n = 2: Parity → raise `EvenCubeCornerSwapException`

### Unified Pattern (Same as Edge Parity)

```python
# In L3Corners:
if n == 2:
    raise EvenCubeCornerSwapException()  # Just signal, don't fix

# Orchestrator catches and fixes via reducer:
except EvenCubeCornerSwapException:
    self._reducer.fix_corner_parity()  # Fix here
    self._reducer.reduce(debug)         # Re-reduce
    continue  # Retry
```

This matches the edge parity pattern exactly - both parities use:
detector raises → orchestrator catches → reducer fixes → re-reduce → retry

---

## Corner Swap vs Edge Flip - Both Work in 3x3 State

> **UPDATE (2025-12-16):** Testing on real cubes confirmed that both algorithms
> work as long as the cube is in 3x3 state (yellow up). The corner swap is NOT
> truly "position-sensitive" - any diagonal swap fixes parity regardless of Y rotation.

### Corner Swap Algorithm

```python
# From BeginnerReducer.fix_corner_parity() → L3Corners._do_corner_swap()
alg = R[2:nh+1]×2  U×2
      R[2:nh+1]×2  U[1:nh+1]×2
      R[2:nh+1]×2  U[1:nh+1]×2
```

This swaps **diagonal corners** on the U face. After Y rotation:
- Yellow is still up (Y rotates around up axis)
- Different corners are in R-side positions, so different diagonal pair gets swapped
- But **any diagonal swap** flips corner permutation parity from odd to even

**Conclusion:** Works with any Y rotation. Only requirement is yellow stays up.

### Edge Flip Algorithm

```python
def fix_edge_parity(self) -> None:
    self._nxn_edges.do_even_full_edge_parity_on_any_edge()
    # Flips any edge at FU position
```

Can be done on any edge.

### Unified Pattern (Implemented 2025-12-16)

Both edge and corner parity now use the same clean pattern:
1. Detector raises exception (L3Cross / L3Corners)
2. Orchestrator catches
3. Reducer fixes (`fix_edge_parity()` / `fix_corner_parity()`)
4. Re-reduce and retry

The old asymmetry (L3Corners fixing before throwing) and the `dont_fix_corner_parity`
flag have been removed. The code is now consistent and simpler.

---

## Parity Detection for Non-Detecting Solvers

### The Problem

Some 3x3 solvers (like Kociemba two-phase algorithm) cannot detect parity:
- They use mathematical approaches that fail silently on parity states
- Or they might produce very long solutions for "impossible" states

### The Solution: Query Mode with Parity Detector

```python
if use_parity_detector:
    with self._op.with_query_restore_state():  # Save state, restore after
        parity_detector.solve_3x3(debug, what)
    # If no exception: no parity, state restored
    # If exception: state restored, orchestrator handles fix
    self._solver_3x3.solve_3x3(debug, what)  # Now let actual solver work
```

With the unified parity handling pattern, L3Corners always just throws without fixing.
The orchestrator catches the exception and calls `reducer.fix_corner_parity()` on
the restored state. No special flag needed.

---

## Summary: Orchestrator vs Old BeginnerSolver

| Aspect | Old BeginnerSolver | NxNSolverOrchestrator |
|--------|-------------------|----------------------|
| **Architecture** | Monolithic | Composed (Reducer + Solver3x3) |
| **Parity loop** | In solver | In orchestrator |
| **Edge parity fix** | `nxn_edges.do_even_full_edge_parity_on_any_edge()` | `reducer.fix_edge_parity()` |
| **Corner parity fix** | In L3Corners before throw | Orchestrator via `reducer.fix_corner_parity()` |
| **Non-detecting solvers** | N/A | Query mode with parity detector |
| **Flexibility** | Fixed LBL method | Any reducer + any 3x3 solver |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `NxNSolverOrchestrator.py` | Main orchestrator with parity retry loop |
| `protocols/ReducerProtocol.py` | Reducer interface with `fix_edge_parity()`, `fix_corner_parity()` |
| `protocols/Solver3x3Protocol.py` | 3x3 solver interface with `can_detect_parity` |
| `reducers/BeginnerReducer.py` | Standard reducer implementation |
| `beginner/BeginnerSolver3x3.py` | Pure 3x3 LBL solver |
| `beginner/L3Cross.py` | Edge parity detection |
| `beginner/L3Corners.py` | Corner parity detection and fix |
| `beginner/NxNEdges.py` | Edge parity algorithms |

---

## Flow Diagram

```
Start
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  REDUCE: reducer.reduce()                                   │
│  ┌─────────┐   ┌─────────────────────────────────────────┐ │
│  │ Centers │ → │ Edges (partial parity handled silently) │ │
│  └─────────┘   └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  SOLVE 3x3: solver_3x3.solve_3x3()                         │
│  (or parity_detector.solve_3x3() in query mode first)       │
│                                                              │
│  ┌────┐   ┌────┐   ┌─────────┐   ┌───────────┐             │
│  │ L1 │ → │ L2 │ → │ L3Cross │ → │ L3Corners │             │
│  └────┘   └────┘   └────┬────┘   └─────┬─────┘             │
│                         │              │                    │
│              EvenCubeEdgeParity?    EvenCubeCornerSwap?     │
└─────────────────────────┼──────────────┼────────────────────┘
                          │              │
       ┌──────────────────┴──────────────┴──────────────┐
       │                                                │
       ▼                                                ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│ reducer.fix_edge_parity │              │ reducer.fix_corner_parity│
│ (any edge, any time)    │              │ (if using parity detector)│
└───────────┬─────────────┘              └───────────┬─────────────┘
            │                                        │
            └────────────────┬───────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ reducer.reduce()│ Re-reduce (fix disturbs edges)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  RETRY SOLVE    │
                    └────────┬────────┘
                             │
                             ▼
                          SOLVED
```

---

## Why Three Iterations Maximum?

Same reasoning as old design:

| Iteration | What Might Happen |
|-----------|-------------------|
| 1 | Normal solve OR edge parity detected |
| 2 | After edge parity fix: normal solve OR corner parity detected |
| 3 | After corner parity fix: should complete |

Each parity type can only occur once. Detecting same parity twice = bug.
