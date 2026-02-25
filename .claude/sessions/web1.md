# Session: web1 — Three.js Web Frontend + Animation

## Goal
1. ~~Rewrite the JS client (`cube.js`) from Canvas 2D to Three.js WebGL for proper 3D rendering.~~ ✅ Done
2. ~~**Get smooth face rotation animation working**~~ ✅ Done — face visually rotates 0°→90° over ~2s
3. **Build full web UI** — toolbar, slider controls, status display, mouse interaction

## Commits Made
- `fcd7063d` — Add web animation manager, Three.js lighting, and sticker gaps
- `33e81fe1` — Add web frontend design plan document
- `806e4eb3` — Rewrite web frontend to Three.js WebGL 3D rendering
- `9c77c2c7` — Fix web animation: prevent stale display list IDs during face rotation

## Current Status (session 5) — Speed Slider Added

### What Works
- 3D cube renders correctly in Chrome via Three.js
- Keyboard controls work (R, L, U, D, F, B, scramble, solve, etc.)
- WebSocket communication is solid
- **Smooth face rotation animation** — 22 frames over ~2s, 127 cmds per frame
- rAF render loop with FIFO queue renders frames smoothly
- Debug animation progress bar shows angle and queue status
- **Speed slider** — drag to change speed 0-7, syncs with +/- keys

### Speed Slider Implementation (uncommitted)
- `index.html` — slider HTML + CSS (blue gradient track, white thumb, dark container)
- `cube.js` — `_setupSpeedSlider()`, `updateSpeedSlider()`, `speed_update` message
- `WebEventLoop.py` — `set_speed` message handler + `_speed_handler` callback
- `WebAppWindow.py` — `_handle_browser_speed()`, `_broadcast_speed()`, speed sync in `inject_command()`

### Bidirectional Speed Sync
- Slider → server: `{type: 'set_speed', value: N}` via WebSocket
- Server → slider: `{type: 'speed_update', value: N}` when +/- keys change speed
- On client connect: server broadcasts initial speed to sync slider

---

## Feature Map: Pyglet2 vs Web Backend

### Legend
- ✅ = Implemented | ⚠️ = Partial | ❌ = Missing | 🔑 = Keyboard-only (no UI)

### 1. Core Rendering

| Feature | Pyglet2 | Web | Notes |
|---------|---------|-----|-------|
| 3D cube rendering | ✅ OpenGL | ✅ Three.js | Both work well |
| Face rotation animation | ✅ Blocking | ✅ Async | Web uses rAF queue |
| Sticker gaps (dark body) | ✅ | ✅ | Inset factor 0.08 |
| Lighting/shading | ✅ | ✅ | Three.js ambient+directional |
| Clear color (background) | ✅ | ✅ | Light gray default |

### 2. Toolbar — Row 1: Size & Scramble

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Size label + display | ✅ Toolbar | ❌ | Medium |
| Size -/+ buttons | ✅ Toolbar | 🔑 Q/W | Medium |
| Scramble F button | ✅ Toolbar | 🔑 F | High |
| Scramble 0-9 buttons | ✅ Toolbar | 🔑 0-9 | High |
| Reset button | ✅ Toolbar | 🔑 Ctrl+R | High |

### 3. Toolbar — Row 2: Texture, Solver, Mode

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Texture <, >, ON/OFF | ✅ Toolbar | ❌ N/A | Low |
| Shadow toggle | ✅ Toolbar | ❌ | Low |
| Solver selector | ✅ Toolbar | 🔑 V | Medium |
| Full mode toggle | ✅ Toolbar | ❌ | Low |
| Quit button | ✅ Toolbar | 🔑 Q | Low |

### 4. Toolbar — Row 3: Solver Steps

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Diag button | ✅ Toolbar | ❌ | Low |
| Help button | ✅ Toolbar | 🔑 H | Medium |
| Solve button | ✅ Toolbar | 🔑 ? | High |
| Solver step buttons (L1,L2...) | ✅ Dynamic | ❌ | Medium |

