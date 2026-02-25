# Session: web1 — Three.js Web Frontend + Animation

## Goal
1. ~~Rewrite the JS client (`cube.js`) from Canvas 2D to Three.js WebGL for proper 3D rendering.~~ ✅ Done
2. ~~**Get smooth face rotation animation working**~~ ✅ Done — face visually rotates 0°→90° over ~2s
3. **Build full web UI** — toolbar, slider controls, status display, mouse interaction

## Commits Made
- `fcd7063d` — Add web animation manager, Three.js lighting, and sticker gaps
- `33e81fe1` — Add web frontend design plan document
- `806e4eb3` — Rewrite web frontend to Three.js WebGL 3D rendering
- `9c77c2c7` — Fix web animation: prevent stale display list IDs during face rotation
- `f2b34590` — Add web toolbar with speed slider, buttons, and text overlays

## Current Status (session 6) — Two-Phase Solve + Size Slider + Bug Fixes

### What Works
- 3D cube renders correctly in Chrome via Three.js
- Keyboard controls work (R, L, U, D, F, B, scramble, solve, etc.)
- WebSocket communication is solid
- **Smooth face rotation animation** — async coroutine with real sleeps
- rAF render loop with FIFO queue renders frames smoothly
- **Toolbar** — Scramble, Solve, Reset buttons + Debug/Animation toggles
- **Speed slider** — drag to change speed 0-7, syncs with +/- keys bidirectionally
- **Size slider** — drag to change cube size 2-7, syncs with keyboard
- **Text overlays** — animation text (top-left) + solver status (bottom-left)
- **Two-phase solve** — `slv.solution()` computes instantly, `op.play()` replays with animation
- **Correct keyboard mapping** — `-`/`=` control size, numpad `+`/`-` control speed

### Two-Phase Solve Architecture
The critical innovation for the web backend. Solves the fundamental problem that
the solver runs synchronously (blocking asyncio) and would see stale state with
non-blocking animation.

**Flow:**
1. `slv.solution()` — computes full solution with animation OFF, undoes all moves, returns `Alg`
2. `op.play(solution_alg)` — replays solution with animation ON
3. `WebAnimationManager` queues all moves, plays them one at a time
4. Each move: animate → cleanup → apply model change → rebuild display lists → next

**Key insight:** No solver runs during animation. Model changes are deferred to
`_on_animation_done()`, matching the base class `_op_and_play_animation()` flow.
`AbstractSolver.solution()` already existed — we just needed to use it.

### Files Modified This Session
- `WebAnimationManager.py` — Rewrote to defer model changes (two-phase compatible)
- `WebAppWindow.py` — Added `_two_phase_solve()`, size slider handler, size broadcast sync
- `WebEventLoop.py` — Fixed `-`/`=` key mapping (size not speed), added size handler
- `cube.js` — Added size slider setup, removed debug bar per-frame DOM queries
- `index.html` — Added size slider, removed debug bar HTML/CSS, rounded canvas bottom

### Bug Fixes This Session
1. **Keyboard `-`/`=` controlling speed instead of size** — JS keycodes 189/187 were mapped
   to `Keys.NUM_SUBTRACT`/`Keys.NUM_ADD` (speed). Fixed to `Keys.MINUS`/`Keys.EQUAL` (size).
2. **Size slider not updating on keyboard size change** — `inject_command()` tracked speed
   changes but not size. Added `size_before`/`_broadcast_size()` check.
3. **Animation model-change timing** — Solver saw stale state because `run_animation()`
   returned immediately but model change was deferred. Fixed via two-phase solve approach.

---

## Feature Map: Pyglet2 vs Web Backend

### Legend
- ✅ = Implemented | ⚠️ = Partial | ❌ = Missing | 🔑 = Keyboard-only (no UI)

### 1. Core Rendering

| Feature | Pyglet2 | Web | Notes |
|---------|---------|-----|-------|
| 3D cube rendering | ✅ OpenGL | ✅ Three.js | Both work well |
| Face rotation animation | ✅ Blocking | ✅ Async 2-phase | Web uses rAF queue + deferred model |
| Sticker gaps (dark body) | ✅ | ✅ | Inset factor 0.08 |
| Lighting/shading | ✅ | ✅ | Three.js ambient+directional |
| Clear color (background) | ✅ | ✅ | Light gray default |

### 2. Toolbar Controls

| Feature | Pyglet2 | Web | Notes |
|---------|---------|-----|-------|
| Size slider (2-7) | ✅ Buttons | ✅ Slider | Web slider + keyboard sync |
| Size -/+ keyboard | ✅ | ✅ | `-`/`=` keys mapped correctly |
| Scramble button | ✅ Toolbar | ✅ Toolbar | Button + keyboard |
| Solve button | ✅ Toolbar | ✅ Toolbar | Two-phase solve |
| Reset button | ✅ Toolbar | ✅ Toolbar | Button + keyboard |
| Speed slider (0-7) | ✅ Buttons | ✅ Slider | Bidirectional sync |
| Debug toggle | ✅ Toolbar | ✅ Toolbar | Dbg:ON/OFF button |
| Animation toggle | ✅ Toolbar | ✅ Toolbar | Anim:ON/OFF button |

### 3. Status Displays

| Feature | Pyglet2 | Web | Notes |
|---------|---------|-----|-------|
| Animation text (solver phase) | ✅ Overlay | ✅ Overlay | Top-left on canvas |
| Solver status text | ✅ Bottom bar | ✅ Overlay | Bottom-left on canvas |
| Connection status | ❌ N/A | ✅ | Web-only |

### 4. Missing Features (Future)

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Drag to rotate cube | ✅ | ❌ | **Critical** |
| Click face to turn | ✅ Ray picking | ❌ | **Critical** |
| Scroll wheel zoom | ✅ | ❌ | Medium |
| Solver selector | ✅ Toolbar | 🔑 V | Medium |
| Solver step buttons | ✅ Dynamic | ❌ | Medium |
| Help popup | ✅ Modal | 🔑 H | Medium |
| Move history + count | ✅ Bottom bar | ❌ | Medium |
| Brightness/background | ✅ | ❌ | Low |
| Texture support | ✅ | ❌ | Low |
| Celebration effects | ✅ Confetti | ❌ | Low |
| Single-step mode | ✅ | ❌ | Low |

---

## Key Architecture Decisions

### Two-Phase Solve (Critical)
- **Problem:** Pyglet2 `run_animation()` blocks until animation completes. Web can't block (asyncio).
  If solver runs during non-blocking animation, it sees stale cube state → assertion failures.
- **Solution:** `slv.solution()` computes solution instantly (animation OFF), then `op.play()`
  replays with animation. No solver runs during animation playback.
- **Future benefit:** Enables teaching mode — solution is an `Alg` that can be stepped through.

### Web-Specific Advantages
- **Sliders** are better than discrete +/- buttons (continuous control)
- **rAF render loop** with frame queue is smoother than pyglet's timer-driven rendering
- **Cross-platform** — works in any browser, no native dependencies

### Web-Specific Challenges
- **Mouse interaction** requires ray casting in JS (not trivial with the matrix stack approach)
- **Solver blocks event loop** during `solution()` computation (brief freeze for complex cubes)

## Next Steps
- [ ] Test two-phase solve on 3x3 and larger cubes
- [ ] Implement mouse drag-to-rotate (Critical)
- [ ] Implement click face to turn (Critical)
- [ ] Add solver selector
