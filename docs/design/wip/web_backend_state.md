# Web Backend Migration State

**Last Updated:** 2025-12-01
**Branch:** `web-backend`
**Status:** Phase 1 Complete (Empty Window)

## Overview

The web backend renders the Rubik's cube in a browser using WebGL, with a Python server communicating via WebSocket. This allows cross-platform viewing without local GUI dependencies.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PYTHON SERVER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  WebAppWindow    │───▶│   WebRenderer    │───▶│  WebEventLoop    │       │
│  │  (orchestrates)  │    │  (collects cmds) │    │  (aiohttp server)│       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │   GCubeViewer    │    │ JSON Commands    │    │  HTTP + WebSocket│       │
│  │   (_Board)       │    │ (frame batches)  │    │  on port 8765    │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ WebSocket (JSON)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER CLIENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │   index.html     │───▶│    cube.js       │───▶│  HTML5 Canvas    │       │
│  │   (page)         │    │  (WS client)     │    │  (rendering)     │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│                                                                              │
│  Phase 2+: Replace Canvas with Three.js/WebGL for depth buffer              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
src/cube/presentation/gui/backends/web/
├── __init__.py           # create_backend() factory function
├── WebRenderer.py        # Renderer protocol - collects draw commands as JSON
├── WebEventLoop.py       # EventLoop protocol - aiohttp HTTP + WebSocket server
├── WebWindow.py          # Window protocol - browser connection state
├── WebAppWindow.py       # AppWindow protocol - combines all components
└── static/
    ├── index.html        # HTML page with canvas element
    └── cube.js           # WebSocket client + Canvas2D rendering (temporary)
```

## Implementation Status

### Phase 1: Empty Window ✅ COMPLETE

| Component | Status | Notes |
|-----------|--------|-------|
| WebRenderer | ✅ Done | Collects all shape commands as JSON |
| WebEventLoop | ✅ Done | aiohttp server, HTTP + WebSocket on port 8765 |
| WebWindow | ✅ Done | Event handlers, state tracking |
| WebAppWindow | ✅ Done | Orchestrates components, creates GCubeViewer |
| BackendRegistry | ✅ Done | "web" registered as valid backend |
| main_any_backend | ✅ Done | --backend web option added |
| index.html | ✅ Done | Canvas page with status display |
| cube.js | ✅ Done | WebSocket client, basic 2D rendering |

**What works:**
- Server starts: `python -m cube.main_any_backend --backend web`
- Browser opens automatically to http://localhost:8765
- WebSocket connection established
- Gray background renders (clear command)
- Shape commands are sent to browser

**What doesn't work yet:**
- Cube not visible (needs WebGL depth buffer)
- Keyboard events not forwarded
- Mouse events not forwarded
- Animation not working

### Phase 2: WebGL Rendering 🔄 PENDING

Replace Canvas2D with Three.js WebGL for proper depth handling.

| Task | Status | Details |
|------|--------|---------|
| Add Three.js library | Pending | CDN or local |
| Create WebGL scene | Pending | Scene, camera, renderer |
| Implement shape commands | Pending | quad, line, triangle → Three.js meshes |
| Depth buffer working | Pending | Front faces hide back faces |
| Transform commands | Pending | Matrix stack → Three.js transforms |

### Phase 3: Interactivity 🔄 PENDING

| Task | Status | Details |
|------|--------|---------|
| Keyboard events | Pending | Forward to Python, map to Commands |
| Mouse rotation | Pending | OrbitControls or custom drag |
| Animation frames | Pending | Sync with Python scheduler |

## Component Details

### WebRenderer (`WebRenderer.py`)

Implements the `Renderer` protocol by collecting draw commands into a list and sending them as JSON via WebSocket.

**Key classes:**
- `WebShapeRenderer` - Implements `ShapeRenderer` protocol
- `WebDisplayListManager` - Implements `DisplayListManager` protocol
- `WebViewStateManager` - Implements `ViewStateManager` protocol
- `WebRenderer` - Main renderer, composes the above

**Command flow:**
```python
renderer.begin_frame()      # Clears command buffer
renderer.clear(color)       # Adds {"cmd": "clear", "color": [...]}
renderer.shapes.quad(...)   # Adds {"cmd": "quad", "vertices": [...], ...}
renderer.view.translate(...) # Adds {"cmd": "translate", "x": ..., ...}
renderer.end_frame()        # Sends JSON to browser via WebSocket
```

### WebEventLoop (`WebEventLoop.py`)

Uses `aiohttp` for both HTTP static file serving and WebSocket on the same port.

**Key features:**
- HTTP routes: `/` (index.html), `/{filename}` (static files), `/ws` (WebSocket)
- Scheduled callbacks via `schedule_once()` and `schedule_interval()`
- `broadcast(message)` sends to all connected WebSocket clients
- Main loop runs at ~60fps checking scheduled callbacks

**Startup sequence:**
```python
async def _async_run(self):
    # Create aiohttp app with routes
    app = web.Application()
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', index_handler)

    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8765)
    await site.start()

    # Open browser
    webbrowser.open("http://localhost:8765")

    # Main loop
    while not self._has_exit:
        await self._process_scheduled()
        await asyncio.sleep(0.016)
