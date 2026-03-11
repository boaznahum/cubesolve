# Web Frontend Plan — WebGL2 3D Rendering

## Today's Goal

Get a **working 3D cube in the browser** with:
- 3D rendered cube (colored face quads with borders)
- Keyboard commands: R, L, U, D, F, B (and primes), X, Y, Z rotations
- Scramble (number keys) and Solve (S key)
- Instant moves (no animation)

**Explicitly out of scope today:** animation, textures, markers/stickers, lighting,
mouse camera controls, text overlay, performance optimization, multi-user.

---

## Current State

### Python server side — DONE (no changes needed today)
- `WebRenderer` — collects rendering commands as JSON dicts, sends via WebSocket
- `WebEventLoop` — aiohttp HTTP + WebSocket server, serves static files, key events
- `WebAppWindow` — full AppWindow protocol, viewer/renderer/event-loop wiring
- `WebDisplayListManager` — stores/replays command sequences (Python-side)
- Key mapping from JS keyCode → internal Keys constants
- Animation already disabled: `app.op.toggle_animation_on(False)`
- Entry point: `python -m cube.main_web`

### JavaScript client side — needs rewrite
- `cube.js` — Canvas 2D with isometric projection (no real 3D)
- Transform commands (`push_matrix`, `rotate`, `translate`, etc.) are ignored
- No depth buffer → back faces render over front faces

### What the server sends per frame
A JSON array of commands in draw order:
```json
{"cmd": "clear", "color": [217, 217, 217, 255]}
{"cmd": "projection", "width": 720, "height": 720, "fov_y": 50.0, "near": 0.1, "far": 100.0}
{"cmd": "load_identity"}
{"cmd": "translate", "x": 0, "y": 0, "z": -400}
{"cmd": "push_matrix"}
{"cmd": "translate", "x": ..., "y": ..., "z": ...}
{"cmd": "rotate", "angle": ..., "x": 0, "y": 1, "z": 0}
{"cmd": "quad_border", "vertices": [[x,y,z],...], "face_color": [r,g,b], "line_width": 1, "line_color": [0,0,0]}
{"cmd": "pop_matrix"}
... (hundreds of commands per frame)
```

---

## Architecture: Three.js

**Why Three.js over raw WebGL2:**
- Matrix stack, depth buffer, scene graph built-in
- Geometry primitives ready to use
- ~150KB gzipped from CDN
- Command mapping is direct:

| Server command | Three.js equivalent |
|---|---|
| `clear` | `renderer.setClearColor()` |
| `projection` | `PerspectiveCamera(fov, aspect, near, far)` |
| `look_at` | `camera.position.set()` + `camera.lookAt()` |
| `push_matrix` | push new `THREE.Group` as child of current |
| `pop_matrix` | pop back to parent group |
| `load_identity` | reset current group's matrix |
| `translate` | `group.applyMatrix4(makeTranslation(...))` |
| `rotate` | `group.applyMatrix4(makeRotation(...))` |
| `scale` | `group.applyMatrix4(makeScale(...))` |
| `multiply_matrix` | `group.applyMatrix4(matrix)` |
| `quad` | `BufferGeometry` (2 triangles) + `MeshBasicMaterial` |
| `quad_border` | quad mesh + `LineLoop` for border |
| `triangle` | `BufferGeometry` (1 triangle) + `MeshBasicMaterial` |
| `line` | `Line` + `LineBasicMaterial` |

---

## Implementation Steps (Today)

### Step 1: Update index.html
Add Three.js from CDN. Keep the canvas and status div.

```html
<script src="https://cdn.jsdelivr.net/npm/three@0.170/build/three.min.js"></script>
```

**File:** `src/cube/presentation/gui/backends/web/static/index.html`

---

### Step 2: Rewrite cube.js — WebSocket + Three.js setup

Replace the CubeClient class. Keep:
- WebSocket connection logic (connect, reconnect, send)
- Keyboard event handling (already sends keys to server)

Replace:
- Canvas 2D context → `THREE.WebGLRenderer`
- Add `THREE.Scene` + `THREE.PerspectiveCamera`
- `renderFrame(commands)` → rebuild scene from commands each frame

**Structure of new cube.js:**
```
class CubeClient {
    // --- WebSocket (keep as-is) ---
    constructor()
    connect()
    send(data)
    handleMessage(data)

    // --- Three.js setup (new) ---
    initThreeJS()          // renderer, scene, camera

    // --- Frame rendering (rewrite) ---
    renderFrame(commands)  // clear scene, execute commands, render
    executeCommand(cmd)    // dispatch to handler

    // --- Matrix stack (new) ---
    pushMatrix()           // push new Group as child of current
    popMatrix()            // pop to parent
    resetMatrix()          // load identity on current group

    // --- Shape handlers (rewrite) ---
    handleClear(cmd)
    handleProjection(cmd)
    handleLookAt(cmd)
    handleTranslate(cmd)
    handleRotate(cmd)
    handleScale(cmd)
    handleMultiplyMatrix(cmd)
    handleQuad(cmd)
    handleQuadBorder(cmd)
    handleTriangle(cmd)
    handleLine(cmd)
}
```

