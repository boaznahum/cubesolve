# Parity Error Handling in CubeSolve (Before NxN Orchestrator)

> **Explored Code Commit**: `378bc87` (Document GUI abstraction migration state)
> **Branch**: `claude/learn-project-structure-01WYYtkueCTRzNjpBziMJtBB`
> **Codebase Structure**: `cube/` (legacy structure before `src/cube/` refactor)

This document describes the parity handling approach used **before** the introduction of the `NxNSolverOrchestrator` pattern. In this design, `BeginnerSolver` handles both NxN reduction and 3x3 solving in a single class with a retry loop for parity.

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [The Problem: Why Parity Requires Retries](#the-problem-why-parity-requires-retries)
3. [Architecture Overview](#architecture-overview)
4. [The Main Solve Algorithm](#the-main-solve-algorithm)
5. [Pseudo Code](#pseudo-code)
6. [Edge Parity Handling](#edge-parity-handling)
7. [Corner Parity Handling](#corner-parity-handling)
8. [Why Corner Fix Happens Immediately But Edge Fix Doesn't](#why-corner-fix-happens-immediately-but-edge-fix-doesnt)
9. [Why Three Iterations?](#why-three-iterations)
10. [Key Files Reference](#key-files-reference)

---

## Design Philosophy

The `BeginnerSolver` class is a **monolithic solver** that handles:
1. NxN reduction (centers + edges) for big cubes
2. 3x3 layer-by-layer solving (L1 → L2 → L3)
3. Parity detection and recovery via exceptions and retry

**Key design decisions:**
- Parity is detected **during** the solve (not before)
- Detection happens via **exceptions** thrown by L3Cross and L3Corners
- Recovery uses a **retry loop** - fix the parity and restart the solve
- The solver doesn't know in advance if parity will occur

---

## The Problem: Why Parity Requires Retries

### Edge Parity (Full Even - OLL Parity)

On even cubes (4x4, 6x6), after reduction, ALL slices of an edge might be flipped the same way. This is **undetectable during edge pairing** because there's no reference point (no center slice).

The problem only becomes visible during **L3 Cross** when we see 1 or 3 edges flipped (impossible on a real 3x3).

**Solution flow:**
1. L3Cross detects impossible state → raises `EvenCubeEdgeParityException`
2. Solver catches exception → calls `nxn_edges.do_even_full_edge_parity_on_any_edge()`
3. This disturbs the reduction → need to re-reduce and re-solve

### Corner Parity (PLL Parity)

On even cubes, we might end up with exactly 2 corners in position (impossible on 3x3).

**Solution flow:**
1. L3Corners detects impossible state → performs corner swap → raises `EvenCubeCornerSwapException`
2. The swap disturbs edges → need to re-reduce and re-solve

---

## Architecture Overview

```
BeginnerSolver
├── Components:
│   ├── nxn_centers: NxNCenters    # Reduction: solve centers
│   ├── nxn_edges: NxNEdges        # Reduction: pair edges + partial parity
│   ├── l1_cross: L1Cross          # 3x3: white cross
│   ├── l1_corners: L1Corners      # 3x3: white corners
│   ├── l2: L2                     # 3x3: middle layer
│   ├── l3_cross: L3Cross          # 3x3: yellow cross (detects edge parity)
│   └── l3_corners: L3Corners      # 3x3: yellow corners (detects corner parity)
│
├── solve() method:
│   └── Retry loop (max 3 iterations)
│       ├── Try: _reduce() → _l1() → _l2() → _l3()
│       ├── Catch EvenCubeEdgeParityException → fix → retry
│       └── Catch EvenCubeCornerSwapException → retry (already fixed)
│
└── Result tracking:
    ├── was_even_edge_parity
    ├── was_corner_swap
    └── was_partial_edge_parity
```

---

## The Main Solve Algorithm

### Location: `cube/solver/begginer/beginner_solver.py:111-226`

The `_solve()` method implements a **nested function pattern** where each layer builds on the previous:

```python
def _centers():    # Solve NxN centers
def _edges():      # Pair NxN edges (may detect partial parity)
def _reduce():     # _centers() + _edges()
def _l1x():        # _reduce() + L1 cross
def _l1():         # _l1x() + L1 corners
def _l2():         # _l1() + L2 edges
def _l3x():        # _l2() + L3 cross (may raise EvenCubeEdgeParityException)
def _l3():         # _l3x() + L3 corners (may raise EvenCubeCornerSwapException)
```

This nesting means that when parity is detected and we retry, **the entire solve restarts from the beginning**, including re-reduction.

---

## Pseudo Code

```
FUNCTION solve(cube, what=ALL):

    results = new SolverResults()

    IF cube.is_solved:
        RETURN results

    # Parity tracking flags
    edge_parity_detected = FALSE
    corner_parity_detected = FALSE
    partial_edge_parity = FALSE

    # Nested solve functions (each builds on previous)
    FUNCTION reduce():
        solve_nxn_centers()
        partial_edge_parity = solve_nxn_edges()  # Returns TRUE if last-edge parity fixed

    FUNCTION solve_l1():
        reduce()
        solve_l1_cross()
        solve_l1_corners()

    FUNCTION solve_l2():
        solve_l1()
        solve_l2_edges()

    FUNCTION solve_l3_cross():
        solve_l2()
        solve_l3_cross()  # MAY THROW EvenCubeEdgeParityException on even cubes

    FUNCTION solve_l3():
        solve_l3_cross()
        solve_l3_corners()  # MAY THROW EvenCubeCornerSwapException on even cubes

    # Main retry loop
    FOR iteration IN [1, 2, 3]:

        IF cube.is_solved:
            BREAK

        TRY:
            MATCH what:
                CASE ALL:     solve_l3()
                CASE L3:      solve_l3()
                CASE L3x:     solve_l3_cross()
                CASE L2:      solve_l2()
                CASE L1:      solve_l1()
                CASE Centers: solve_nxn_centers()
                CASE Edges:   solve_nxn_edges()

            # If we get here without exception and requested ALL, verify solved
            IF what == ALL AND NOT cube.is_solved:
                THROW InternalSWError("Not solved but no parity detected")

        CATCH EvenCubeEdgeParityException:
            # Full edge parity detected during L3 Cross
            # All slices of some edge are flipped - couldn't detect during pairing

            IF edge_parity_detected:
                THROW InternalSWError("Edge parity detected twice!")

            edge_parity_detected = TRUE

            # Fix: flip all inner slices of an edge
            nxn_edges.do_even_full_edge_parity_on_any_edge()

            # This disturbs reduction, so retry will re-reduce and re-solve
            CONTINUE  # Next iteration

        CATCH EvenCubeCornerSwapException:
            # Corner parity detected during L3 Corners
            # Only 2 corners in position - impossible on 3x3
            # Note: L3Corners already performed the corner swap before throwing

            IF corner_parity_detected:
                THROW InternalSWError("Corner parity detected twice!")

            corner_parity_detected = TRUE

            # Corner swap disturbs edges, so retry will re-reduce and re-solve
            CONTINUE  # Next iteration

    # Record results
    results.was_even_edge_parity = edge_parity_detected
    results.was_corner_swap = corner_parity_detected
    results.was_partial_edge_parity = partial_edge_parity

    RETURN results
```

---

## Edge Parity Handling

### Types of Edge Parity

| Type | When Detected | How Fixed | Exception? |
|------|---------------|-----------|------------|
| **Partial (odd cube)** | During last edge pairing | Use center slice as reference, flip mismatched | No |
| **Partial (even cube)** | During last edge pairing | Use first slice (reversed) as guess | No |
| **Full (even cube)** | During L3 Cross (1 or 3 edges flipped) | Flip all inner slices | Yes |

---

## Odd Cube Edge Parity - Detailed Flow

### Why Odd Cubes Are Different

On odd cubes (5x5, 7x7, etc.), the **center slice of each edge is fixed** - it cannot be flipped because it's directly attached to the fixed center piece. This gives us a **reference point** during edge pairing.

```
5x5 Edge cross-section:
  [slice 0][slice 1][CENTER][slice 3][slice 4]
                       ↑
            Fixed reference - cannot be flipped
```

**Key insight**: On odd cubes, we can DETECT parity during edge pairing because we know which slices are "wrong" (flipped relative to the center). On even cubes, there's no center reference, so all slices could be flipped the same way and we wouldn't know.

### When Parity Is Detected

Parity is detected in `NxNEdges.solve()` when exactly **1 edge remains unsolved** after solving the first 11:

```python
# NxNEdges.solve() - nxn_edges.py:48-72
def solve(self) -> bool:
    self._do_first_11()           # Solve first 11 edges

    if self._is_solved():
        return False              # All 12 solved - no parity

    assert self._left_to_fix == 1  # Exactly 1 unsolved = PARITY!

    self._do_last_edge_parity()    # Fix parity

    self._do_first_11()            # Re-pair if needed (simple algo case)

    assert self._is_solved()
    return True                    # Parity was detected and fixed
```

### The Two Algorithms: Simple vs Advanced

The `advanced_edge_parity` flag (set during `NxNEdges` construction) controls which algorithm is used:

#### CASE 1: Simple Algorithm (`advanced_edge_parity=False`)

Uses **M-slice** moves to flip the misoriented slices:

```python
# nxn_edges.py:426-431
if not self._advanced_edge_parity:
    # M-slice based algorithm
    for _ in range(4):
        M'[slices] U2
    M'[slices]
```

**Consequence**: This algorithm **DISTURBS the edge pairing**. After the fix, some edges that were previously paired become unpaired again.

**Flow after simple fix:**
```
1. Parity detected (1 edge unsolved)
2. _do_last_edge_parity() flips slices using M-slice
3. Edge pairing is disturbed!
4. _do_first_11() is called AGAIN to re-pair edges
5. Now all 12 edges solved
```

#### CASE 2: Advanced Algorithm (`advanced_edge_parity=True`)

Uses **R/L-slice** moves that preserve edge pairing:

```python
# nxn_edges.py:432-453
else:
    # From https://speedcubedb.com/a/6x6/6x6L2E
    # Rw' U2 Lw F2 Lw' F2 Rw2 U2 Rw U2 Rw' U2 F2 Rw2 F2

    Rs = Algs.R[plus_one]  # Inner R slices
    Ls = Algs.L[plus_one]  # Inner L slices

    alg = Rs' U2 Ls F2 Ls' F2 Rs2 U2 Rs U2 Rs' U2 F2 Rs2 F2
    self.op.play(alg)
```

**Consequence**: This algorithm **PRESERVES edge pairing**. No re-pairing needed.

**Flow after advanced fix:**
```
1. Parity detected (1 edge unsolved)
2. _do_last_edge_parity() flips slices using R/L-slice
3. Edge pairing is PRESERVED
4. _do_first_11() runs but finds all edges already solved
5. Solve continues normally
```

### Slice Selection Logic

The algorithm determines WHICH slices need to be flipped by comparing each slice to the center:

```python
# nxn_edges.py:389-411
if n_slices % 2:  # ODD cube
    required_color = self._get_slice_ordered_color(face, edge.get_slice(n_slices // 2))
    # Center slice is the reference - it's always "correct"

for i in range(n_slices // 2):
    s = edge.get_slice(i)
    color = self._get_slice_ordered_color(face, s)
    if color != required_color:
        slices_indices_to_fix.append(i)  # This slice is flipped
```

### Why No Exception Is Thrown

Unlike even cube full parity (which throws `EvenCubeEdgeParityException`), odd cube parity is handled **silently** during reduction:

1. **No L3Cross involvement** - parity is fixed before 3x3 solving begins
2. **Return value signals** - `solve()` returns `True` if parity was fixed
3. **Results tracking** - `partial_edge_parity` flag is set for reporting

```python
# In BeginnerSolver._solve() - beginner_solver.py
def _edges():
    partial_edge_parity = self.nxn_edges.solve(holder)  # True if parity fixed
```

### Summary: Odd vs Even Cube Edge Parity

| Aspect | Odd Cube | Even Cube |
|--------|----------|-----------|
| **Reference point** | Center slice (fixed) | None |
| **When detected** | During edge pairing | During L3Cross |
| **Who detects** | NxNEdges | L3Cross |
| **Exception?** | No - handled silently | Yes - `EvenCubeEdgeParityException` |
| **Who fixes?** | NxNEdges | Orchestrator/BeginnerSolver |
| **Re-reduction needed?** | Maybe (simple algo) or No (advanced algo) | Yes (always) |
| **Algorithm choice** | Simple M-slice OR Advanced R/L-slice | Always uses full edge flip |

---

### Detection Logic in L3Cross (Even Cubes Only)

```python
# Count edges with yellow facing up
n = sum of edges matching yellow face

if n not in [0, 2, 4]:  # 1 or 3 is impossible on 3x3
    if cube.n_slices % 2 == 0:  # Even cube
        raise EvenCubeEdgeParityException()
```

### Fix Algorithm

The fix flips ALL inner slices of an edge using the algorithm from `nxn_edges.py`:

```
M-slice based (simple):
    REPEAT 4 times:
        M'[inner_slices] U2
    M'[inner_slices]

R/L-slice based (advanced):
    Rw' U2 Lw F2 Lw' F2 Rw2 U2 Rw U2 Rw' U2 F2 Rw2 F2
```

---

## Corner Parity Handling

### Detection Logic in L3Corners

```python
if not all_corners_in_position:
    if cube.n_slices % 2 == 0:  # Even cube
        n = count of corners in position
        if n == 2:  # Exactly 2 in position = parity
            _do_corner_swap()  # Fix it first
            raise EvenCubeCornerSwapException()  # Then signal retry
```

### Why Fix Before Throwing?

The `L3Corners` class performs the corner swap **before** raising the exception. This is because:
1. The corner swap algorithm is specific to L3Corners (uses inner R and U slices)
2. After the swap, edges are disturbed and need re-reduction
3. The exception signals "retry needed" rather than "error to fix"

---

## Corner Fix vs Edge Fix - Historical Asymmetry

> **UPDATE (2025-12-16):** Testing on real cubes confirmed that the corner swap
> algorithm is NOT truly "position-sensitive". It works as long as yellow is up
> because any diagonal corner swap fixes parity. The original asymmetry was based
> on a misunderstanding.

### Corner Parity: Fix First, Then Throw (Historical)

```python
# In L3Corners._do_positions() (l3_corners.py:104-108)
if n == 2:  # Parity detected
    self._do_corner_swap()                    # FIX FIRST
    raise EvenCubeCornerSwapException()       # THEN signal retry
```

```python
# In BeginnerSolver._solve() (beginner_solver.py:203-209)
except EvenCubeCornerSwapException:
    even_corner_swap_was_detected = True
    continue  # Just retry - fix already done
```

### Edge Parity: Only Throw, Fix Later

```python
# In L3Cross._do_yellow_cross() (l3_cross.py:96-99)
if n not in [0, 2, 4]:  # Parity detected
    raise EvenCubeEdgeParityException()       # ONLY signal - NO FIX
```

```python
# In BeginnerSolver._solve() (beginner_solver.py:194-201)
except EvenCubeEdgeParityException:
    even_edge_parity_was_detected = True
    self.nxn_edges.do_even_full_edge_parity_on_any_edge()  # FIX HERE
    continue  # Then retry
```

### Why Both Actually Work the Same Way

**Corner swap algorithm:**
- Swaps diagonal corners on the U face
- Any diagonal swap flips corner permutation parity from odd to even
- Works after Y rotation because different diagonal pair still fixes parity
- Only requirement: yellow face is up (true in 3x3 state)

**Edge flip algorithm:**
- Flips all inner slices of any edge
- Can be done on any edge at FU position

### Summary Table

| Aspect | Corner Parity | Edge Parity |
|--------|---------------|-------------|
| **Requires yellow up?** | Yes | Yes |
| **Works after Y rotation?** | Yes | Yes |
| **Who detects?** | L3Corners | L3Cross |
| **Who fixes?** | Orchestrator → Reducer | Orchestrator → Reducer |
| **Pattern** | Throw → Catch → Fix | Throw → Catch → Fix |

> **NOTE (2025-12-16):** The code has been refactored to use a unified pattern.
> L3Corners now just throws without fixing, matching L3Cross. See
> PARITY_HANDLING_ORCHESTRATOR.md for the current implementation.

### Fix Algorithm

```python
nh = n_slices // 2

# Inner slice corner swap
alg = R[2:nh+1]×2  U×2
      R[2:nh+1]×2  U[1:nh+1]×2
      R[2:nh+1]×2  U[1:nh+1]×2
```

---

## Why Three Iterations?

The retry loop runs **maximum 3 iterations**:

| Iteration | What Might Happen |
|-----------|-------------------|
| 1 | Normal solve OR edge parity detected |
| 2 | After edge parity fix: normal solve OR corner parity detected |
| 3 | After corner parity fix: should complete |

**Why not 2?**
- Iteration 1: Edge parity detected → fix → retry
- Iteration 2: Corner parity detected → fix → retry
- Iteration 3: Both parities fixed → should solve

**Why not 4+?**
- If we detect the same parity twice, it's a bug (`InternalSWError`)
- Each parity type can only occur once per solve
- Edge and corner parity are independent

---

## Flow Diagram

```
Start
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  ITERATION 1                                                │
│  ┌─────────┐   ┌─────────┐   ┌────┐   ┌────┐   ┌─────────┐ │
│  │ Centers │ → │  Edges  │ → │ L1 │ → │ L2 │ → │ L3Cross │ │
│  └─────────┘   └─────────┘   └────┘   └────┘   └────┬────┘ │
│                     │                               │      │
│              partial parity?              EvenCubeEdgeParity?
│              (fixed silently)                       │      │
│                                                     ▼      │
│                                              ┌───────────┐ │
│                                              │ L3Corners │ │
│                                              └─────┬─────┘ │
│                                                    │       │
│                                        EvenCubeCornerSwap? │
└────────────────────────────────────────────────────┼───────┘
                                                     │
       ┌──────────────────────────────┬──────────────┴──────────┐
       │                              │                         │
       ▼                              ▼                         ▼
    SOLVED                   Edge Parity Fix            Corner Parity
       │                     (flip all slices)          (swap done)
       │                              │                         │
       │                              └────────┬────────────────┘
       │                                       │
       │                                       ▼
       │                             ┌─────────────────┐
       │                             │  ITERATION 2+   │
       │                             │  (retry solve)  │
       │                             └────────┬────────┘
       │                                      │
       └──────────────────────────────────────┘
                                              │
                                              ▼
                                           SOLVED
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `cube/solver/begginer/beginner_solver.py` | Main solver with retry loop |
| `cube/solver/begginer/nxn_edges.py` | Edge pairing + parity algorithms |
| `cube/solver/begginer/l3_cross.py` | L3 cross + edge parity detection |
| `cube/solver/begginer/l3_corners.py` | L3 corners + corner parity detection/fix |
| `cube/solver/common/advanced_even_oll_big_cube_parity.py` | Advanced edge parity algorithm |
| `cube/app/app_exceptions.py` | Exception definitions |
| `cube/solver/solver.py` | SolverResults class |

---

## Comparison with Later NxN Orchestrator

This design was later refactored to use the **Orchestrator pattern** (`NxNSolverOrchestrator`) which:

1. **Separates concerns**: Reducer (NxN→3x3) and 3x3 Solver are separate classes
2. **Protocol-based**: Uses `ReducerProtocol` and `Solver3x3Protocol` interfaces
3. **Composable**: Any reducer can work with any 3x3 solver
4. **Same parity logic**: Still uses exception + retry pattern

The monolithic `BeginnerSolver` approach documented here is simpler but less flexible - all solving logic is in one class.

---

## Summary

The `BeginnerSolver._solve()` method implements parity handling through:

1. **Nested functions** that build solve steps incrementally
2. **Exception-based detection** when impossible states are found
3. **Retry loop** that restarts the entire solve after fixes
4. **Result tracking** to report what parities occurred

This pattern ensures even cubes (4x4, 6x6, etc.) can always be solved despite parity issues that are undetectable during the reduction phase.
