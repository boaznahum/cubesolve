# CubeSolve — WebGL Backend

## Start the Server

```bash
python -m cube.main_webgl
```

Opens `http://localhost:8766` in your browser.

```bash
python -m cube.main_webgl --cube-size 5     # 5x5 cube
python -m cube.main_webgl --debug-all       # verbose logging
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| R / L / U / D / F / B | Rotate face clockwise |
| Shift + R/L/U/D/F/B | Rotate face counter-clockwise |
| M / E / S | Rotate middle slice |
| X / Y / Z | Rotate whole cube |
| 1 | Scramble |
| S | Solve |
| + / - | Speed up / slow down animation |
| Alt+C / Ctrl+C | Reset camera |

## Mouse Controls

### Camera

| Action | Effect |
|--------|--------|
| Left-drag on background | Orbit camera |
| Right-drag | Orbit camera |
| Scroll wheel | Zoom in/out |
| Alt+Left-drag | Pan camera |

### Face/Slice Rotation (drag on sticker)

Left-click and drag on any sticker to rotate a face or slice. The rule is the same for **all** sticker types (corner, edge, center):

| Drag direction | What rotates |
|----------------|-------------|
| **Horizontal** (along face's right axis) | The **ROW** the sticker is on |
| **Vertical** (along face's up axis) | The **COLUMN** the sticker is on |

**Row rotation:**
- Top row → rotates the adjacent face above (e.g., on F face: top row → U)
- Bottom row → rotates the adjacent face below (e.g., on F face: bottom row → D)
- Inner row → rotates the horizontal slice (E-type)

**Column rotation:**
- Right column → rotates the adjacent face to the right (e.g., on F face: right col → R)
- Left column → rotates the adjacent face to the left (e.g., on F face: left col → L)
- Inner column → rotates the vertical slice (M-type)

**Visual feedback:** When you touch a sticker, arrow guides appear:
- **Orange arrows** — row rotation path (horizontal)
- **Cyan arrows** — column rotation path (vertical)

As you drag, the non-matching arrows fade out.

**Adjacent face map** (which face rotates for boundary rows/columns):

```
Face | Top adj | Bottom adj | Right adj | Left adj
-----|---------|------------|-----------|----------
  F  |    U    |     D      |     R     |    L
  B  |    U    |     D      |     L     |    R
  U  |    B    |     F      |     R     |    L
  D  |    F    |     B      |     R     |    L
  R  |    U    |     D      |     B     |    F
  L  |    U    |     D      |     F     |    B
```

## Touch Controls (mobile)

| Gesture | Effect |
|---------|--------|
| 1-finger drag on sticker | Face/slice rotation (same rules as mouse) |
| 1-finger drag on background | Orbit camera |
| 2-finger pinch | Zoom in/out |
| 2-finger drag | Pan camera |

## Architecture

The `webgl` backend differs from the `web` backend:

- **Python server** sends **cube state** (face colors as NxN grids) and **animation events**
- **Browser client** (`cube.js`) builds and owns the 3D model using Three.js, rendering at 60fps
- Camera orbit, zoom, pan are all client-side (no server round-trips)
- Face rotation animations run client-side with easing

## Deployment

```bash
fly deploy -c fly-webgl.toml
```

Port: 8766 (vs 8765 for the `web` backend)
