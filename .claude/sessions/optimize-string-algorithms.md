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

## Proposed Solution: `op.wb()` — Buffered Play Context Manager

### Core Design

```python
with op.wb():  # "with buffer"
    op.play(R)
    op.play(R)
    op.play(R')
    op.play(L)
# on __exit__: _flush() runs .simplify() on buffer → plays R R' cancel, R→nothing, L stays
# after exit: cube state is correct, caller can query cube safely
```

### Rules

1. **Context manager only** — buffer mode can ONLY be entered via `with op.wb():`. No way to forget to flush. This is CRITICAL.

2. **Flush on context exit** — `_flush()` is private, called by `__exit__`. Why on exit? Because the solver says: "these operations can be buffered, but AFTER this block I need to query the cube state." The flush ensures the cube is up-to-date before the next line runs.

3. **Nestable** — `with op.wb():` can nest inside another `with op.wb():`. Inner flush pushes to outer buffer (only outermost flush actually plays).

4. **Config-controlled** — buffer mode is controlled by a config/protocol flag. If disabled, `wb()` is a transparent no-op — plays happen immediately as before. This lets us disable buffering to isolate bugs ("is this a buffer bug or a solver bug?").

5. **`_flush()` behavior** — takes the buffer, runs `.simplify()`, then plays each resulting move normally (with animation, respecting current mode — whatever `op.play()` would normally do).

### Open Question: Query Mode Inside Buffer

**Problem:** The operator has a context manager for query mode (`with op.query_mode():`), and there are other places that enter query mode (cube query, rotate-and-check, etc.). What happens when query mode is entered WHILE we're inside `with op.wb():`?

The buffer hasn't been flushed yet → cube state is STALE → queries return wrong results.

**Options to resolve (TBD):**
- Auto-flush before entering query mode?
- Flush buffer, enter query mode, then resume buffering?
- Error/assert if query mode entered while buffer is non-empty?
- Something else?

**Awaiting user direction on this.**

## Why You CANNOT Optimize at Operator/AnimationManager Level (Without Buffering)

1. **Solver queries cube state between moves** — without buffering boundaries, the operator doesn't know when it's safe to delay/merge moves vs. when the solver needs current state.

2. **Annotation algs** (`AnnotationAlg`) — no-op GUI refresh markers mixed into sequences. Optimizer doesn't understand these.

3. **Animation algs** (`AnimationAbleAlg`) — carry animation metadata. Merging loses info.

The `wb()` design solves constraint #1: the solver explicitly marks safe-to-buffer regions. The solver knows when it will query and wraps non-query sections in `with op.wb():`.

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

- Paths 1 and 2 already optimized via `.simplify()`
- Path 3 (animated solve) is the problem — raw unoptimized moves
- Designing `op.wb()` buffered context manager to solve Path 3
- Open question: how to handle query mode inside buffer

## Next Steps

- Resolve query mode interaction (awaiting user input)
- More design questions TBD
