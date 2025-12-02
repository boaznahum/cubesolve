# Command Test Mapping

This document maps each keyboard command to the **state it changes**, enabling automated testing.

## How to Use This Document

For each command, the "State to Check" column shows what assertion to make:

```python
def test_zoom_in():
    initial = window.app.vs._fov_y
    window.inject_command(Command.ZOOM_IN)
    assert window.app.vs._fov_y < initial  # fov decreases = zoom in
```

---

## Keyboard Commands

### View Control

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `ZOOM_IN` | Ctrl+Up | `vs._fov_y` | Decreases |
| `ZOOM_OUT` | Ctrl+Down | `vs._fov_y` | Increases |
| `PAN_UP` | Up | `vs._offset[1]` | Increases |
| `PAN_DOWN` | Down | `vs._offset[1]` | Decreases |
| `PAN_LEFT` | Left | `vs._offset[0]` | Decreases |
| `PAN_RIGHT` | Right | `vs._offset[0]` | Increases |
| `VIEW_ALPHA_X_DEC` | Ctrl+X | `vs.alpha_x` | Decreases by `alpha_delta` |
| `VIEW_ALPHA_X_INC` | Alt+X | `vs.alpha_x` | Increases by `alpha_delta` |
| `VIEW_ALPHA_Y_DEC` | Ctrl+Y | `vs.alpha_y` | Decreases by `alpha_delta` |
| `VIEW_ALPHA_Y_INC` | Alt+Y | `vs.alpha_y` | Increases by `alpha_delta` |
| `VIEW_ALPHA_Z_DEC` | Ctrl+Z | `vs.alpha_z` | Decreases by `alpha_delta` |
| `VIEW_ALPHA_Z_INC` | Alt+Z | `vs.alpha_z` | Increases by `alpha_delta` |
| `VIEW_RESET` | Alt+C | `vs.alpha_x/y/z`, `vs._fov_y`, `vs._offset` | All reset to initial values |

### Shadow Toggles

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SHADOW_TOGGLE_L` | F10 | `vs._draw_shadows` | Contains/doesn't contain "L" |
| `SHADOW_TOGGLE_D` | F11 | `vs._draw_shadows` | Contains/doesn't contain "D" |
| `SHADOW_TOGGLE_B` | F12 | `vs._draw_shadows` | Contains/doesn't contain "B" |

### Animation Speed

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SPEED_UP` | + (numpad) | `vs._speed` | Increases (max 7) |
| `SPEED_DOWN` | - (numpad) | `vs._speed` | Decreases (min 0) |
| `PAUSE_TOGGLE` | Space | `vs.paused_on_single_step_mode` | Set to None |
| `SINGLE_STEP_TOGGLE` | Ctrl+Space | `vs.single_step_mode` | Toggles True/False |

