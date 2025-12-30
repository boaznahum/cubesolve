# Face and Slice Rotation: Complete Guide

This document explains the rotation mechanics in the cube model - how face rotations
and slice rotations work, the data flow, and where texture direction handling could fit.

**Prerequisites:** Read `edge-coordinate-system.md` first for understanding of index mapping.

---

## Overview: Types of Rotations

```
┌─────────────────────────────────────────────────────────────────┐
│                     ROTATION TYPES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FACE ROTATIONS (R, L, U, D, F, B)                              │
│  └── Rotates one face + adjacent stickers                       │
│      Implemented in: Face.rotate()                              │
│                                                                  │
│  SLICE ROTATIONS (M, E, S)                                      │
│  └── Rotates middle layer(s) between two opposite faces         │
│      Implemented in: Slice.rotate()                             │
│                                                                  │
│  CUBE ROTATIONS (x, y, z)                                       │
│  └── Composed of face rotations (e.g., x = R + L')              │
│      No separate implementation needed                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Face Rotation

### What Moves During a Face Rotation

When face F rotates 90° clockwise:

```
                    BEFORE                              AFTER

         U                                   U
    ┌─────────┐                         ┌─────────┐
    │ a  b  c │ ← F-U edge              │ g  d  a │ ← Was L edge
    └─────────┘                         └─────────┘
         │                                   │
    L    │    R                         L    │    R
   ┌─┐   │   ┌─┐                       ┌─┐   │   ┌─┐
   │g│   │   │j│                       │p│   │   │c│
   │h│   │   │k│                       │q│   │   │b│ ← Was U edge
   │i│   │   │l│                       │r│   │   │a│   (reversed!)
   └─┘   │   └─┘                       └─┘   │   └─┘
         │                                   │
    ┌─────────┐                         ┌─────────┐
    │ p  q  r │ ← F-D edge              │ l  k  j │ ← Was R edge
    └─────────┘                         └─────────┘
         D                                   D

    ALSO: The face itself rotates (corners + centers move on face F)
```

### Components That Move

1. **Edge stickers**: 4 edges × N slices each = 4N stickers cycle around
2. **Corner stickers**: 4 corners cycle (each corner has 3 faces, only F-face sticker moves on F)
3. **Center stickers**: (N-2)² center pieces rotate within face F
4. **Face colors**: The face's own stickers rotate in place

### The Rotation Algorithm (Face.rotate)

```
Face.rotate(n_rotations=1)
│
├── for each rotation (0 to n_rotations % 4):
│   │
│   ├── Step 1: SAVE TEMPORARIES
│   │   │   saved_top = edge_top.copy()      # Clone to prevent overwrite
│   │   │   e_right = edge_right.copy()
│   │   │   e_bottom = edge_bottom.copy()
│   │   └── e_left = edge_left.copy()
│   │
│   ├── Step 2: ROTATE EDGES (4-cycle)
│   │   │
│   │   │   For each slice index (0 to n_slices-1):
│   │   │   │
│   │   │   │   # Calculate correct indices using direction flag
│   │   │   │   i_top = get_ltr_index(saved_top, index)
│   │   │   │   i_left = get_slice_index(e_left, i_top)
│   │   │   │   i_right = get_ltr_index(e_right, inv(i_top))
│   │   │   │   i_bottom = get_ltr_index(e_bottom, inv(i_top))
│   │   │   │
│   │   │   │   # Copy colors around the cycle:
│   │   │   │   TOP ← LEFT:    edge_top.copy_colors_horizontal(e_left, ...)
│   │   │   │   LEFT ← BOTTOM: edge_left.copy_colors_horizontal(e_bottom, ...)
│   │   │   │   BOTTOM ← RIGHT: edge_bottom.copy_colors_horizontal(e_right, ...)
│   │   │   └── RIGHT ← saved: edge_right.copy_colors_horizontal(saved_top, ...)
│   │   │
│   │   └── (Index conversion handles direction differences automatically)
│   │
│   ├── Step 3: ROTATE CORNERS (4-cycle)
│   │   │   saved_bl = corner_bottom_left.copy()
│   │   │   BL ← BR: corner_bl.replace_colors(corner_br, ...)
│   │   │   BR ← TR: corner_br.replace_colors(corner_tr, ...)
│   │   │   TR ← TL: corner_tr.replace_colors(corner_tl, ...)
│   │   └── TL ← saved: corner_tl.replace_colors(saved_bl, ...)
│   │
│   ├── Step 4: ROTATE CENTER (in-place rotation)
│   │   │   For each center slice (N-2)²:
│   │   │   │   Calculate new position after 90° rotation
│   │   │   └── Copy color to new position
│   │   └── (Uses temporary clone to prevent overwrite)
│   │
│   ├── cube.modified()     # Mark cube as changed
│   └── cube.sanity()       # Validate cube state
│
└── Done
```

---

## Part 2: The Copy Chain

Understanding how colors actually move is crucial for texture handling.

### Call Hierarchy

```
Face.rotate()
    │
    ├── Edge.copy_colors_horizontal()
    │       │
    │       └── Part._replace_colors()
    │               │
    │               └── PartSlice.copy_colors()
    │                       │
    │                       ├── PartEdge.copy_color()  ← ATOMIC OPERATION
    │                       │       │
    │                       │       ├── Copy _color
    │                       │       ├── Copy _annotated_by_color
    │                       │       └── Copy c_attributes  ← TEXTURE HANDLE HERE
    │                       │
    │                       └── Copy slice c_attributes
    │
    └── Corner.replace_colors()
            │
            └── (Similar chain to PartSlice.copy_colors)
