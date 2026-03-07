# Paint Mode — Manual Sticker Color Setting

## Overview

Paint mode allows users to manually set sticker colors on the 3D cube,
then validate and apply the configuration. This is useful for entering
a real-world cube state to solve.

## Architecture

### Client Side (`static/js/ColorPicker.js`)

The `ColorPicker` class manages the paint mode UI and sticker painting.

**Color tracking uses color NAMES, not RGB values.** This avoids
PBR color correction mismatch between client rendering and server
color model.

**Key data:**
- `palette[]` — 6 entries from center stickers: `{faceName, colorName, rgb}`
- `_originalNames{}` — snapshot: `{face: [colorName, ...]}`
- `_paintedNames{}` — edits: `{face: [colorName, ...]}`
- `_colorMap{}` — from server `color_map` message: `{colorName: [r,g,b]}`
- `_rgbToName{}` — reverse: `"r,g,b" → colorName`

**Color flow:**
```
Server color_map → setColorMap() → _colorMap + _rgbToName
Server cube_state → serverState → _buildPalette() uses center RGB → lookup → colorName
Paint click → stores colorName in _paintedNames
_getFullState() → sends {face: [colorName, ...]} to server
Server → Color enum lookup by name → apply to cube
```

### Apply Button 3-State

| State  | Color  | Enabled | Meaning |
|--------|--------|---------|---------|
| red    | Red    | No      | Sanity check failed (wrong color count) |
| orange | Orange | No      | Sanity passed, not solve-verified |
| green  | Green  | Yes     | Full solve check passed |

### Server Side (`ClientSession.py` + `CubeStateSerializer.py`)

**Message types:**

| Client → Server | Handler | Description |
|-----------------|---------|-------------|
| `quick_check_colors` | `_handle_quick_check_colors` | Creates fresh app, sets colors, runs `is_sanity(force_check=True)` |
| `full_check_colors` | `_handle_full_check_colors` | Creates fresh app, sets colors, runs solver with `animation=False, debug=False` |
| `set_cube_colors` | `_handle_set_cube_colors` | Applies colors to the real cube, clears history |

| Server → Client | Fields | Description |
|-----------------|--------|-------------|
| `quick_check_result` | `valid: bool` | Result of sanity check |
| `full_check_result` | `valid: bool, error?: str` | Result of solve attempt |

**`apply_cube_colors(cube, faces)`** — sets sticker colors on a Cube from
`{face: [colorName, ...]}` dict. Iterates corners, edges, centers
(mirrors `extract_cube_state` layout). Uses `Color` enum name lookup.

### Validation Strategy

- **Quick check** (on every paint): Fast — only checks color distribution
  (9 of each color for 3x3). Creates a fresh `AbstractApp`, sets colors,
  calls `is_sanity(force_check=True)`.

- **Full check** (on Check button): Slow — creates a fresh `AbstractApp`,
  sets colors, attempts to solve. If solver completes without exception,
  the configuration is valid.

Both use a **clone** (fresh `AbstractApp.create_app()`) to avoid modifying
the real cube state.

## UI Layout

```
Paint toolbar:  [Cancel]  [Y][W][B][G][R][O]  [Check]  [Apply]
                          ↑ palette swatches
```

- History panel hidden during paint mode
- Main toolbar hidden, replaced by paint toolbar
- Cursor changes to crosshair over canvas
- Keyboard: 1-6 select palette colors, Escape cancels

## Files Modified

| File | Changes |
|------|---------|
| `static/js/ColorPicker.js` | Core paint mode module (created) |
| `static/js/main.js` | Wiring: callbacks, message handlers, serverState |
| `static/js/FaceTurnHandler.js` | `paintMode` flag to allow hit detection |
| `static/js/OrbitControls.js` | `onStickerClick` callback for paint clicks |
| `static/index.html` | Paint button SVG, paint toolbar HTML |
| `static/styles.css` | Paint toolbar, swatch, 3-state Apply button styles |
| `ClientSession.py` | 3 new message handlers |
| `CubeStateSerializer.py` | `apply_cube_colors()` function |
