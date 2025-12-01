# Web Backend Implementation Plan

**Created:** 2025-12-01
**Status Document:** `docs/design/web_backend_state.md`

## Overview

Implement a web-based backend that renders the Rubik's cube in a browser using WebGL (Three.js), with a Python server communicating via WebSocket. This enables cross-platform viewing without local GUI dependencies.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PYTHON SERVER                                   │
│                                                                              │
│  WebAppWindow ──► WebRenderer ──► WebEventLoop                              │
│       │          (JSON cmds)     (aiohttp server)                           │
│       │                               │                                      │
│       ▼                               │                                      │
│  GCubeViewer                          │ HTTP: static files                   │
│  (cube model)                         │ WS: /ws endpoint                     │
│                                       │                                      │
└───────────────────────────────────────┼──────────────────────────────────────┘
                                        │ WebSocket (JSON)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER CLIENT                                  │
│                                                                              │
│  index.html ──► cube.js ──► Three.js/WebGL                                  │
│                (WS client)   (depth buffer)                                 │
│                     │                                                        │
│                     ▼                                                        │
│              Keyboard/Mouse Events ──► WebSocket ──► Python                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why WebGL (not Canvas2D)

Canvas2D has no depth buffer - front faces cannot automatically hide rear faces.

| Approach | Pros | Cons |
|----------|------|------|
| Canvas2D + Z-sorting | Simple API | Complex sorting, edge cases with intersecting polygons |
| **WebGL + Three.js** | Hardware depth buffer, same as OpenGL | More complex setup |

**Decision:** WebGL + Three.js - matches Pyglet/OpenGL depth handling.

## Implementation Phases

| Phase | Goal | Status |
|-------|------|--------|
| Phase 1 | Empty Window - WebSocket works | ✅ Complete |
| Phase 2 | Basic Shapes - Three.js renders quads/lines | 🔄 Next |
| Phase 3 | View Transforms - Matrix stack works | Pending |
| Phase 4 | Full Cube Display - Cube visible | Pending |
| Phase 5 | Interactivity - Keyboard/mouse | Pending |

---

## Phase 1: Empty Window ✅ COMPLETE

**Goal:** Verify WebSocket communication works

**Completed:**
- [x] Create directory structure
- [x] Implement WebRenderer (collects commands as JSON)
- [x] Implement WebEventLoop (aiohttp HTTP + WebSocket)
- [x] Implement WebWindow (event handlers)
- [x] Implement WebAppWindow (orchestrates components)
- [x] Create index.html with canvas
- [x] Create cube.js with WebSocket client
- [x] Register in BackendRegistry
- [x] Add to main_any_backend CLI

**Success Criteria (all met):**
1. ✅ `python -m cube.main_any_backend --backend web` starts server
2. ✅ Browser opens to http://localhost:8765
3. ✅ Canvas shows gray background
4. ✅ Console shows "Client connected"

---

## Phase 2: Basic Shapes (Three.js) 🔄 NEXT

**Goal:** Render simple geometry with proper depth

### Step 2.1: Add Three.js Library

Option A: CDN (simpler, requires internet)
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

Option B: Local (offline, larger repo)
```
static/
├── three.min.js
├── index.html
└── cube.js
```

**Decision:** Start with CDN, can switch to local later.

### Step 2.2: Create WebGL Scene

Replace Canvas2D context with Three.js:

```javascript
class CubeClient {
    constructor() {
        this.canvas = document.getElementById('canvas');

        // Three.js setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
        this.camera.position.z = 400;

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(720, 720);

        // For collecting frame geometry
        this.frameGroup = new THREE.Group();
        this.scene.add(this.frameGroup);

        // Animation loop
        this.animate();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
}
```

### Step 2.3: Implement Shape Commands

**Quad command:**
```javascript
executeQuad(cmd) {
    const vertices = cmd.vertices;
    const color = new THREE.Color(
        cmd.color[0]/255,
        cmd.color[1]/255,
        cmd.color[2]/255
    );

    // Create geometry from 4 vertices (two triangles)
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array([
        // Triangle 1
        vertices[0][0], vertices[0][1], vertices[0][2],
        vertices[1][0], vertices[1][1], vertices[1][2],
        vertices[2][0], vertices[2][1], vertices[2][2],
        // Triangle 2
        vertices[0][0], vertices[0][1], vertices[0][2],
        vertices[2][0], vertices[2][1], vertices[2][2],
        vertices[3][0], vertices[3][1], vertices[3][2],
    ]);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.computeVertexNormals();

    const material = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.applyMatrix4(this.currentMatrix);
    this.frameGroup.add(mesh);
}
```