```

### PartEdge.copy_color() - The Atomic Operation

```python
# PartEdge.py - The core copy operation

def copy_color(self, source: "PartEdge"):
    """Copy color and associated attributes from source.

    This is the ATOMIC operation - everything that should "move with"
    the color must be copied here.
    """
    # 1. Copy the color itself
    self._color = source._color

    # 2. Copy annotation state
    self._annotated_by_color = source._annotated_by_color

    # 3. Copy color-associated attributes (c_attributes)
    #    This includes texture handles!
    self.c_attributes.clear()
    self.c_attributes.update(source.c_attributes)

    # NOTE: These are NOT copied:
    # - attributes (structural, position-based)
    # - f_attributes (fixed, like selection state)
```

### What Gets Copied vs What Stays

```
┌─────────────────────────────────────────────────────────────────┐
│                    ATTRIBUTE BEHAVIOR                            │
├──────────────────┬──────────────────┬───────────────────────────┤
│   Attribute      │  Copies?         │  Purpose                  │
├──────────────────┼──────────────────┼───────────────────────────┤
│ _color           │  YES             │  Sticker color            │
│ c_attributes     │  YES             │  Moves with color         │
│   └─ texture     │  YES             │  Texture handle           │
│   └─ direction?  │  YES (if added)  │  Texture orientation      │
├──────────────────┼──────────────────┼───────────────────────────┤
│ attributes       │  NO              │  Structural/position info │
│ f_attributes     │  NO              │  Fixed state (selection)  │
└──────────────────┴──────────────────┴───────────────────────────┘
```

---

## Part 3: Slice Rotation

### What is a Slice?

A slice is the middle layer(s) between two opposite faces:

```
    M slice (between L and R):      E slice (between U and D):

         ┌───┬───┬───┐                   ┌───┬───┬───┐
        /   /   /   /│                  /   /   /   /│
       ┌───┬───┬───┐ │                 ┌───┬───┬───┐ │
      /   / M /   /│ │                / E / E / E /│ │
     ┌───┼───┼───┤ │/│               ┌───┬───┬───┤ │/│
     │   │ M │   │/│ │               │   │   │   │/│ │
     ├───┼───┼───┤ │/                ├───┼───┼───┤ │/
     │   │ M │   │/│                 │   │   │   │/│
     ├───┼───┼───┤ │                 ├───┼───┼───┤ │
     │   │ M │   │/                  │   │   │   │/
     └───┴───┴───┘                   └───┴───┴───┘

    S slice (between F and B): similar, perpendicular to F/B
