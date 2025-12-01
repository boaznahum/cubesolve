# Web Backend Implementation Plan

## Overview

Implement a web-based backend that renders the Rubik's cube in a browser using WebGL (Three.js), with a Python server communicating via WebSocket.

## Architecture

```
Python Backend                    Browser Frontend
┌──────────────────┐              ┌──────────────────┐
│   WebRenderer    │   WebSocket  │  Three.js/WebGL  │
│   (collects      │ ──────────►  │  (renders with   │
│    draw calls)   │              │   depth buffer)  │
│                  │              │                  │
│   WebEventLoop   │ ◄──────────  │  Event handlers  │
│   (asyncio +     │   WebSocket  │  (keyboard,      │
│    websockets)   │              │   mouse)         │
└──────────────────┘              └──────────────────┘
```

## Why WebGL (not Canvas2D)

Canvas2D has no depth buffer - front faces cannot automatically hide rear faces.
Options considered:
1. **Canvas2D + Z-sorting**: Sort polygons by depth each frame - complex, edge cases
2. **WebGL + Three.js**: Hardware depth buffer like OpenGL - correct, fast

Decision: **WebGL + Three.js** - same depth handling as Pyglet/OpenGL backend.

## Implementation Phases

### Phase 1: Empty Window (Current)

**Goal:** Verify WebSocket communication works

- Python WebSocket server starts
- Browser connects and shows empty canvas
- Server can send "clear" command with background color
- Browser renders background color

### Phase 2: Basic Shapes

**Goal:** Render simple geometry

- Implement `quad`, `line`, `triangle` commands
- Server sends shape commands, browser renders
- No transformations yet (identity matrix)

### Phase 3: View Transforms

**Goal:** Support rotation/translation

- Implement matrix stack (push/pop/rotate/translate)
- Send transform state with frame
- Three.js camera/scene setup

### Phase 4: Full Cube Display

**Goal:** Display static cube

- All ShapeRenderer methods working
- Display lists (batch commands)
- Cube renders correctly

### Phase 5: Interactivity

**Goal:** Keyboard and mouse

- Forward keyboard events to Python
- Mouse drag for rotation
- Animation support

## File Structure

```
src/cube/presentation/gui/backends/web/
├── __init__.py           # create_backend() factory
├── WebRenderer.py        # Renderer protocol - collects commands
├── WebEventLoop.py       # EventLoop protocol - asyncio + WebSocket
├── WebWindow.py          # Window protocol - connection state
├── WebAppWindow.py       # AppWindow protocol
└── static/
    ├── index.html        # Main page with canvas
    └── cube.js           # Three.js renderer + WebSocket client
```

## Protocol Messages

### Server → Browser

```json
// Frame with commands
{
  "type": "frame",
  "commands": [
    {"cmd": "clear", "color": [217, 217, 217, 255]},
    {"cmd": "quad", "vertices": [[x,y,z],...], "color": [r,g,b]},
    {"cmd": "line", "p1": [x,y,z], "p2": [x,y,z], "color": [r,g,b], "width": 1}
  ]
}

// Simple clear (Phase 1)
{"type": "clear", "color": [217, 217, 217, 255]}
```

### Browser → Server

```json
{"type": "key", "key": "r", "code": 82, "modifiers": 0}
{"type": "mouse_press", "x": 100, "y": 200, "button": 1}
{"type": "mouse_drag", "x": 110, "y": 210, "dx": 10, "dy": 10}
{"type": "resize", "width": 800, "height": 600}
{"type": "connected"}
```

## Phase 1 Implementation Details

### Step 1.1: Create directory structure
```
src/cube/presentation/gui/backends/web/
├── __init__.py
├── WebRenderer.py
├── WebEventLoop.py
├── WebWindow.py
├── WebAppWindow.py
└── static/
    ├── index.html
    └── cube.js
```

### Step 1.2: Minimal WebEventLoop
- Start asyncio event loop
- Run WebSocket server on port 8765
- Serve static files (index.html, cube.js)
- Track connected clients

### Step 1.3: Minimal WebRenderer
- Implement `clear()` - queue clear command
- Implement `end_frame()` - send queued commands via WebSocket
- Other methods: no-op for now

### Step 1.4: Minimal WebWindow
- Store width/height
- Track connection state

### Step 1.5: Browser client
- Connect to WebSocket
- On "clear" message: fill canvas with color
- Send "connected" message on open

### Step 1.6: Register backend
- Add to BackendRegistry
- Test with: `python -m cube.main_any_backend --backend web`

## Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
web = ["websockets>=12.0", "aiohttp>=3.9.0"]
```

Using `aiohttp` for serving static files alongside WebSocket.

## Success Criteria - Phase 1

1. `python -m cube.main_any_backend --backend web` starts server
2. Browser opens to `http://localhost:8765`
3. Canvas shows gray background (color from clear command)
4. Console shows "Client connected"
5. No errors in browser console or Python

## Future Phases (Brief)

### Phase 2: Basic Shapes
- Three.js scene with BufferGeometry
- Interpret quad/line/triangle commands
- Simple flat shading

### Phase 3: Transforms
- Three.js camera positioning
- Matrix stack in JS
- Rotation/translation commands

### Phase 4: Full Cube
- All shape types
- Display list batching (send once, replay)
- Performance optimization

### Phase 5: Events
- Keyboard capture → WebSocket → Python handler
- Mouse OrbitControls or custom drag
- Animation frame sync

