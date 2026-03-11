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

## Proposed Solution: `op.with_buffer()` — Buffered Play Context Manager

### Core Design

```python
with op.with_buffer():  # "with buffer"
    op.play(R)
    op.play(R)
    op.play(R')
    op.play(L)
# on __exit__: _flush() runs .simplify() on buffer → plays R R' cancel, R→nothing, L stays
# after exit: cube state is correct, caller can query cube safely
```

### Rules

1. **Context manager only** — buffer mode can ONLY be entered via `with op.with_buffer():`. No way to forget to flush. This is CRITICAL.

2. **Flush on context exit** — `_flush()` is private, called by `__exit__`. Why on exit? Because the solver says: "these operations can be buffered, but AFTER this block I need to query the cube state." The flush ensures the cube is up-to-date before the next line runs.

3. **Nestable** — `with op.with_buffer():` can nest inside another `with op.with_buffer():`. Inner flush pushes to outer buffer (only outermost flush actually plays).

4. **Config-controlled** — buffer mode is controlled by a config/protocol flag. If disabled, `with_buffer()` is a transparent no-op — plays happen immediately as before. This lets us disable buffering to isolate bugs ("is this a buffer bug or a solver bug?").

5. **`_flush()` behavior** — takes the buffer, runs `.simplify()`, then plays each resulting move normally (with animation, respecting current mode — whatever `op.play()` would normally do).

6. **AnnotationAlg triggers flush** — when `op.play()` receives an `AnnotationAlg` while in buffer mode: flush the buffer first (simplify + play all buffered moves), THEN play the annotation immediately. Annotations are GUI state markers (text overlays, phase markers) that must fire at the correct point in the sequence. They cannot be buffered or reordered. After the annotation plays, buffering resumes for subsequent moves.

```python
with op.with_buffer():
    op.play(R)          # buffered
    op.play(R)          # buffered
    op.play(ann)        # AnnotationAlg → flush! simplify [R,R]→R2, play R2, then play ann
    op.play(L)          # buffered (new buffer starts)
    op.play(L')         # buffered
# exit: flush [L, L'] → simplify → cancel → nothing played
```

### Resolved: Query Mode Inside Buffer

**Problem:** The operator has a context manager for query mode (`with op.with_query_restore_state():`), and `rotate_and_check` enters query mode. What happens when query mode is entered WHILE we're inside `with op.with_buffer():`?

The buffer hasn't been flushed yet → cube state is STALE → queries return wrong results.

**Solution: Flush + temporarily disable buffering.**

`with_query_restore_state()` now:
1. Flushes the buffer (simplify + play all buffered moves)
2. Disables buffering (sets `_buffer = None`, `_buffer_depth = 0`)
3. Runs the query body (moves play immediately, tracked in history for rollback)
4. On exit: undoes all query moves, restores buffer state

`rotate_and_check()` now takes an `op` parameter and uses `op.with_query_restore_state()` instead of manually managing `_in_query_mode` and undo. This eliminates the duplicate query mode logic that was in CubeQueries2.

```python
# Example flow:
with op.with_buffer():
    op.play(R)          # buffered
    op.play(R)          # buffered

    # rotate_and_check calls op.with_query_restore_state():
    #   1. flush buffer → simplify [R,R]→R2, play R2
    #   2. disable buffering
    #   3. query rotations via op.play() (immediate)
    #   4. rollback via undo
    #   5. re-enable buffering
    n = cmn.rotate_face_and_check(face, pred, op)

    op.play(L)          # buffered again
# exit: flush [L] → play L
```

## Why You CANNOT Optimize at Operator/AnimationManager Level (Without Buffering)

1. **Solver queries cube state between moves** — without buffering boundaries, the operator doesn't know when it's safe to delay/merge moves vs. when the solver needs current state.

2. **Annotation algs** (`AnnotationAlg`) — no-op GUI refresh markers mixed into sequences. Optimizer doesn't understand these.

3. **Animation algs** (`AnimationAbleAlg`) — carry animation metadata. Merging loses info.

The `with_buffer()` design solves constraint #1: the solver explicitly marks safe-to-buffer regions. The solver knows when it will query and wraps non-query sections in `with op.with_buffer():`.

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
- `op.with_buffer()` buffered context manager implemented on Operator
- Config flag `OPERATOR_BUFFER_MODE` added (default True, set False to disable)
- Query mode interaction resolved: flush + disable buffering during query
- `rotate_and_check` refactored to use `op.with_query_restore_state()` (takes `op` param)
- All callers updated to pass `op`

## Next Steps

- Add `with op.with_buffer():` wrapping in solver code (Path 3 callers)
- Write tests for with_buffer() buffering behavior
- Integration test with animated solve path
