# WebGL Backend - Session Notes

## Branch: `web3-new-app` (from `web2`)

## Overview
New `webgl/` backend where server sends **cube state** (face colors + animation events) and the Three.js client builds and owns the 3D model locally, rendering at 60fps.

## Commits
- `36ac2e05` — Add WebGL backend with client-side 3D cube rendering (session 1-3)
- `be8b8809` — Webgl issues file
- `fab89e2f` — Fix rotation directions, row mapping, animation state ordering (session 4)

## Files Created (all new)

### Python Backend
| File | Purpose |
|------|---------|
| `src/cube/presentation/gui/backends/webgl/__init__.py` | Factory `create_backend()` |
| `src/cube/presentation/gui/backends/webgl/WebglRenderer.py` | No-op stub (rendering is client-side) |
| `src/cube/presentation/gui/backends/webgl/WebglWindow.py` | Window/TextRenderer protocol stubs |
| `src/cube/presentation/gui/backends/webgl/WebglEventLoop.py` | Async aiohttp server on port 8766 |
| `src/cube/presentation/gui/backends/webgl/WebglAppWindow.py` | Thin shell delegating to sessions |
| `src/cube/presentation/gui/backends/webgl/SessionManager.py` | Session lifecycle + GeoIP |
| `src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py` | Sends animation events to client |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py` | State-based session (no per-frame rendering) |
| `src/cube/presentation/gui/backends/webgl/CubeStateSerializer.py` | Extracts NxN face color grids |
| `src/cube/main_webgl.py` | Entry point (`python -m cube.main_webgl`) |

### Client (Three.js)
| File | Purpose |
|------|---------|
| `src/cube/presentation/gui/backends/webgl/static/index.html` | Toolbar, overlays, dark background |
| `src/cube/presentation/gui/backends/webgl/static/cube.js` | Full 3D cube (~960 lines) |

### Deployment
| File | Purpose |
|------|---------|
| `fly-webgl.toml` | Fly.io config (app=cubesolve-webgl, port=8766) |
| `Dockerfile.webgl` | Docker build for webgl backend |

### Modified Files
| File | Change |
|------|--------|
| `src/cube/presentation/gui/BackendRegistry.py` | Added "webgl" to BACKENDS + get_backend() |
| `src/cube/main_any_backend.py` | Added "webgl" to argparse choices |
| `src/cube/resources/version.txt` | version bumps |
| `fly-io-deploy.md` | Added webgl deployment docs |

---

## Architecture

```
Server sends:
  cube_state  → {size, faces: {U: [[r,g,b],...], F:..., ...}}
  animation_start → {face, direction, slices, duration_ms, alg, state}
  animation_stop  → flush client queue
  text_update, toolbar_state, version, client_count

Client sends:
  connected, key, command, set_speed, set_size, set_solver