```

### Slice.rotate() Algorithm

```
Slice.rotate(n=1, slices_indexes=None)
│
├── Determine which slice indices to rotate
│   │   Default: all middle slices (indices 1 to n-2 for NxN cube)
│   └── Or specific indices if provided
│
├── for each rotation (0 to n % 4):
│   │
│   │   for each slice_index in range:
│   │   │
│   │   ├── Get 4 edge slices around the slice
│   │   │   elements = _get_slices_by_index(i)
│   │   │   edges: [EdgeWing × 4]        # One from each adjacent face
│   │   │   centers: [CenterSlice × 4*n] # Center slices on 4 faces
│   │   │
│   │   ├── ROTATE EDGES (4-cycle, vertical copy)
│   │   │   │   e0_saved = edges[0].clone()
│   │   │   │
│   │   │   │   edges[0] ← edges[1]:  edges[0].copy_colors_ver(edges[1])
│   │   │   │   edges[1] ← edges[2]:  edges[1].copy_colors_ver(edges[2])
│   │   │   │   edges[2] ← edges[3]:  edges[2].copy_colors_ver(edges[3])
│   │   │   └── edges[3] ← saved:     edges[3].copy_colors_ver(e0_saved)
│   │   │
│   │   └── ROTATE CENTERS (4-cycle per center position)
│   │       │   For each center position in slice:
│   │       │       c0_saved = centers[j].clone()
│   │       │       centers[j] ← centers[j+n]
│   │       │       centers[j+n] ← centers[j+2n]
│   │       │       centers[j+2n] ← centers[j+3n]
│   │       └──     centers[j+3n] ← c0_saved
│   │
│   └── cube.modified()
│
├── cube.reset_after_faces_changes()  # Critical: reset all caches
└── cube.sanity()
```

### Key Difference: Vertical vs Horizontal Copy

```
FACE ROTATION uses copy_colors_horizontal():
    - Copies within the SAME shared face
    - Both source and dest are on the same edge

SLICE ROTATION uses copy_colors_ver():
    - Copies between DIFFERENT faces
    - Source on face A, dest on face B
    - Also called "vertical" because it crosses face boundaries
```

---

## Part 4: The Texture Direction Problem

### Current State

```
Before F rotation:
    PartEdge at position (F, row=2, col=1):
        _color = GREEN
        c_attributes = {
            "cell_texture": 42,    # Texture handle - COPIES correctly
            # NO direction info!
        }

After F rotation (sticker moves to row=1, col=2):
    PartEdge at position (F, row=1, col=2):
        _color = GREEN             # ✓ Correct
        c_attributes = {
            "cell_texture": 42,    # ✓ Correct - handle moved with color
        }
        # But UV mapping is fixed → texture appears wrong orientation!
