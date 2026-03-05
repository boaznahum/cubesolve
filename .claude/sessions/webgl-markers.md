# WebGL Markers — Session Notes

## Branch: `webgl-markers`

## Goal
Add full marker rendering to the WebGL backend so solver annotations (rings, circles, arrows, checkmarks, etc.) are visible during solve/animation, matching the pyglet2 backend.

## What's Done (All 5 checks pass)

### Phase 1: Python — Marker Serialization (COMPLETE)
1. **`src/cube/application/markers/_complementary_colors.py`** (NEW) — shared complementary color table extracted from pyglet2
2. **`src/cube/application/markers/__init__.py`** — added `get_complementary_color` export
3. **`src/cube/presentation/gui/backends/pyglet2/_modern_gl_cell.py`** — imports from shared module instead of local copy
4. **`src/cube/presentation/gui/backends/webgl/CubeStateSerializer.py`** (REWRITTEN) — extracts markers alongside colors. Face format changed from `[[r,g,b], ...]` to `{"colors": [...], "markers": [...]}`. Added `_serialize_marker()` with isinstance dispatch for all 8 marker types.
5. **`src/cube/presentation/gui/backends/webgl/SessionState.py`** — updated `cube_faces` type hint

### Phase 2: JavaScript — Parse & Render Markers (COMPLETE)
6. **`src/cube/presentation/gui/backends/webgl/static/js/MarkerRenderer.js`** (NEW) — Three.js marker geometry for all 8 types (filled_circle, ring, cross, bold_cross, checkmark, arrow, character, outlined_circle). Uses `MeshBasicMaterial` (unlit), flat 2D geometry.
7. **`src/cube/presentation/gui/backends/webgl/static/js/CubeModel.js`** — backward-compatible face parsing, marker mesh lifecycle (`updateFaceMarkers`, `clearAllMarkers`, `_disposeMarkerGroup`)
8. **Version bumped to 1.24**

### Key Bug Fix: Z-offset
- Markers were initially invisible because they were placed at local Z=0.02, but the sticker's visible surface is at Z=stickerDepth (0.45 * cellSize) due to ExtrudeGeometry orientation
- Fixed by computing `zBase = stickerDepth + Z_LIFT` in MarkerRenderer.js
- Constants: `STICKER_DEPTH_FACTOR = 0.45`, `Z_LIFT = 0.02`, `Z_STEP = 0.005`

### Vite Build Required
- JS files served via Vite bundle (`dist/assets/index-*.js`), NOT from `static/js/` directly
- After ANY JS change: `cd src/cube/presentation/gui/backends/webgl && npx vite build`
- Python changes require server restart; JS-only changes need browser refresh

## What Works
- **LTR coordinate markers** (origin black circle, red arrow X, blue arrow Y) render correctly in WebGL
- Full pipeline confirmed: Python serialization → WebSocket → JS parsing → Three.js rendering
- Backward compatibility: old format (array) and new format (object with colors+markers) both work
- All 5 checks pass (ruff, mypy, pyright, 11389 non-GUI tests, 36 GUI tests)

## What's Broken — Solver Annotations Not Visible

### Root Cause
The WebGL backend uses a **two-phase solve** (`_two_phase_solve()` in ClientSession.py:967):
1. `slv.solution()` runs the solver — this plays moves inside `with self.ann.annotate()` blocks which add/remove transient markers
2. Solution algorithm is enqueued as redo steps via `op.enqueue_redo(steps)`
3. During playback from redo queue, `op.redo()` replays bare moves — **no annotation context exists**, so no solver markers

In pyglet2, the solve runs **one-phase** (synchronously with animation) — each `op.play()` inside `annotate()` blocks waits for animation to finish, so markers are visible during each animated step.

