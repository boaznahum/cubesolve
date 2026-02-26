# Session: web1 — Three.js Web Frontend + Animation

## Goal
1. ~~Rewrite the JS client (`cube.js`) from Canvas 2D to Three.js WebGL for proper 3D rendering.~~ ✅ Done
2. ~~**Get smooth face rotation animation working**~~ ✅ Done
3. **Build full web UI** — toolbar, slider controls, status display, mouse interaction

## Commits Made
- `fcd7063d` — Add web animation manager, Three.js lighting, and sticker gaps
- `33e81fe1` — Add web frontend design plan document
- `806e4eb3` — Rewrite web frontend to Three.js WebGL 3D rendering
- `9c77c2c7` — Fix web animation: prevent stale display list IDs during face rotation
- `f2b34590` — Add web toolbar with speed slider, buttons, and text overlays
- `d9ac26f1` — Two-phase solve, size slider, keyboard fix, remove debug bar
- `cb267a35` — Add try/finally to animation async task to prevent stuck queue
- `58113367` — Fix infinite loop: AnnotationAlg must disable animation on re-play
- `e845e26f` — Add Escape key to cancel animation and discard queued moves
- `d14925fc` — Add Stop button and wire STOP_ANIMATION command

## Current Status (session 7)

### What Works
- 3D cube renders correctly in Chrome via Three.js
- Keyboard controls work (R, L, U, D, F, B, scramble, etc.)
- WebSocket communication is solid
- **Smooth face rotation animation** — async coroutine with real sleeps
- rAF render loop with FIFO queue renders frames smoothly
- **Toolbar** — Scramble, Solve, Stop, Reset buttons + Debug/Animation toggles
- **Speed slider** — drag to change speed 0-7, syncs with keyboard bidirectionally
- **Size slider** — drag to change cube size 2-7, syncs with keyboard
- **Text overlays** — animation text (top-left) + solver status (bottom-left)
- **Two-phase solve** — `slv.solution()` computes instantly, `op.play()` replays with animation
- **Stop button / S key** — cancels animation, discards remaining queued moves
- **Correct keyboard mapping** — `-`/`=` control size, numpad `+`/`-` control speed

### Two-Phase Solve Architecture
The critical innovation for the web backend:

1. `slv.solution()` — computes full solution with animation OFF, undoes all moves, returns `Alg`
2. `op.play(solution_alg)` — replays solution with animation ON
3. `WebAnimationManager` queues all moves, plays them one at a time
4. Each move: animate → cleanup → apply model change → rebuild display lists → next

**Key insight:** No solver runs during animation. Model changes are deferred to
`_on_animation_done()`, matching the base class `_op_and_play_animation()` flow.
`AbstractSolver.solution()` already existed — we just needed to use it.

### Critical Bugs Fixed This Session
1. **Infinite loop / RecursionError** — `_process_next()` used recursion for non-animatable
   moves. With many AnnotationAlgs, this blew the stack. Fixed: use a `while` loop.
2. **AnnotationAlg re-entry** — `_process_next()` called `move.op(alg, False)` for annotations
   without disabling animation. Operator re-entered animation branch → `run_animation()` →
   re-queued the annotation → infinite loop. Fixed: use `_apply_model_change()` which wraps
   with `with_animation(animation=False)`.
3. **Stuck queue after crash** — If `_animate_async` or `_on_animation_done` crashed,
   `_is_processing` stayed True forever. Fixed: `try/finally` with emergency reset.
4. **Keyboard `-`/`=` controlling speed instead of size** — JS keycodes 189/187 were mapped
   to `Keys.NUM_SUBTRACT`/`Keys.NUM_ADD` (speed). Fixed to `Keys.MINUS`/`Keys.EQUAL` (size).
5. **Size slider not syncing on keyboard** — `inject_command()` tracked speed changes but
   not size. Added `size_before`/`_broadcast_size()` check.

### Key Files
- `WebAnimationManager.py` — Non-blocking animation with deferred model changes, cancel support
- `WebAppWindow.py` — Two-phase solve, command intercepts (SOLVE_ALL, STOP_ANIMATION), sliders
- `WebEventLoop.py` — Key mapping, WebSocket message handlers for speed/size/commands
- `static/index.html` — Toolbar HTML/CSS (buttons, sliders, overlays)
- `static/cube.js` — Three.js renderer, slider wiring, text overlay updates

### Cube.py Change
- Default color scheme changed from `purple_pink()` to `boy_scheme()` (user preference)

---

## Feature Map: Pyglet2 vs Web Backend

### Implemented ✅

| Feature | Pyglet2 | Web | Notes |
|---------|---------|-----|-------|
| 3D cube rendering | OpenGL | Three.js | Both work well |
| Face rotation animation | Blocking | Async 2-phase | Web defers model changes |
| Sticker gaps | ✅ | ✅ | Inset factor 0.08 |
| Lighting/shading | ✅ | ✅ | Three.js ambient+directional |
| Size slider (2-7) | Buttons | Slider | Bidirectional keyboard sync |
| Scramble button | ✅ | ✅ | Button + keyboard |
| Solve button | ✅ | ✅ | Two-phase solve |
| Stop button | ✅ | ✅ | S key + toolbar button |
| Reset button | ✅ | ✅ | Button + keyboard |
| Speed control (0-7) | Buttons | Slider | Bidirectional sync |
| Debug toggle | ✅ | ✅ | Dbg:ON/OFF button |
| Animation toggle | ✅ | ✅ | Anim:ON/OFF button |
| Animation text overlay | ✅ | ✅ | Top-left on canvas |
| Solver status text | ✅ | ✅ | Bottom-left on canvas |

### Missing ❌ (Future Work)

| Feature | Priority | Notes |
|---------|----------|-------|
| Drag to rotate cube | **Critical** | Mouse interaction |
| Click face to turn | **Critical** | Ray picking |
| Scroll wheel zoom | Medium | |
| Solver selector | Medium | V key works but no UI |
| Solver step buttons | Medium | Dynamic based on solver |
| Help popup | Medium | H key works but no modal |
| Move history + count | Medium | |
| Brightness/background | Low | |
| Texture support | Low | |
| Celebration effects | Low | |
| Single-step mode | Low | |

---

## Architecture Notes

### WebAnimationManager Safety
- `_process_next()` uses a **while loop** (not recursion) to skip non-animatable moves
- ALL model changes go through `_apply_model_change()` which disables animation to prevent re-entry
- `_animate_async` has `try/finally` that catches crashes in both the animation loop AND `_on_animation_done`
- Emergency reset ensures `_is_processing` never gets permanently stuck

### Browser Caching
- Static files (index.html, cube.js) are cached by the browser
- After code changes, users must **Ctrl+F5** (hard refresh) to pick up new HTML/JS
- Consider adding cache-busting query params in the future

### PYTHONIOENCODING
- Must set `PYTHONIOENCODING=utf-8` on Windows to prevent Unicode crash from logger box-drawing chars

## Next Steps
- [ ] **Add full mouse controls** — detailed plan in `web1-mouse-controls.md`
  - [ ] Step 1: Sticker metadata in Python quad commands
  - [ ] Step 2: Tag Three.js meshes with userData
  - [ ] Step 3: Right-click drag orbit rotation
  - [ ] Step 4: Scroll wheel zoom
  - [ ] Step 5: ALT+left-drag pan
  - [ ] Step 6: Shift/Ctrl click-to-turn face
  - [ ] Step 7: Store cube_info geometry in JS
  - [ ] Step 8: Drag-to-turn face
- [ ] Add solver selector UI
- [ ] Consider cache-busting for static files
