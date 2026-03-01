# Session: web1 — Add Mouse Controls to Web Backend

## Goal
Implement 5 mouse features matching the pyglet2 backend:
1. Orbit rotation (right-click drag)
2. Scroll wheel zoom
3. ALT+left-drag pan
4. Shift/Ctrl click-to-turn face
5. Drag-to-turn face (most complex)

## Architecture Decision
**Client-side raycasting** using Three.js `Raycaster` — avoids WebSocket round-trips.
Only the resulting commands (face turns, view changes) are sent to the Python server.

## Pre-existing Python Infrastructure (ALREADY DONE — DO NOT REIMPLEMENT)

### WebEventLoop.py (lines 62-64, 100-106, 267-276)
- `set_mouse_rotate_handler(handler)` and `set_mouse_pan_handler(handler)` exist
- Message dispatch for `mouse_rotate_view` and `mouse_pan` types exists
- `command` type handler exists (can send ZOOM_IN/ZOOM_OUT, face rotations etc.)

### WebAppWindow.py
- `_handle_mouse_rotate(dx, dy)` (line 193) — converts pixel deltas to radians, updates `vs.alpha_x/y`
- `_handle_mouse_pan(dx, dy)` (line 206) — calls `vs.change_offset(dx, -dy, 0)`
- `_handle_browser_command(name)` (line 235) — maps command names to Commands enum:
  - Face rotations: `ROTATE_R/L/U/D/F/B` and `_PRIME` variants
  - Slice moves: `SLICE_M/E/S` and `_PRIME` variants
  - Zoom: `ZOOM_IN`, `ZOOM_OUT`
- `_broadcast_cube_info()` (line 378) — sends face geometry JSON to browser:
  ```json
  { "type": "cube_info", "size": 3, "faceSize": 60.0,
    "faces": { "F": {"center":[30,30,60],"right":[1,0,0],"up":[0,1,0]}, ... } }
  ```
  Sent on connect and cube size change.

## Current State — NOTHING IMPLEMENTED YET

Despite task list showing Step 1 complete, **no sticker metadata code exists** in the codebase.
The only uncommitted change is a minor CSS tweak in `index.html` (font size/color for status text).

## Implementation Plan (8 Steps)

### Step 1: Add sticker metadata to quad commands (Python side) — NOT DONE

**Goal:** Each colored sticker quad carries `face`, `row`, `col` so JS can identify clicked stickers.

**Files to modify:**
1. `WebRenderer.py` — `WebShapeRenderer` class (line 38):
   - Add `_sticker_face: str | None = None`, `_sticker_row: int = -1`, `_sticker_col: int = -1`
   - Add `set_sticker_context(face: str, row: int, col: int)` and `clear_sticker_context()`
   - In `quad()` (line 54) and `quad_with_border()` (line 62): if sticker context set, add `"face"`, `"row"`, `"col"` to the command dict

2. `_cell.py` — `draw_facet()` inner function (line 522):
   - Before calling `renderer.shapes.quad_with_border()`/`quad_with_texture()`, call `renderer.shapes.set_sticker_context(face_name, row, col)`
   - After drawing, call `renderer.shapes.clear_sticker_context()`
   - **Challenge:** `_Cell` knows its parent `_FaceBoard` (via `self._face_board`), which has `cube_face_supplier()` returning a `Face` object. The `Face` has a `.name` property (e.g., "R", "U", "F"). Row/col need to come from the cell's position in the face grid.

3. `_faceboard.py` — `_create_cell()` (line 79):
   - Currently passes `cy, cx, part` to create cells. Need to store `row`/`col` on each `_Cell` object.
   - Add `row` and `col` attributes to `_Cell.__init__()` or set them during `prepare_gui_geometry()`.

**Key insight:** The `_FaceBoard` grid is:
```
 0,0 | 0,1 | 0,2
 1,0 | 1,1 | 1,2
 2,0 | 2,1 | 2,2
```
So `cy` = row (0=top), `cx` = col (0=left). But for N×N cubes, the grid is N×N (not always 3).

**Protocol consideration:** `set_sticker_context()` should be on `ShapeRenderer` protocol but as a no-op default. Only `WebShapeRenderer` does anything with it. Alternative: use `isinstance` check or just add to WebShapeRenderer only and call via cast/hasattr.

**Better approach:** Don't modify the protocol. In `_cell.py`, check if the renderer's shapes object has `set_sticker_context` before calling it (duck typing), or add it to WebShapeRenderer only and have `_Cell` not call it directly — instead, set context on the renderer before `_update_polygon()` is called from `_FaceBoard`. This keeps the change minimal.

**Simplest approach:** Add `set_sticker_context`/`clear_sticker_context` to the `ShapeRenderer` protocol as no-op methods with a default implementation. The `WebShapeRenderer` overrides them. This way `_cell.py` can call them unconditionally without `isinstance` checks.

### Step 2: Tag Three.js meshes with userData (JS side) — NOT DONE

**File:** `static/cube.js`

In `addQuad()` function (around line ~180): when creating the sticker mesh, if the command dict has `face`/`row`/`col` keys, set:
```javascript
mesh.userData = { face: cmd.face, row: cmd.row, col: cmd.col, isSticker: true };
```

Similarly in `addQuadBorder()` (which creates both a face mesh and border lines).

### Step 3: Mouse orbit rotation (right-click drag) — NOT DONE

**File:** `static/cube.js` — add at the bottom (after keyboard handler)

