# Session: webgl-4 — ES Modules + Vite + History Panel + Undo/Redo

## Branch: webgl-4
## Current Version: 1.9.6

## All Commits (chronological)

| Commit | Description | Version |
|--------|-------------|---------|
| `741e1bb8` | Split cube.js (1573 lines) into 10 ES modules | 1.8.0 |
| `7f8ef989` | Add Vite build system + fix Dockerfile for deployment | 1.8.1 |
| `6b81f215` | Session notes, design.md, build-run docs | 1.8.1 |
| `668f09fb` | Fix WebGL docs: browser no longer auto-opens | 1.8.1 |
| `8204b1c7` | Set D0 to 2000ms for slower debugging animations | 1.8.1 |
| `a4777d0b` | Configurable speed range formula | 1.8.1 |
| `51fcb3ab` | Remove arbitrary speed floor | 1.8.1 |
| `9ba442df` | Add animation & stop button design document | 1.8.1 |
| `8769777e` | History panel UI + server-side undo/redo queue | 1.9.0 |
| `177f5c42` | Use separate FLY_API_TOKEN_DEV for dev deploys | 1.9.0 |
| `ae8d3db0` | Token management + GitHub Actions docs | 1.9.0 |
| `6806b06c` | Solve fills redo queue, fast-play, last-done highlight | 1.9.1 |
| `3e1c37d8` | Add fast-forward >> and fast-rewind << buttons | 1.9.2 |
| `a74fd836` | Stoppable fast-play/rewind, instant scramble, context labels | 1.9.4 |
| `c4112545` | Fix redo queue order, NOW marker info, next-redo highlight | 1.9.6 |
| `d0be4c5d` | Clean up: remove F badges, simplify NOW marker | 1.9.6 |

## Completed Features

### Phase 1: ES Modules Split (DONE)
- Split monolithic `cube.js` (1573 lines) into 10 ES modules in `static/js/`
- Native import map for Three.js ESM
- Updated `WebglEventLoop.py` for subdirectory serving

### Vite Build System (DONE)
- `package.json` + `vite.config.js` in webgl backend dir
- Multi-stage Dockerfile (Node builds frontend → Python serves)
- Python auto-serves `dist/` (production) or `static/` (dev with CDN import map)

### History Panel UI (DONE)
- `static/js/HistoryPanel.js` — glassmorphism panel
- Two-column layout (panel left + canvas right)
- Done items (solid blue), redo items (faded dashed)
- NOW marker with solver step count: `NOW (solver 21)`
- Last-done item highlighted (blue glow)
- First redo item highlighted (orange glow) — shows next to play
- SCR badge for scramble, S for slice, R for rotation
- Footer buttons: `<<` (fast-rewind) `<` (undo) `>` (redo/play) `>>` (fast-play/play-all)

### Server-side Undo/Redo (DONE)
- **OperatorProtocol** — `redo()`, `redo_queue()`, `clear_redo()`, `enqueue_redo()`
- **Operator** — `_redo_queue` (list), `_in_undo_redo` flag
  - `undo()` pushes to redo queue (LIFO)
  - `redo()` pops from redo queue (LIFO)
  - `enqueue_redo()` stores reversed so pop() gives correct FIFO order for solver
  - `_play()` clears redo on new operations (not during undo/redo)
  - `reset()` clears both history and redo
- **ClientSession** — `send_history_state()`, `_classify_alg()`
  - `redo_source` field: `"solver"` or `"undo"` for context-aware UI labels
  - Reverses redo queue for display (internal storage is reversed for LIFO pop)

### Solve-as-Redo (DONE)
- `_two_phase_solve()` flattens solution and enqueues as redo (not auto-play)
- User controls playback: redo (one step), fast-play (all steps)
- Kociemba 3x3 gives ~21 steps, Reducer 4x4 gives ~564 steps

### Stoppable Fast-play/Rewind (DONE)
- Step-by-step execution using `schedule_once()` with animation duration delay
- `_fast_playing` flag checked between steps
- Stop button sets flag to False → remaining items stay in queue
- No more draining the entire queue in a synchronous loop

### Instant Scramble (DONE)
- Scramble intercepted in `_handle_command("scramble")`
- Wrapped in `op.with_animation(animation=False)` — applies instantly
- User can replay via fast-rewind + fast-play

### Context-aware Button Labels (DONE)
- Solver redo: `>` = "Play next step", `>>` = "Play all"
- Manual redo: `>` = "Redo", `>>` = "Redo all"
- Based on `_redo_is_solver` flag sent as `redo_source` in history_state

### Fly.io Auto-Deploy (DONE)
- GitHub Actions: push to `webgl-4` → deploy to `cubesolve-dev`
- Per-app deploy tokens: `FLY_API_TOKEN` (prod), `FLY_API_TOKEN_DEV` (dev)

## Known Issues / Bugs for QA

### Duplicate history_state messages from Vite HMR
- Each Vite HMR update creates new HistoryPanel instances but old listeners persist
- Causes 3-5 duplicate `history_state` log entries per action
- Harmless — final state is always correct (last message wins)
- Fix: proper HMR cleanup in main.js (low priority)

### Scramble shows as single compound alg in history
- Scramble appears as `{scrmbl1/468[468]}` — one item, not individual moves
- This is correct behavior (scramble is a SeqAlg)
- User can fast-rewind to undo it

### User workflow notes
- **Python restart required** for any server-side changes (Operator, ClientSession, etc.)
- **No restart needed** for JS/CSS changes (Vite HMR auto-reloads)
- **Always bump version** so user sees update in browser status bar
- **Always tell user** when Python restart is needed

## Key Files Modified in This Session

| File | What changed |
|------|-------------|
| `src/cube/domain/solver/protocols/OperatorProtocol.py` | Added redo protocol methods |
| `src/cube/application/commands/Operator.py` | Full undo/redo implementation |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py` | History state, solve-as-redo, fast-play/rewind, instant scramble |
| `src/cube/presentation/gui/backends/webgl/static/js/HistoryPanel.js` | Panel UI, server data binding |
| `src/cube/presentation/gui/backends/webgl/static/index.html` | Panel CSS, layout, badges |
| `.github/workflows/fly-deploy.yml` | Fixed branch trigger + dev token |

## Development Modes

| Mode | URL | Needs npm? |
|------|-----|------------|
| Vite dev | http://localhost:5173 | Yes (`npm run dev`) |
| Python-only | http://localhost:8766 | No (CDN import map) |
| Docker/Fly.io | cubesolve-dev.fly.dev | Built in Dockerfile |

## Next Steps / Future Work

- **Visual assist markers on stickers** (Phase 4) — when redo exists, show hints on stickers
- **Stop button during single redo/undo animation** — currently only stops fast-play
- **Widget library evaluation** — Lit, Preact, or vanilla JS
- **Better scramble display** — show individual moves instead of compound alg
- **Mobile responsive improvements** — history panel sizing