### 5. Toolbar — Row 4: Animation & Debug

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Animation ON/OFF toggle | ✅ Toolbar | 🔑 A | Medium |
| Speed -/+ buttons | ✅ Toolbar | ✅ Slider | Done (better!) |
| Speed label | ✅ Toolbar | ✅ Slider value | Done |
| Debug toggle | ✅ Toolbar | 🔑 D | Low |
| Single-step toggle | ✅ Toolbar | 🔑 | Low |
| Next/Stop buttons | ✅ Toolbar | 🔑 Space/Esc | Low |
| File algorithm F1-F5 | ✅ Toolbar | ❌ | Low |

### 6. Status Displays

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Solver status text | ✅ Bottom bar | ❌ | High |
| Move history + count | ✅ Bottom bar | ❌ | Medium |
| Animation move display (R, U2') | ✅ Top-right overlay | ❌ | **Critical** |
| Keyboard help legend | ✅ Bottom bar | ❌ | Medium |
| Connection status | ❌ N/A | ✅ | Web-only |
| Animation debug bar | ❌ N/A | ✅ | Web-only |
| Speed slider | ❌ N/A | ✅ | Web-only (better!) |

### 7. Mouse Interaction

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Drag to rotate cube | ✅ | ❌ | **Critical** |
| Click face to turn | ✅ Ray picking | ❌ | **Critical** |
| Scroll wheel zoom | ✅ | ❌ | Medium |
| Toolbar button hover | ✅ | ❌ | Low |

### 8. Visual Controls

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Brightness [/] keys | ✅ | ❌ | Medium |
| Background {/} keys | ✅ | ❌ | Low |
| Texture cycling | ✅ | ❌ | Low |
| Face shadows | ✅ | ❌ | Low |

### 9. Dialogs & Popups

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Help popup (keyboard legend) | ✅ Modal | ❌ | Medium |
| Text popup system | ✅ | ❌ | Medium |

### 10. Advanced

| Feature | Pyglet2 | Web | Priority |
|---------|---------|-----|----------|
| Celebration effects | ✅ Confetti | ❌ | Low |
| Recording playback | ✅ | ❌ | Low |
| Diagnostics display | ✅ | ❌ | Low |
| Sanity check toggle | ✅ | ❌ | Low |

---

## Proposed Implementation Phases

### Phase W1: Essential Controls (MVP) — HIGH
1. Toolbar with core buttons: Scramble, Solve, Reset, Size +/-
2. Move notation overlay during animation ("R", "U2'", "Rw")
3. Solver status text display
4. Help popup (keyboard legend)

### Phase W2: Mouse Interaction — CRITICAL
1. Drag to rotate cube (mouse down + move)
2. Click on face to turn (ray picking → face identification)
3. Scroll wheel zoom

### Phase W3: Rich Status & Controls — MEDIUM
1. Solver selector button
2. Solver step buttons (dynamic based on solver)
3. Move history display
4. Animation toggle, debug toggle
5. Single-step mode controls

### Phase W4: Visual Polish — LOW
1. Brightness/background controls
2. Texture support (if applicable in WebGL)
3. Celebration effects
4. Recording playback
5. Full mode toggle

---

## Key Architecture Decisions

### Web-Specific Advantages
- **Speed slider** is better than discrete +/- buttons (continuous control)
- **rAF render loop** with frame queue is smoother than pyglet's timer-driven rendering
- **Async animation** (non-blocking) is architecturally cleaner than pyglet's blocking approach
- **Cross-platform** — works in any browser, no native dependencies

### Web-Specific Challenges
- **Mouse interaction** requires ray casting in JS (not trivial with the matrix stack approach)
- **Toolbar** needs HTML/CSS overlay rather than OpenGL-rendered shapes
- **Move notation** needs HTML overlay positioned relative to the canvas
- **No display lists** in WebGL — each frame rebuilds geometry (already working)

## Next Steps
- [ ] Review and commit speed slider changes
- [ ] Decide on Phase W1 vs W2 priority
- [ ] Design toolbar HTML/CSS layout
- [ ] Implement mouse drag-to-rotate