### Why Pyglet2 Doesn't Have This Problem
Pyglet2 uses **one-phase solve on a single thread**:
1. Solver calls `op.play(move)` inside `with annotate()` block
2. `AnimationManager._op_and_play_animation()` handles the move
3. For real moves: enters `while not animation.done:` loop that **pumps the pyglet event loop** (`event_loop.idle()` + `event_loop.step()`)
4. Solver is FROZEN (same thread, blocked in the while loop) while UI keeps rendering with markers visible
5. For `AnnotationAlg`: just calls `operator(alg, inv)` + `update_gui_elements()` + `notify()` — refreshes GUI so markers appear
6. When animation finishes, control returns to solver → continues inside `annotate()` → markers still present

Key: pyglet event loop can be pumped cooperatively from within the animation function. This is NOT possible with asyncio (solver would block the event loop → deadlock).

### Solver Markers (from MarkerFactory)
- `c0()` — RingMarker, complementary color, radius 1.0, thickness 0.8 (tracker anchor)
- `c1()` — FilledCircleMarker, complementary color, radius 0.6 (moved piece indicator)
- `c2()` — RingMarker, complementary color, radius 1.0, thickness 0.3 (destination slot)
- `at_risk()` — BoldCrossMarker, red, radius 0.85 (pieces that may be destroyed)

### LTR Coordinate Markers (always present, work fine)
- `ltr_origin()` — FilledCircleMarker, black, radius 0.4
- `ltr_arrow_x()` — ArrowMarker, red, direction 0 (right)
- `ltr_arrow_y()` — ArrowMarker, blue, direction 90 (up)

---

## Approach Options for Fixing Solver Annotations

### Option A: Extend AnnotationAlg to carry marker snapshots
**Concept:** Embed marker state into the `AnnotationAlg` instances that flow through the redo queue.

**How it would work:**
1. During `solution()`, `OpAnnotation._annotate()` already plays `Algs.AN` at entry (markers added) and exit (markers removed)
2. Instead of the singleton `Algs.AN`, create a new `AnnotationAlg` instance that carries a snapshot of the current marker state
3. During playback, when the WebGL AM encounters an `AnnotationAlg`, it reads the marker snapshot and applies it to the cube's part edges before sending state to client

**Pros:**
- No threading, no deadlock risk
- Works within existing two-phase architecture
- Minimal changes to solver code

**Cons:**
- Need to figure out how to snapshot marker state (what data to capture)
- `AnnotationAlg` is currently frozen/immutable — need subclass or new class
- The relationship between markers and part edges is complex (moveable markers move with pieces between annotate entry and exit)
- May not capture the full visual state (text annotations, marker removal timing)

**Key files:**
- `src/cube/domain/algs/AnnotationAlg.py` — extend or subclass
- `src/cube/application/commands/OpAnnotation.py` — capture marker state when playing AN
- `src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py` — apply marker state from AN alg
- `src/cube/presentation/gui/backends/webgl/CubeStateSerializer.py` — already handles marker extraction

**Status:** Not started. Feasible but complex interaction with moveable markers.

### Option B: One-phase solve (like pyglet2) — CHOSEN APPROACH
**Concept:** Run the solver synchronously with animation, exactly like pyglet2, but using threading to avoid blocking the async event loop.

**How it would work:**
1. Run `slv.solution()` in a separate thread via `asyncio.to_thread()`
2. When solver calls `op.play(move)` → AM blocks using `threading.Event.wait()`
3. Main async thread stays free to process WebSocket messages
4. When client sends `animation_done` → set the `threading.Event` → solver thread unblocks
5. For `AnnotationAlg`: send state update (with markers), return immediately (no blocking)
6. Markers are naturally present because state is extracted while inside `annotate()` context

**Pros:**
- **Proven approach** — this is exactly how pyglet2 works, just with threading instead of event loop pumping
- Markers naturally visible — no snapshot/replay needed
- Works for ALL marker types and all solvers without per-solver changes
- Text annotations also work naturally

