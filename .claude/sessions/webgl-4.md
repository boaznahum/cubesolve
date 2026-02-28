# Session: webgl-4 — ES Modules + Vite Build System

## Commits
- `741e1bb8` — Split cube.js (1573 lines) into 10 ES modules
- `7f8ef989` — Add Vite build system + fix Dockerfile for deployment

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

## Development Modes
| Mode | URL | Needs npm? |
|------|-----|------------|
| Vite dev | http://localhost:5173 | Yes |
| Python-only | http://localhost:8766 | No (CDN import map) |
| Docker/Fly.io | production URL | Built in Dockerfile |

Note: Once we add npm UI widgets, Python-only mode won't have those features.
Eventually we'll drop Python-only mode entirely.

## Next — Queue UI with Beautiful Widgets

### Phase 2: Server-side undo/redo (Operator protocol)
- Undo/redo commands via OperatorProtocol
- Undo takes from last operation, plays it reversed, enters redo queue
- Redo plays forward from redo queue

### Phase 3: History panel UI + solver-as-redo
- **Beautiful npm widget** for the operation queue panel (left side of screen)
- Professional, elegant UI — NOT a simple list
- Show last N operations + redo operations
- Beautiful undo/redo buttons
- Fast replay button (reuses existing solver play/stop mechanism)
- Solver = private case of redo (solve fills redo queue, user steps through)
- Rename "redo" button to "next" when solver solution is queued
- **Decision:** Solve clears redo queue, replaces with solution

### Phase 4: Visual assist markers on stickers
- When redo operations exist, show visual hints ON the stickers
- Not above like drag arrows — integrated into the cell itself
- Beautiful signs that feel like part of the sticker
- Disappear when no redo operations available

### Widget library candidates (evaluate during Phase 3)
- Lit (web components, lightweight)
- Preact (React-like, tiny)
- Custom CSS + vanilla JS (if simple enough)
- Or: full React if complexity warrants it

## Key Files
- `fly.toml` — Fly.io deployment config
- `Dockerfile` — Multi-stage Docker build (Node + Python)
- `src/cube/presentation/gui/backends/webgl/package.json` — npm config
- `src/cube/presentation/gui/backends/webgl/vite.config.js` — Vite config
- `src/cube/presentation/gui/backends/webgl/static/` — frontend source
- `WEBGL-build-run.md` — Build & run instructions
- `zplaning/webgl-queue-undo-redo.md` — Full undo/redo feature spec
