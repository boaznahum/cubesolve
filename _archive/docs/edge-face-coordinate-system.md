# Edge-Face Coordinate System: right_top_left_same_direction

This document explains the most complex concept in the cube model - the edge coordinate system
and the `right_top_left_same_direction` flag.

**Reference:** See the hand-drawn diagram below.

---

## Critical Insight: Face Coordinate Consistency (Issue #53)

### The Problem: Two Edges Must Agree

Each face has 4 edges. When we use left-to-right (ltr) coordinates on a face, **all edges
of that face must interpret ltr the same way**. Otherwise, code that uses ltr coordinates
to access different edges would get inconsistent results.

For example, on Face U:
- If `edge_left.get_slice_index_from_ltr_index(U, 0)` returns slice 0
- Then `edge_right.get_slice_index_from_ltr_index(U, 0)` must ALSO behave consistently

The ltr coordinate system belongs to the **Face**, not to individual edges!

### Why Edges Need the `right_top_left_same_direction` Flag

An edge is shared by exactly two faces. Each face has its own coordinate system (R→ and T↑).
The edge must store a single array of slices, but the two faces may "see" this array in
opposite directions.

The flag tells us: do both faces see the slices in the same order, or reversed?

### The Arbitrary f1 Choice - And Its Constraint

When `right_top_left_same_direction=False`, we must pick ONE face as the "reference" (f1)
where indices are used directly, and the OTHER face (f2) gets inverted indices.

**Critical constraint:** For any face F that appears in multiple edges with `same_direction=False`,
F must be consistently f1 (or consistently f2) across ALL such edges. Otherwise, F's coordinate
system would be inconsistent.

Example of the bug that was fixed:
```python
# BEFORE (inconsistent - U is f2 in one, f1 in other):
l._edge_top = u._edge_left = _create_edge(edges, l, u, False)  # U is f2
u._edge_top = b._edge_top = _create_edge(edges, u, b, False)   # U is f1  ← WRONG!

# AFTER (consistent - U is always f1):
l._edge_top = u._edge_left = _create_edge(edges, u, l, False)  # U is f1  ← FIXED!
u._edge_top = b._edge_top = _create_edge(edges, u, b, False)   # U is f1
```

### Coordinate Conversion: Face Methods (Preferred)

Since the ltr coordinate system belongs to the Face, the conversion methods should
ideally be on Face, not Edge. The Face can delegate to its edges but ensures consistency.

See `Face.get_slice_index_from_ltr_index()` and related methods.

---

## Hand-Drawn Reference Diagram

![Edge Coordinate System - Hand-drawn diagram showing R/T directions for all edges](images/right-top-left-coordinates.jpg)

*Human-drawn diagram showing the R (right) and T (top) direction arrows for each face, illustrating which edge pairs have same vs opposite indexing directions.*

## Generated Diagram (Clean Version)

![Edge Coordinate System - Generated diagram with 3D and unfolded views](images/edge-coordinate-system.png)

*Generated diagram showing:*
- *Left: 3D cube with ✓ (green) = same_direction True, ✗ (red) = False*
- *Right: Unfolded cube with R (blue→) and T (red↑) direction arrows on each face*
- *Summary: 8 edges SAME, 4 edges OPPOSITE (L-U, U-B, D-R, D-B)*

---

## The Problem: Edge Slice Indexing

When rotating a face, we need to copy colors from one edge to another.
But edges have multiple slices (in NxN cubes), and we need to know which slice maps to which.

```
    Face F rotation (clockwise):

    LEFT edge slices → TOP edge slices

    But which slice index on LEFT maps to which slice index on TOP?
```

The answer depends on whether the two faces have their "left-to-right" direction
pointing the same way along the shared edge.

---

## The Concept: Left-to-Right Direction

Each face has a natural coordinate system:
- **R direction**: Left → Right (along horizontal edges)
- **T direction**: Bottom → Top (along vertical edges)