**Line command:**
```javascript
executeLine(cmd) {
    const material = new THREE.LineBasicMaterial({
        color: new THREE.Color(cmd.color[0]/255, cmd.color[1]/255, cmd.color[2]/255),
        linewidth: cmd.width  // Note: linewidth > 1 not supported in WebGL
    });

    const points = [
        new THREE.Vector3(cmd.p1[0], cmd.p1[1], cmd.p1[2]),
        new THREE.Vector3(cmd.p2[0], cmd.p2[1], cmd.p2[2])
    ];

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geometry, material);
    line.applyMatrix4(this.currentMatrix);
    this.frameGroup.add(line);
}
```

**Quad with border:**
```javascript
executeQuadBorder(cmd) {
    // Draw filled quad
    this.executeQuad({
        cmd: 'quad',
        vertices: cmd.vertices,
        color: cmd.face_color
    });

    // Draw border lines
    const v = cmd.vertices;
    for (let i = 0; i < 4; i++) {
        this.executeLine({
            cmd: 'line',
            p1: v[i],
            p2: v[(i + 1) % 4],
            width: cmd.line_width,
            color: cmd.line_color
        });
    }
}
```

### Step 2.4: Frame Management

Clear scene at start of each frame:

```javascript
handleFrame(commands) {
    // Clear previous frame geometry
    while (this.frameGroup.children.length > 0) {
        const child = this.frameGroup.children[0];
        child.geometry?.dispose();
        child.material?.dispose();
        this.frameGroup.remove(child);
    }

    // Reset matrix stack
    this.matrixStack = [];
    this.currentMatrix = new THREE.Matrix4();

    // Execute all commands
    for (const cmd of commands) {
        this.executeCommand(cmd);
    }
}
```

---

## Phase 3: View Transforms

**Goal:** Implement matrix stack for proper 3D positioning

### Matrix Stack Implementation

```javascript
class CubeClient {
    constructor() {
        // ... Three.js setup ...
        this.matrixStack = [];
        this.currentMatrix = new THREE.Matrix4();
    }

    executePushMatrix() {
        this.matrixStack.push(this.currentMatrix.clone());
    }

    executePopMatrix() {
        if (this.matrixStack.length > 0) {
            this.currentMatrix = this.matrixStack.pop();
        }
    }

    executeLoadIdentity() {
        this.currentMatrix = new THREE.Matrix4();
    }

    executeTranslate(cmd) {
        const m = new THREE.Matrix4().makeTranslation(cmd.x, cmd.y, cmd.z);
        this.currentMatrix.multiply(m);
    }

    executeRotate(cmd) {
        const axis = new THREE.Vector3(cmd.x, cmd.y, cmd.z).normalize();
        const m = new THREE.Matrix4().makeRotationAxis(axis, cmd.angle * Math.PI / 180);
        this.currentMatrix.multiply(m);
    }

    executeScale(cmd) {
        const m = new THREE.Matrix4().makeScale(cmd.x, cmd.y, cmd.z);
        this.currentMatrix.multiply(m);
    }
}
```

### Camera Setup

```javascript
executeProjection(cmd) {
    this.camera = new THREE.PerspectiveCamera(
        cmd.fov_y,           // Field of view
        cmd.width / cmd.height,  // Aspect ratio
        cmd.near,            // Near plane
        cmd.far              // Far plane
    );
}

executeLookAt(cmd) {
    this.camera.position.set(cmd.eye[0], cmd.eye[1], cmd.eye[2]);
    this.camera.lookAt(cmd.center[0], cmd.center[1], cmd.center[2]);
    this.camera.up.set(cmd.up[0], cmd.up[1], cmd.up[2]);
}
```

---

## Phase 4: Full Cube Display

**Goal:** Render the complete cube correctly

### Additional Shape Commands

**Sphere:**
```javascript
executeSphere(cmd) {
    const geometry = new THREE.SphereGeometry(cmd.radius, 16, 16);
    const material = new THREE.MeshBasicMaterial({
        color: new THREE.Color(cmd.color[0]/255, cmd.color[1]/255, cmd.color[2]/255)
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(cmd.center[0], cmd.center[1], cmd.center[2]);
    mesh.applyMatrix4(this.currentMatrix);
    this.frameGroup.add(mesh);
}
```

**Cylinder:**
```javascript
executeCylinder(cmd) {
    const height = new THREE.Vector3(...cmd.p2).sub(new THREE.Vector3(...cmd.p1)).length();
    const geometry = new THREE.CylinderGeometry(cmd.radius1, cmd.radius2, height, 16);
    // ... position and orient between p1 and p2 ...
}
```