### Cube Size

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SIZE_INC` | = | `vs.cube_size`, `cube.size` | Both increase by 1 |
| `SIZE_DEC` | - | `vs.cube_size`, `cube.size` | Both decrease by 1 (min 3) |

### Slice Selection

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SLICE_START_INC` | [ | `vs.slice_start` | Increases (capped at slice_stop) |
| `SLICE_START_DEC` | Shift+[ | `vs.slice_start` | Decreases (min 1) |
| `SLICE_STOP_INC` | ] | `vs.slice_stop` | Increases (capped at cube.size) |
| `SLICE_STOP_DEC` | Shift+] | `vs.slice_stop` | Decreases (min slice_start) |
| `SLICE_RESET` | Alt+[ | `vs.slice_start`, `vs.slice_stop` | Both set to 0 |

### Cube Rotations (Face Moves)

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `ROTATE_R` | R | `cube.front.corner_top_right.colors` | Color sequence changes |
| `ROTATE_R_PRIME` | Shift+R | Cube state | Inverse of R |
| `ROTATE_L` | L | Cube state | Left face rotates |
| `ROTATE_U` | U | Cube state | Top face rotates |
| `ROTATE_D` | D | Cube state | Bottom face rotates |
| `ROTATE_F` | F | Cube state | Front face rotates |
| `ROTATE_B` | B | Cube state | Back face rotates |
| (+ Shift variants) | | | Inverse rotations |
| (+ Ctrl variants) | | | Wide rotations |

### Slice Moves

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SLICE_M` | M | Cube state | Middle slice (parallel to L/R) |
| `SLICE_E` | E | Cube state | Equator slice (parallel to U/D) |
| `SLICE_S` | S | Cube state | Standing slice (parallel to F/B) |

### Cube Rotations (Whole Cube)

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `CUBE_X` | X | Cube orientation | Rotates on X axis (like R) |
| `CUBE_Y` | Y | Cube orientation | Rotates on Y axis (like U) |
| `CUBE_Z` | Z | Cube orientation | Rotates on Z axis (like F) |

### Scramble/Solve

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `SCRAMBLE_0` - `SCRAMBLE_9` | 0-9 | `cube.solved` | Becomes False |
| `SCRAMBLE_F9` | F9 | `cube.solved` | Becomes False |
| `SOLVE_ALL` | / | `cube.solved` | Becomes True |
| `SOLVE_ALL_NO_ANIMATION` | Shift+/ | `cube.solved` | Becomes True (instant) |
| `SOLVE_L1` | F1 | Solver progress | L1 solved |
| `SOLVE_L2` | F2 | Solver progress | L2 solved |
| `SOLVE_L3` | F3 | Solver progress | L3 solved |

### Recording

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `RECORDING_TOGGLE` | Ctrl+P | `op.is_recording` | Toggles True/False |
| `RECORDING_PLAY` | P | Cube state | Replays last recording |
| `RECORDING_PLAY_PRIME` | Shift+P | Cube state | Replays inverse |
| `RECORDING_CLEAR` | Alt+P | `vs.last_recording` | Set to None |

### Config Toggles

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `TOGGLE_ANIMATION` | O | `op.animation_enabled` | Toggles True/False |
| `TOGGLE_DEBUG` | Ctrl+O | `config.SOLVER_DEBUG` | Toggles True/False |
| `TOGGLE_SANITY_CHECK` | Alt+O | `config.CHECK_CUBE_SANITY` | Toggles True/False |

### Application

| Command | Key | State to Check | Assertion |
|---------|-----|----------------|-----------|
| `QUIT` | Q | Window closes | Raises `AppExit` |
| `RESET_CUBE` | C | `cube.solved` | Becomes True |
| `RESET_CUBE_AND_VIEW` | Ctrl+C | `cube.solved`, view state | Both reset |
| `UNDO` | , | Cube state | Reverts last move |
| `SWITCH_SOLVER` | \ | `slv.name` | Changes solver |

---

## Mouse Commands (Manual Testing Required)

Mouse commands require **visual verification** - see `docs/design/mouse_testing.md`.

| Action | Effect | Visual Check |
|--------|--------|--------------|
| Left-click + drag | Rotate view | Cube rotates in 3D |
| Right-click + drag on face | Face rotation | Face animates rotation |
| Scroll wheel | Zoom in/out | Cube appears larger/smaller |
| Click on face cell | Select face | Highlights cell (if implemented) |

---

## Test File Structure

```
tests/gui/test_all_commands.py
├── TestViewCommands
│   ├── test_zoom_in
│   ├── test_zoom_out
│   ├── test_pan_*
│   └── test_view_rotate_*
├── TestShadowCommands
│   ├── test_shadow_toggle_L
│   ├── test_shadow_toggle_D
│   └── test_shadow_toggle_B
├── TestSpeedCommands
│   ├── test_speed_up
│   └── test_speed_down
├── TestCubeStateCommands
│   ├── test_scramble_*
│   ├── test_solve_*
│   └── test_rotation_*
└── TestConfigCommands
    ├── test_toggle_animation
    └── test_toggle_debug
```
