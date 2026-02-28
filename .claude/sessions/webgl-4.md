# Session: webgl-4 — ES Modules + Vite Build System + History Panel

## Commits
- `741e1bb8` — Split cube.js (1573 lines) into 10 ES modules
- `7f8ef989` — Add Vite build system + fix Dockerfile for deployment
- `6b81f215` — Session notes, design.md, build-run docs
- (pending) — History panel UI + server-side undo/redo

## Completed

### Phase 1: Split cube.js into ES Modules (DONE — commit 741e1bb8)
- Split monolithic `cube.js` (1573 lines) into 10 ES modules in `static/js/`
- Native import map for Three.js ESM (no build tool yet)
- Updated `WebglEventLoop.py` for subdirectory serving
- Updated `index.html` with importmap + module script
- Created `design.md` with module structure
- Version: 1.7.0 → 1.8.0

### Build System (Vite) — DONE — commit 7f8ef989
- `package.json` + `vite.config.js` in webgl backend dir
- Multi-stage Dockerfile (Node builds frontend → Python serves)
- `fly-webgl.toml` → `fly.toml`
- Python auto-serves `dist/` (production) or `static/` (dev with CDN import map)
- Updated WEBGL-build-run.md, WEBGL-README.md, running.md
- Version: 1.8.0 → 1.8.1

### History Panel UI — DONE (pending commit)
- Created `static/js/HistoryPanel.js` — glassmorphism panel with done/redo items
- Updated `index.html` — two-column layout (panel + canvas), extensive CSS
- Updated `main.js` — wired HistoryPanel to message handler
- User confirmed: "beautiful !!!"

### Server-side Undo/Redo — DONE (pending commit)
- **OperatorProtocol** — added `redo()`, `redo_queue()`, `clear_redo()` methods
- **Operator** — added `_redo_queue`, `_in_undo_redo` flag
  - `undo()` pushes undone alg to redo queue
  - `redo()` pops from redo queue, plays forward
  - `_play()` clears redo queue on new operations (not during undo/redo)
  - `reset()` clears redo queue
- **ClientSession** — added `send_history_state()`, `_classify_alg()`
  - Classifies algs: scramble, rotation, slice, face, move
  - Sends history_state after: connect, commands, face turns, solve, size/solver change
  - Handles undo/redo/clear_history commands from client
- **HistoryPanel.js** — removed mock data, starts empty, receives real server data

## Development Modes
| Mode | URL | Needs npm? |
|------|-----|------------|
| Vite dev | http://localhost:5173 | Yes |
| Python-only | http://localhost:8766 | No (CDN import map) |
| Docker/Fly.io | production URL | Built in Dockerfile |

Note: Once we add npm UI widgets, Python-only mode won't have those features.
Eventually we'll drop Python-only mode entirely.

## Next Steps

### Solver-as-redo
- When user presses solve, solution goes into redo queue
- User steps through with "Next" (redo) button or "Fast Play"
- Solve clears existing redo queue, replaces with solution

### Fast Play button
- Reuses existing solver play/stop mechanism
- Plays through redo queue with animation

### Phase 4: Visual assist markers on stickers
- When redo operations exist, show visual hints ON the stickers
- Not above like drag arrows — integrated into the cell itself
- Beautiful signs that feel like part of the sticker
- Disappear when no redo operations available

### Widget library candidates (evaluate later)
- Lit (web components, lightweight)
- Preact (React-like, tiny)
- Custom CSS + vanilla JS (if simple enough)

## Key Files
- `fly.toml` — Fly.io deployment config
- `Dockerfile` — Multi-stage Docker build (Node + Python)
- `src/cube/presentation/gui/backends/webgl/package.json` — npm config
- `src/cube/presentation/gui/backends/webgl/vite.config.js` — Vite config
- `src/cube/presentation/gui/backends/webgl/static/` — frontend source
- `src/cube/presentation/gui/backends/webgl/static/js/HistoryPanel.js` — history panel
- `src/cube/application/commands/Operator.py` — undo/redo logic
- `src/cube/domain/solver/protocols/OperatorProtocol.py` — protocol with redo
- `WEBGL-build-run.md` — Build & run instructions
- `zplaning/webgl-queue-undo-redo.md` — Full undo/redo feature spec