### Display Lists (Optional Optimization)

If performance is an issue, cache geometry:

```javascript
class CubeClient {
    constructor() {
        this.displayLists = new Map();  // id -> Three.js Group
    }

    executeDisplayList(cmd) {
        if (this.displayLists.has(cmd.id)) {
            const cached = this.displayLists.get(cmd.id).clone();
            cached.applyMatrix4(this.currentMatrix);
            this.frameGroup.add(cached);
        }
    }
}
```

---

## Phase 5: Interactivity

**Goal:** Handle keyboard and mouse events

### Keyboard Events

Browser side (cube.js):
```javascript
document.addEventListener('keydown', (event) => {
    if (!this.connected) return;

    // Prevent default for cube control keys
    if (['r', 'l', 'u', 'd', 'f', 'b'].includes(event.key.toLowerCase())) {
        event.preventDefault();
    }

    this.send({
        type: 'key',
        key: event.key,
        code: event.keyCode,
        modifiers: (event.shiftKey ? 1 : 0) |
                   (event.ctrlKey ? 2 : 0) |
                   (event.altKey ? 4 : 0)
    });
});
```

Python side (WebEventLoop.py):
```python
async def _handle_message(self, websocket, message: str):
    data = json.loads(message)

    if data["type"] == "key":
        # Convert to KeyEvent and dispatch
        from cube.presentation.gui.types import KeyEvent
        event = KeyEvent(
            symbol=data["code"],
            modifiers=data["modifiers"]
        )
        if self._key_handler:
            self._key_handler(event)
```

### Mouse Rotation

Option A: OrbitControls (simpler)
```javascript
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

this.controls = new OrbitControls(this.camera, this.canvas);
this.controls.enableDamping = true;
```

Option B: Custom drag (matches pyglet behavior)
```javascript
let isDragging = false;
let lastX, lastY;

canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;

    this.send({
        type: 'mouse_drag',
        x: e.clientX,
        y: e.clientY,
        dx: dx,
        dy: dy
    });

    lastX = e.clientX;
    lastY = e.clientY;
});
```

### Animation Sync

Python schedules frames, browser renders them:

```javascript
// Browser maintains consistent frame rate
animate() {
    requestAnimationFrame(() => this.animate());
    this.renderer.render(this.scene, this.camera);
}

// When frame arrives from server, update geometry
handleFrame(commands) {
    this.pendingCommands = commands;
}

// Apply pending commands in animation loop
animate() {
    if (this.pendingCommands) {
        this.applyCommands(this.pendingCommands);
        this.pendingCommands = null;
    }
    requestAnimationFrame(() => this.animate());
    this.renderer.render(this.scene, this.camera);
}
```

---

## File Structure

```
src/cube/presentation/gui/backends/web/
├── __init__.py           # create_backend() factory
├── WebRenderer.py        # Renderer protocol - collects JSON commands
├── WebEventLoop.py       # EventLoop protocol - aiohttp server
├── WebWindow.py          # Window protocol - event handlers
├── WebAppWindow.py       # AppWindow protocol - orchestrates all
└── static/
    ├── index.html        # HTML page with canvas
    ├── cube.js           # Three.js client + WebSocket
    └── style.css         # Optional styling
```

## Protocol Specification

See `docs/design/web_backend_state.md` for complete protocol specification.

## Dependencies

```toml
[project.optional-dependencies]
web = ["aiohttp>=3.9.0"]
```

Note: `websockets` package not needed - aiohttp handles WebSocket.

## How to Run

```bash
# Install dependencies (if not already)
pip install aiohttp

# Run web backend
python -m cube.main_any_backend --backend web

# Server starts at http://localhost:8765
# Browser opens automatically
```

## Testing Strategy

1. **Manual testing:** Visual verification of cube rendering
2. **Unit tests:** WebRenderer command generation
3. **Integration tests:** WebSocket message flow
4. **Browser automation:** Playwright for end-to-end tests

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket disconnects | Medium | Auto-reconnect in cube.js |
| Slow rendering | Low | Batch commands, optimize Three.js |
| Browser compatibility | Low | Target modern browsers only |
| Line width limitation | Low | WebGL doesn't support linewidth > 1; use cylinders |

## References

- Current state: `docs/design/web_backend_state.md`
- GUI abstraction: `docs/design/gui_abstraction.md`
- Pyglet backend (reference): `src/cube/presentation/gui/backends/pyglet/`
- Three.js docs: https://threejs.org/docs/
