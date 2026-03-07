# Color Picker Session Notes

## Branch: color-picker

## Status: In Progress — Deploying v1.39

## What's Done

### Paint Mode UI
- Paint button in toolbar with colorful SVG icon (red, green, blue, orange dots)
- Paint toolbar: Cancel, 6 color swatches, Check, Apply
- History panel hidden during paint mode
- Crosshair cursor on canvas
- Keyboard: 1-6 select colors, Escape cancels

### Color Protocol (color names, not RGB)
- Client sends COLOR NAMES (e.g., "blue", "yellow") to server, not RGB values
- This avoids PBR color correction mismatch between client/server
- `ColorPicker.setColorMap()` receives server `color_map` message
- Builds reverse lookup: RGB → color name
- `_getFullState()` returns `{face: [colorName, ...]}`

### Server Handlers
- `quick_check_colors` → creates fresh AbstractApp, sets colors, runs `is_sanity(force_check=True)`
- `full_check_colors` → creates fresh AbstractApp, sets colors, attempts solve
- `set_cube_colors` → applies colors to real cube

### Apply Button 3-State
- Red (disabled): sanity check failed
- Orange (disabled): sanity passed, not solve-verified
- Green (enabled): full solve check passed

### Validation
- Quick check fires on every sticker paint (fast, color distribution only)
- Full check fires on Check button (slow, attempts solve)
- Both use clone (fresh AbstractApp) — never modifies real cube

## Key Files Modified
- `static/js/ColorPicker.js` — core module
- `static/js/main.js` — wiring
- `static/js/FaceTurnHandler.js` — paintMode flag
- `static/js/OrbitControls.js` — onStickerClick callback
- `static/index.html` — paint button + toolbar HTML
- `static/styles.css` — paint toolbar + 3-state Apply styles
- `ClientSession.py` — 3 new handlers
- `CubeStateSerializer.py` — apply_cube_colors()
- `docs/design/paint_mode.md` — design document

## Tested Locally
- Paint mode enter/exit works
- Painting stickers changes color visually
- Quick check correctly detects invalid distribution (Apply stays red)
- Full check on solved cube → Apply turns green
- Apply exits paint mode and sends colors to server
- Cancel restores original colors

## Commits
- `75269cd3` — Add paint mode with 3-state validation and color-name protocol

## Known Issues
- iPhone: Paint button may disappear on small screens (toolbar overflow)
- Mobile paint mode CSS may need attention (styles potentially outside @media query)

## Next Steps
- Test on cubesolve-dev.fly.dev after deploy
- Test scrambled cube paint → check → apply → solve flow
- Handle solve error display when solving an invalid painted cube
