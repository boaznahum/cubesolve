# Python Big Cube Solver
Yet another Big Cube solver
Python

  Don't search for sophisticated algorithm, my challenge was exactly the contrary - to mimic the way I solve the cube – a very beginner solver. So, when animation is turn on – you even can see how the cube does a whole rotate just to put the parts in front face – the way I know to solve.
  
  

## Installing and running



  Better to create a virtual enviroment, then
```  
  python -m pip install -U -r requirements.txt
  python main_g.py
  
```

![image](https://user-images.githubusercontent.com/3913990/172592023-3513feb2-28ea-4f8d-94e6-d9fbd4c99cb7.png)




https://user-images.githubusercontent.com/3913990/172692615-eb9aacf8-bc06-4a95-9aeb-c8ddd9519647.mp4



## Keyboard


### Controlling view 
    Ctlr/Alt X, Y, Z - Rotate cube over X, Y , Z Axis
    This is alos can be down by dragging mouse
### Modes
    o - Turn animation on/off
    Num Pad +/- Change Animation speed
    +/-   Cube size

    S - during the animation stop the solver

### Rotating
    R, L, F, B, U, B  - As suauls - rotate faces
    X, Y, Z - Entire cube over R, U and F 
    M, E, S - Middle slice over R, **D** and F

### Scrambling 

    0 to 6 -  Scramble with diffrent random seed, yet no good scramble agorithm
                Only 0 is animated 


### Solving

    ?/  - Solve the cube, See above animation mode


# Code layout

## Algs
   All basic algs are in algs.py
   Algs can be combined, inverted sliced and multiplied
   ```python
    @property
    def rf(self) -> algs.Alg:
        return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F
        
    ....
    
    slice_alg = Algs.E[ [ltr + 1  for ltr in ltrs]]
   ```

## Model
    In package model:
     Cube, Face, Slice, Corner, Edge, Center ...

## Operator
    Operator accept any algorithn and apply it on cube, if animation is enabled then play it ...
    Keep history of operation and can undo them
    Contained in Solver to animate and track solution
## Solver
  nxn_edges.py
  nxn_centers.py
  l1_cross.py
  l1_corners.py
  l2.py 
  l3_cross.py
  l3_corners.py
    
  Operate on cube using Operator
    
  The operator is very naive, it is simply mimics the beginner solver, for example from l2.py, bring edge from top to its location
  ```python
            if te().on_face(cube.right):
                self.op.op(self._ur_alg) # U R U' R' U' F' U F 
            else:
                self.op.op(self._ul_alg)
                
            ...
            
            @property
            def _ur_alg(self) -> Alg:
              return Algs.alg("L2-UR", Algs.U, Algs.R, Algs.U.prime, Algs.R.prime, Algs.U.prime, Algs.F.prime, Algs.U, Algs.F)

            @property
            def _ul_alg(self) -> Alg:
              return Algs.alg("L2-UL", Algs.U.prime + Algs.L.prime + Algs.U + Algs.L + Algs.U + Algs.F + Algs.U.prime + Algs.F.prime)


    ```
   
## Viewer/GUI