```

### CubeStateSerializer Convention
- `grid[row][col]` where **row 0 = bottom**, row N-1 = top
- Flattened row-major: flat index 0 = bottom-left

### Animation Flow
1. Server: `WebglAnimationManager._process_next()` dequeues move
2. Server: applies model change FIRST (`_apply_model_change`)
3. Server: sends `animation_start` with post-move state embedded
4. Server: sends `cube_state` (same post-move state)
5. Client: `AnimationQueue.enqueue()` → `_processNext()`
6. Client: creates temp group, attaches affected stickers, animates rotation
7. Client: on completion, reparents stickers back, applies state colors, resets positions

---

## Bugs Fixed in Sessions 2 & 3

1. Body mesh too large (replaced ExtrudeGeometry with BoxGeometry)
2. D face stickers placed on U face (fixed normal calculation)
3. Sticker edge overlap (switched to flat ShapeGeometry)
4. Only face surface rotated (added position-based layer selection)
5. Sticker position drift (added resetPositions after each animation)
6. Rotation pivot at origin (added pivotMap for face centers)
7. Whole-cube/slice not animated (added x/y/z and M/E/S to affected stickers)
8. Camera reset keys not working (added client-side Alt+C/Ctrl+C handling)

## Bugs Fixed in Session 4

### 9. Row mapping inverted
- Server row 0 = bottom, client placed row 0 at top
- Fix: `cy = (row + 0.5) * cellSize - half` (both build and resetPositions)

### 10. Animation rotation direction wrong for x/z-axis faces
- R, L, F, B, M, S, x, z all had inverted angles
- Fix: Swapped angle/-angle for x-axis and z-axis entries in rotation map

### 11. Animation state ordering (stickers snap back after animation)
- Server sent animation_start BEFORE model change → client had pre-move state
- Fix: Apply model change FIRST, then embed post-move state in animation_start message

### 12. Browser shortcuts captured (Ctrl+R, F5, F12)
- Fix: Early return in _bindKeyboard for browser shortcuts

### 13. Y-axis rotation direction (U, D, E, y)
- Swapped y-axis signs: U: angle, D: -angle, E: -angle, y: angle
- User confirmed U direction now correct

### 14. X/Y/Z face name case mismatch (NO ANIMATION for x/y/z)
- Server's `str(WholeCubeAlg)` returns uppercase "X"/"Y"/"Z"
- Client rotation map uses lowercase "x"/"y"/"z"
- Fix: Added X→x, Y→y, Z→z mapping in `_alg_to_face_name`

### 15. Sliced alg face name extraction ("[2:2]M" → "[" instead of "M")
- `str(Algs.M[2])` = "[2:2]M", first char is "["
- Fix: Changed `_alg_to_face_name` to search for face letter in string instead of just first char

---

## CURRENT STATUS (Session 5)

### Working ✅
- R, L, F, B, M, S face rotations (correct direction + animation)
- U, D, E rotations (correct direction, user confirmed)
- Cube state correctly updates after all moves
- Row mapping correct (bottom = row 0)
- Browser shortcuts (F5, Ctrl+R, F12) work
- Animation state ordering (post-move state embedded)

### In Progress / Needs Testing 🔄
- **x/y/z whole-cube animation** — BOTH server + client-side fix applied, needs browser refresh + testing
  - Root cause: `str(WholeCubeAlg)` returns uppercase "X"/"Y"/"Z", client map uses lowercase
  - Server fix: `_alg_to_face_name` maps X→x, Y→y, Z→z (may still be cached in .pyc)
  - Client fix: `_processNext()` normalizes face name before lookup (belt-and-suspenders)
- **Sliced slice animation** (M[2], E[2] on 4x4) — BOTH server + client-side fix applied, needs testing
  - Root cause: `str(Algs.M[2])` = "[2:2]M", first char is "[" not "M"
  - Server fix: `_alg_to_face_name` scans for face letter instead of first char
  - Client fix: `_processNext()` scans multi-char face names for known letters

### Known Remaining Bugs ❌
- **Speed slider change → stuck** (bug #2 in issues file)
- **Orange displays as yellow** (bug #17 — color mapping issue)
- **Mouse controls** — only orbits, doesn't rotate faces (bug #3)
- **e.keyCode deprecated** (bug #19 — should use e.code)
- **WideFaceAlg/DoubleLayerAlg** — may not animate properly

---

## Key Code Sections

### _getRotationAxis map (cube.js ~line 434)
```
R: angle, L: -angle     (x-axis)
U: angle, D: -angle     (y-axis)
F: angle, B: -angle     (z-axis)
M: -angle (follows L), E: -angle (follows D), S: angle (follows F)
x: angle, y: angle, z: angle
```
Where angle = -π/2 for CW (direction=1), +π/2 for CCW (direction=-1)

### _alg_to_face_name (ClientSession.py)
- Searches string for first known face letter (handles "[2:2]M" format)
- Maps X→x, Y→y, Z→z (uppercase WholeCubeAlg names)

---

## How to Test
```bash
python -m cube.main_webgl          # Start server
python -m cube.main_webgl --cube-size 3   # Start with 3x3
```
Open http://localhost:8766 in browser.
