# WebGL Backend — Build & Run

## Prerequisites

```bash
# Install frontend dependencies (one-time)
cd src/cube/presentation/gui/backends/webgl
npm install
```

## Development (two terminals)

```bash
# Terminal 1: Python backend (WebSocket + cube logic)
python -m cube.main_webgl

# Terminal 2: Vite dev server (HMR + auto-reload)
cd src/cube/presentation/gui/backends/webgl
npm run dev
```

**Open http://localhost:5173** (Vite) — NOT the Python port.
Vite proxies `/ws` to Python automatically, plus gives you HMR (instant reload on JS changes).

| URL | When to use |
|-----|-------------|
| http://localhost:5173 | Development with Vite (recommended) |
| http://localhost:8766 | Python-only, no Node.js needed |

### Alternative: Python-only (no Vite, no Node.js needed)

```bash
python -m cube.main_webgl --open-browser
```

Opens http://localhost:8766 — serves source files directly via import maps. No HMR, no npm packages.

### Options

```bash
python -m cube.main_webgl --open-browser    # auto-open browser
python -m cube.main_webgl --debug-all       # verbose logging
python -m cube.main_webgl --quiet           # minimal output
python -m cube.main_webgl --cube-size 5     # 5×5 cube
```

### Windows (PowerShell) — UTF-8 fix

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m cube.main_webgl --open-browser
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
