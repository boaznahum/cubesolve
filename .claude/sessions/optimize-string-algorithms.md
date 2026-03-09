# Session: Optimize String Algorithms

**Branch:** `claude/optimize-string-algorithms-zyo3s`

## Goal

Eliminate redundant moves (R R → R2, R R' → identity) from the animated solution queue in WebGL.

## Problem Statement

Currently the queue displays non-optimized solutions — consecutive moves like `R R` (should be `R2`) or `R R'` (should cancel out).

### Where optimization currently happens

Both solve paths in `ClientSession.py` already call `.simplify()`:

- **Instant solve** (`_solve_and_apply_instant`, line 1040-1041):
  ```python
  solution_alg = slv.solution()
  solution_alg = solution_alg.simplify()
  ```

- **Two-phase solve** (`_two_phase_solve`, line 1068-1069):
  ```python
  solution_alg = slv.solution()
  solution_alg = solution_alg.simplify()
  ```

### Why you CANNOT optimize at the Operator/AnimationManager level

This is a **dangerous change** — three critical constraints:

1. **Annotation algs** (`AnnotationAlg`) — special no-op moves mixed into sequences that trigger GUI refreshes (markers, text overlays). They have `count() == 0` and `play()` is a no-op. The optimizer doesn't know about these — stripping or reordering them would break solver visualization.

2. **Animation algs** (`AnimationAbleAlg`) — algs that carry animation metadata (which face/pieces to rotate). Merging two animation-able algs at the operator level would lose animation information.

3. **Buffered operations and solver state** — The solver feeds moves one-by-one via `op.play(Algs.R)`, then queries cube state to decide next moves. If the operator buffer optimized/merged moves before applying them, the solver would query a cube state that doesn't match what it expects. Example:
   ```
   Solver: op.play(R)      → expects R applied to cube
   Solver: check_condition  → queries cube state (expects R applied)
   Solver: op.play(R)      → expects R2 state now

   If operator merged R+R → R2 and delayed application:
     Solver queries after first R → but R wasn't applied yet → WRONG STATE
     Solver makes wrong decision → broken solution
   ```

### Where optimization IS safe

Optimization is safe **only after the solver is done** — on the complete solution algorithm, before flattening into the step-by-step queue. This is exactly what `.simplify()` does in `ClientSession.py`.

## Key Files

| File | Role |
|------|------|
| `src/cube/domain/algs/optimizer.py` | `simplify()` and `_combine()` — merges consecutive same-form algs |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py:1031-1079` | Both solve paths call `.simplify()` |
| `src/cube/domain/solver/common/BaseSolver.py:27-44` | `solution()` — generates raw (unoptimized) solution |
| `src/cube/application/commands/Operator.py:147-170` | `play()` — feeds moves one-by-one for animation |
| `src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py` | Queue processing, one move at a time |
| `src/cube/domain/algs/AnnotationAlg.py` | No-op GUI refresh markers |
| `src/cube/domain/algs/AnimationAbleAlg.py` | Mixin for animatable moves |

## Current Status

- `.simplify()` IS called on solutions before enqueuing — so R R and R R' should already be optimized in the queue
- Need to investigate: where exactly are non-optimized moves appearing? Possible sources:
  - Scramble sequences (not simplified?)
  - Direct operator play (not through solution path?)
  - Optimizer bug (not catching all cases?)

## Next Steps

- TBD based on user direction — this is a dangerous change, proceed carefully
