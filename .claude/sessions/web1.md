<<<<<<< HEAD
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
=======
# Session: web1 — Dwalton Table-Based Solver

## Goal
Implement a new solver inspired by [dwalton76/rubiks-cube-NxNxN-solver](https://github.com/dwalton76/rubiks-cube-NxNxN-solver), which uses precomputed lookup/pruning tables with IDA* search based on Herbert Kociemba's two-phase algorithm.

## Research Phase

### What dwalton76's solver does
- For **3x3**: Delegates to the external `kociemba` CLI binary (not its own algorithm)
- For **NxN**: Reduces to a virtual 3x3 using IDA* with lookup tables, then calls kociemba
- Key technique: **precomputed pruning tables** as heuristics for IDA* search
- Cube state: 1-indexed list of 55 chars (ULFRBD order), moves as permutation tuples
- Move application: `new_state = [old_state[perm[i]] for i in range(55)]` — O(54) per move

### What we implemented
Instead of delegating to an external binary, we implemented the **full Kociemba two-phase algorithm from scratch** in pure Python, using the same table-based approach.

---

## Algorithm: Kociemba Two-Phase

### Overview
The cube's 4.3×10^19 states are split into two nested subgroups:

```
G0 (all states)  →  G1 = <U, D, R2, L2, F2, B2>  →  G2 = {solved}
     Phase 1                   Phase 2
```

- **Phase 1**: Reduce the cube so that corner orientations are correct, edge orientations are correct, and equator-layer (E-slice) edges are in the equator — regardless of exact permutation.
- **Phase 2**: Solve the remaining permutation using only moves that preserve G1 membership (U, U2, U', D, D2, D', R2, L2, F2, B2).

### Coordinate System

Each phase uses integer **coordinates** that compactly represent the relevant aspects of the cube state:

#### Phase 1 Coordinates (track orientation + E-slice membership)
| Coordinate | Range | What it encodes |
|-----------|-------|-----------------|
| **CO** (Corner Orientation) | 0..2186 (3^7) | Twist of 7 corners (8th determined by sum mod 3) |
| **EO** (Edge Orientation) | 0..2047 (2^11) | Flip of 11 edges (12th determined by sum mod 2) |
| **UD-slice** | 0..494 (C(12,4)) | Which 4 of 12 edge positions hold E-slice edges |

Phase 1 goal: CO=0, EO=0, UD-slice=494 (solved value)

#### Phase 2 Coordinates (track permutation)
| Coordinate | Range | What it encodes |
|-----------|-------|-----------------|
| **CP** (Corner Permutation) | 0..40319 (8!) | Which corner is in which position (Lehmer code) |
| **UDEP** (UD-Edge Permutation) | 0..40319 (8!) | Permutation of 8 U/D-layer edges |
| **EP** (E-slice Permutation) | 0..23 (4!) | Permutation of 4 E-slice edges within their slots |

Phase 2 goal: CP=0, UDEP=0, EP=0

### Move Tables
For each of the 18 moves (6 faces × {CW, 180°, CCW}), a **move table** stores how each coordinate changes:

```
co_move[move][old_coord] = new_coord
```

Built by: for each possible coordinate value, decode it to cubie arrays, apply the move via composition, re-encode to coordinate.

Total move table entries: 18 × (2187 + 2048 + 495 + 40320 + 40320 + 24) = ~1.5M integers

### Pruning Tables
Pruning tables store the **minimum number of moves** to reach the goal from any pair of coordinates. They serve as admissible heuristics for IDA*.

Built via **BFS from the goal state**:

```python
# Start: goal = 0 moves
table[goal_a * n_b + goal_b] = 0

# BFS: for each state at depth d, apply all moves to find depth d+1 states
while not all states filled:
    for each state at current depth:
        for each move:
            new_state = move_table[move][state]
            if new_state not yet visited:
                table[new_state] = depth + 1
```

#### Phase 1 Pruning Tables
| Table | Size | What it combines |
|-------|------|-----------------|
| **CO × UD-slice** | 2187 × 495 = 1,082,565 | Corner orient + E-slice position |
| **EO × UD-slice** | 2048 × 495 = 1,013,760 | Edge orient + E-slice position |

Heuristic: `h = max(CO×UD_table[co,ud], EO×UD_table[eo,ud])`

#### Phase 2 Pruning Tables
| Table | Size | What it combines |
|-------|------|-----------------|
| **CP × EP** | 40320 × 24 = 967,680 | Corner perm + E-slice perm |
| **UDEP × EP** | 40320 × 24 = 967,680 | UD-edge perm + E-slice perm |

Heuristic: `h = max(CP×EP_table[cp,ep], UDEP×EP_table[udep,ep])`

### IDA* Search

**Iterative Deepening A***: tries increasing depth limits, pruning branches where `g + h > threshold`.

```
Phase 1:
  for depth = 0, 1, 2, ..., 12:
    DFS with pruning: if h(co, eo, ud) > remaining_depth → prune
    When Phase 1 goal reached → compute Phase 2 coords from cubie state → run Phase 2

Phase 2:
  for depth = 0, 1, 2, ..., 18:
    DFS with pruning: if h(cp, udep, ep) > remaining_depth → prune
    When all coords = 0 → solution found!
```

**Move pruning**: Skip moves on the same face as the previous move, and enforce ordering for opposite faces (U before D, R before L, F before B) to avoid redundant sequences like `U D U`.

### Key Design Decision: Cubie State Tracking in Phase 1

Phase 2 coordinates (CP, UDEP, EP) can't be tracked through Phase 1 via move tables because moves mix UD and E-slice edges, making the UDEP/EP coordinates invalid when E-slice edges aren't in their slots.

**Solution**: Track full cubie arrays (cp, co, ep, eo) alongside Phase 1 coordinates. When Phase 1 completes, compute Phase 2 coordinates directly from the cubie state.

---

## Table Build Performance

All tables built in ~12 seconds on first use, cached in module-level variables (no disk I/O):

| Table Type | Entries | Build Time |
|-----------|---------|------------|
| Move tables (6 coords × 18 moves) | ~1.5M | ~8s |
| Pruning tables (4 tables) | ~4M | ~4s |
| **Total** | **~5.5M integers** | **~12s** |

Tables are **not persisted to disk** — purely in-memory. They're rebuilt each time the solver is first used in a session.

---

## File Structure

### New Files (6 files in `src/cube/domain/solver/_3x3/dwalton/`)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 5 | Package init, exports `Dwalton3x3` |
| `cubie_defs.py` | 105 | 8 corners, 12 edges, 18 moves as permutation+orientation arrays. Derives half/inverse turns from quarter turns via composition. |
| `coords.py` | 99 | Coordinate encoding functions: `corner_orientation_coord()`, `edge_orientation_coord()`, `ud_slice_coord()`, `corner_perm_coord()`, `edge8_perm_coord()`, `eslice_perm_coord()` |
| `tables.py` | 185 | Move table builder (decode coord → apply move → re-encode) and pruning table builder (BFS from goal). `build_all_tables()` entry point. |
| `search.py` | 120 | IDA* search for Phase 1 and Phase 2 with move pruning. `solve(cp, co, ep, eo)` entry point. |
| `Dwalton3x3.py` | 189 | Main solver class. Converts cube model → 54-char URFDLB string → cubie arrays → search → play solution moves. Implements `Solver3x3Protocol`. |

### Modified Files (5 files)

| File | Change |
|------|--------|
| `SolverName.py` | Added `DWALTON = SolverMeta("Dwalton")` to enum |
| `Solvers.py` | Added `dwalton()` factory method + `by_name()` match case |
| `Solvers3x3.py` | Added `dwalton()` factory method + `by_name()` match case |
| `README.md` | Added credits for dwalton76 and Herbert Kociemba |
| `.claude/sessions/web1.md` | This file |

---

## How the Cube Model ↔ Solver Bridge Works

1. **Cube → Facelet String**: Read 54 facelets in URFDLB order using dynamic color→face mapping (handles center color changes from slice moves)
2. **Facelet String → Cubies**: For each corner/edge position, match the 3/2 colors against all solved corner/edge color triples to identify which piece is there and its orientation
3. **Cubies → Coordinates**: Encode cubie arrays as integer coordinates
4. **Search**: IDA* finds a sequence of move names (e.g., `["R'", "U2", "F"]`)
5. **Execute**: Parse move names via `parse_alg()` and play via `op.play()`

### Corner Orientation Convention
- Twist 0: U/D reference sticker on U/D face (correct position)
- Twist 1: U/D reference sticker at position 1 in the corner triple
- Twist 2: U/D reference sticker at position 2 in the corner triple

This matches the cubie_defs move definitions where R move gives CO = [2,0,0,1,1,0,0,2].

---

## Test Results

**7,578 tests passed** (all solvers, all cube sizes):

```
Dwalton 3x3: 314 passed — all scramble seeds
Dwalton 4x4: 314 passed — with BeginnerReducer + parity handling
Dwalton 5x5: 314 passed — with BeginnerReducer
Dwalton 8x8: 314 passed — with BeginnerReducer + parity handling
Other solvers (LBL, CFOP, Kociemba, Cage, LBL-Big): all passed unchanged
```

Solve performance (after table build):
- Fast scrambles: 10-50ms
- Hard scrambles: 0.5-1.5s
- Table build (one-time): ~12s

---

## Commits
- Not yet committed — awaiting user review.
>>>>>>> new-solver
