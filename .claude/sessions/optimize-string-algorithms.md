# Session: Optimize String Algorithms

**Branch:** `claude/optimize-string-algorithms-zyo3s`

## Goal

Eliminate redundant moves (R R → R2, R R' → identity) from the animated solution queue in WebGL.

## Problem Statement

Currently the queue displays non-optimized solutions — consecutive moves like `R R` (should be `R2`) or `R R'` (should cancel out).

## Three Solve Paths in ClientSession.py

### Path 1: `_solve_and_apply_instant` (line 1031) — HAS simplify ✅
```python
solution_alg = slv.solution()       # solver runs with animation=False, collects moves
solution_alg = solution_alg.simplify()  # optimize the complete solution
steps = list(solution_alg.flatten())
app.op.enqueue_redo(steps)           # put in redo queue
# then drain queue instantly with animation=False
```
`solution()` runs the solver silently, undoes all moves, returns the complete alg. Then `.simplify()` optimizes it. No animation.

### Path 2: `_two_phase_solve` (line 1059) — HAS simplify ✅
```python
solution_alg = slv.solution()
solution_alg = solution_alg.simplify()
steps = list(solution_alg.flatten())
app.op.enqueue_redo(steps)           # put in redo queue, user steps through
```
Same as path 1, but the user manually advances moves (redo/next). Already optimized.

### Path 3: `_run_solver_blocking` (line 1128) — NO simplify ❌ THIS IS THE PROBLEM
```python
self._app.slv.solve(animation=True)
```
The solver runs **live with animation**. Each `op.play(R)` call goes directly through the Operator → AnimationManager → client animation. The solver controls the cube step-by-step. There is **no post-processing**, no `.simplify()`. Raw unoptimized moves go straight to the animation queue.

## Why You CANNOT Optimize in the Animated Path

The animated path (Path 3) cannot be optimized at the Operator or AnimationManager level because:

1. **Solver queries cube state between moves** — The solver calls `op.play(R)`, then inspects the cube to decide the next move. If the operator delayed or merged moves, the cube state would be wrong and the solver would make incorrect decisions → broken solution.

2. **Annotation algs** (`AnnotationAlg`) — No-op moves mixed in that trigger GUI refreshes (markers, text overlays). The optimizer doesn't understand these — stripping or reordering them breaks solver visualization.

3. **Animation algs** (`AnimationAbleAlg`) — Each carries animation metadata (which face/pieces to rotate). Merging two at the operator level loses this information.

**Bottom line:** In Path 3, the solver IS the driver. It plays moves one-by-one, reads the cube, decides next moves. You cannot batch, reorder, or merge moves mid-solve without breaking the solver's logic.

## Where Optimization IS Safe

Only in Paths 1 and 2 — where `solution()` runs the solver silently (animation=False), collects the complete move list, THEN `.simplify()` optimizes it as a finished sequence before putting it in the redo queue.

## Key Files

| File | Role |
|------|------|
| `src/cube/domain/algs/optimizer.py` | `simplify()` and `_combine()` — merges consecutive same-form algs |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py:1031` | Path 1: instant solve (has simplify) |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py:1059` | Path 2: two-phase solve (has simplify) |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py:1128` | Path 3: animated blocking solve (NO simplify) |
| `src/cube/domain/solver/common/BaseSolver.py:27-44` | `solution()` — runs solver silently, returns complete alg |
| `src/cube/application/commands/Operator.py:147-170` | `play()` — feeds moves one-by-one for animation |
| `src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py` | Queue processing, one move at a time |
| `src/cube/domain/algs/AnnotationAlg.py` | No-op GUI refresh markers |
| `src/cube/domain/algs/AnimationAbleAlg.py` | Mixin for animatable moves |

## Current Status

- Paths 1 and 2 are already optimized via `.simplify()`
- Path 3 (animated solve) shows raw unoptimized moves — this is the user-visible problem
- Path 3 CANNOT be optimized at operator/animation level due to solver state dependency

## Next Steps

- TBD based on user direction — this is a dangerous change, proceed carefully
