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

https://user-images.githubusercontent.com/3913990/172692615-eb9aacf8-bc06-4a95-9aeb-c8ddd9519647.mp4

## Keyboard/Mouse Control

    This is alos can be done by dragging mouse+right bottun

### Modes

    O - Turn animation on/off
    Ctrl+O - Turn of/off solver debug level
    Alt+O -  Turn of/off cube sanity(corruption) check (run after each step)
    Num Pad +/- Change Animation speed
    +/-   Cube size
    
    S - during the animation stop the solver
    
    Ctrl+Space - enter/exit single step mode, in this mode animation is suspned till user hit 'SPACE' (or Ctrl+SPACE)
    Very useful for debugging new algorithms

### Face rotate and slicing

    R, L, F, B, U, B  - As suauls - rotate faces
    X, Y, Z - Entire cube over R, U and F 
    M, E, S - Middle slice over L, D and F
        according to:
[Ruwix](https://ruwix.com/the-rubiks-cube/notation/advanced)

        and:
        
[cubing](https://alg.cubing.net/?alg=mx)
            
    
    Drag mouse on corners face to rotate this face(TBD - fix it to rotate the adjust face)
    On edge, if in parallel to wing then slice that wing, otherwise rotate face accroding to parallel direction of edge.
    On center pieces - slice accroding to direction

    Shit/Ctrl + Mouse click  on wing/corner - rotate slice/face clockwise/counterclockwise

### Panning

    Alt + Mouse drag 
    Arrows up/down/right/left

### Zoom in/out

    ctl up/down zoom in/out
    Mouse weel

### Rotating model

    Mouse + Click right - rotate model

    Ctrl/Alt  X/Y/Z rotate around axis

###  LBD faces shadow
    F10/F11/F12 toggle on/off shadowing of L, D and B faces

https://user-images.githubusercontent.com/3913990/172851026-05582a7f-1c12-4732-a18f-719876cb7b59.mp4

### Undo/Reset

    < - Undo last move (user or sovlver)

    C - Reset the cube 
    Ctrl+C - reset the cube and and view
    Alt+C - reset view

### Scrambling

    0 to 6 -  Scramble with diffrent random seed, yet no good scramble agorithm
                Only 0 is animated 

### Solving

    SHIFT + any one the one below force animation off (useful for skipping to specific step)
    ?/  - Solve the cube, See above animation mode
    F1 - First Layer
    F2 - Second Layer
    Ctrl+F3 - Third Layer cross
    F3 - Third Layer

    F4 - Big cube centers
    F5 - Big cube edges

### Recording
    Ctrl+P start/stop recording: manual sequnces, scrambilg, solutions
    P / Shift P - play last recoding (or play reverse)
    Alt - P - reset last recording
    
    You can do nice things with it:
        Ctrl P - start recording    
        1  - scramble
        /  - solve
        Ctrl P - Stop recording
        Shift P - ( scramble, solve)' - bring you again to solved cube

### Testing

    T - Run heavy testing on the solver. During this, GUI does not response. TBD 

    Use it if you are going to improve the solver

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
    
    
      