```

### WebAppWindow (`WebAppWindow.py`)

Combines all components and implements the `AppWindow` protocol.

**Key responsibilities:**
- Creates/gets renderer and event_loop from backend factory
- Creates WebWindow for event handling
- Creates GCubeViewer with renderer
- Implements `inject_command()` for command execution
- Handles draw/resize/key events

### Browser Client (`static/cube.js`)

JavaScript WebSocket client that receives commands and renders to canvas.

**Current implementation (Canvas2D - temporary):**
```javascript
class CubeClient {
    constructor() {
        this.ws = new WebSocket(`ws://${window.location.host}/ws`);
        this.ws.onmessage = (event) => this.handleMessage(event.data);
    }

    handleMessage(data) {
        const message = JSON.parse(data);
        if (message.type === 'frame') {
            for (const cmd of message.commands) {
                this.executeCommand(cmd);
            }
        }
    }

    executeCommand(cmd) {
        switch (cmd.cmd) {
            case 'clear': this.clear(cmd.color); break;
            case 'quad': this.drawQuad(cmd.vertices, cmd.color); break;
            // ... etc
        }
    }
}
```

**Isometric projection (temporary, for 2D):**
```javascript
project(point3d) {
    const [x, y, z] = point3d;
    const scale = this.canvas.width * 0.4 / 90;
    const x2d = (x - z) * 0.866 * scale + offsetX;
    const y2d = offsetY - (y * scale - (x + z) * 0.5 * scale);
    return [x2d, y2d];
}
```

## Protocol Specification

### Server → Browser Messages

**Frame message (batch of commands):**
```json
{
  "type": "frame",
  "commands": [
    {"cmd": "clear", "color": [217, 217, 217, 255]},
    {"cmd": "projection", "width": 720, "height": 720, "fov_y": 50.0, "near": 0.1, "far": 100.0},
    {"cmd": "load_identity"},
    {"cmd": "translate", "x": 0, "y": 0, "z": -400},
    {"cmd": "push_matrix"},
    {"cmd": "rotate", "angle": 45, "x": 1, "y": 0, "z": 0},
    {"cmd": "quad", "vertices": [[0,0,0], [10,0,0], [10,10,0], [0,10,0]], "color": [255, 0, 0]},
    {"cmd": "quad_border", "vertices": [...], "face_color": [255,0,0], "line_width": 2, "line_color": [0,0,0]},
    {"cmd": "line", "p1": [0,0,0], "p2": [10,10,10], "width": 1, "color": [0,0,0]},
    {"cmd": "pop_matrix"}
  ]
}
```

**All command types:**
| Command | Parameters | Description |
|---------|------------|-------------|
| clear | color: [r,g,b,a] | Clear with background color |
| projection | width, height, fov_y, near, far | Set projection matrix |
| push_matrix | - | Push matrix stack |
| pop_matrix | - | Pop matrix stack |
| load_identity | - | Load identity matrix |
| translate | x, y, z | Translate |
| rotate | angle, x, y, z | Rotate (degrees) |
| scale | x, y, z | Scale |
| look_at | eye[], center[], up[] | Camera look-at |
| quad | vertices[], color[] | Draw quad |
| quad_border | vertices[], face_color[], line_width, line_color[] | Quad with border |
| triangle | vertices[], color[] | Draw triangle |
| line | p1[], p2[], width, color[] | Draw line |
| lines | points[[[p1],[p2]],...], width, color[] | Draw multiple lines |
| sphere | center[], radius, color[] | Draw sphere |
| cylinder | p1[], p2[], radius1, radius2, color[] | Draw cylinder |
| disk | center[], normal[], inner_radius, outer_radius, color[] | Draw disk |
| box | bottom[], top[], face_color[], line_width, line_color[] | Draw box |

### Browser → Server Messages

```json
{"type": "connected"}
{"type": "resize", "width": 800, "height": 600}
{"type": "key", "key": "r", "code": 82, "modifiers": 0}
{"type": "mouse_press", "x": 100, "y": 200, "button": 1}
{"type": "mouse_drag", "x": 110, "y": 210, "dx": 10, "dy": 10}
```

**Modifier flags:** shift=1, ctrl=2, alt=4

## Dependencies

Required packages (add to pyproject.toml):
```toml
[project.optional-dependencies]
web = ["websockets>=12.0", "aiohttp>=3.9.0"]
```

Currently installed in dev environment.

## How to Run

```bash
# Start web backend
python -m cube.main_any_backend --backend web