**Cons:**
- Requires threading — solver runs on a separate thread
- Need thread-safe communication between solver thread and async event loop
- `threading.Event` for synchronization between threads
- Solver code accesses cube model from a different thread — need to ensure safety

**Key insight — asyncio vs pyglet:**
- Pyglet: single thread, cooperative multitasking via event loop pumping
- WebGL/asyncio: must use real threads because solver is synchronous and asyncio can't be pumped from within a sync function
- Solution: `asyncio.to_thread()` runs solver in a thread pool, main thread runs asyncio event loop

**Threading safety:**
- During animation, the solver thread is BLOCKED (waiting for `threading.Event`)
- Only one thread accesses the cube model at a time: solver modifies, then blocks; client reads state
- This is the same safety model as pyglet2 (solver blocked during animation)

**Key files to modify:**
- `src/cube/presentation/gui/backends/webgl/ClientSession.py` — replace `_two_phase_solve()` with `_one_phase_solve()`
- `src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py` — add blocking mode for one-phase solve
- May need a new `WebglOnePhaseAnimationManager` or mode flag

**Implementation sketch:**
```python
# ClientSession.py
async def _one_phase_solve(self):
    """Run solver with animation in a separate thread."""
    # Enable animation so solver's op.play() goes through AM
    # AM is configured to block on each move
    self._animation_manager.set_blocking_mode(True)
    try:
        await asyncio.to_thread(self._run_solver_sync)
    finally:
        self._animation_manager.set_blocking_mode(False)

def _run_solver_sync(self):
    """Runs in a worker thread — solver blocks here."""
    slv = self._app.slv
    slv.solution()  # Each op.play() blocks until animation_done

# WebglAnimationManager.py — blocking mode
def run_animation(self, cube, op, alg):
    if self._blocking_mode:
        # Apply move
        op(alg, False)
        if isinstance(alg, AnnotationAlg):
            # Just send state (with markers!) and return
            self._send_state_threadsafe()
            return
        # Send animation_start to client
        self._send_animation_threadsafe(alg)
        # Block until client sends animation_done
        self._animation_done_event.wait()
        self._animation_done_event.clear()
    else:
        # Original non-blocking queue mode (for redo playback)
        ...
```

### Option C: Re-run annotation logic during playback (REJECTED)
Too complex. Solver logic is tightly coupled to annotation placement. Would need to reverse-engineer which markers go where for each solver step.

---

## Decision: Option B — One-Phase Solve

Chosen because:
1. Proven approach (pyglet2 uses this exact model)
2. All markers work naturally — no per-solver or per-marker-type changes
3. Text annotations also work
4. Clean separation: solver runs normally, AM handles blocking

---

## Phase 3: One-Phase Solve (COMPLETE ✅)

Solver annotations (transient markers from `annotate()` blocks) are now visible during
WebGL solve animation. The solver runs in a worker thread with blocking animation mode.

### Architecture
```
Before (two-phase — REPLACED):
    _two_phase_solve():
        slv.solution()          ← runs fast, markers add/remove transiently
        enqueue_redo(steps)     ← bare moves only, no markers
        playback via _handle_play_next() ← no annotations

After (one-phase — IMPLEMENTED):
    _start_one_phase_solve() → loop.create_task(_one_phase_solve())
    _one_phase_solve():
        am.set_blocking_mode(True)
        await asyncio.to_thread(_run_solver_blocking)
            → slv.solve(animation=True)
                → each op.play() → AM._run_blocking()
                    → AnnotationAlg: apply + send_state (markers visible!)
                    → Animatable: apply + send_animation_start + Event.wait()
                → annotate() contexts stay active → markers present
        am.set_blocking_mode(False)
        fsm.send(SOLVE_DONE)
```

