# WebGL Backend - Session Notes

## Branch: `web3-new-app` (from `web2`)

## Overview
New `webgl/` backend where server sends **cube state** (face colors + animation events) and the Three.js client builds and owns the 3D model locally, rendering at 60fps.

## Git Status: NOT COMMITTED
All changes are uncommitted. No commits have been made on this branch for the webgl work.
Must run all 5 checks before committing (ruff, mypy, pyright, non-GUI tests, GUI tests).

## Files Created (all new, untracked)

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
| `src/cube/presentation/gui/backends/webgl/static/cube.js` | Full 3D cube (~950 lines) |

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
| `src/cube/resources/version.txt` | 1.2.4 → 1.3.0 |
| `fly-io-deploy.md` | Added webgl deployment docs |

---

## Architecture

```
Server sends:
  cube_state  → {size, faces: {U: [[r,g,b],...], F:..., ...}}  (NxN flat arrays)
  animation_start → {face, direction, duration_ms}
  animation_stop  → flush client queue
  text_update, toolbar_state, version, client_count

Client sends:
  connected, key, command, set_speed, set_size, set_solver

Key difference from web/ backend:
  web/:   Server renders → sends draw commands → Client replays (dumb)
  webgl/: Server sends state → Client builds 3D model + animates (smart)
```

### CubeStateSerializer Convention
- `grid[row][col]` where **row 0 = bottom**, row N-1 = top
- Flattened to `[item for row in grid for item in row]` (row 0 first)
- So flat index 0 = bottom-left, flat index N*N-1 = top-right

### Client Sticker Storage (cube.js)
- Build loop: `for row 0..N-1, for col 0..N-1`
- `meshes[]` array: index 0 = row 0, col 0
- Position: `cy = ((size-1-row) + 0.5) * cellSize - half` → **row 0 placed at TOP**
- Comment says "row 0 is top (server convention)" — **THIS IS WRONG, server row 0 = bottom**
- `updateFaceColors(faceName, colors)`: `meshes[i].color = colors[i]`
- **BUG**: meshes[0] = top-left (client), colors[0] = bottom-left (server) → VERTICALLY FLIPPED

---

## Bugs Fixed in Sessions 2 & 3

### 1. Body mesh too large (gray cube hiding stickers)
- **Symptom**: 3D cube was a big gray box, no stickers visible
- **Cause**: `createRoundedBoxGeometry` used ExtrudeGeometry with bevel extending body ±0.6 beyond sticker positions
- **Fix**: Replaced with simple `BoxGeometry(totalSize - 0.01)`

### 2. D face stickers placed on U face (white/yellow mix)
- **Symptom**: White and yellow stickers mixed in middle of U face
- **Cause**: Normal calculation `crossVectors(right, up)` then `negate()` for negative faces was inverted. For D: cross gave (0,-1,0), negate made (0,1,0) = UP
- **Fix**: Compute normal directly from axis+sign: `if (def.axis === 'y') normal.set(0, def.sign, 0)`

### 3. Sticker edge overlap
- **Symptom**: Stickers clipping at cube edges
- **Cause**: ExtrudeGeometry depth caused overlap between adjacent face stickers
- **Fix**: Switched to flat `ShapeGeometry`

### 4. Only face surface rotated during animation, not full layer
- **Symptom**: During solve, only the face's own stickers rotated, adjacent stickers stayed
- **Cause**: `_getAffectedStickers` only grabbed face stickers, not adjacent layer stickers
- **Fix**: Position-based filtering includes all stickers in the rotating layer (face + 4 adjacent edges)

### 5. Sticker position drift after animations
- **Symptom**: After several animations, wrong stickers selected for subsequent moves
- **Cause**: `attach()` reparenting accumulated position errors
- **Fix**: Added `resetPositions()` method that resets ALL stickers to canonical positions after each animation

### 6. Rotation pivot at origin (stickers flying off)
- **Symptom**: Stickers orbiting around wrong point during face rotation
- **Cause**: Temp group at (0,0,0) but face rotations should pivot around face center (e.g., R on 4x4 at x=2)
- **Fix**: `pivotMap` positions temp group at face center: `{R: [half,0,0], L: [-half,0,0], ...}`

### 7. Whole-cube and slice moves not animated
- **Symptom**: x/y/z and M/E/S moves snapped without animation
- **Cause**: `_getAffectedStickers` returned 0 stickers for these move types
- **Fix**: Added x/y/z (all stickers) and M/E/S (middle layer) to `_getAffectedStickers` + pivot map

### 8. Camera reset keys (C, Ctrl+C, Alt+C) not working
- **Symptom**: No way to reset camera to initial view
- **Cause**: Camera is client-side OrbitControls but keys were only sent to server
- **Fix**: Added `OrbitControls.reset()` method + intercept Alt+C/Ctrl+C in `_bindKeyboard()` client-side

---

## KNOWN REMAINING BUGS (user reported "there are many other bugs")