# Server starts at http://localhost:8765
# Browser opens automatically
```

## Next Implementation Steps

### Step 2.1: Add Three.js to cube.js

Replace Canvas2D with Three.js WebGL renderer:

```javascript
// In cube.js
import * as THREE from 'three';

class CubeClient {
    constructor() {
        // Three.js setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(50, 720/720, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas });
        this.renderer.setSize(720, 720);

        // Matrix stack for transforms
        this.matrixStack = [];
        this.currentMatrix = new THREE.Matrix4();

        // Connect WebSocket
        this.ws = new WebSocket(`ws://${window.location.host}/ws`);
    }

    executeCommand(cmd) {
        switch (cmd.cmd) {
            case 'clear':
                this.scene.background = new THREE.Color(
                    cmd.color[0]/255, cmd.color[1]/255, cmd.color[2]/255
                );
                break;
            case 'quad':
                const geometry = new THREE.BufferGeometry();
                // ... create quad mesh
                this.scene.add(mesh);
                break;
            case 'push_matrix':
                this.matrixStack.push(this.currentMatrix.clone());
                break;
            // ... etc
        }
    }

    render() {
        this.renderer.render(this.scene, this.camera);
    }
}
```

### Step 2.2: Implement Transform Commands

```javascript
executeTransform(cmd) {
    switch (cmd.cmd) {
        case 'translate':
            this.currentMatrix.multiply(
                new THREE.Matrix4().makeTranslation(cmd.x, cmd.y, cmd.z)
            );
            break;
        case 'rotate':
            const axis = new THREE.Vector3(cmd.x, cmd.y, cmd.z).normalize();
            this.currentMatrix.multiply(
                new THREE.Matrix4().makeRotationAxis(axis, cmd.angle * Math.PI / 180)
            );
            break;
        case 'scale':
            this.currentMatrix.multiply(
                new THREE.Matrix4().makeScale(cmd.x, cmd.y, cmd.z)
            );
            break;
    }
}
```

### Step 2.3: Wire Keyboard Events

In `cube.js`:
```javascript
document.addEventListener('keydown', (event) => {
    this.send({
        type: 'key',
        key: event.key,
        code: event.keyCode,
        modifiers: (event.shiftKey ? 1 : 0) | (event.ctrlKey ? 2 : 0) | (event.altKey ? 4 : 0)
    });
});
```

In `WebEventLoop.py`:
```python
async def _handle_message(self, websocket, message: str):
    data = json.loads(message)
    if data["type"] == "key":
        # Forward to WebWindow key handler
        self._on_key_event(data)
```

### Step 2.4: Animation Support

The Python side already sends frames via `end_frame()`. The browser needs to:
1. Clear scene each frame
2. Rebuild geometry from commands
3. Use `requestAnimationFrame` for smooth rendering

## Known Issues

1. **No depth buffer (Phase 2)** - Currently using Canvas2D which has no depth buffer. Front faces cannot hide back faces. Three.js WebGL will fix this.

2. **Commands sent but not rendered** - Shape commands are being sent but the 2D projection doesn't match the cube viewer's coordinate system properly.

3. **Texture not supported** - `load_texture()` returns None. Textures will need to be sent as base64 or URLs.

## Testing

Currently no automated tests for web backend. Manual testing:

1. Start server: `python -m cube.main_any_backend --backend web`
2. Check browser opens
3. Check WebSocket connects (status shows "Connected")
4. Check gray background renders
5. Check Python console shows "Client connected"

Future: Add pytest tests using playwright or similar for browser automation.

## References

- Main design doc: `docs/design/web_backend_plan.md`
- GUI abstraction: `docs/design/gui_abstraction.md`
- Backend protocols: `src/cube/presentation/gui/protocols/`
- Other backends for reference: `src/cube/presentation/gui/backends/pyglet/`