---

### Step 3: Implement matrix stack

The Python side sends `push_matrix/pop_matrix/translate/rotate/scale` to position
each face and sticker. The JS side needs to track a matrix stack.

**Approach: accumulate into a single Matrix4**

Instead of nested THREE.Group objects (which would create hundreds per frame),
maintain a matrix stack as an array of `THREE.Matrix4`:

```javascript
this.matrixStack = [new THREE.Matrix4()];  // starts with identity

pushMatrix() {
    this.matrixStack.push(this.currentMatrix().clone());
}
popMatrix() {
    this.matrixStack.pop();
}
currentMatrix() {
    return this.matrixStack[this.matrixStack.length - 1];
}
translate(x, y, z) {
    const m = new THREE.Matrix4().makeTranslation(x, y, z);
    this.currentMatrix().multiply(m);
}
rotate(angleDeg, x, y, z) {
    const axis = new THREE.Vector3(x, y, z).normalize();
    const m = new THREE.Matrix4().makeRotationAxis(axis, angleDeg * Math.PI / 180);
    this.currentMatrix().multiply(m);
}
```

When creating a mesh (quad/triangle/line), apply `currentMatrix()` to position it:
```javascript
mesh.applyMatrix4(this.currentMatrix());
this.scene.add(mesh);
```

---

### Step 4: Implement shape rendering

**quad(vertices, color):**
```javascript
// vertices = [[x,y,z], [x,y,z], [x,y,z], [x,y,z]]
// Create BufferGeometry with 2 triangles (0,1,2) and (0,2,3)
// MeshBasicMaterial({ color, side: THREE.DoubleSide })
// Apply current matrix, add to scene
```

**quad_border(vertices, face_color, line_width, line_color):**
```javascript
// Draw filled quad (same as above)
// Draw LineLoop around the 4 vertices with line_color
```

**triangle(vertices, color):**
```javascript
// BufferGeometry with 3 vertices
// MeshBasicMaterial
```

**line(p1, p2, width, color):**
```javascript
// THREE.Line with LineBasicMaterial
// Note: Three.js LineBasicMaterial doesn't support width on most platforms
// Acceptable for today — lines will be 1px
```

---

### Step 5: Handle projection and camera

**projection(width, height, fov_y, near, far):**
```javascript
this.camera.fov = fov_y;
this.camera.aspect = width / height;
this.camera.near = near;
this.camera.far = far;
this.camera.updateProjectionMatrix();
```

**look_at(eye, center, up):**
```javascript
this.camera.position.set(eye[0], eye[1], eye[2]);
this.camera.up.set(up[0], up[1], up[2]);
this.camera.lookAt(center[0], center[1], center[2]);
```

**Note:** The server currently sends `translate(0, 0, -400)` instead of `look_at`.
This means the camera stays at origin and the cube is translated -400 in Z.
The matrix stack handles this — no special camera logic needed beyond projection setup.

---

### Step 6: Frame lifecycle

Each WebSocket `frame` message triggers a full scene rebuild:

```javascript
renderFrame(commands) {
    // 1. Remove all objects from scene
    while (this.scene.children.length > 0) {
        this.scene.remove(this.scene.children[0]);
    }

    // 2. Reset matrix stack
    this.matrixStack = [new THREE.Matrix4()];

    // 3. Execute all commands (add meshes to scene)
    for (const cmd of commands) {
        this.executeCommand(cmd);
    }

    // 4. Render
    this.threeRenderer.render(this.scene, this.camera);
}
```

---

### Step 7: Test and iterate

1. Run `python -m cube.main_web`
2. Browser opens → should see 3D cube with colored faces
3. Press R → front face rotates (instant, redraws)
4. Press 1 → scramble
5. Press S → solve
6. Verify all 6 faces visible, correct colors, no z-fighting

**Debug aids:**
- `console.log` command counts per frame
- Check for unknown commands in `executeCommand` default case

---

## Files to Modify (Today)

| File | Change |
|---|---|
| `static/index.html` | Add Three.js CDN script tag |
| `static/cube.js` | Full rewrite: Three.js renderer + matrix stack |

**No Python changes needed.** The server already sends all the right commands.

---

## Possible Issues & Solutions

| Issue | Solution |
|---|---|
| Quads not visible | Check `DoubleSide` material, check matrix stack balance |
| Z-fighting between quad and border | Use `polygonOffset` on quad material or slight depth offset |
| Colors wrong | Verify `[r,g,b]` range: server sends 0-255, Three.js uses 0-1 |
| Lines too thin | Three.js limitation on most platforms — acceptable for now |
| Too many objects per frame (slow) | Acceptable for today; optimize later with batching |
| Camera not right | Log the first few commands to understand coordinate system |

---

## Future Phases (Not Today)

| Phase | Description |
|---|---|
| Camera controls | OrbitControls for mouse drag/zoom |
| Animation | Remove `toggle_animation_on(False)`, async animation loop |
| Lighting | MeshPhongMaterial + ambient/directional lights |
| Text overlay | HTML div over canvas for status/help |
| Performance | Display list caching, geometry batching, binary protocol |
| Multi-user | Room system, shared cube sessions |
