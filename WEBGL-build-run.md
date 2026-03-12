# WebGL Backend — Build & Run

## Prerequisites

1. **Node.js** (v18+) — download from https://nodejs.org/ (includes `npm`)
2. Install frontend dependencies (one-time):

```bash
cd src/cube/presentation/gui/backends/webgl
npm install          # installs Vite, Three.js, and other dependencies
```

## Development (two terminals)

```powershell
# Terminal 1: Python backend with auto-reload on .py changes
$env:PYTHONIOENCODING="utf-8"; watchfiles ".venv\Scripts\python.exe -m cube.main_webgl" src/cube/
```
```powershell
# Terminal 2: Vite dev server (HMR for JS changes)
cd src/cube/presentation/gui/backends/webgl
npm run dev
```

**Open http://localhost:5173** (Vite) — NOT the Python port.
Vite proxies `/ws` to Python automatically, plus gives you HMR (instant reload on JS changes).

`watchfiles` monitors `src/cube/` and auto-restarts the Python server when `.py` files change.
Install once: `uv add --dev watchfiles`.

| URL | When to use |
|-----|-------------|
| http://localhost:5173 | Development with Vite (recommended) |
| http://localhost:8766 | Python-only, no Node.js needed |

### Python-only (no Vite, no Node.js needed)

```powershell
$env:PYTHONIOENCODING="utf-8"; watchfiles ".venv\Scripts\python.exe -m cube.main_webgl --open-browser" src/cube/
```

Opens http://localhost:8766 — serves source files directly via import maps. No bundling needed.

### Options

```powershell
python -m cube.main_webgl --open-browser    # auto-open browser
python -m cube.main_webgl --debug-all       # verbose logging
python -m cube.main_webgl --quiet           # minimal output
python -m cube.main_webgl --cube-size 5     # 5×5 cube
```

## Production Build

```bash
cd src/cube/presentation/gui/backends/webgl
npm run build
```

Outputs bundled files to `static/dist/`. The Python server auto-detects and serves from there.

## Deploy (Fly.io)

```bash
fly deploy          # uses fly.toml + Dockerfile (multi-stage: Node build + Python)
```

Port: 8766 (vs 8765 for the `web` backend)