### Thread communication:
```
Solver Thread (asyncio.to_thread)    Main Async Thread (event loop)
    |                                     |
    slv.solve(animation=True)             |
    → annotate() adds markers             |
    → op.play(Algs.AN)                    |
    → AM: send state WITH MARKERS ──→  WS → client (markers appear)
    → returns immediately                 |
    |                                     |
    → op.play(actual_move)                |
    → AM: apply move, send anim_start ──→ WS → client (animates)
    → Event.wait() [BLOCKED]              |
    |                                ←── client sends animation_done
    |                                     Event.set()
    → Event.wait() returns                |
    → check_clear_rais_abort()            |
    → continue solving (markers present)  |
```

### Files changed for Phase 3:
| File | Change |
|------|--------|
| `WebglEventLoop.py` | `send_to()` → thread-safe via `call_soon_threadsafe` |
| `WebglAnimationManager.py` | Added blocking mode: `_blocking_mode`, `_blocking_event`, `set_blocking_mode()`, `_run_blocking()`. Modified `run_animation()`, `on_client_animation_done()`, `cancel_animation()` |
| `FlowStateMachine.py` | Added `STOP` from `SOLVING`, `SOLVE_DONE` from `STOPPING`, `SOLVING` in stop button table, guard for aborted solve |
| `ClientSession.py` | Replaced `_two_phase_solve()` with `_start_one_phase_solve()` + `_one_phase_solve()` async + `_run_solver_blocking()`. Modified STOP handler for blocking mode |
| `version.txt` | 1.24 → 1.25 |

### Cancel/Abort:
1. User clicks stop → FSM: SOLVING → STOPPING
2. `am.cancel_animation()` → `operator.abort()` + `_blocking_event.set()`
3. Solver thread unblocks → `check_clear_rais_abort()` → `OpAborted`
4. `AbstractSolver.solve()` catches OpAborted, returns cleanly
5. `_one_phase_solve` finally: `set_blocking_mode(False)`, sends `SOLVE_DONE`
6. FSM: STOPPING → READY/IDLE

### Key design decisions:
- **`threading.Event`** for blocking: zero CPU, wakes instantly when set
- **`call_soon_threadsafe`** for all WebSocket sends from solver thread
- **Moves go to history** (not redo queue): user can undo to step back through solve
- **`_auto_play` cleared** after one-phase solve: solve IS the play

## Visual Quality — Future Work
- Current markers are **flat 2D geometry** (CircleGeometry, RingGeometry, PlaneGeometry)
- Pyglet2 renders markers as **3D cylinders** with height (using `height_offset` parameter)
- Could upgrade to CylinderGeometry/extruded shapes for visual parity with pyglet2
- **Performance:** Solve animation is slow (~8s/move at speed 6) due to marker rendering overhead — each `send_state()` triggers full marker rebuild in JS. Consider: debouncing, diffing markers, or lazy marker updates.

---

## Bug Fixes (Post-Phase 3)

### v1.25.1 — Markers persist after solve/stop + scramble in redo queue
**Markers persist:** Race condition where `send_state()` fires before solver thread callbacks drain (annotate `__exit__` removing markers). Fix: `await asyncio.sleep(0)` in `_one_phase_solve` before final `send_state()`.