### Bug A: Row mapping inverted (colors vertically flipped per face)
- **Status**: IDENTIFIED BUT NOT FIXED
- **Symptom**: After solve, cube may show colors in wrong positions per face (flipped vertically)
- **Root cause**: Server sends row 0 = bottom, but client places row 0 at top
- **Where**: `cube.js` build loop line ~146: `cy = ((size-1-row) + 0.5) * cellSize - half`
- **Fix needed**: Change to `cy = (row + 0.5) * cellSize - half` (row 0 = bottom)
- **Also update**: `resetPositions()` method uses the same formula — must match
- **Also update**: Comment on line ~144: change "row 0 is top" to "row 0 is bottom"
- **Note**: For a SOLVED cube this bug is invisible (all same color per face), but for scrambled/mid-solve it shows wrong sticker positions

### Bug B: WideFaceAlg/DoubleLayerAlg moves not animated
- **Status**: Known, low priority
- **Symptom**: Wide moves (face name "[") snap without animation
- **Where**: `_getAffectedStickers()` doesn't handle these move types
- **Fix needed**: Add wide move support (select multiple layers)

### Bug C: Speed slider change during solve may cause stuck state
- **Status**: User reported, needs investigation
- **Symptom**: Changing speed during solve caused "stuck, no rotation"
- **Where**: Speed change sends `set_speed` to server, server updates animation duration. Client-side animation duration may not update for queued animations.

### Bug D: Unknown additional bugs
- **Status**: User says "there are many other bugs" — needs testing session
- **Likely areas to investigate**:
  1. Animation sync issues (client animation queue vs server state)
  2. Sticker color mapping per face (see Bug A above)
  3. Edge cases with different cube sizes (2x2, 5x5, etc.)
  4. Keyboard shortcuts that don't work or behave differently from pyglet2
  5. UI controls (sliders, buttons) edge cases

---

## Key Code Sections in cube.js

### FACE_DEFS (line ~26)
```javascript
const FACE_DEFS = {
    U: { axis: 'y', sign: +1, right: [1, 0, 0], up: [0, 0, -1] },
    D: { axis: 'y', sign: -1, right: [1, 0, 0], up: [0, 0,  1] },
    F: { axis: 'z', sign: +1, right: [1, 0, 0], up: [0, 1,  0] },
    B: { axis: 'z', sign: -1, right: [-1, 0, 0], up: [0, 1,  0] },
    R: { axis: 'x', sign: +1, right: [0, 0, -1], up: [0, 1,  0] },
    L: { axis: 'x', sign: -1, right: [0, 0,  1], up: [0, 1,  0] },
};
```

### Constants (line ~19)
```javascript
const STICKER_GAP = 0.10;
const CORNER_RADIUS = 0.10;
const BODY_COLOR = 0x1e1e1e;
const BG_COLOR = 0x2a2a2a;
```

### CubeModel class (~line 68)
- `build(size)` — creates body mesh + all sticker meshes
- `updateFaceColors(faceName, colors)` — updates sticker material colors from server
- `updateFromState(state)` — calls updateFaceColors for each face
- `resetPositions()` — resets all stickers to canonical positions (undo reparenting drift)

### AnimationQueue class (~line 265)
- `enqueue(face, direction, durationMs, state)` — add animation to queue
- `_processNext()` — start next animation (reparent stickers to temp group, animate rotation)
- `_finishCurrent()` — complete animation (reparent back, apply state, resetPositions)
- `_getAffectedStickers(face, slices)` — position-based layer selection
- `flush()` / `skipAll()` — skip remaining animations

### OrbitControls class (~line 525)
- Custom orbit controls (not THREE.OrbitControls)
- `spherical` coords: radius=8, phi=π/4, theta=π/6
- `reset()` — restore default angles and clear pan offset
- `setForCubeSize(size)` — adjust distance for cube size

### CubeClient class (~line 640)
- Main app class
- Manages WebSocket connection, message handling, UI bindings
- `_bindKeyboard()` — intercepts Alt+C/Ctrl+C for camera reset, sends all keys to server

---

## Server-Side Key Components

### WebglAnimationManager.py
- Converts `AnimationAbleAlg` moves to `animation_start` messages
- `_alg_to_animation_data()` extracts face name + direction from algorithm object
- Sends `cube_state` after each move completes (model already updated)
- Handles: FaceAlgBase, WholeCubeAlg, SliceAlgBase (M/E/S), WideFaceAlg, DoubleLayerAlg

### ClientSession.py
- `_alg_to_face_name()` maps alg strings to face names (R/L/U/D/F/B/M/E/S/x/y/z)
- `send_animation_start(face, direction, duration_ms)` — sends to client
- `_handle_key(symbol, modifiers)` — uses same `lookup_command()` as pyglet2
- `_js_keycode_to_symbol()` in WebglEventLoop — converts JS keyCodes to abstract Keys

### CubeStateSerializer.py
- Row 0 = bottom, row N-1 = top
- Handles corners, edges, centers for any NxN
- Returns flat list of [r,g,b] per face in row-major order

---

## How to Test
```bash
python -m cube.main_webgl          # Start server
python -m cube.main_webgl --cube-size 3   # Start with 3x3
```
Open http://localhost:8766 in browser.

## Pre-Commit Checklist
1. Fix all remaining bugs
2. Run: `python -m ruff check src/cube`
3. Run: `python -m mypy -p cube`
4. Run: `python -m pyright src/cube`
5. Run: `CUBE_QUIET_ALL=1 python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
6. Run: `CUBE_QUIET_ALL=1 python -m pytest tests/gui -v --speed-up 5`
7. Bump version if needed (currently 1.3.0)
8. Get user approval before committing
