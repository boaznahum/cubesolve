


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

    Ctrl+R - Wide R rotation (Rw)

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

# Code layout

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

![Algs](/assets/algs.png)

## Model

    In package model:
     Cube, Face, Slice, Corner, Edge, Center ...

![Model](/assets/cube_model.png)

## Operator

    Operator accept any algorithn and apply it on cube, if animation is enabled then play it ...
    Keep history of operation and can undo them
    Contained in Solver to animate and track solutionx

    Still have a probelm that I need to solve, animation manager <-> window/operator runtime relation are bidirectional 

![Operator-Animation](/assets/win-animation.png)

## Solver

nxn_edges.py
nxn_centers.py
l1_cross.py
l1_corners.py
l2.py
l3_cross.py
l3_corners.py

Solver operates on cube using Operator

![Solver](/assets/solver.png)

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

## Known Issues

Solver , need to rearrange hierarchy and make it abstract, so it can be replaced

## TODO
    
    
      



