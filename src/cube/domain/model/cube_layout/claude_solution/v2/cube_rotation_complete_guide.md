# 🎲 Cube Grid Coordinate Transformation - Complete Guide

## Problem Overview

You have a 3D Rubik's cube where each of the 6 faces has an N×N grid. You want to perform a slice rotation and need to determine the coordinates of each cell visited on each face as the slice rotates around the cube.

---

## INPUT

```
1. N              = Grid size (e.g., 4 means 4×4 grid on each face)

2. Starting Face  = Which face you're on (F, B, L, R, U, D)

3. Rotate With    = Which adjacent face determines the rotation (F, B, L, R, U, D)

4. SI             = Slice Index (0 to N-1)
                    0 = slice closest to rotating face
                    N-1 = slice farthest from rotating face

5. Edge Connection Map = For each face, which edge connects to which face and edge
                         Format: face.edge → adjacent_face.edge
                         Example: F.RIGHT → R.LEFT means:
                                  Face F's RIGHT edge connects to Face R's LEFT edge
```

---

## OUTPUT

```
For each of the 4 faces in the rotation path:

  - Face name
  - Enter point (row, col)
  - Direction (LEFT→RIGHT, RIGHT→LEFT, BOTTOM→TOP, TOP→BOTTOM)
  - Visited cells: list of N coordinates
  - Exit edge
  - P value (position along exit edge)
```

---

## The LTR Coordinate System

Every face uses the **LTR (Left-To-Right, bottom-To-top)** coordinate system:

```
                        TOP edge
                  
      col→   0       1       2       3
           +-------+-------+-------+-------+
           |       |       |       |       |
     3     | (3,0) | (3,1) | (3,2) | (3,3) |    row = N-1
           |       |       |       |       |
           +-------+-------+-------+-------+
           |       |       |       |       |
LEFT 2     | (2,0) | (2,1) | (2,2) | (2,3) |              RIGHT
edge       |       |       |       |       |              edge
           +-------+-------+-------+-------+
   ↑       |       |       |       |       |                ↑
row  1     | (1,0) | (1,1) | (1,2) | (1,3) |
           |       |       |       |       |
           +-------+-------+-------+-------+
           |       |       |       |       |
     0     | (0,0) | (0,1) | (0,2) | (0,3) |    row = 0
           |       |       |       |       |
           +-------+-------+-------+-------+
      
                      BOTTOM edge


★ (0,0) is ALWAYS at the corner of LEFT and BOTTOM edges
★ Rows increase from BOTTOM to TOP
★ Columns increase from LEFT to RIGHT
```

---

## Key Concept: Rotation Path

When you rotate with a face, the slice travels through the **4 faces that surround** the rotating face (NOT through the rotating face itself):

```
Rotate with R → path: F → U → B → D → F (around R)
Rotate with L → path: F → D → B → U → F (around L)
Rotate with U → path: F → R → B → L → F (around U)
Rotate with D → path: F → L → B → R → F (around D)
Rotate with F → path: U → R → D → L → U (around F)
Rotate with B → path: U → L → D → R → U (around B)
```

---

## CW Rotation Rule

All rotations are **Clockwise (CW)** as viewed from the rotating face:

```
CW means: TOP edge → RIGHT edge → BOTTOM edge → LEFT edge → TOP edge

                TOP
                 ↓
          LEFT ←   → RIGHT
                 ↑
              BOTTOM
```

---

## STEP-BY-STEP ALGORITHM

### Step 1: Find the Path

Determine which 4 faces surround the rotating face. The starting face must be one of these 4.

### Step 2: Find Starting Direction and Point (Table 2)

Use the edge connections to determine:
- Which edge of your starting face connects to the rotating face? → **My Edge**
- Which edge of the rotating face connects to your starting face? → **Rotating Edge**

Look up (My Edge, Rotating Edge) in **Table 2** to get:
- Direction
- Start Point (using SI)
- Exit Edge

### Step 3: Walk on First Face

Visit N cells based on direction:
- Calculate P value at exit

### Step 4: Cross to Next Face (Table 1)

Use the edge connections:
- Exit Edge of current face
- Enter Edge of next face (from Edge Connection Map)

Look up in **Table 1** to get:
- New row, new col
- New direction

### Step 5: Repeat Steps 3-4

Continue for all 4 faces until you return to start.

---

## TABLE 1: Crossing Transformations (16 cases)

When crossing from one face to another:

```
P = position along exit edge (row for horizontal, col for vertical)
```

