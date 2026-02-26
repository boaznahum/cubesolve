# WebGL Backend — Running Instructions

## Start the Server

```bash
python -m cube.main_webgl
```

This starts an HTTP + WebSocket server on `http://localhost:8766` and auto-opens the browser.

### Options

```bash
python -m cube.main_webgl --debug-all      # verbose logging
python -m cube.main_webgl --quiet           # minimal output
python -m cube.main_webgl --cube-size 5     # 5×5 cube
```

### Windows (PowerShell) — UTF-8 fix

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m cube.main_webgl
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

## Mouse Controls

| Action | Effect |
|--------|--------|
| Drag | Orbit camera around cube |
| Scroll | Zoom in/out |
| Alt+Drag / Right-drag | Pan camera |

## Architecture

Unlike the `web` backend (which streams rendering commands per frame), the `webgl` backend:

- **Python server** sends **cube state** (face colors as NxN grids of RGB values) and **animation events** (face/direction/duration)
- **Browser client** (`backends/webgl/static/cube.js`) **builds and owns the 3D model** using Three.js, rendering at 60fps on the GPU
- No per-frame server dependency — camera orbit, zoom, pan are all client-side
- Face rotation animations run client-side at 60fps with easing

### Message Protocol (Server → Client)

| Message | Description |
|---------|-------------|
| `cube_state` | NxN grid of RGB colors per face |
| `animation_start` | Face rotation event (face, direction, duration) |
| `animation_stop` | Cancel all client animations |
| `text_update` | Solver status, move count, animation text |
| `toolbar_state` | Debug/animation toggles, solver list |
| `version` | Server version string |
| `client_count` | Number of connected clients |

### Message Protocol (Client → Server)

| Message | Description |
|---------|-------------|
| `connected` | Client ready, request initial state |
| `key` | Keyboard input (keyCode + modifiers) |
| `command` | Toolbar button command (scramble, solve, etc.) |
| `set_speed` | Speed slider change |
| `set_size` | Size slider change |
| `set_solver` | Solver dropdown change |

## Ports

| Backend | Default Port |
|---------|-------------|
| `web` | 8765 |
| `webgl` | 8766 |
