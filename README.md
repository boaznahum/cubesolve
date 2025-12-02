


# Python Big Cube Solver - A place to develop your algorithm

Yet another Big Cube solver
Python

Don't search for sophisticated algorithm, my challenge was exactly the contrary - to mimic the way I solve the cube – a
very beginner solver. So, when animation is turn on – you even can see how the cube does a whole rotate just to put the
parts in front face – the way I know to solve.

But the code is organized(see below) in such way that you can enhance and even replace the solver, the model and the
viewer are totally seperated from other layers(as should be :wink:)

## Credits:
[Ruwix](https://ruwix.com/the-rubiks-cube/notation/advanced)
        
[cubing](https://alg.cubing.net/?alg=mx)

## Installing and running

Better to create a virtual environment, then

```
  python -m pip install -U -r requirements.txt
  python main_g.py

```

### Recent Updates

**Dependencies Cleanup** - Removed unused dependencies:
- ✅ Removed unused `glooey` dependency
- Staying on `pyglet 1.5.x` (codebase uses deprecated OpenGL 1.x functions)
- Future: Gradual migration to modern OpenGL planned

https://user-images.githubusercontent.com/3913990/172692615-eb9aacf8-bc06-4a95-9aeb-c8ddd9519647.mp4

## Keyboard/Mouse Control

    This can also be done by dragging mouse + right button

### Modes

    O - Turn animation on/off
    Ctrl+O - Turn on/off solver debug level
    Alt+O - Turn on/off cube sanity (corruption) check (run after each step)
    Num Pad +/- - Change animation speed
    +/- (EQUAL/MINUS) - Change cube size

    S - During animation, stop the solver
    Q - Quit application (during animation: abort and quit)

    Ctrl+Space - Enter/exit single step mode. In this mode, animation is suspended until user hits 'SPACE' (or Ctrl+SPACE)
                 Very useful for debugging new algorithms
    SPACE - In single step mode, advance to next step

    \ - Switch solver

### Face Rotate and Slicing

    R, L, F, B, U, D - As usual - rotate faces
    X, Y, Z - Entire cube over R, U and F axes
    M, E, S - Middle slice over L, D and F

According to: [Ruwix](https://ruwix.com/the-rubiks-cube/notation/advanced) and [cubing](https://alg.cubing.net/?alg=mx)

    Ctrl+R/L/F/B/U/D - Wide (double-layer) rotations (Rw, Lw, Fw, Bw, Uw, Dw)

    Shift + Face key - Rotate face counterclockwise (inverse)

    [ and ] - Control slice range (used with Shift/Alt modifiers)

    Drag mouse on corner face to rotate this face (TBD - fix it to rotate the adjacent face)
    On edge, if parallel to wing then slice that wing, otherwise rotate face according to parallel direction of edge
    On center pieces - slice according to direction

    Shift/Ctrl + Mouse click on wing/corner - Rotate slice/face clockwise/counterclockwise

### Panning

    Alt + Mouse drag
    Arrow keys (Up/Down/Left/Right)

### Zoom In/Out

    Ctrl+Up/Down - Zoom in/out
    Mouse wheel

### Rotating Model

    Mouse + Right button - Rotate model

    Ctrl+X/Y/Z - Rotate around X/Y/Z axis (negative direction)
    Alt+X/Y/Z - Rotate around X/Y/Z axis (positive direction)

### LBD Faces Shadow
    F10/F11/F12 - Toggle on/off shadowing of L, D and B faces

https://user-images.githubusercontent.com/3913990/172851026-05582a7f-1c12-4732-a18f-719876cb7b59.mp4

### Lighting (pyglet2 backend only)
    Ctrl+[ - Decrease ambient light brightness
    Ctrl+] - Increase ambient light brightness

    Adjusts the overall lighting level from 10% to 100%. The current brightness is displayed
    in the status bar as "Light:XX%". Works during animation.

### Undo/Reset

    , (COMMA) - Undo last move (user or solver)

    C - Reset the cube
    Ctrl+C - Reset the cube and view
    Alt+C - Reset view only

### Scrambling

    0 to 9 - Scramble with different random seed (only 0 is animated)
    Shift/Alt + 0-9 - Special scramble variations
    Ctrl + 1-9 - Scramble with animation and step-by-step testing
    F9 - Special scramble with configured key

### Solving

    SHIFT + any solve key below forces animation off (useful for skipping to specific step)
    / (or ? with Shift) - Solve the cube (see animation mode above)
    F1 - First Layer
    Ctrl+F1 - First Layer cross only
    F2 - Second Layer
    F3 - Third Layer
    Ctrl+F3 - Third Layer cross only
    F4 - Big cube centers
    F5 - Big cube edges

### Recording
    Ctrl+P - Start/stop recording manual sequences, scrambling, solutions
    P - Play last recording
    Shift+P - Play last recording in reverse
    Alt+P - Reset (clear) last recording

    You can do nice things with it:
        Ctrl+P - Start recording
        1 - Scramble
        / - Solve
        Ctrl+P - Stop recording
        Shift+P - Play recording in reverse: (scramble, solve)' brings you back to solved cube

### Testing

    T - Run heavy testing on the solver. During this, GUI does not respond. TBD
    Alt+T - Rerun last test
    Ctrl+T - Rerun last scramble

    Use it if you are going to improve the solver

### Debug/Development (Internal)

    I - Print debug information (camera angles, distribution)
    W - Annotation test
    A - Special algorithm test

## Complete Command Reference

> **Note:** Key bindings shown below are for the **pyglet backend**. Other backends (tkinter, console, headless) may have different or limited key mappings.

All commands below can be executed via keyboard or programmatically via `--commands` CLI option:

```bash
python -m cube.main_any_backend --commands="SCRAMBLE_1,SOLVE_ALL,QUIT"
python -m cube.main_any_backend -c "SPEED_UP+SPEED_UP+SCRAMBLE_1+SOLVE_ALL+QUIT"
```

| Category | Key | Modifiers | Command | Description |
|----------|-----|-----------|---------|-------------|
| **Face Rotations** | R | - | `ROTATE_R` | Rotate right face clockwise |
| | R | Shift | `ROTATE_R_PRIME` | Rotate right face counter-clockwise |
| | R | Ctrl | `ROTATE_RW` | Wide rotation (Rw) - right two layers |
| | R | Ctrl+Shift | `ROTATE_RW_PRIME` | Wide rotation (Rw') counter-clockwise |
| | L | - | `ROTATE_L` | Rotate left face clockwise |
| | L | Shift | `ROTATE_L_PRIME` | Rotate left face counter-clockwise |
| | L | Ctrl | `ROTATE_LW` | Wide rotation (Lw) - left two layers |
| | L | Ctrl+Shift | `ROTATE_LW_PRIME` | Wide rotation (Lw') counter-clockwise |
| | U | - | `ROTATE_U` | Rotate up face clockwise |
| | U | Shift | `ROTATE_U_PRIME` | Rotate up face counter-clockwise |
| | U | Ctrl | `ROTATE_UW` | Wide rotation (Uw) - top two layers |
| | U | Ctrl+Shift | `ROTATE_UW_PRIME` | Wide rotation (Uw') counter-clockwise |
| | D | - | `ROTATE_D` | Rotate down face clockwise |
| | D | Shift | `ROTATE_D_PRIME` | Rotate down face counter-clockwise |
| | D | Ctrl | `ROTATE_DW` | Wide rotation (Dw) - bottom two layers |
| | D | Ctrl+Shift | `ROTATE_DW_PRIME` | Wide rotation (Dw') counter-clockwise |
| | F | - | `ROTATE_F` | Rotate front face clockwise |
| | F | Shift | `ROTATE_F_PRIME` | Rotate front face counter-clockwise |
| | F | Ctrl | `ROTATE_FW` | Wide rotation (Fw) - front two layers |
| | F | Ctrl+Shift | `ROTATE_FW_PRIME` | Wide rotation (Fw') counter-clockwise |
| | B | - | `ROTATE_B` | Rotate back face clockwise |
| | B | Shift | `ROTATE_B_PRIME` | Rotate back face counter-clockwise |
| | B | Ctrl | `ROTATE_BW` | Wide rotation (Bw) - back two layers |
| | B | Ctrl+Shift | `ROTATE_BW_PRIME` | Wide rotation (Bw') counter-clockwise |
| **Slice Moves** | M | - | `SLICE_M` | Middle slice (parallel to L) |
| | M | Shift | `SLICE_M_PRIME` | Middle slice counter-clockwise |
| | E | - | `SLICE_E` | Equatorial slice (parallel to D) |
| | E | Shift | `SLICE_E_PRIME` | Equatorial slice counter-clockwise |
| | S | - | `SLICE_S` | Standing slice (parallel to F) |
| | S | Shift | `SLICE_S_PRIME` | Standing slice counter-clockwise |
| **Cube Rotations** | X | - | `CUBE_X` | Rotate entire cube on R axis |
| | X | Shift | `CUBE_X_PRIME` | Rotate entire cube on R axis (inverse) |
| | Y | - | `CUBE_Y` | Rotate entire cube on U axis |
| | Y | Shift | `CUBE_Y_PRIME` | Rotate entire cube on U axis (inverse) |
| | Z | - | `CUBE_Z` | Rotate entire cube on F axis |
| | Z | Shift | `CUBE_Z_PRIME` | Rotate entire cube on F axis (inverse) |
| **Scramble** | 0 | - | `SCRAMBLE_0` | Scramble with seed 0 (animated) |
| | 1 | - | `SCRAMBLE_1` | Scramble with seed 1 |
| | 2 | - | `SCRAMBLE_2` | Scramble with seed 2 |
| | 3 | - | `SCRAMBLE_3` | Scramble with seed 3 |
| | 4 | - | `SCRAMBLE_4` | Scramble with seed 4 |
| | 5 | - | `SCRAMBLE_5` | Scramble with seed 5 |
| | 6 | - | `SCRAMBLE_6` | Scramble with seed 6 |
| | 7 | - | `SCRAMBLE_7` | Scramble with seed 7 |
| | 8 | - | `SCRAMBLE_8` | Scramble with seed 8 |
| | 9 | - | `SCRAMBLE_9` | Scramble with seed 9 |
| | F9 | - | `SCRAMBLE_F9` | Scramble with configured key |
| **Solve** | / | - | `SOLVE_ALL` | Solve the entire cube |
| | / | Shift | `SOLVE_ALL_NO_ANIMATION` | Solve instantly (no animation) |
| | F1 | - | `SOLVE_L1` | Solve layer 1 (cross + corners) |
| | F1 | Ctrl | `SOLVE_L1X` | Solve layer 1 cross only |
| | F2 | - | `SOLVE_L2` | Solve layer 2 |
| | F3 | - | `SOLVE_L3` | Solve layer 3 (OLL + PLL) |
| | F3 | Ctrl | `SOLVE_L3X` | Solve layer 3 cross only |
| | F4 | - | `SOLVE_CENTERS` | Solve big cube centers (NxN) |
| | F5 | - | `SOLVE_EDGES` | Solve big cube edges (NxN) |
| **View Control** | X | Ctrl | `VIEW_ALPHA_X_DEC` | Rotate view around X axis (negative) |
| | X | Alt | `VIEW_ALPHA_X_INC` | Rotate view around X axis (positive) |
| | Y | Ctrl | `VIEW_ALPHA_Y_DEC` | Rotate view around Y axis (negative) |
| | Y | Alt | `VIEW_ALPHA_Y_INC` | Rotate view around Y axis (positive) |
| | Z | Ctrl | `VIEW_ALPHA_Z_DEC` | Rotate view around Z axis (negative) |
| | Z | Alt | `VIEW_ALPHA_Z_INC` | Rotate view around Z axis (positive) |
| | Up | - | `PAN_UP` | Pan view up |
| | Down | - | `PAN_DOWN` | Pan view down |
| | Left | - | `PAN_LEFT` | Pan view left |
| | Right | - | `PAN_RIGHT` | Pan view right |
| | Up | Ctrl | `ZOOM_IN` | Zoom in |
| | Down | Ctrl | `ZOOM_OUT` | Zoom out |
| | C | Alt | `VIEW_RESET` | Reset view to default |
| **Animation** | + (NumPad) | - | `SPEED_UP` | Increase animation speed |
| | - (NumPad) | - | `SPEED_DOWN` | Decrease animation speed |
| | Space | - | `PAUSE_TOGGLE` | Pause/resume animation |
| | Space | Ctrl | `SINGLE_STEP_TOGGLE` | Toggle single-step mode |
| | S | - | `STOP_ANIMATION` | Stop animation (during animation only) |
| **Shadow** | F10 | - | `SHADOW_TOGGLE_L` | Toggle left face shadow |
| | F11 | - | `SHADOW_TOGGLE_D` | Toggle down face shadow |
| | F12 | - | `SHADOW_TOGGLE_B` | Toggle back face shadow |
| **Lighting** | [ | Ctrl | `BRIGHTNESS_DOWN` | Decrease brightness (pyglet2 only) |
| | ] | Ctrl | `BRIGHTNESS_UP` | Increase brightness (pyglet2 only) |
| **Cube Size** | = | - | `SIZE_INC` | Increase cube size |
| | - | - | `SIZE_DEC` | Decrease cube size |
| **Slice Selection** | [ | - | `SLICE_START_INC` | Increase slice start index |
| | [ | Shift | `SLICE_START_DEC` | Decrease slice start index |
| | [ | Alt | `SLICE_RESET` | Reset slice selection |
| | ] | - | `SLICE_STOP_INC` | Increase slice stop index |
| | ] | Shift | `SLICE_STOP_DEC` | Decrease slice stop index |
| **Recording** | P | - | `RECORDING_PLAY` | Play recorded sequence |
| | P | Shift | `RECORDING_PLAY_PRIME` | Play recording in reverse |
| | P | Ctrl | `RECORDING_TOGGLE` | Start/stop recording |
| | P | Alt | `RECORDING_CLEAR` | Clear recording |
| **Debug/Config** | O | - | `TOGGLE_ANIMATION` | Toggle animation on/off |
| | O | Ctrl | `TOGGLE_DEBUG` | Toggle solver debug output |
| | O | Alt | `TOGGLE_SANITY_CHECK` | Toggle cube sanity checking |
| | I | - | `DEBUG_INFO` | Print debug information |
| **Testing** | T | - | `TEST_RUN` | Run solver tests |
| | T | Alt | `TEST_RUN_LAST` | Rerun last test |
| | T | Ctrl | `TEST_SCRAMBLE_LAST` | Rerun last scramble |
| **Application** | Q | - | `QUIT` | Quit application |
| | C | - | `RESET_CUBE` | Reset cube to solved state |
| | C | Ctrl | `RESET_CUBE_AND_VIEW` | Reset cube and view |
| | , | - | `UNDO` | Undo last move |
| | \ | - | `SWITCH_SOLVER` | Switch between solvers |
| **Special** | W | - | `ANNOTATE` | Toggle annotation mode |
| | A | - | `SPECIAL_ALG` | Run special algorithm test |

# Code layout

## Architecture Overview

The application is organized into distinct layers:

- **Entry Points** - `main_pyglet.py`, `main_headless.py`, `main_any_backend.py`
- **GUI Layer** - Window, Viewer, Animation Manager
- **Application Core** - App, Cube, Operator, Solver, ViewState
- **Backend Abstraction** - Renderer, EventLoop protocols with multiple implementations

![Architecture](/readme_files/architecture.png)

## Algs

All basic algs are in algs.py
Algs can be combined, inverted sliced and multiplied

   ```python
    @property


def rf(self) -> algs.Alg:
    return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F


....

slice_alg = Algs.E[[ltr + 1 for ltr in ltrs]]
   ```

![Algs](/readme_files/algs.png)

## Model

    In package model:
     Cube, Face, Slice, Corner, Edge, Center ...

![Model](/readme_files/cube_model.png)

## Operator

    Operator accept any algorithn and apply it on cube, if animation is enabled then play it ...
    Keep history of operation and can undo them
    Contained in Solver to animate and track solutionx

    Still have a probelm that I need to solve, animation manager <-> window/operator runtime relation are bidirectional 

![Operator-Animation](/readme_files/win-animation.png)

## Solver

nxn_edges.py
nxn_centers.py
l1_cross.py
l1_corners.py
l2.py
l3_cross.py
l3_corners.py

Solver operates on cube using Operator

![Solver](/readme_files/solver.png)

The operator is very naive, it is simply mimics the beginner solver, for example from l2.py, bring edge from top to its
location

  ```python
            if te().on_face(cube.right):
self.op.op(self._ur_alg)  # U R U' R' U' F' U F 
else:
self.op.op(self._ul_alg)

...


@property
def _ur_alg(self) -> Alg:
    return Algs.alg("L2-UR", Algs.U, Algs.R, Algs.U.prime, Algs.R.prime, Algs.U.prime, Algs.F.prime, Algs.U, Algs.F)


@property
def _ul_alg(self) -> Alg:
    return Algs.alg("L2-UL",
                    Algs.U.prime + Algs.L.prime + Algs.U + Algs.L + Algs.U + Algs.F + Algs.U.prime + Algs.F.prime)


  ```

## Viewer/GUI

The GUI layer uses a **backend abstraction** pattern to support multiple rendering backends:

| Backend | Description | Use Case |
|---------|-------------|----------|
| **Pyglet** | OpenGL-based 3D rendering | Main GUI, full features |
| **Headless** | No-op renderer | Testing, CI/CD |
| **Tkinter** | Canvas-based rendering | Alternative GUI |
| **Console** | Text-based display | Debugging |

### Backend Architecture

Each backend implements three protocols:
- **Renderer** - Shape drawing, display lists, view transformations
- **EventLoop** - Event scheduling, run loop management
- **AppWindow** - Window creation, input handling

![GUI Backends](/readme_files/gui-backends.png)

### Command System

Keyboard input flows through a **Command pattern**:

1. Backend receives native key event
2. Converts to abstract `Keys` value
3. `lookup_command()` finds matching `Command` enum
4. `command.execute(ctx)` runs the handler

![Command Flow](/readme_files/command-flow.png)

This design allows:
- Type-safe command injection for testing
- Declarative key bindings in one place
- Lazy handler creation for fast startup

## Known Issues

Solver , need to rearrange hierarchy and make it abstract, so it can be replaced

## TODO
    
    
      



