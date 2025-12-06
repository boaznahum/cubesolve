# Rubik's Cube Model - Architecture Overview

> **Note:** This document provides a high-level overview of the model architecture.
> For detailed documentation with visual diagrams, see the specialized documents below.

## Related Detailed Documentation

| Topic | Document | Contents |
|-------|----------|----------|
| ID System | [model-id-system.md](model-id-system.md) | fixed_id, position_id, colors_id with visual diagrams |
| Edge Coordinates | [edge-coordinate-system.md](edge-coordinate-system.md) | right_top_left_same_direction explained |
| Attribute System | [partedge-attribute-system.md](partedge-attribute-system.md) | attributes, c_attributes, f_attributes for animation |

## Table of Contents

1. [Overview](#overview)
2. [Core Design Philosophy](#core-design-philosophy)
3. [Object Hierarchy](#object-hierarchy)
4. [The Part System](#the-part-system)
5. [Part Sharing and Wiring](#part-sharing-and-wiring)
6. [Identity Concepts](#identity-concepts)
7. [Rotation Algorithms](#rotation-algorithms)
8. [NxN Cube Support](#nxn-cube-support)
9. [Coordinate Systems](#coordinate-systems)
10. [Slice Rotations](#slice-rotations)
11. [Implementation Details](#implementation-details)

---

## Overview

This document provides a deep dive into the Rubik's Cube model implementation. The model supports NxN cubes (3x3, 4x4, 5x5, etc.) with a sophisticated architecture that maintains fixed parts and rotates colors.

**Key Innovation:** Unlike physical cubes where pieces move in 3D space, this model keeps all parts at FIXED POSITIONS and rotates their COLORS instead.

---

## Core Design Philosophy

### Fixed Parts, Rotating Colors

```
Physical Cube:              Virtual Model:
┌─────────┐                ┌─────────┐
│    B    │  Piece moves   │    B    │  Colors rotate
│  ┌───┐  │  in 3D space   │  Part   │  but part stays
│  │ R │  │  ────────>     │  Fixed  │  in same position
│  └───┘  │                │  [R→G]  │
└─────────┘                └─────────┘

Advantages:
- Simpler state management (no 3D coordinates)
- Faster queries (parts have fixed positions)
- Easier to validate (graph structure never changes)
- Natural for algorithm generation
```

---

## Object Hierarchy

### Complete Structure

```
Cube (size=N)
├── 6 Faces (F, B, L, R, U, D)
│   ├── 4 Edges per face (shared with adjacent faces)
│   ├── 4 Corners per face (shared with 2 adjacent faces)
│   └── 1 Center per face (NxN grid of center slices)
│
├── 12 Edges (each shared between 2 faces)
│   └── Each Edge contains (N-2) EdgeWing slices
│       └── Each EdgeWing contains 2 PartEdges
│
├── 8 Corners (each shared between 3 faces)
│   └── Each Corner contains 1 CornerSlice
│       └── Each CornerSlice contains 3 PartEdges
│
└── 3 Slices (M, E, S - middle layers)
    └── Each Slice contains edges and centers from 4 faces
```

### Class Hierarchy

```
Part (Abstract Base Class)
├── Edge (2-face piece)
│   └── Contains EdgeWing slices
├── Corner (3-face piece)
│   └── Contains CornerSlice (always 1)
└── Center (1-face piece)
    └── Contains CenterSlice grid (NxN)

PartSlice (Abstract)
├── EdgeWing - has 2 PartEdges (e1, e2)
├── CornerSlice - has 3 PartEdges (p1, p2, p3)
└── CenterSlice - has 1 PartEdge

PartEdge
└── Atomic unit: (Face, Color)
```

### Cube Net Visualization

```
Standard Cube Layout (BOY Color Scheme)
========================================

                ┌───────────┐
                │           │
                │  YELLOW   │  U (Up)
                │           │
    ┌───────────┼───────────┼───────────┬───────────┐
    │           │           │           │           │
    │  ORANGE   │   BLUE    │    RED    │   GREEN   │
    │           │           │           │           │
    │  L (Left) │  F (Front)│  R (Right)│  B (Back) │
    └───────────┼───────────┼───────────┴───────────┘
                │           │
                │   WHITE   │  D (Down)
                │           │
                └───────────┘

Face original colors NEVER change
Part colors DO change with rotations
```

---

## The Part System

### What is a Part?

A **Part** represents a physical piece on the cube. The key insight:

**Parts NEVER move in space - only their COLORS rotate!**

```python
# Physical reality: Edge piece moves from FR to UR
# Our model: FR Part stays at FR, but its colors change

Before R:  FR_part.colors = {BLUE, RED}
After R:   FR_part.colors = {WHITE, RED}  # Colors changed, part stayed
```

### PartSlice - The Atomic Unit

For NxN cubes, edges split into multiple physical pieces. Solution: **PartSlice**

```
3x3 Cube Edge:
  [═══════════]  One Edge, one EdgeWing slice

4x4 Cube Edge:
  [═════][═════]  One Edge, TWO EdgeWing slices

5x5 Cube Edge:
  [════][════][════]  One Edge, THREE EdgeWing slices
```

**Key relationship:**
```
Part = Logical concept (the "white-red edge")
PartSlice = Physical piece (one segment of that edge)
PartEdge = Atomic sticker (one colored square)
```

### Example: Edge Structure

```python
# 3x3 Front-Right edge
fr_edge = Edge(
    face1=Front,
    face2=Right,
    slices=[
        EdgeWing(index=0,
                 e1=PartEdge(Front, BLUE),
                 e2=PartEdge(Right, RED))
    ]
)

# 4x4 Front-Right edge
fr_edge = Edge(
    face1=Front,
    face2=Right,
    slices=[
        EdgeWing(0, PartEdge(Front, c1), PartEdge(Right, c1)),  # Outer
        EdgeWing(1, PartEdge(Front, c2), PartEdge(Right, c2))   # Inner
    ]
)
```

---

## Part Sharing and Wiring

### The Most Important Concept

**Parts are SHARED between faces!** One Part object, multiple references.

### Edge Sharing Example

```
         ┌───────────┐
         │     *     │  U (Up) face
         └───────────┘
              ↑
              │ SAME OBJECT
              ↓
         ┌───────────┐
         │     *     │  F (Front) face
         └───────────┘

Code:
  fu_edge = Edge(...)
  front.edge_top = fu_edge      # First reference
  up.edge_bottom = fu_edge      # Second reference (SAME object!)

  assert front.edge_top is up.edge_bottom  # True!
```

**Why this matters:**
- Rotate Front face → colors on `front.edge_top` change
- This AUTOMATICALLY affects `up.edge_bottom` (same object!)
- No need to manually update adjacent faces
- Impossible to have mismatched edges

### Corner Sharing Example

```
         FRU Corner touches THREE faces:

              U
              ┌─────┐
              │  *  │  Corner
         ┌────┼─────┤
         │  * │  *  │
     L   │ F  │  R  │
         └────┴─────┘

Code:
  fru_corner = Corner(...)
  front.corner_top_right = fru_corner
  right.corner_top_left = fru_corner
  up.corner_bottom_right = fru_corner

  # All three references point to SAME object
```

### Complete Wiring (3x3 Example)

```python
# In Cube._reset(), edges are wired:

# Front-Top edge shared with Up-Bottom
f._edge_top = u._edge_bottom = _create_edge(edges, f, u, True)

# Front-Right edge shared with Right-Left
f._edge_right = r._edge_left = _create_edge(edges, f, r, True)

# Front-Right-Up corner shared by all three faces
f._corner_top_right = r._corner_top_left = u._corner_bottom_right =
    _create_corner(corners, f, r, u)

# Result: 12 Edge objects, 8 Corner objects (not 24 and 24!)
```

---

## Identity Concepts

> **Detailed documentation:** See [model-id-system.md](model-id-system.md) for visual diagrams and in-depth explanation.

### Three Types of Identity

Each Part has THREE different identity concepts:

```
┌─────────────────────────────────────────────────────────┐
│  fixed_id (Physical Identity)                           │
│  - Never changes, even when scrambled                   │
│  - Based on: Face names + slice index                   │
│  - Example: frozenset([FaceName.F, FaceName.U, 0])     │
│  - Use: Tracking the physical piece object              │
│  - Analogy: Serial number stamped on piece              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  colors_id (Current State)                              │
│  - Current colors showing on this piece                 │
│  - Changes with every rotation                          │
│  - Example: frozenset([Color.BLUE, Color.YELLOW])      │
│  - Use: Checking what colors piece currently shows      │
│  - Analogy: Looking at visible stickers                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  position_id (Required Colors)                          │
│  - Colors that SHOULD be here if cube were solved       │
│  - Based on face colors where piece currently sits      │
│  - Example: At F/U → frozenset([Color.BLUE, YELLOW])   │
│  - Use: Checking if piece in correct position           │
│  - Analogy: The "home slot" colors                      │
└─────────────────────────────────────────────────────────┘
```

### Key Relationships

```python
# Piece is correctly solved
piece.colors_id == piece.position_id and piece.match_faces == True

# Piece is in correct slot but flipped/twisted
piece.colors_id == piece.position_id and piece.match_faces == False

# Piece is in wrong slot
piece.colors_id != piece.position_id
```

### Example Scenario

```python
# The white-red edge piece:
edge = cube.find_edge_by_color(frozenset([Color.WHITE, Color.RED]))

# fixed_id: ALWAYS frozenset([FaceName.F, FaceName.R, 0])
#           Never changes, identifies the FR slot

# colors_id: frozenset([Color.WHITE, Color.RED])
#            The actual colors on this piece (never changes for this piece)

# position_id: Depends on WHERE piece currently sits
#   - At FR slot: frozenset([Color.BLUE, Color.RED]) (expected FR colors)
#   - At FU slot: frozenset([Color.BLUE, Color.YELLOW]) (expected FU colors)

# If white-red piece is at FR slot:
edge.colors_id == frozenset([WHITE, RED])
edge.position_id == frozenset([BLUE, RED])
edge.in_position == False  # Colors don't match expected

# If white-red piece is at its correct slot (wherever that is based on cube state):
edge.colors_id == edge.position_id  # True
```

---

## Rotation Algorithms

### Face Rotation Overview

When rotating a face (e.g., F clockwise):

```
1. Edge Cycle:
   Top ← Left ← Bottom ← Right ← Top

2. Corner Cycle:
   TL ← BL ← BR ← TR ← TL

3. Center Rotation:
   Rotate center grid 90° clockwise

4. Update State:
   Increment modify counter
   Invalidate cached IDs
   Run sanity check if enabled
```

### Edge Rotation Details

```
Before F Rotation:            After F Clockwise:

      U                             U
    ┌─A─┐                         ┌─D─┐
  L │   │ R                     L │   │ R
    │ F │                         │ F │
    └─B─┘                         └─A─┘
      D                             D

Edge movement: A→R, R→B, B→L, L→A

Code:
  1. Save top edge: saved = top.clone()
  2. Copy left → top
  3. Copy bottom → left
  4. Copy right → bottom
  5. Copy saved → right
```

### Color Copying Mechanism

Only colors on the ROTATING FACE are copied:

```python
def copy_colors_horizontal(self, source):
    """
    Copy edge colors during rotation.
    Only the colors on shared faces are mapped.
    """
    shared_face = self.single_shared_face(source)  # The rotating face
    source_other = source.get_other_face(shared_face)
    dest_other = self.get_other_face(shared_face)

    # Map: (source_face → dest_face) for both stickers
    self.copy_colors(source,
                     (shared_face, shared_face),      # F → F (stays)
                     (source_other, dest_other))      # U → R (moves)
```

---

## NxN Cube Support

### Scaling Strategy

```
Size | n_slices | Edge Slices | Center Slices | Total Stickers
-----|----------|-------------|---------------|----------------
 3x3 |    1     |      1      |      1        |      54
 4x4 |    2     |      2      |    2x2 = 4    |      96
 5x5 |    3     |      3      |    3x3 = 9    |     150
 NxN |   N-2    |     N-2     |   (N-2)²      |     6N²
```

### Edge Structure for NxN

```
3x3 Edge (n_slices=1):
  Part.slices = [EdgeWing(0)]

4x4 Edge (n_slices=2):
  Part.slices = [EdgeWing(0), EdgeWing(1)]
               [  Outer    ][   Inner   ]

5x5 Edge (n_slices=3):
  Part.slices = [EdgeWing(0), EdgeWing(1), EdgeWing(2)]
               [  Outer    ][   Middle  ][  Outer    ]
```

### Center Structure for NxN

```
3x3 Center (1x1 grid):
  [C]

4x4 Center (2x2 grid):
  [C₀₀][C₀₁]
  [C₁₀][C₁₁]

5x5 Center (3x3 grid):
  [C₀₀][C₀₁][C₀₂]
  [C₁₀][C₁₁][C₁₂]
  [C₂₀][C₂₁][C₂₂]

Access: center.get_slice((row, col))
```

---

## Coordinate Systems

> **Detailed documentation:** See [edge-coordinate-system.md](edge-coordinate-system.md) for visual diagrams of edge direction mapping.

### Per-Face Local Coordinates

Each face uses local coordinates when looking AT it:

```
Front Face (looking at blue):
    ┌─── +X (right) →
    │  0  1  2
+Y  │  3  4  5
(↓) │  6  7  8

Convention:
  - Origin (0,0) is top-left
  - +X goes right
  - +Y goes down
  - Clockwise rotation from this viewpoint
```

### Edge Direction Flags

Adjacent faces may traverse shared edges in opposite directions:

```
      ┌───────────┐
      │  L → R    │  U face (left to right)
      └───────────┘
           ↕ SAME EDGE
      ┌───────────┐
      │  L → R    │  F face (left to right)
      └───────────┘

These traverse in SAME direction: right_top_left_same_direction = True

But:
      ┌───────────┐
      │  L → R    │  U face (left to right)
      └───────────┘
           ↕ SAME EDGE
      ┌───────────┐
      │  R → L    │  B face (RIGHT to left!)
      └───────────┘

These traverse in OPPOSITE direction: right_top_left_same_direction = False
```

This flag is critical for correct index mapping during rotations.

---

## Implementation Details

### Initialization Sequence

```python
# 1. Create faces with colors
f = Face(cube, FaceName.F, Color.BLUE)
r = Face(cube, FaceName.R, Color.RED)
# ... etc

# 2. Set opposite faces (for queries)
f.set_opposite(b)
r.set_opposite(l)
u.set_opposite(d)

# 3. Create parts (edges, corners, centers)
edges = []
corners = []
centers = []

# 4. Wire parts to faces (shared references!)
f._edge_top = u._edge_bottom = _create_edge(edges, f, u, True)
f._corner_top_right = r._corner_top_left = u._corner_bottom_right =
    _create_corner(corners, f, r, u)

# 5. Finish initialization (compute fixed_ids)
for part in edges + corners + centers:
    part.finish_init()

# 6. Create slices
slice_m = Slice(cube, SliceName.M, ...)
slice_e = Slice(cube, SliceName.E, ...)
slice_s = Slice(cube, SliceName.S, ...)
```

### Performance Characteristics

```
Operation             | Complexity | Notes
---------------------|------------|-------------------------------
Create cube          | O(N²)      | N = cube size
Face rotation        | O(N)       | Edges only, centers are O(N²)
Slice rotation       | O(N)       | 4 edges + centers
Find part by color   | O(1)       | With caching
Sanity check         | O(N²)      | Validates all parts
Reset cube           | O(N²)      | Rebuilds structure
```

### Memory Usage

```
3x3: ~5KB
- 12 edges × 1 slice = 12 EdgeWing objects
- 8 corners × 1 slice = 8 CornerSlice objects
- 6 centers × 1 slice = 6 CenterSlice objects

4x4: ~15KB
- 12 edges × 2 slices = 24 EdgeWing objects
- 8 corners × 1 slice = 8 CornerSlice objects
- 6 centers × 4 slices = 24 CenterSlice objects

5x5: ~35KB
- 12 edges × 3 slices = 36 EdgeWing objects
- 8 corners × 1 slice = 8 CornerSlice objects
- 6 centers × 9 slices = 54 CenterSlice objects
```

---

## Quick Reference

### Common Operations

```python
# Create cube
cube = Cube(size=3)

# Access faces
front = cube.front
right = cube.right

# Rotate face
front.rotate(1)    # 90° clockwise
front.rotate(-1)   # 90° counter-clockwise
front.rotate(2)    # 180°

# Find parts
white_red = frozenset([Color.WHITE, Color.RED])
edge = cube.find_edge_by_color(white_red)

# Check state
if cube.solved:
    print("Solved!")

if edge.in_position and edge.match_faces:
    print("Edge is correctly solved")

# Reset
cube.reset()
```

### Terminology Mapping

```
Physical Cube Term    →    Code Term
─────────────────────────────────────
Sticker               →    PartEdge
Piece                 →    Part / PartSlice
Edge piece            →    Edge
Corner piece          →    Corner
Center piece          →    Center
Face                  →    Face
Move (F, R, U)        →    face.rotate(n)
Wide move (Fw)        →    rotate_face_and_slice()
Slice (M, E, S)       →    rotate_slice()
```

---

## See Also

### Design Documentation
- [model-id-system.md](model-id-system.md) - ID system with visual diagrams
- [edge-coordinate-system.md](edge-coordinate-system.md) - Edge direction mapping
- [partedge-attribute-system.md](partedge-attribute-system.md) - Animation attribute system

### Source Code
- [`Cube.py`](../src/cube/domain/model/Cube.py) - Main Cube class implementation
- [`Face.py`](../src/cube/domain/model/Face.py) - Face rotation algorithms
- [`Part.py`](../src/cube/domain/model/Part.py) - Part base class and identity logic
- [`_part_slice.py`](../src/cube/domain/model/_part_slice.py) - PartSlice implementations
- [`PartEdge.py`](../src/cube/domain/model/PartEdge.py) - Atomic sticker unit
- [`CubeQueries2.py`](../src/cube/domain/model/CubeQueries2.py) - Query operations