| # | Exit Edge | Enter Edge | new_row | new_col | New Direction |
|---|-----------|------------|---------|---------|---------------|
| 1 | RIGHT | LEFT | P | 0 | LEFT→RIGHT |
| 2 | RIGHT | RIGHT | P | N-1 | RIGHT→LEFT |
| 3 | RIGHT | BOTTOM | 0 | P | BOTTOM→TOP |
| 4 | RIGHT | TOP | N-1 | P | TOP→BOTTOM |
| 5 | LEFT | RIGHT | P | N-1 | RIGHT→LEFT |
| 6 | LEFT | LEFT | P | 0 | LEFT→RIGHT |
| 7 | LEFT | BOTTOM | 0 | P | BOTTOM→TOP |
| 8 | LEFT | TOP | N-1 | P | TOP→BOTTOM |
| 9 | TOP | BOTTOM | 0 | P | BOTTOM→TOP |
| 10 | TOP | TOP | N-1 | P | TOP→BOTTOM |
| 11 | TOP | LEFT | P | 0 | LEFT→RIGHT |
| 12 | TOP | RIGHT | P | N-1 | RIGHT→LEFT |
| 13 | BOTTOM | TOP | N-1 | P | TOP→BOTTOM |
| 14 | BOTTOM | BOTTOM | 0 | P | BOTTOM→TOP |
| 15 | BOTTOM | LEFT | P | 0 | LEFT→RIGHT |
| 16 | BOTTOM | RIGHT | P | N-1 | RIGHT→LEFT |

---

## TABLE 2: Starting Face (16 cases)

When determining starting direction based on rotation:

```
My Edge = edge of current face that connects to rotating face
Rotating Edge = edge of rotating face that connects to current face
SI = Slice Index (0 to N-1)
```

| # | My Edge | Rotating Edge | Direction | Start Point | Exit Edge |
|---|---------|---------------|-----------|-------------|-----------|
| 1 | RIGHT | LEFT | BOTTOM→TOP | (0, (N-1)-SI) | TOP |
| 2 | RIGHT | RIGHT | TOP→BOTTOM | (N-1, (N-1)-SI) | BOTTOM |
| 3 | RIGHT | TOP | TOP→BOTTOM | (N-1, (N-1)-SI) | BOTTOM |
| 4 | RIGHT | BOTTOM | BOTTOM→TOP | (0, (N-1)-SI) | TOP |
| 5 | LEFT | LEFT | BOTTOM→TOP | (0, SI) | TOP |
| 6 | LEFT | RIGHT | TOP→BOTTOM | (N-1, SI) | BOTTOM |
| 7 | LEFT | TOP | TOP→BOTTOM | (N-1, SI) | BOTTOM |
| 8 | LEFT | BOTTOM | BOTTOM→TOP | (0, SI) | TOP |
| 9 | TOP | LEFT | LEFT→RIGHT | ((N-1)-SI, 0) | RIGHT |
| 10 | TOP | RIGHT | RIGHT→LEFT | ((N-1)-SI, N-1) | LEFT |
| 11 | TOP | TOP | LEFT→RIGHT | ((N-1)-SI, 0) | RIGHT |
| 12 | TOP | BOTTOM | RIGHT→LEFT | ((N-1)-SI, N-1) | LEFT |
| 13 | BOTTOM | LEFT | RIGHT→LEFT | (SI, N-1) | LEFT |
| 14 | BOTTOM | RIGHT | LEFT→RIGHT | (SI, 0) | RIGHT |
| 15 | BOTTOM | TOP | RIGHT→LEFT | (SI, N-1) | LEFT |
| 16 | BOTTOM | BOTTOM | LEFT→RIGHT | (SI, 0) | RIGHT |

---

## TABLE 3: Visit Sequences

Based on direction and entry point:

| Direction | Enter Point | Visit Sequence | Exit Edge | P = |
|-----------|-------------|----------------|-----------|-----|
| LEFT→RIGHT | (row, 0) | (row,0), (row,1), ..., (row,N-1) | RIGHT | row |
| RIGHT→LEFT | (row, N-1) | (row,N-1), (row,N-2), ..., (row,0) | LEFT | row |
| BOTTOM→TOP | (0, col) | (0,col), (1,col), ..., (N-1,col) | TOP | col |
| TOP→BOTTOM | (N-1, col) | (N-1,col), (N-2,col), ..., (0,col) | BOTTOM | col |

---

## WORKED EXAMPLE

### Input