```

### Where Direction Changes

```
FACE ROTATION (e.g., F clockwise):
    ┌─────────────────────────────────────────────────────────────┐
    │ Stickers ON face F:                                         │
    │   All rotate 90° CW → texture direction += 90°              │
    │                                                              │
    │ Stickers on ADJACENT edges (U, R, D, L):                    │
    │   Move to new edge → texture direction UNCHANGED            │
    │   (They slide along, don't rotate in place)                 │
    └─────────────────────────────────────────────────────────────┘

    Example: F rotation

    Before:          After:

        ↑ A              A →
    L ──┼── R        L ──┼── R
        │                │

    Sticker A was on TOP edge, pointing UP (toward U).
    After F rotation, A is on RIGHT edge, still pointing UP (toward U)!
    Direction didn't change because it just slid from edge to edge.

    But sticker ON face F:

    Before:          After:

    ┌───────┐        ┌───────┐
    │   ↑   │        │   →   │
    │   B   │   →    │   B   │
    │       │        │       │
    └───────┘        └───────┘

    Sticker B was ON face F, pointing UP.
    After F rotation, B is still ON face F but rotated 90° CW.
    Now it points RIGHT → direction += 90°
```

### Slice Rotation Direction Changes

```
SLICE ROTATION (e.g., M slice = between L and R):
    ┌─────────────────────────────────────────────────────────────┐
    │ Stickers move from one face to another:                     │
    │   F → U → B → D → F                                         │
    │                                                              │
    │ When sticker moves to new face, its "up" direction          │
    │ may change relative to the new face's coordinate system!    │
    └─────────────────────────────────────────────────────────────┘

    Example: M rotation (like doing x' but just middle layer)

    Sticker on F face, pointing UP (toward U):

        F face:          U face (after M):
        ┌───────┐        ┌───────┐
        │   ↑   │   →    │   ↑   │  Still UP? Or changed?
        │   X   │        │   X   │
        └───────┘        └───────┘

    This depends on how the faces' coordinate systems relate!
    Need to track direction changes across face transitions.
```

---

## Part 5: Solution Options

### Option A: Store Direction in c_attributes (Current Proposal)

```python
c_attributes = {
    "cell_texture": 42,
    "cell_texture_rotation": 0,  # 0, 1, 2, 3 = 0°, 90°, 180°, 270° CW
}
```

**Challenge**: `copy_color()` doesn't know rotation context. Need to update
direction AFTER copy in a separate step.

```
Rotation flow:
    1. copy_color() copies handle + direction as-is
    2. After all copies done, iterate affected stickers
    3. Update direction based on rotation type
```

**Problem**: Where to hook step 3? Multiple entry points for rotation.

---

### Option B: Add Direction Attribute to PartEdge

```python
class PartEdge:
    _color: Color
    _texture_direction: int = 0  # 0, 1, 2, 3 = quarter turns CW

    def copy_color(self, source: "PartEdge"):
        self._color = source._color
        self._texture_direction = source._texture_direction
        self.c_attributes.clear()
        self.c_attributes.update(source.c_attributes)
```

**Benefit**: Direction is a first-class attribute, not buried in dict.
**Challenge**: Still need to update direction after rotation.

---

### Option C: Track Direction in Rotation Methods

```python
# In Face.rotate():
def _rotate(self):
    # ... existing copy logic ...

    # After copies, update directions for stickers ON this face
    for cell in self.get_all_face_cells():
        edge = cell.part_edge
        edge._texture_direction = (edge._texture_direction + 1) % 4  # +90° CW
```

**Benefit**: Direction update happens at rotation site where context is known.
**Challenge**: Need to modify both Face.rotate() and Slice.rotate().

---

### Option D: Compute Direction from Position History

Instead of storing direction, compute it from the sticker's journey:

```python
class PartEdge:
    _home_face: FaceName      # Where this sticker started (never changes)
    _home_direction: int = 0  # Original orientation (never changes)

    @property
    def texture_direction(self) -> int:
        """Compute direction from home vs current position."""
        # Calculate how much rotation from home to current position
        return compute_rotation(self._home_face, self._home_direction,
                               self.current_face)
```

**Benefit**: No need to update anything during rotation.
**Challenge**: Computing rotation from position is complex, may not be unique.

---

## Part 6: Recommended Approach

Based on the investigation, **Option B + C** seems most practical:

1. Add `_texture_direction: int` attribute to PartEdge
2. Copy it in `copy_color()` like other attributes
3. Update it in `Face.rotate()` for stickers ON the rotating face
4. Update it in `Slice.rotate()` based on face transitions

### Implementation Sketch

```python
# PartEdge.py
class PartEdge:
    __slots__ = ['_face', '_color', '_texture_direction', ...]

    def __init__(self, ...):
        self._texture_direction: int = 0  # 0=0°, 1=90°CW, 2=180°, 3=270°CW

    def copy_color(self, source: "PartEdge"):
        self._color = source._color
        self._texture_direction = source._texture_direction  # NEW
        self.c_attributes.clear()
        self.c_attributes.update(source.c_attributes)

# Face.py
def rotate(self, n_rotations=1):
    def _rotate():
        # ... existing copy logic ...

        # NEW: Update direction for stickers ON this face (not edge stickers)
        self._update_face_texture_directions(n=1)

    for _ in range(n_rotations % 4):
        _rotate()
        self.cube.modified()
        self.cube.sanity()

def _update_face_texture_directions(self, n: int):
    """Rotate texture direction for all stickers on this face."""
    for row in range(self.cube.size):
        for col in range(self.cube.size):
            part_edge = self.get_part_edge_at(row, col)
            if part_edge:
                part_edge._texture_direction = (part_edge._texture_direction + n) % 4
```

---

---

## Part 7: Texture Direction Example - 4x4 F Rotation

### Initial State (All directions = 0)

Looking at face F from outside the cube. Each cell shows `[texture_dir]`.
The arrow shows which way the texture's "up" points.

```
                        FACE U (looking down from above)
                    ┌─────┬─────┬─────┬─────┐
                    │  ↑  │  ↑  │  ↑  │  ↑  │
                    │ [0] │ [0] │ [0] │ [0] │  ← U's bottom edge (will move to R)
                    └─────┴─────┴─────┴─────┘
                              │
           FACE L             │              FACE R
        ┌─────┐               │               ┌─────┐
        │  ↑  │               │               │  ↑  │
        │ [0] │               │               │ [0] │
        ├─────┤               │               ├─────┤
        │  ↑  │               │               │  ↑  │
        │ [0] │    ┌──────────┴──────────┐    │ [0] │
        ├─────┤    │                     │    ├─────┤
        │  ↑  │    │       FACE F        │    │  ↑  │
        │ [0] │    │    (looking at it)  │    │ [0] │
        ├─────┤    │                     │    ├─────┤
        │  ↑  │    └──────────┬──────────┘    │  ↑  │
        │ [0] │               │               │ [0] │
        └─────┘               │               └─────┘
     L's right edge           │            R's left edge
     (will move to U)         │            (will move to D)
                              │
                    ┌─────┬─────┬─────┬─────┐
                    │  ↑  │  ↑  │  ↑  │  ↑  │  ← D's top edge (will move to L)
                    │ [0] │ [0] │ [0] │ [0] │
                    └─────┴─────┴─────┴─────┘
                        FACE D (looking up from below)
```

### FACE F Detail (4x4) - Before Rotation

```
    FACE F - Looking at it from outside (initial state, all direction=0)

    col:    0       1       2       3

    row 3: ┌───────┬───────┬───────┬───────┐
           │   ↑   │   ↑   │   ↑   │   ↑   │
           │  [0]  │  [0]  │  [0]  │  [0]  │   ← Top row (adjacent to U)
           │  F03  │  F13  │  F23  │  F33  │
    row 2: ├───────┼───────┼───────┼───────┤
           │   ↑   │   ↑   │   ↑   │   ↑   │
           │  [0]  │  [0]  │  [0]  │  [0]  │
           │  F02  │  F12  │  F22  │  F32  │
    row 1: ├───────┼───────┼───────┼───────┤
           │   ↑   │   ↑   │   ↑   │   ↑   │
           │  [0]  │  [0]  │  [0]  │  [0]  │
           │  F01  │  F11  │  F21  │  F31  │
    row 0: ├───────┼───────┼───────┼───────┤
           │   ↑   │   ↑   │   ↑   │   ↑   │
           │  [0]  │  [0]  │  [0]  │  [0]  │   ← Bottom row (adjacent to D)
           │  F00  │  F10  │  F20  │  F30  │
           └───────┴───────┴───────┴───────┘

    All 16 stickers on F have texture pointing UP (direction=0)
```

### After F Rotation (90° Clockwise) - Option B+C Applied

According to Option B+C:
1. `copy_color()` copies color + direction from source to destination
2. Then we update direction for stickers ON face F: `direction += 1`

```
    FACE F - After 90° CW rotation

    Sticker movement (colors cycle):
        F00 → F03    F10 → F02    F20 → F01    F30 → F00
        F01 → F13    F11 → F12    F21 → F11    F31 → F10
        F02 → F23    F12 → F22    F22 → F21    F32 → F20
        F03 → F33    F13 → F32    F23 → F31    F33 → F30

    col:    0       1       2       3

    row 3: ┌───────┬───────┬───────┬───────┐
           │   →   │   →   │   →   │   →   │
           │  [1]  │  [1]  │  [1]  │  [1]  │   ← Was: F00,F01,F02,F03 (left col)
           │ wasF00│wasF01 │wasF02 │wasF03 │      Now direction=1 (90° CW)
    row 2: ├───────┼───────┼───────┼───────┤
           │   →   │   →   │   →   │   →   │
           │  [1]  │  [1]  │  [1]  │  [1]  │
           │wasF10 │wasF11 │wasF12 │wasF13 │
    row 1: ├───────┼───────┼───────┼───────┤
           │   →   │   →   │   →   │   →   │
           │  [1]  │  [1]  │  [1]  │  [1]  │
           │wasF20 │wasF21 │wasF22 │wasF23 │
    row 0: ├───────┼───────┼───────┼───────┤
           │   →   │   →   │   →   │   →   │
           │  [1]  │  [1]  │  [1]  │  [1]  │   ← Was: F30,F31,F32,F33 (right col)
           │wasF30 │wasF31 │wasF32 │wasF33 │
           └───────┴───────┴───────┴───────┘

    ALL 16 stickers on F now have direction=1 (texture points RIGHT)
    Because they ALL rotated 90° CW with the face.
```

### What About Adjacent Edge Stickers?

The adjacent edge stickers cycle: L → U → R → D → L

```
    QUESTION: Do adjacent edge stickers also get direction += 1?

    Physical reality:
    - The PIECES rotate 90° CW (looking at F)
    - A sticker on L's right edge moves to U's bottom edge
    - In 3D space, that sticker has rotated 90° CW

    BUT:
    - The sticker was on FACE L, now it's on FACE U
    - Face L and Face U have DIFFERENT coordinate systems
    - The sticker's "up" relative to its OLD face vs NEW face...?

    Example: Sticker X on L's right edge (row=3), direction=0

    BEFORE: On Face L
    ┌───────┐
    │   ↑   │  Looking at L from left side
    │  [0]  │  Texture "up" points toward L's top (which is toward U in 3D)
    │   X   │
    └───────┘

    AFTER: On Face U's bottom edge (col=0)

    Two possibilities:

    A) Direction stays 0 (no change):
       ┌───────┐
       │   ↑   │  On U, texture "up" still points toward U's "up" (toward B)
       │  [0]  │  The face coordinate systems "align" for this transition
       │   X   │
       └───────┘

    B) Direction becomes 1:
       ┌───────┐
       │   →   │  Texture rotated 90° CW because piece rotated
       │  [1]  │
       │   X   │
       └───────┘

    WHICH IS CORRECT? Need to trace through the coordinate systems!
