# Session: web1 — Three.js Web Frontend

## Goal
Rewrite the JS client (`cube.js`) from Canvas 2D to Three.js WebGL for proper 3D rendering.

## What Was Done
1. **index.html** — Added Three.js r134 CDN (last version with UMD/script-tag support)
2. **cube.js** — Full rewrite:
   - THREE.WebGLRenderer, PerspectiveCamera, Scene
   - OpenGL-style matrix stack (push/pop/identity/translate/rotate/scale/multiply_matrix)
   - Shape rendering: quad (with auto black borders), quad_border, triangle, line
   - Frame lifecycle: dispose all geometries/materials each frame, rebuild from commands
   - Color conversion: 0-255 → 0.0-1.0
   - WebSocket + keyboard handling preserved
3. **WebRenderer.py** — Fixed `far` clipping plane: 100 → 1000 (cube at z=-400 was clipped)
4. **WebAppWindow.py** — Added rotation transforms (base + user) matching pyglet2 backend
5. **main_web.md** — Running instructions

## Key Findings
- Server sends `quad` not `quad_border` — display list compilation issue (not yet fixed)
- Workaround: JS adds black border lines to ALL quads client-side
- `far=100` default was clipping the cube at z=-400
- Three.js r134 is the latest on cdnjs with UMD build (r135+ is ES modules only)
- PyCharm's built-in browser interferes with the web backend — use command line

## Known Issues
- Server sends `quad` instead of `quad_border` (display list compilation doesn't emit borders)
- PyCharm run config causes scrambled cube on startup (built-in browser interference)
- `matplotlib` had to be added as dependency (`uv add matplotlib`)

## Key Bindings (same as pyglet2)
- `/` — solve, `1-9` — scramble, `x/y/z` — rotate view

## Status
Working: 3D cube visible in Chrome, keyboard controls, scramble/solve functional.