**Scramble in redo queue:** Scramble moves were recorded in history, then appeared in redo queue on undo. Fix: `op._history.clear()` after scramble in the WebGL `_handle_command()` handler. (`op.history()` returns a copy, so `.clear()` on it doesn't work — must access `op._history` directly.)

### v1.25.2 — "Solve" behaves like "Solve and Play"
Both "solve" and "solve_and_play" commands were routed to `_start_one_phase_solve()`. Fix: restored `_two_phase_solve()` for "solve" command (enqueues to redo queue), kept one-phase only for "solve_and_play" (animates with markers). Also fixed `inject_command` for `SOLVE_ALL`.

### v1.25.3 — Reset resets solver type
`app.reset()` recreates solver with `Solvers.default()`, losing user's solver selection. Fix: save `prev_solver = app.slv.get_code` before reset, restore with `app.switch_to_solver(prev_solver)` after. Applied to both `reset_session` and `RESET_CUBE` handlers.

### v1.25.4 — iPhone reconnect aborts solve (INCOMPLETE FIX)
iOS Safari suspends tab → WebSocket dies → `reattach()` was calling `cancel_animation()` which aborts the one-phase solve. Fix: skip cancel when `am._blocking_mode` is active. **Problem:** Didn't unblock the solver thread which stays stuck on `_blocking_event.wait()`.

### v1.25.5 — Fix reconnect: unblock solver thread
Root cause: `reattach()` swapped the WebSocket but left the solver thread blocked on `_blocking_event.wait()` for `animation_done` from the dead WebSocket. Fix: `am._blocking_event.set()` in reattach to unblock solver. Also added `timeout=60.0` to `_blocking_event.wait()` as safety net.

### v1.25.5 (second commit) — Configurable blocking timeout + abort on timeout
- `blocking_timeout` (60s) added to `AnimationSpeedConfig` dataclass and `AnimationSpeedConfigProtocol`
- On timeout: `self._operator.abort()` — prevents solver grinding through all moves at 60s each
- User can press Solve again on reconnect to restart from partially-solved state

### v1.25.7 — Config protocol cleanup
- Added `SessionConfigProtocol` + `session_config` to `ConfigProtocol` (session keepalive timeout)
- Added `prevent_random_face_pick_up_in_geometry` to `ConfigProtocol`
- `SessionManager.py` no longer imports `_config` directly — receives config via constructor
- `slice_layout.py` no longer imports `_config` — uses `IServiceProvider.config`
- Only `config_impl.py` imports `_config` now (as intended by architecture)
- Removed legacy `DEPLOY_SESSION_KEEPALIVE_TIMEOUT` alias

### Deploy script improvements
- `gh_acreate_pr.ps1` now accepts `-branch` parameter (default `webgl-dev`). Use `-branch main` for production.
- `.claude/skills/deploy/SKILL.md` updated with environment table.

### GitHub Actions — Version display
- `.github/workflows/fly-deploy.yml` reads `version.txt`, shows `::notice::` annotation, prints version before/after deploy.

---

## Commits
| Hash | Version | Description |
|------|---------|-------------|
| `fda82af5` | 1.25 | feat: WebGL marker rendering with one-phase solve |
| `f531124d` | 1.25.1 | fix: markers persist after solve/stop, scramble in redo queue |
| `8e83e70f` | 1.25.2 | fix: restore two-phase solve for "solve" command |
| `707ba059` | 1.25.3 | fix: preserve solver type on reset and reset_session |
| `6f40a39a` | 1.25.4 | fix: don't abort solve on WebSocket reconnect |
| `5cc24162` | 1.25.5 | fix: unblock solver thread on reconnect during solve |
| `a88503d9` | — | docs: add WebGL backend section to gui_abstraction.md |
| `22deba4d` | — | feat: make blocking timeout configurable, abort solver on timeout |
| `f1c2940a` | — | chore: show version in GitHub Actions deploy logs |
| `6cdf4c23` | 1.25.6 | chore: bump version to test workflow version display |
| `e8a47f20` | 1.25.7 | feat: add session keepalive timeout to config protocol, clean _config violations |

---

## Known Issues
- **Slow solve animation:** ~8s per move even at speed 6. Marker rendering overhead in JS (10,000+ MARKERS console logs). Each `send_state()` rebuilds all marker Three.js objects.
- **Operator self-annotation overhead:** `operator_show_alg_annotation` wraps each compound alg with `annotate(h3=str(alg))`, sending extra state updates.

---

## All Checks Status
- Ruff: ✅
- Mypy: ✅ (356 files)
- Pyright: ✅ (0 errors)
- Non-GUI tests: ✅ (11389 passed)
- GUI tests: ✅ (36 passed)
- Manual WebGL test: ✅ (markers visible during solve!)
