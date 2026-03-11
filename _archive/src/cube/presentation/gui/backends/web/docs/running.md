# Web Backend — Running Instructions

## Start the Server

```bash
python -m cube.main_web
```

This starts an HTTP + WebSocket server on `http://localhost:8765` and auto-opens Chrome.

### Options

```bash
python -m cube.main_web --debug-all      # verbose logging
python -m cube.main_web --quiet           # minimal output
python -m cube.main_web --cube-size 5     # 5×5 cube
```

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m cube.main_web
```

## Keyboard Controls (in browser)

| Key | Action |
|-----|--------|
| R / L / U / D / F / B | Rotate face clockwise |
| Shift + R/L/U/D/F/B | Rotate face counter-clockwise |
| X / Y / Z | Rotate whole cube |
| 1 | Scramble |
| S | Solve |
| + / - | Speed up / slow down animation |

## Architecture

- **Python server** (`main_web.py`) — serves static files and sends rendering commands over WebSocket
- **Browser client** (`backends/web/static/cube.js`) — receives commands, renders 3D cube with Three.js (WebGL)
- **Three.js** loaded from CDN (r134) — no npm or build step needed
