# Session: webgl-4 — ES Modules + Vite Build System

## Completed

### Phase 1: Split cube.js into ES Modules (DONE — commit 741e1bb8)
- Split monolithic `cube.js` (1573 lines) into 10 ES modules in `static/js/`
- Native import map for Three.js ESM (no build tool yet)
- Updated `WebglEventLoop.py` for subdirectory serving
- Updated `index.html` with importmap + module script
- Created `design.md` with module structure
- Version: 1.7.0 → 1.8.0
- All checks pass (ruff, mypy, pyright)

## TODO — Build System Migration (Vite)

### Why Vite?
- Need npm packages for beautiful UI widgets (queue panel, undo/redo buttons, assist markers)
- Current setup uses CDN import maps — can't use npm packages
- Vite gives: npm dependency management, HMM dev server, production bundling, CSS modules

### Tasks (IN ORDER):

1. **Add `package.json` + Vite config** in `src/cube/presentation/gui/backends/webgl/`
   - `npm init`, add vite as dev dep, add three as dep
   - Vite config: dev server proxies /ws to Python backend
   - Entry point: `src/js/main.js` (Vite convention)

2. **Rename `fly-webgl.toml` → `fly.toml`** (or update to reference correct Dockerfile)
   - Current: `fly-webgl.toml` references `Dockerfile`
   - Fly.io expects `fly.toml` by default

3. **Update Dockerfile** for Vite build step
   - Add Node.js install stage (multi-stage build)
   - `npm ci && npm run build` to produce `dist/` with bundled JS
   - Python serves `dist/` instead of `static/`
   - Or: pre-build and COPY dist/ into image

4. **Update `docs/running.md`** with new dev workflow
   - `npm install` step
   - `npm run dev` for Vite dev server (with HMR)
   - `npm run build` for production bundle
   - Python server serves built files

5. **Restructure static/ for Vite**
   - Move JS source to `src/js/` (Vite convention)
   - `index.html` stays at root of webgl static dir
   - Vite outputs to `dist/`

## Future Phases (from zplaning/webgl-queue-undo-redo.md)

- **Phase 2:** Server-side undo/redo (Operator protocol + commands)
- **Phase 3:** History panel UI + solver-as-redo (needs npm widgets)
- **Phase 4:** Visual assist markers on stickers
- **Decision:** Solve clears redo queue, replaces with solution

## Key Files
- `fly-webgl.toml` — Fly.io deployment config
- `Dockerfile` — Docker build (Python 3.14-slim, uv)
- `src/cube/presentation/gui/backends/webgl/static/` — current static files
- `src/cube/presentation/gui/backends/webgl/docs/running.md` — running instructions
- `zplaning/webgl-queue-undo-redo.md` — full undo/redo feature spec
