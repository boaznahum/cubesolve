# CubeSolve Web — User Guide

A free, interactive 3D Rubik's Cube solver that runs in your browser.
Supports cubes from 2x2 up to 20x20 with animated step-by-step solutions.

Live at **[cubesolve.fly.dev](https://cubesolve.fly.dev/)**

---

## Table of Contents

- [Getting Started](#getting-started)
- [Features (Desktop & Mobile)](#features-desktop--mobile)
  - [Toolbar](#toolbar)
  - [Solving a Cube](#solving-a-cube)
  - [Drag-to-Turn](#drag-to-turn)
  - [Camera Controls](#camera-controls)
  - [Paint Mode](#paint-mode)
  - [History Panel](#history-panel)
  - [Shadow Faces (LDB)](#shadow-faces-ldb)
  - [Assist Mode](#assist-mode)
  - [Sound Effects](#sound-effects)
  - [Solver Options](#solver-options)
  - [Animation & Speed](#animation--speed)
  - [Debug Overlay](#debug-overlay)
  - [Status Overlays](#status-overlays)
  - [Connection Status](#connection-status)
  - [Info Button](#info-button)
- [Desktop-Specific Features](#desktop-specific-features)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Mouse Controls](#mouse-controls)
  - [Desktop Layout](#desktop-layout)
- [Mobile-Specific Features](#mobile-specific-features)
  - [Touch Gestures](#touch-gestures)
  - [Move Buttons](#move-buttons)
  - [Shift Button (Prime Moves)](#shift-button-prime-moves)
  - [Mobile Layout](#mobile-layout)
  - [Viewport Handling](#viewport-handling)
- [Tips & Tricks](#tips--tricks)

---

## Getting Started

1. Open [cubesolve.fly.dev](https://cubesolve.fly.dev/) in any modern browser (Chrome, Firefox, Safari, Edge)
2. The app loads a solved 3x3 cube by default
3. Tap/click **Scramble** to randomize, then **Solve** to watch it solve itself step by step

That's it! Read on for the full feature set.

---

## Features (Desktop & Mobile)

Everything in this section works the same on both desktop and mobile unless noted.

### Toolbar

The toolbar sits at the top of the screen with action buttons, toggles, and dropdowns.
All buttons are available on both desktop and mobile.

#### Action Buttons

| Button | What it does |
|--------|-------------|
| **Scramble** | Applies a random scramble (30-40 random moves) |
| **Solve** | Computes a solution AND auto-plays it with animation |
| **Solution** | Computes a solution and queues it, but does NOT auto-play |
| **Stop** | Stops auto-play or aborts an in-progress solve computation |
| **Reset** | Resets the cube back to solved state |

#### Utility Buttons

| Button | What it does |
|--------|-------------|
| **↻ (Reset Session)** | Starts a completely fresh session — clears cube, history, everything |
| **🎨 (Paint)** | Enters paint mode to manually set sticker colors |
| **🧭 (Compass)** | Resets camera back to the default isometric viewing angle |

#### Toggle Buttons

| Button | States | Purpose |
|--------|--------|---------|
| **Dbg** | ON / OFF | Shows/hides the debug overlay (algorithm name, layer info, sticker count) |
| **Anim** | ON / OFF | Enables/disables rotation animations. When OFF, moves apply instantly |
| **Assist** | Checked / Unchecked | Shows arrow previews on the cube before each solver move |
| **🔊** | On / Muted | Toggles mechanical cube-turning sound effects |
| **LDB** | ON / OFF | Shows/hides shadow faces for the Left, Down, and Back sides |

#### Configuration Dropdowns

| Dropdown | Options | Purpose |
|----------|---------|---------|
| **Solver** | Beginner, CFOP, CubeSolve, etc. | Choose which solving algorithm to use |
| **Size** | 2 through 20 | Select cube dimension (2x2 up to 20x20) |
| **Spd** | 0 through 7 | Animation speed (0 = slowest, 7 = fastest) |

#### Info Button

The **ⓘ** button at the end of the toolbar opens a terminal-styled popup with credits and a quick-start guide. Dismiss it with OK, Escape, Enter, or by clicking outside.

---

### Solving a Cube

#### Quick Solve (Automatic)
1. Tap **Scramble** to randomize the cube
2. Tap **Solve** — the solver computes a solution and plays it automatically
3. Watch the cube solve itself with animated moves

#### Step-by-Step (Manual)
1. Tap **Scramble**
2. Tap **Solution** — the solver computes moves but does NOT auto-play
3. Step forward one move at a time:
   - Desktop: press **Space**
   - Mobile: tap **▶** in the history panel
4. Step backward:
   - Desktop: press **Backspace**
   - Mobile: tap **◀** in the history panel

#### From a Custom Position (Solve Your Real Cube)
1. Tap the **🎨 Paint** button to enter paint mode
2. Set each sticker to match your physical cube's current state
3. Tap **Check** to validate color counts, then **Apply** when it turns green
4. Tap **Solve** to compute and play the solution
5. Follow along on your physical cube with **Assist** mode on

---

### Drag-to-Turn

Turn any face by dragging a sticker in the direction you want to rotate:

1. Tap/click and hold on a sticker
2. Drag in the direction you want to turn — small arrow guides appear after 5px of movement
3. After dragging 15px, the move commits and the face rotates with animation

This works with both mouse (desktop) and touch (mobile). While dragging, you'll see visual arrows showing which stickers will move and in which direction.

Face turns are blocked during animation — wait for the current move to finish before starting another.

---

### Camera Controls

You can orbit, zoom, and pan the 3D view on both platforms:

| Action | Desktop | Mobile |
|--------|---------|--------|
| **Orbit** (rotate view) | Left-click drag on canvas | Single-finger drag on canvas |
| **Orbit** (alternative) | Right-click drag | — |
| **Zoom** in/out | Scroll wheel | Two-finger pinch |
| **Pan** (move view) | Alt + drag | Two-finger drag |
| **Reset view** | Compass button (or Alt+C / Ctrl+C) | Compass button |

When you drag on a sticker it turns the face; when you drag on empty canvas space it orbits the camera. The app distinguishes between the two automatically.

---

### Paint Mode

Paint mode lets you manually color each sticker to match a physical cube you want to solve. It works identically on desktop and mobile.

#### How to Use

1. Tap the **🎨 Paint** button on the toolbar
2. The main toolbar is replaced by a paint toolbar with a color palette (6 colors, one per face center)
3. Select a color:
   - Tap a color swatch in the palette
   - Or press **1–6** on a keyboard (if available)
4. Tap/click stickers on the cube to paint them with the selected color
5. You can still orbit and zoom the cube while painting — only tapping a sticker paints it

#### Validation

| Button | What it does |
|--------|-------------|
| **Check** | Quick sanity check — verifies each color appears the correct number of times |
| **Apply** | Full validation — runs the solver to verify the cube is actually solvable |

The **Apply** button changes color to show status:
- **Red** — sanity check failed (wrong color counts)
- **Green** — solver verified the cube is solvable (safe to apply)

#### Exiting Paint Mode

- Tap **Apply** (when green) to accept the painted configuration and return to normal mode
- Tap **Cancel** to discard all changes
- Press **Escape** to cancel (on keyboard)

The history panel is hidden during paint mode to give more space.

---

### History Panel

The history panel sits on the left side and shows all executed and queued moves.

#### Sections

| Section | Appearance | Meaning |
|---------|-----------|---------|
| **Done items** | Blue background | Moves that have been executed |
| **NEXT marker** | Label with count (e.g., "NEXT 20") | Shows how many queued moves remain |
| **Redo items** | Faded text | Queued moves waiting to be played |

#### Playback Buttons

| Button | Action |
|--------|--------|
| **⏮** (Rewind) | Undo ALL moves, playing backward to the start |
| **◀** (Undo) | Step back one move |
| **▶** (Redo) | Step forward one move |
| **⏭** (Fast Play) | Auto-play all remaining queued moves |

#### Tainted Queue Warning

If you manually turn a face while solver moves are queued, a **⚠** warning icon appears.
This means the queued moves may no longer produce a correct solution for the current cube position.

#### Clear History

Tap the **✕** button in the history header to clear all history.

On mobile, the history panel is narrower (58px vs 220px) and hides move badges and numbers to save space.

---

### Shadow Faces (LDB)

By default, you can only see three faces of the cube at once (typically U, F, R).
The **LDB** button toggles "shadow faces" — flat, semi-transparent copies of the
Left, Down, and Back faces rendered beside the cube.

This lets you see all 6 faces without rotating the camera — useful for understanding
what the solver is doing on hidden faces.

Shadow faces are slightly transparent (88% opacity) so you can distinguish them from the real cube.

Toggle: **LDB button** on both platforms, or **F10** key on desktop.

---

### Assist Mode

When the **Assist** checkbox is enabled (on by default), the app shows animated
arrow indicators on the cube **400ms before** each solver move animates.

This helps you:
- **Learn** what moves the solver is making and in what order
- **Anticipate** the next rotation before it happens
- **Follow along** on a physical cube by seeing the move preview first

Uncheck **Assist** to disable the preview arrows and speed up auto-play.

Assist works on both desktop and mobile with no difference in behavior.

---

### Sound Effects

Tap the **🔊** speaker button to toggle sound effects. Each face rotation plays a
short mechanical click sound, synthesized entirely in-browser (no audio files needed).

The sound has three layered components:
- A warm thump (low frequency, 80–280 Hz)
- A plastic tick (mid frequency, 260–520 Hz)
- A soft friction whisper (filtered noise at 1200 Hz)

Sound works identically on desktop and mobile. On mobile, the first tap on the page
activates the audio system (browser autoplay policy requires a user gesture).

---

### Solver Options

The **Solver** dropdown lets you choose different solving algorithms:

| Solver | Description | Best for |
|--------|-------------|----------|
| **Beginner** | Layer-by-layer beginner method | Learning — easy to follow steps |
| **CFOP** | Fridrich method (Cross, F2L, OLL, PLL) | Efficiency — fewer total moves |
| **CubeSolve** | The project's native solving engine | General use |

Different solvers produce different solutions. The beginner solver makes more moves
but each step is easier to understand.

Available solvers may vary by cube size — not all solvers support all sizes.

---

### Animation & Speed

The **Spd** dropdown controls how fast moves animate (0 = slowest, 7 = fastest).
The **Anim** toggle enables/disables animation entirely — when OFF, moves apply instantly.

Playback modes:
- **Single move**: Step one move at a time (Space/▶)
- **Continuous forward**: Auto-play all queued moves (Solve or ⏭)
- **Continuous backward**: Auto-undo all moves (⏮)
- **Stop**: Pause at any time (current animation finishes gracefully)

---

### Debug Overlay

When **Dbg:ON** is toggled, an overlay shows technical information:
- **Alg**: Name of the current algorithm/move being executed
- **Layers**: Which cube layers are rotating (e.g., [0], [0,1])
- **Stickers**: Count of stickers being animated

On desktop the overlay appears in the bottom-right corner. On mobile it moves to the
top-right corner. On very small screens (below 480px) it's hidden entirely.

---

### Status Overlays

The status overlay at the bottom of the canvas shows real-time information:
- **Solver**: Current solving stage (e.g., "L1 White", "L2", "L3 Cross")
- **Status**: Validation or error messages
- **Moves**: Total moves executed and queued

The animation text overlay at the top shows the current algorithm being executed
(e.g., "R U R' U'"), color-coded by solving stage.

---

### Connection Status

The status bar at the bottom shows connection state:
- **Green dot** + "Connected v1.X #N" — connected (version and client count)
- "Connecting..." — attempting to connect

Each browser tab gets its own independent session with its own cube state.

---

## Desktop-Specific Features

These features are only available (or work differently) on desktop.

### Keyboard Shortcuts

#### Face Turns
Press a letter key to rotate that face 90° clockwise (as seen from outside):

| Key | Face |
|-----|------|
| **U** | Up (top) |
| **D** | Down (bottom) |
| **F** | Front |
| **B** | Back |
| **R** | Right |
| **L** | Left |

Hold **Shift** to reverse direction (counter-clockwise / prime move, e.g., Shift+U = U').

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

#### Playback & Utility Keys

| Key | Action |
|-----|--------|
| **Space** | Play next queued move (single step forward) |
| **Backspace** | Undo last move (single step backward) |
| **F10** | Toggle shadow faces (L/D/B) visibility |
| **Alt+C** or **Ctrl+C** | Reset camera to default viewing angle |

#### Paint Mode Keys

| Key | Action |
|-----|--------|
| **1–6** | Select palette color (by position) |
| **Escape** | Cancel paint mode |

### Mouse Controls

| Action | Effect |
|--------|--------|
| **Left-click drag on canvas** | Orbit camera around the cube |
| **Right-click drag** | Orbit camera (alternative) |
| **Scroll wheel** | Zoom in / out |
| **Alt + drag** | Pan camera (move the view position) |
| **Click sticker + drag** | Turn a face by dragging in the desired direction |
| **Shift+click sticker** | Quick-rotate face without dragging |
| **Ctrl+click sticker** | Quick-rotate face without dragging |

### Desktop Layout

```
┌──────────┬──────────────────────────────────────┐
│          │ [Toolbar — single horizontal row]     │
│ History  ├──────────────────────────────────────┤
│ Panel    │                                      │
│ (220px)  │         Canvas (square, 1:1)         │
│          │                                      │
│ Full     ├──────────────────────────────────────┤
│ width    │ [Status bar]                         │
└──────────┴──────────────────────────────────────┘
```

- History panel is 220px wide with full move badges, item numbers, and algorithm names
- Canvas renders as a square (1:1 aspect ratio)
- Toolbar groups separated by vertical dividers
- Move buttons are NOT shown (keyboard used instead)

---

## Mobile-Specific Features

These features are only available (or work differently) on mobile / touch devices.

### Touch Gestures

| Gesture | Action |
|---------|--------|
| **Single-finger drag on canvas** | Orbit camera around the cube |
| **Two-finger pinch** | Zoom in / out |
| **Two-finger drag** | Pan camera (may also zoom slightly) |
| **Tap sticker + drag** | Turn a face by dragging direction |

Note: Starting a two-finger pinch while dragging a sticker cancels the face turn and switches to zoom mode.

### Move Buttons

On screens narrower than 768px, a dedicated move button panel appears below the cube:

**Top row:** ⇧ (Shift), X, Y, Z, E, S, M
**Bottom row:** F, U, R, L, D, B

- Tap any button to execute that move
- Button labels update dynamically to show prime notation (e.g., F → F') when Shift is active
- Buttons are sized for comfortable touch targets (44px minimum height)
- These buttons replace the keyboard shortcuts that aren't available on touch devices

### Shift Button (Prime Moves)

Since mobile devices don't have a Shift key, the **⇧ button** provides a three-state system:

| Action | State | Visual | Effect |
|--------|-------|--------|--------|
| **Tap** | "Once" | Orange glow | Next move only is reversed (prime), then auto-resets to Off |
| **Hold (500ms)** | "Locked" | Orange + underline | ALL subsequent moves are reversed until tapped again |
| **Tap again** | "Off" | Default color | Returns to normal (clockwise) moves |

This lets you easily do single prime moves (tap shift, tap F = F') or strings of prime moves (hold shift, tap multiple buttons).

### Mobile Layout

```
┌────┬─────────────────────────────┐
│    │ [Toolbar — wrapped rows]    │
│ HP ├─────────────────────────────┤
│    │                             │
│58px│     Canvas (flexible)       │
│    │  (portrait or landscape)    │
│    ├─────────────────────────────┤
│    │ [Move buttons — 2 rows]     │
│    ├─────────────────────────────┤
│    │ [Status bar — compact]      │
└────┴─────────────────────────────┘
```

- History panel is collapsed to 58px — shows buttons and algorithms only, hides badges and numbers
- Canvas uses flexible aspect ratio (fills available space between toolbar and move buttons)
- Toolbar wraps into multiple rows, dividers are hidden to save space
- Move buttons appear below the canvas
- Status bar uses smaller text (9px)
- Debug overlay is hidden on very small screens (below 480px)

### Viewport Handling

The app includes several mobile-specific viewport optimizations:
- **Pinch-zoom blocking**: Page-level pinch-zoom is disabled to prevent accidental zooming of the UI. 3D cube zoom (via OrbitControls) still works normally.
- **Dynamic viewport height**: Uses `100dvh` to handle the iOS address bar appearing/disappearing
- **Zoom recovery**: If the page loads while zoomed in (common on iOS Chrome), the UI counter-scales to fit the visible viewport
- **Orientation changes**: The canvas automatically resizes when switching between portrait and landscape

---

## Tips & Tricks

- **Speed up solving**: Use the **Spd** dropdown to increase animation speed, or turn **Anim** off for instant moves
- **Study a specific step**: Use **Solution** instead of **Solve**, then step through moves at your own pace
- **See hidden faces**: Toggle **LDB** to see the Left, Down, and Back faces without rotating the camera
- **Solve a real cube**: Use **Paint mode** to input your cube's current state, then follow the solution on your physical cube with **Assist** mode on
- **Large cubes**: Cubes larger than 5x5 may take a moment to solve. The status overlay shows solver progress during computation
- **Mobile tip**: Use the move buttons at the bottom of the screen instead of trying to drag stickers. Tap Shift for prime moves
- **Desktop tip**: Use keyboard shortcuts for fast cube manipulation — all face keys (U/D/F/B/R/L) plus Shift for prime moves
- **Step backward**: Made a wrong turn? Use Backspace (desktop) or ◀ (mobile) to undo
- **Fresh start**: The Reset Session button (↻) clears everything — cube, history, queue — for a clean slate