```
N = 4
Starting Face = F
Rotate With = R
SI = 0 (closest slice to R)

Edge Connection Map:
  F.RIGHT  → R.LEFT
  F.TOP    → U.BOTTOM
  F.LEFT   → L.RIGHT
  F.BOTTOM → D.TOP
  
  U.RIGHT  → R.TOP
  U.BACK   → B.TOP
  
  B.RIGHT  → R.RIGHT
  B.TOP    → U.BACK
  
  D.RIGHT  → R.BOTTOM
  D.BACK   → B.BOTTOM
```

### Step 1: Find the Path

```
Rotate with R → faces around R are: F, U, B, D
Path: F → U → B → D → back to F
```

### Step 2: Starting Face (F)

```
F connects to R via: F.RIGHT → R.LEFT

My Edge = RIGHT
Rotating Edge = LEFT

Table 2 lookup: (RIGHT, LEFT) → Row #1
  Direction: BOTTOM→TOP
  Start Point: (0, (N-1)-SI) = (0, 3-0) = (0, 3)
  Exit Edge: TOP
```

### Step 3: Walk on Face F

```
Face F:
  Direction: BOTTOM→TOP
  Start: (0, 3)
  
        +-------+-------+-------+-------+
  3     |       |       |       |(3,3)↑ | EXIT → to U
        +-------+-------+-------+-------+
  2     |       |       |       |(2,3)↑ |
        +-------+-------+-------+-------+
  1     |       |       |       |(1,3)↑ |
        +-------+-------+-------+-------+
  0     |       |       |       |(0,3)↑ | START
        +-------+-------+-------+-------+

  Visited: (0,3), (1,3), (2,3), (3,3)
  Exit Edge: TOP
  P = col = 3
```

### Step 4: Cross to Face U

```
F.TOP → U.BOTTOM (from Edge Connection Map)

Exit Edge: TOP
Enter Edge: BOTTOM

Table 1 lookup: (TOP, BOTTOM) → Row #9
  new_row = 0
  new_col = P = 3
  new_direction = BOTTOM→TOP
```

### Step 5: Walk on Face U

```
Face U:
  Direction: BOTTOM→TOP
  Enter: (0, 3)
  
        +-------+-------+-------+-------+
  3     |       |       |       |(3,3)↑ | EXIT → to B
        +-------+-------+-------+-------+
  2     |       |       |       |(2,3)↑ |
        +-------+-------+-------+-------+
  1     |       |       |       |(1,3)↑ |
        +-------+-------+-------+-------+
  0     |       |       |       |(0,3)↑ | ENTER
        +-------+-------+-------+-------+

  Visited: (0,3), (1,3), (2,3), (3,3)
  Exit Edge: TOP
  P = col = 3
```

### Step 6: Cross to Face B

```
U.TOP → B.??? (need from Edge Connection Map)
Let's say: U.TOP → B.TOP

Exit Edge: TOP
Enter Edge: TOP

Table 1 lookup: (TOP, TOP) → Row #10
  new_row = N-1 = 3
  new_col = P = 3
  new_direction = TOP→BOTTOM
```

### Step 7: Walk on Face B

```
Face B:
  Direction: TOP→BOTTOM
  Enter: (3, 3)
  
        +-------+-------+-------+-------+
  3     |       |       |       |(3,3)↓ | ENTER
        +-------+-------+-------+-------+
  2     |       |       |       |(2,3)↓ |
        +-------+-------+-------+-------+
  1     |       |       |       |(1,3)↓ |
        +-------+-------+-------+-------+
  0     |       |       |       |(0,3)↓ | EXIT → to D
        +-------+-------+-------+-------+

  Visited: (3,3), (2,3), (1,3), (0,3)
  Exit Edge: BOTTOM
  P = col = 3
```

### Step 8: Cross to Face D

```
B.BOTTOM → D.??? (need from Edge Connection Map)
Let's say: B.BOTTOM → D.BOTTOM

Exit Edge: BOTTOM
Enter Edge: BOTTOM

Table 1 lookup: (BOTTOM, BOTTOM) → Row #14
  new_row = 0
  new_col = P = 3
  new_direction = BOTTOM→TOP
```

### Step 9: Walk on Face D

```
Face D:
  Direction: BOTTOM→TOP
  Enter: (0, 3)
  
        +-------+-------+-------+-------+
  3     |       |       |       |(3,3)↑ | EXIT → back to F
        +-------+-------+-------+-------+
  2     |       |       |       |(2,3)↑ |
        +-------+-------+-------+-------+
  1     |       |       |       |(1,3)↑ |
        +-------+-------+-------+-------+
  0     |       |       |       |(0,3)↑ | ENTER
        +-------+-------+-------+-------+

  Visited: (0,3), (1,3), (2,3), (3,3)
  Exit Edge: TOP
  P = col = 3
```

### Step 10: Verify Return to Start