```
    Looking at Face F from outside the cube:

                    T (top)
                    ↑
                    │
         ┌─────────┼─────────┐
         │         │         │
         │    0    1    2    │  ← Edge slices indexed 0,1,2
    ─────┼─────────┼─────────┼─────→ R (right)
         │         │         │
         │         │         │
         └─────────┴─────────┘
```

---

## The Key Insight: Direction Agreement

When two faces share an edge, their R/T directions along that edge may:
- **Agree** (`right_top_left_same_direction = True`): Both faces index slices the same way
- **Disagree** (`right_top_left_same_direction = False`): Slice indices are reversed

### Example: Same Direction (F-U edge)

```
         Face U (looking down at top)          Face F (looking at front)

              R→                                    R→
         ┌─────────┐                           ┌─────────┐
         │ 0  1  2 │ ← F-U edge                │ 0  1  2 │ ← F-U edge (same edge!)
         │         │                           └─────────┘
         │    U    │                           (viewing from F)
         └─────────┘

    Slice 0 on U = Slice 0 on F  ✓
    Slice 1 on U = Slice 1 on F  ✓
    Slice 2 on U = Slice 2 on F  ✓

    right_top_left_same_direction = TRUE
```

### Example: Opposite Direction (L-U edge)

```
         Face U (looking down at top)          Face L (looking at left side)

              R→
         ┌─────────┐                           ┌─────────┐
       2 │         │                           │         │ 0  ← L-U edge
       1 │    U    │ ← L-U edge                │    L    │ 1
       0 │         │                           │         │ 2
         └─────────┘                           └─────────┘
              ↑                                      ↑
         T direction                            T direction

    From U's view: slice 0 is at bottom of edge
    From L's view: slice 0 is at TOP of edge (T↑ points up!)

    Slice 0 on U = Slice 2 on L  (reversed!)
    Slice 1 on U = Slice 1 on L
    Slice 2 on U = Slice 0 on L

    right_top_left_same_direction = FALSE
```

---

## Visual Reference: Interpreting the Hand-Drawn Diagram

The hand-drawn diagram at the top of this document shows:

```
                         U
                        ┌─┐
                       →R  (R points right on U)
                       ←R  (and shows Back's R is opposite!)


            L ──────────┼────────── R
           T↑          │           T↑
           R→          │           ←R  (R direction on R face)
                       │
                       │
                       F
                      R→

    For each edge, the diagram shows:
    - R→ : The "right" direction from each face's perspective
    - T↑ : The "top" direction from each face's perspective

    Where arrows point SAME way: same_direction = TRUE
    Where arrows point OPPOSITE: same_direction = FALSE
```

---

## All 12 Edges: Direction Mapping

From `Cube.py` edge creation:

```python
# SAME DIRECTION (True) - indices match directly
f._edge_top = u._edge_bottom = _create_edge(edges, f, u, True)    # F-U
f._edge_left = l._edge_right = _create_edge(edges, f, l, True)    # F-L
f._edge_right = r._edge_left = _create_edge(edges, f, r, True)    # F-R
f._edge_bottom = d._edge_top = _create_edge(edges, f, d, True)    # F-D
l._edge_bottom = d._edge_left = _create_edge(edges, l, d, True)   # L-D
r._edge_right = b._edge_left = _create_edge(edges, r, b, True)    # R-B
l._edge_left = b._edge_right = _create_edge(edges, l, b, True)    # L-B
u._edge_right = r._edge_top = _create_edge(edges, u, r, True)     # U-R

# OPPOSITE DIRECTION (False) - indices are inverted
l._edge_top = u._edge_left = _create_edge(edges, l, u, False)     # L-U
d._edge_right = r._edge_bottom = _create_edge(edges, d, r, False) # D-R
d._edge_bottom = b._edge_bottom = _create_edge(edges, d, b, False) # D-B
u._edge_top = b._edge_top = _create_edge(edges, u, b, False)      # U-B
```

### Visual Summary:

```
    SAME DIRECTION (8 edges):        OPPOSITE DIRECTION (4 edges):

    F-U, F-L, F-R, F-D               L-U
    L-D, L-B                         U-B
    R-B                              D-R
    U-R                              D-B

    Pattern: All Front edges are SAME.
             Back edges with U or D are OPPOSITE.
             L-U and D-R are OPPOSITE.
```