```javascript
// Right-click drag → orbit rotation
canvas.addEventListener('contextmenu', e => e.preventDefault());
canvas.addEventListener('mousedown', onMouseDown);
canvas.addEventListener('mousemove', onMouseMove);
canvas.addEventListener('mouseup', onMouseUp);
```

Logic:
- On right-button mousedown: set `isDragging = true`, record `lastX/lastY`
- On mousemove while dragging: compute `dx = e.clientX - lastX`, `dy = e.clientY - lastY`
- Send `{ type: "mouse_rotate_view", dx, dy }` via WebSocket
- Update `lastX/lastY`
- On mouseup: `isDragging = false`

The Python side already handles this message (see above).

### Step 4: Scroll wheel zoom — NOT DONE

**File:** `static/cube.js`

```javascript
canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const cmd = e.deltaY < 0 ? "ZOOM_IN" : "ZOOM_OUT";
    ws.send(JSON.stringify({ type: "command", name: cmd }));
}, { passive: false });
```

### Step 5: ALT+left-drag pan — NOT DONE

**File:** `static/cube.js` — integrate into the mousedown/mousemove handlers from Step 3.

If left button + ALT key: send `{ type: "mouse_pan", dx, dy }` instead of orbit.

### Step 6: Shift/Ctrl click-to-turn face — NOT DONE

**File:** `static/cube.js`

On left-click with Shift or Ctrl:
1. Create `THREE.Raycaster` from click coordinates
2. Intersect with scene children
3. Find first mesh with `userData.isSticker`
4. Read `userData.face` (e.g., "R")
5. Send `{ type: "command", name: "ROTATE_R" }` (Shift) or `"ROTATE_R_PRIME"` (Ctrl)

### Step 7: Send cube geometry info — ALREADY DONE

`_broadcast_cube_info()` in WebAppWindow.py already sends face center/right/up vectors.
JS just needs to store them when receiving `cube_info` messages.

### Step 8: Drag-to-turn face — NOT DONE (most complex)

**Logic in JS:**
1. On left mousedown (no ALT, no Shift, no Ctrl): raycast to find sticker
2. If hit: store `hitFace`, `hitRow`, `hitCol`, `startX`, `startY`
3. On mousemove: accumulate drag distance, wait for threshold (~5px)
4. Once threshold reached: determine drag direction
   - Use `cube_info` face geometry (right/up vectors) to project screen drag onto face axes
   - If drag aligns more with face's "right" → row turn; with face's "up" → column turn
5. Determine command:
   - Row turn on face F, row 0 → U face rotation
   - Row turn on face F, row 2 → D' face rotation
   - etc. (need a mapping table from face + row/col + direction → command)
6. Send the command

**Face-turn mapping (for 3×3):**
This is the hardest part. When you drag horizontally on face F:
- Row 0 (top) → turn U (or U')
- Row 1 (middle) → turn E (or E')
- Row 2 (bottom) → turn D' (or D)
When you drag vertically on face F:
- Col 0 (left) → turn L' (or L)
- Col 1 (middle) → turn M' (or M)
- Col 2 (right) → turn R (or R')

The direction (CW vs CCW) depends on the sign of the drag projected onto the face axis.

For larger cubes (N>3), middle rows/cols all map to slice moves. Need to generalize.

## Key Files Reference

| File | Path | Role |
|------|------|------|
| cube.js | `src/cube/presentation/gui/backends/web/static/cube.js` | JS frontend (617 lines) |
| index.html | `src/cube/presentation/gui/backends/web/static/index.html` | HTML page (265 lines) |
| WebRenderer.py | `src/cube/presentation/gui/backends/web/WebRenderer.py` | Shape/display list/view (468 lines) |
| WebEventLoop.py | `src/cube/presentation/gui/backends/web/WebEventLoop.py` | HTTP + WS server (445 lines) |
| WebAppWindow.py | `src/cube/presentation/gui/backends/web/WebAppWindow.py` | App window (646 lines) |
| _cell.py | `src/cube/presentation/viewer/_cell.py` | Cell/sticker drawing (658 lines) |
| _faceboard.py | `src/cube/presentation/viewer/_faceboard.py` | Face grid (241 lines) |
| _board.py | `src/cube/presentation/viewer/_board.py` | All 6 faces (370 lines) |
| ShapeRenderer protocol | `src/cube/presentation/gui/protocols/ShapeRenderer.py` | Protocol for shapes |

## Implementation Order
1. Step 1+2 (sticker metadata) — enables raycasting
2. Step 3 (orbit) — most impactful, easiest to test
3. Step 4 (zoom) — trivial
4. Step 5 (ALT-pan) — easy
5. Step 6 (shift/ctrl click) — needs Steps 1+2
6. Step 7 (cube_info in JS) — store the data
7. Step 8 (drag-to-turn) — needs all above

## How to Run & Test
```bash
# Start web backend
PYTHONIOENCODING=utf-8 python -m cube.main_web

# Opens at http://localhost:<port> — check console output for port
# Use Ctrl+F5 in browser after JS changes (cache busting)
```

## Notes
- The `addQuad` function in cube.js (around line ~180-200) creates a `THREE.Mesh` with `BufferGeometry` and `MeshPhongMaterial`. This is where `userData` gets set.
- The `addQuadBorder` creates TWO objects: a filled face mesh + border lines. Only the face mesh needs userData.
- `cube_info` message is already received in cube.js and stored (check the WebSocket `onmessage` handler).
- Right-click context menu must be suppressed on the canvas for orbit to work.