```
D.TOP → F.BOTTOM (from Edge Connection Map)

Exit Edge: TOP
Enter Edge: BOTTOM

Table 1 lookup: (TOP, BOTTOM) → Row #9
  new_row = 0
  new_col = P = 3
  new_direction = BOTTOM→TOP

This matches our starting point on F! ✓
```

---

## FINAL OUTPUT

```
INPUT:
  N = 4
  Starting Face = F
  Rotate With = R
  SI = 0

OUTPUT:

Face 1 (F):
  Enter: (0, 3)
  Direction: BOTTOM→TOP
  Visited: [(0,3), (1,3), (2,3), (3,3)]
  Exit: TOP
  P = 3

Face 2 (U):
  Enter: (0, 3)
  Direction: BOTTOM→TOP
  Visited: [(0,3), (1,3), (2,3), (3,3)]
  Exit: TOP
  P = 3

Face 3 (B):
  Enter: (3, 3)
  Direction: TOP→BOTTOM
  Visited: [(3,3), (2,3), (1,3), (0,3)]
  Exit: BOTTOM
  P = 3

Face 4 (D):
  Enter: (0, 3)
  Direction: BOTTOM→TOP
  Visited: [(0,3), (1,3), (2,3), (3,3)]
  Exit: TOP
  P = 3

→ Returns to starting point on F ✓

Total cells visited: 16 (4 faces × 4 cells)
```

---

## EXAMPLE WITH SI = 2

Same setup but SI = 2:

```
INPUT:
  N = 4
  Starting Face = F
  Rotate With = R
  SI = 2

Step 2: Starting Face (F)
  Table 2: (RIGHT, LEFT)
  Start Point: (0, (N-1)-SI) = (0, 3-2) = (0, 1)

OUTPUT:

Face 1 (F):
  Enter: (0, 1)
  Direction: BOTTOM→TOP
  Visited: [(0,1), (1,1), (2,1), (3,1)]
  Exit: TOP
  P = 1

Face 2 (U):
  Enter: (0, 1)
  Direction: BOTTOM→TOP
  Visited: [(0,1), (1,1), (2,1), (3,1)]
  Exit: TOP
  P = 1

Face 3 (B):
  Enter: (3, 1)
  Direction: TOP→BOTTOM
  Visited: [(3,1), (2,1), (1,1), (0,1)]
  Exit: BOTTOM
  P = 1

Face 4 (D):
  Enter: (0, 1)
  Direction: BOTTOM→TOP
  Visited: [(0,1), (1,1), (2,1), (3,1)]
  Exit: TOP
  P = 1

→ Returns to starting point on F ✓
```

---

## VISUAL: SI Values on Face F (when rotating with R)

```
Rotating with R (R is to the RIGHT of F):

        +-------+-------+-------+-------+
  3     |       |       |       |       |
        +-------+-------+-------+-------+
  2     |       |       |       |       |
        +-------+-------+-------+-------+
  1     |       |       |       |       |
        +-------+-------+-------+-------+
  0     |       |       |       |       |
        +-------+-------+-------+-------+
           col     col     col     col
            0       1       2       3
           SI=3    SI=2    SI=1    SI=0
           
           ←─────────────────────────→
           farthest              closest
           from R                to R
```

---

## SUMMARY

1. **Get inputs**: N, Starting Face, Rotate With, SI, Edge Connection Map

2. **Find path**: 4 faces surrounding the rotating face

3. **Use Table 2**: (My Edge, Rotating Edge) → Starting direction, point, exit edge

4. **Walk first face**: Visit N cells, calculate P

5. **Use Table 1**: (Exit Edge, Enter Edge) → New position and direction

6. **Repeat**: Walk and cross for all 4 faces

7. **Verify**: Return to starting point

---

## VARIANT 2: FaceOutput with get_point() Method

### Overview

Variant 2 provides a `FaceOutput` class with a `get_point(si, other_coord)` method that dynamically calculates coordinates for any slice index.

### Key Features

```
FaceOutput.get_point(si, other_coord) → (row, col)

Parameters:
  - si: Slice Index (0 to N-1)
        0 = closest to rotating face
        N-1 = farthest from rotating face
        
  - other_coord: Position along the path (0 to N-1)
        0 = entry point (where path enters this face)
        N-1 = exit point (where path exits this face)

Returns:
  - (row, col) in the LTR coordinate system
```

### CRITICAL ADJACENCY PROPERTY

For consecutive faces f1 and f2 (where f2 follows f1 in CW rotation):

