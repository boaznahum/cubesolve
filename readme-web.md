# CubeSolve Web — User Guide

A free, interactive 3D Rubik's Cube solver that runs in your browser.
Supports cubes from 2x2 up to 20x20 with animated step-by-step solutions.

Live at **[cubesolve.fly.dev](https://cubesolve.fly.dev/)**

---

## Table of Contents

- [Getting Started](#getting-started)
- [Desktop Controls](#desktop-controls)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Mouse Controls](#mouse-controls)
- [Mobile & Touch Controls](#mobile--touch-controls)
  - [Touch Gestures](#touch-gestures)
  - [Move Buttons](#move-buttons)
  - [Shift Button (Prime Moves)](#shift-button-prime-moves)
- [Toolbar](#toolbar)
  - [Action Buttons](#action-buttons)
  - [Utility Buttons](#utility-buttons)
  - [Toggle Buttons](#toggle-buttons)
  - [Configuration Dropdowns](#configuration-dropdowns)
- [Solving a Cube](#solving-a-cube)
- [Paint Mode](#paint-mode)
- [History Panel](#history-panel)
- [Camera Controls](#camera-controls)
- [Shadow Faces (LDB)](#shadow-faces-ldb)
- [Assist Mode](#assist-mode)
- [Sound](#sound)
- [Solver Options](#solver-options)
- [Tips & Tricks](#tips--tricks)

---

## Getting Started

1. Open [cubesolve.fly.dev](https://cubesolve.fly.dev/) in any modern browser (Chrome, Firefox, Safari, Edge).
2. The app loads a solved 3x3 cube by default.
3. Click **Scramble** to randomize, then **Solve** to watch it solve itself step by step.

That's it! Read on for the full feature set.

---

## Desktop Controls

### Keyboard Shortcuts

#### Face Turns

Press a letter key to rotate that face 90° clockwise (looking at it from outside):

| Key | Face | Direction |
|-----|------|-----------|
| **U** | Up (top) | Clockwise |
| **D** | Down (bottom) | Clockwise |
| **F** | Front | Clockwise |
| **B** | Back | Clockwise |
| **R** | Right | Clockwise |
| **L** | Left | Clockwise |

Hold **Shift** with any face key to reverse the direction (counter-clockwise / prime move).

#### Slice Moves

| Key | Slice | Description |
|-----|-------|-------------|
| **M** | Middle | Between L and R (follows L direction) |
| **E** | Equatorial | Between U and D (follows D direction) |
| **S** | Standing | Between F and B (follows F direction) |

Hold **Shift** for the inverse slice move.

#### Whole-Cube Rotations

| Key | Axis | Description |
|-----|------|-------------|
| **X** | R-L axis | Rotates entire cube like an R move |
| **Y** | U-D axis | Rotates entire cube like a U move |
| **Z** | F-B axis | Rotates entire cube like an F move |

Hold **Shift** for the inverse rotation.

#### Playback Controls

| Key | Action |
|-----|--------|
| **Space** | Play next move (single step forward) |
| **Backspace** | Undo last move (single step backward) |

#### Other Keys

| Key | Action |
|-----|--------|
| **F10** | Toggle shadow faces (L/D/B) visibility |
| **Alt+C** or **Ctrl+C** | Reset camera to default view |

### Mouse Controls

| Action | Effect |
|--------|--------|
| **Click + drag on canvas** | Orbit camera around the cube |
| **Right-click + drag** | Orbit camera (alternative) |
| **Scroll wheel** | Zoom in / out |
| **Alt + drag** | Pan camera (move view position) |
| **Click a sticker + drag** | Turn a face by dragging in the desired direction |

#### Drag-to-Turn

Click any sticker and drag to rotate its face:
1. Click and hold on a sticker
2. Drag in the direction you want to turn (small arrow guides appear after 5px)
3. After dragging 15px, the move commits and the face rotates

---

## Mobile & Touch Controls

### Touch Gestures

| Gesture | Action |
|---------|--------|
| **Single-finger drag on canvas** | Orbit camera around cube |
| **Two-finger pinch** | Zoom in / out |
| **Tap a sticker + drag** | Turn a face |

### Move Buttons

On mobile screens (below 768px), a dedicated button panel appears below the cube:

**Top row:** Shift, X, Y, Z, E, S, M
**Bottom row:** F, U, R, L, D, B

Tap any button to execute that move. The button labels update to show prime notation (e.g., F') when Shift is active.

### Shift Button (Prime Moves)

The shift button (⇧) has a three-state behavior optimized for touch:

| Action | State | Effect |
|--------|-------|--------|
| **Tap** | "Once" | Next move only is reversed (prime), then auto-resets |
| **Hold (500ms)** | "Locked" | All subsequent moves are reversed until tapped again |
| **Tap again** | "Off" | Returns to normal (clockwise) moves |

The shift button glows orange when active.

---

## Toolbar

### Action Buttons

| Button | What it does |
|--------|-------------|
| **Scramble** | Applies a random scramble (30-40 moves) |
| **Solve** | Computes a solution AND auto-plays it |
| **Solution** | Computes a solution (queues it but doesn't auto-play) |
| **Stop** | Stops auto-play or aborts solving |
| **Reset** | Resets cube to solved state |

### Utility Buttons

| Button | What it does |
|--------|-------------|
| **↻ (Reset Session)** | Starts a completely fresh session (clears all history) |
| **🎨 (Paint)** | Enters paint mode to manually set sticker colors |
| **🧭 (Compass)** | Resets camera back to the default isometric angle |

### Toggle Buttons

| Button | States | Purpose |
|--------|--------|---------|
| **Dbg** | ON / OFF | Shows debug overlay (algorithm name, layer info, sticker count) |
| **Anim** | ON / OFF | Enables/disables rotation animations (instant moves when OFF) |
| **Assist** | Checked / Unchecked | Shows arrow previews before each solver move |
| **🔊** | On / Muted | Toggles mechanical cube-turning sound effects |
| **LDB** | ON / OFF | Shows/hides shadow faces for L, D, and B |

### Configuration Dropdowns

| Dropdown | Options | Purpose |
|----------|---------|---------|
| **Solver** | Beginner, CFOP, etc. | Choose solving algorithm |
| **Size** | 2 through 20 | Select cube dimension |
| **Spd** | 0 through 7 | Animation speed (0 = slowest, 7 = fastest) |

---

## Solving a Cube

### Quick Solve
1. Click **Scramble** to randomize the cube
2. Click **Solve** — the solver computes a solution and plays it automatically

### Step-by-Step
1. Click **Scramble**
2. Click **Solution** — the solver computes moves but doesn't auto-play
3. Use **Space** (or ▶ in the history panel) to step through moves one at a time
4. Use **Backspace** (or ◀) to step backward

### From a Custom Position
1. Click **🎨 Paint** to enter paint mode
2. Set each sticker to match your physical cube
3. Click **Check** to validate, then **Apply** when it turns green
4. Click **Solve** to solve from that position

---

## Paint Mode

Paint mode lets you manually set sticker colors to match a physical cube you want to solve.

### How to Use

1. Click the **🎨 Paint** button on the toolbar
2. A color palette appears with 6 colors (one per face center)
3. Select a color by clicking a swatch or pressing **1-6** on the keyboard
4. Tap stickers on the cube to paint them with the selected color
5. You can still orbit and zoom the cube while painting

### Validation

| Button | Action |
|--------|--------|
| **Check** | Quick sanity check — verifies correct color counts |
| **Apply** | Full validation — verifies the cube is actually solvable |

The Apply button changes color to indicate status:
- **Red** — sanity check failed (wrong number of stickers per color)
- **Green** — passed full solver verification (safe to apply)

### Exiting Paint Mode

- Click **Apply** (green) to accept the painted configuration
- Click **Cancel** to discard changes and return to the previous state
- Press **Escape** to cancel

---

## History Panel

The history panel on the left side shows all executed and queued moves.

### Sections

| Section | Appearance | Meaning |
|---------|-----------|---------|
| **Done items** | Blue background | Moves already executed |
| **NEXT marker** | Label with count | Divider showing how many queued moves remain |
| **Redo items** | Faded text | Queued moves waiting to be played |

### Playback Buttons (Bottom)

| Button | Action |
|--------|--------|
| **⏮** | Rewind — undo ALL moves back to start |
| **◀** | Undo one move |
| **▶** | Redo / play one move forward |
| **⏭** | Fast play — auto-play all remaining queued moves |

### Tainted Queue Warning

If you manually turn a face while solver moves are queued, a ⚠ warning icon appears.
This means the queued moves may no longer be valid for the current cube position.

### Clear History

Click the **✕** button in the history header to clear all history.

---

## Camera Controls

### Orbiting

Drag anywhere on the canvas (not on a sticker) to orbit the camera around the cube.
On touch devices, use a single-finger drag.

### Zooming

Use the scroll wheel on desktop, or two-finger pinch on touch devices.

### Panning

Hold **Alt** (or **Meta/Cmd**) and drag to pan the camera position.

### Reset View

Click the **🧭 compass** button or press **Alt+C** / **Ctrl+C** to reset
the camera to the default isometric viewing angle.

---

## Shadow Faces (LDB)

By default, you can only see three faces of the cube at once (typically U, F, R).
The **LDB** button (or **F10** key) toggles "shadow faces" — flat copies of the
Left, Down, and Back faces rendered beside the cube.

This lets you see all 6 faces without rotating the camera.

Shadow faces are slightly transparent to distinguish them from the real cube faces.

---

## Assist Mode

When the **Assist** checkbox is enabled (it is by default), the app shows visual
arrow indicators on the cube 400ms before each solver move animates.

This helps you:
- **Learn** what moves the solver makes and why
- **Anticipate** the next rotation before it happens
- **Follow along** on a physical cube

Uncheck **Assist** to disable the preview arrows and speed up auto-play.

---

## Sound

Click the **🔊** speaker button to toggle sound effects.
Each face rotation plays a short mechanical click sound, synthesized in-browser
(no audio files to download).

The sound has three layered components:
- A warm thump (low frequency)
- A plastic tick (mid frequency)
- A soft friction whisper (filtered noise)

---

## Solver Options

The **Solver** dropdown lets you choose different solving algorithms:

| Solver | Description |
|--------|-------------|
| **Beginner** | Layer-by-layer beginner method (easy to follow) |
| **CFOP** | Fridrich method — Cross, F2L, OLL, PLL (advanced, fewer moves) |
| **CubeSolve** | The project's native solving engine |

Different solvers may produce different solutions. The beginner solver is best
for learning, while CFOP is more efficient.

The available solvers may vary depending on cube size. Not all solvers support all sizes.

---

## Tips & Tricks

- **Speed up solving**: Use the **Spd** dropdown to increase animation speed, or turn
  **Anim** off for instant moves.
- **Study a specific step**: Use **Solution** instead of **Solve**, then step through
  with Space/Backspace at your own pace.
- **See hidden faces**: Toggle **LDB** to see the Left, Down, and Back faces without
  rotating the camera.
- **Solve a real cube**: Use **Paint mode** to input your cube's current state, then
  follow the solution on your physical cube with **Assist** mode on.
- **Large cubes**: Cubes larger than 5x5 may take a moment to solve. The status bar
  shows solver progress during computation.
- **Mobile users**: The move buttons at the bottom of the screen let you make moves
  without a keyboard. Use the **Shift** button for prime (reversed) moves.