---

## How It's Used: Slice Index Conversion

From `Edge.py`:

```python
def get_ltr_index_from_slice_index(self, face: Face, i) -> int:
    """
    Convert slice index to left-to-right index for given face.
    """
    if self.right_top_left_same_direction:
        return i  # Same direction: index unchanged
    else:
        if face is self._f1:
            return i  # f1 is the reference
        else:
            return self.inv_index(i)  # f2: invert the index!

def inv_index(self, i):
    """Invert index: 0↔n-1, 1↔n-2, etc."""
    return self.n_slices - 1 - i
```

---

## How It's Used: Face Rotation

From `Face.py` rotate():

```python
def _rotate(self):
    # Colors move: LEFT → TOP → RIGHT → BOTTOM → LEFT

    for index in range(n_slices):
        # Get the LEFT-TO-RIGHT index for each edge from THIS face's perspective
        top_ltr_index = saved_top.get_face_ltr_index_from_edge_slice_index(self, index)

        # Calculate corresponding indices on other edges
        i_left = e_left.get_edge_slice_index_from_face_ltr_index(self, top_ltr_index)
        i_right = e_right.get_face_ltr_index_from_edge_slice_index(self, inv(top_ltr_index))
        i_bottom = e_bottom.get_face_ltr_index_from_edge_slice_index(self, inv(top_ltr_index))

        # Copy colors with correct index mapping
        self._edge_top.copy_colors_horizontal(e_left, index=i_top, source_index=i_left)
        # ... etc
```

The `get_ltr_index_from_slice_index` method handles the direction conversion automatically!

---

## Concrete Example: 5x5 Cube, F Rotation

```
    BEFORE F rotation:                 AFTER F rotation:

         TOP edge                           TOP edge
        [A B C]                            [1 2 3]  ← Was LEFT edge
            │                                  │
    LEFT    │    RIGHT                 LEFT    │    RIGHT
    [1]     │    [X]                   [Z]     │    [A]
    [2]     │    [Y]                   [Y]     │    [B]
    [3]     │    [Z]                   [X]     │    [C]
            │                                  │
        [P Q R]                            [3 2 1]  ← Was RIGHT (inverted!)
        BOTTOM edge                        BOTTOM edge

    LEFT → TOP:     [1,2,3] → [1,2,3]  (same direction, no inversion)
    TOP → RIGHT:    [A,B,C] → [A,B,C]  (same direction, placed at inverted positions)
    RIGHT → BOTTOM: [X,Y,Z] → [Z,Y,X]  (indices inverted for display order)
    BOTTOM → LEFT:  [P,Q,R] → [R,Q,P]  (reversed back)
```

---

## Why This Matters

Without `right_top_left_same_direction`:
1. ❌ Slice copying would use wrong indices
2. ❌ Colors would end up in wrong positions
3. ❌ Cube would become corrupted after rotations

With `right_top_left_same_direction`:
1. ✅ Each edge knows how its two faces relate
2. ✅ Index conversion is automatic and correct
3. ✅ Rotations work perfectly for any NxN cube

---

## Code References

| Location | Purpose |
|----------|---------|
| [`Cube.py`](../src/cube/domain/model/Cube.py) | `_create_edge()` function with flag parameter |
| [`Cube.py`](../src/cube/domain/model/Cube.py) | All 12 edge creations with True/False values |
| [`Edge.py:127-160`](../src/cube/domain/model/Edge.py) | `get_ltr_index_from_slice_index()` - uses the flag |
| [`Edge.py:162-193`](../src/cube/domain/model/Edge.py) | `get_slice_index_from_ltr_index()` - inverse conversion |
| [`Face.py`](../src/cube/domain/model/Face.py) | `rotate()` - uses index conversion for slice copying |

---

*Document created: 2025-12-06*
*This was identified as "the most complicated thing to understand" by the developer*