```

### Coordinate System Analysis for F Rotation

Let's trace what happens to texture "up" direction:

```
    3D Coordinate Reference:
        Y
        ↑
        │
        │
        └──────→ X
       /
      /
     Z (toward viewer = Front face)

    Face coordinate systems (R = right, T = top on each face):

    Face F: R→ = +X,  T↑ = +Y  (looking at F from +Z)
    Face U: R→ = +X,  T↑ = -Z  (looking at U from +Y)
    Face R: R→ = -Z,  T↑ = +Y  (looking at R from +X)
    Face D: R→ = +X,  T↑ = +Z  (looking at D from -Y)
    Face L: R→ = +Z,  T↑ = +Y  (looking at L from -X)

    During F rotation (90° CW looking at F):
    - Rotation axis: Z (the axis perpendicular to F)
    - Rotation transforms: +X → +Y → -X → -Y → +X

    Sticker on L's right edge:
        Before: On L, texture T↑ = +Y (L's "up")
        The piece rotates 90° CW around Z axis
        After: +Y transforms to -X
        Now sticker is on U's bottom edge
        On U, texture T↑ = -X
        But U's T↑ = -Z (not -X!)

        So the texture is NOT aligned with U's coordinate system!
        The texture has rotated relative to the new face.
```

### Conclusion: ALL Participating Stickers Rotate

```
    ┌────────────────────────────────────────────────────────────────┐
    │  FOR F ROTATION:                                               │
    │                                                                │
    │  ALL stickers that participate in the rotation get direction   │
    │  += 1, INCLUDING adjacent edge stickers!                       │
    │                                                                │
    │  This is because:                                              │
    │  1. They are on pieces that physically rotate 90° CW           │
    │  2. The face coordinate systems don't perfectly align          │
    │  3. The texture orientation changes relative to the new face   │
    │                                                                │
    │  Stickers ON face F:       16 stickers, direction += 1         │
    │  Adjacent edges (U,R,D,L): 16 stickers, direction += 1         │
    │                            (4 per edge × 4 edges)              │
    │                                                                │
    │  TOTAL: 32 stickers get direction += 1 for F rotation          │
    └────────────────────────────────────────────────────────────────┘

    WAIT - But if adjacent edges ALSO get +=1, then we DON'T need
    to copy direction in copy_color()!

    We could simply:
    1. Do all the color copies (direction copied or not - doesn't matter)
    2. After rotation, update ALL affected stickers: direction += 1

    The direction value at each position just gets incremented,
    regardless of what color/texture moved there.

    BUT WAIT - this is only true if ALL faces work the same way...
    Need to verify for other face rotations (R, U, L, D, B).
```

### Question for Verification

```
    Is it true that for ANY face rotation, ALL participating stickers
    (both on-face and adjacent edges) rotate by the same amount?

    If YES: direction += 1 for all, no need to copy in copy_color()
    If NO:  different stickers rotate differently, must copy and track

    TO VERIFY: Analyze R, U, B rotations with same coordinate analysis
```

---

## See Also

- `edge-coordinate-system.md` - Index mapping between adjacent faces
- `texture-per-cell-design.md` - Current texture implementation and bug
- `partedge-attribute-system.md` - c_attributes mechanism

---

*Document created: 2025-12-07*
*Status: Investigation complete, awaiting design decision*