```
f1.get_point(si, N-1)  →  EXIT point (last point on f1)
f2.get_point(si, 0)    →  ENTRY point (first point on f2)

These two points are PHYSICALLY ADJACENT on the 3D cube surface!
```

### Visual Example

```
Rotation path: F → U → B → D → F (rotating with R)
N = 4, SI = 0

Face F:                          Face U:
Direction: BOTTOM→TOP            Direction: BOTTOM→TOP

      TOP                              TOP
  +---+---+---+---+                +---+---+---+---+
3 |   |   |   |(3,3)|  EXIT      3 |   |   |   |(3,3)|
  +---+---+---+---+                +---+---+---+---+
2 |   |   |   |(2,3)|            2 |   |   |   |(2,3)|
  +---+---+---+---+                +---+---+---+---+
1 |   |   |   |(1,3)|            1 |   |   |   |(1,3)|
  +---+---+---+---+                +---+---+---+---+
0 |   |   |   |(0,3)|            0 |   |   |   |(0,3)|  ENTRY
  +---+---+---+---+                +---+---+---+---+
      BOTTOM                           BOTTOM

f1 = Face F (index 0)
f2 = Face U (index 1)

f1.get_point(si=0, other_coord=3) = (3, 3)   ← EXIT from F's TOP edge
f2.get_point(si=0, other_coord=0) = (0, 3)   ← ENTRY to U's BOTTOM edge

On the 3D cube:
- F's TOP edge is adjacent to U's BOTTOM edge
- Point (3,3) on F touches point (0,3) on U
- They are the SAME physical location on the cube's edge!
```

### Understanding other_coord

```
DIRECTION: BOTTOM→TOP (vertical walk upward)
─────────────────────────────────────────────

                 TOP edge
                   ↓
          +---+---+---+---+
    row 3 |   |   | X |   |  ← other_coord = 3 (EXIT)
          +---+---+---+---+
    row 2 |   |   | X |   |  ← other_coord = 2
          +---+---+---+---+
    row 1 |   |   | X |   |  ← other_coord = 1
          +---+---+---+---+
    row 0 |   |   | X |   |  ← other_coord = 0 (ENTRY)
          +---+---+---+---+
                   ↑
              col = (N-1)-SI
              
    Path visits: (0,col) → (1,col) → (2,col) → (3,col)
    other_coord:    0        1          2          3


DIRECTION: LEFT→RIGHT (horizontal walk rightward)
─────────────────────────────────────────────────

          +---+---+---+---+
    row   | X | X | X | X |  ← row = (N-1)-SI
          +---+---+---+---+
            ↑   ↑   ↑   ↑
           oc  oc  oc  oc
           =0  =1  =2  =3
           
    ENTRY              EXIT
    (col=0)          (col=3)
    
    Path visits: (row,0) → (row,1) → (row,2) → (row,3)
    other_coord:    0        1          2          3
```

### Usage Examples

```python
from cube_rotation_walker_v2 import (
    CubeRotationWalkerV2, Face, create_standard_edge_map
)

# Setup
edge_map = create_standard_edge_map()
walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)

# Get FaceOutput objects
faces = walker.calculate_rotation(
    starting_face=Face.F,
    rotate_with=Face.R
)

# Get all points for SI=0
for oc in range(4):
    row, col = faces[0].get_point(si=0, other_coord=oc)
    print(f"Position {oc}: ({row}, {col})")

# Get entry and exit points
entry_point = faces[0].get_point(si=0, other_coord=0)
exit_point = faces[0].get_point(si=0, other_coord=3)

# Verify adjacency between consecutive faces
f1_exit = faces[0].get_point(si=0, other_coord=3)
f2_entry = faces[1].get_point(si=0, other_coord=0)
# f1_exit and f2_entry are adjacent on the cube!

# Get points for different slice indices
for si in range(4):
    point = faces[0].get_point(si=si, other_coord=0)
    print(f"SI={si}: Entry at {point}")
```

### FaceOutput Attributes

```
FaceOutput object contains:

  face           : Face name (F, B, L, R, U, D)
  n              : Grid size
  direction      : Walking direction (LEFT→RIGHT, RIGHT→LEFT, BOTTOM→TOP, TOP→BOTTOM)
  my_edge        : Edge of this face connecting to rotating face
  rotating_edge  : Edge of rotating face connecting to this face
  exit_edge      : Edge where path exits this face
  enter_edge     : Edge where path enters this face
  face_index     : Position in rotation path (0, 1, 2, or 3)
  
Methods:

  get_point(si, other_coord) → (row, col)
      Get coordinate for given SI and position
      
  get_all_points(si) → [(row, col), ...]
      Get all N coordinates for given SI
```
