# WebGL Backend - Session Notes

## Branch: `web3-new-app` (from `web2`)

## Overview
New `webgl/` backend where server sends **cube state** (face colors + animation events) and the Three.js client builds and owns the 3D model locally, rendering at 60fps.

## Commits
- `36ac2e05` — Add WebGL backend with client-side 3D cube rendering (session 1-3)
- `be8b8809` — Webgl issues file
- `fab89e2f` — Fix rotation directions, row mapping, animation state ordering (session 4)
- `62d7b6dc` — Fix x/y/z whole-cube and sliced-slice animation (session 5)

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

## Session 8-9: Mouse Face Turn Rules (2026-02-27)

### What Was Done
Implemented mouse-driven face/slice rotation for the WebGL backend using consistent row/column rules:

**Rule:** Drag horizontal → rotate the ROW, Drag vertical → rotate the COLUMN
(Same for ALL sticker types: corner, edge, center)

**Row mapping:**
- row 0 (bottom) → rotate bottom-adjacent face
- row N-1 (top) → rotate top-adjacent face
- inner row → E-type horizontal slice

**Col mapping:**
- col 0 (left) → rotate left-adjacent face
- col N-1 (right) → rotate right-adjacent face
- inner col → M-type vertical slice

### Files Modified

**cube.js (client):**
- Added `ArrowGuide` class — shows orange (horizontal/row) and cyan (vertical/column) arrows on sticker touch
- Added `FaceTurnHandler` class — state machine: idle→pressed→turning, with drag threshold
- `pickSticker()` — raycasts to find which sticker was clicked
- `_computeFaceDots()` — projects drag vector onto face's right/up axes in screen space
- Modified `OrbitControls` — left-click on sticker → face turn, left-click on background → orbit, right-drag → orbit
- Touch support: 1-finger on sticker → face turn, 1-finger on background → orbit

**ClientSession.py (server):**
- Rewrote `_handle_mouse_face_turn()` with unified row/column logic (removed corner/edge/center branching)
- Added `_FACE_AXES` dict — maps each face to its right/up axis vectors
- Added `_VEC_TO_FACE` dict — maps axis vectors to face names
- Added `_get_adjacent_face_name()` — finds adjacent face in any direction (top/bottom/left/right)
- Generalized `_grid_to_part()` for NxN cubes (was hardcoded 3x3)

### Testing Results (automated via Chrome)
All 6 test cases on F face pass:
1. Horiz drag corner (2,2) → U ✅
2. Vert drag corner (2,2) → R ✅
3. Horiz drag top edge (2,1) → U ✅
4. Vert drag right edge (1,2) → R ✅
5. Horiz drag center (1,1) → [1:1]E slice ✅
6. Vert drag center (1,1) → [1:1]M slice ✅

### Known Issue (being fixed)
- Face rotation directions were inverted (user reported "faces wrong direction, slices ok")
- Fix: flipped `inv` signs for all 4 face rotation cases in `_handle_mouse_face_turn`
- Slices directions are correct and unchanged

### Adjacent Face Lookup Table
```
Face | top adj | bottom adj | right adj | left adj
-----|---------|------------|-----------|----------
F    | U       | D          | R         | L
B    | U       | D          | L         | R
U    | B       | F          | R         | L
D    | F       | B          | R         | L
R    | U       | D          | B         | F
L    | U       | D          | F         | B
```

### Next Steps
- Verify direction fix works on all faces (not just F)
- Test on 4x4+ cubes
- Test touch support on mobile
- Run all checks before final commit

---

## CURRENT STATUS (End of Session 5)

### Working ✅
- R, L, F, B, M, S face rotations (correct direction + animation)
- U, D, E rotations (correct direction, user confirmed)
- x, y, z whole-cube rotations (animation works, user confirmed "all works")
- Sliced slice animation (M[2], E[2] etc.) — fix applied (client+server normalization)
- Cube state correctly updates after all moves
- Row mapping correct (bottom = row 0)
- Browser shortcuts (F5, Ctrl+R, F12) work
- Animation state ordering (post-move state embedded)

### Next Bugs to Fix (Session 6) ❌

#### 16. Gray stickers during rotation animation — FIXED ✅
- **Symptom:** During rotation, some stickers appear gray/transparent — you "see into the cube"
- **Root cause:** Sticker material used default `side: THREE.FrontSide` — back faces invisible
- **Fix:** Added `side: THREE.DoubleSide` to sticker MeshStandardMaterial (cube.js line ~140)
- **Verified:** No gray stickers during slow-speed solve animation

#### 17. Speed slider change → stuck (COULD NOT REPRODUCE)
- User reports slider gets stuck, but testing shows it works (click to change, even during animation)
- HTML slider: min=0, max=7, sends `set_speed` message to server
- Server `_handle_speed()` (ClientSession.py:316) clamps to 0..7, sets `vs._speed`
- `_get_animation_duration_ms()` maps speed index to duration: [500,400,300,200,150,100,70,50]ms
- Speed only affects NEXT move's timer delay (current timer already scheduled)
- May be intermittent or specific to dragging vs clicking — needs user feedback

#### Other Known Bugs
- **Orange displays as yellow** (color mapping issue)
- **Mouse controls** — only orbits, doesn't rotate faces
- **e.keyCode deprecated** — should use e.code
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
