# Cube Layout Geometry - Questions and Solutions

This document tracks geometric questions that arise during cube solving
and the methods needed to answer them.

**Related:** Issue #55 - Replace hard-coded lookup tables with mathematical derivation

## How to Use This Document

When you encounter a geometric question:

1. **Document the question** - What do you want to know?
2. **Define the method signature** - What are the inputs and outputs?
3. **Classify the answer:**
   - `HARDCODED` - Arbitrary decision, cannot be derived
   - `COMPUTED` - Can be derived from other facts
   - `UNKNOWN` - Not yet analyzed
4. **If COMPUTED** - Document what it's derived from
5. **Implement** - Add to `_CubeLayoutGeometry.py` (private), expose via protocol

### Classification Guidelines

| Type | Description | Example |
|------|-------------|---------|
| `HARDCODED` | Convention choice, could have been different | "White face starts on DOWN" |
| `COMPUTED` | Follows logically from other facts | "M slice affects F,U,B,D faces" |
| `UNKNOWN` | Needs investigation | "Does slice[1] align with row 0?" |

---

## Question 1: Which centers belong to a given slice relative to Layer 1?

### Context

When solving a cube layer-by-layer (LBL), after Layer 1 is done, we solve
the remaining "slices" (horizontal layers) from bottom to top.

Each slice consists of:
- One row/column of centers on each of the 4 side faces
- Edge wings connecting them

### The Problem

Layer 1 can be on ANY face (not just DOWN). The "slices" are the layers
parallel to Layer 1, indexed from 0 (closest to L1) to n_slices-1 (closest to opposite).

**Given:**
- Layer 1 face (e.g., DOWN, UP, LEFT, RIGHT, FRONT, BACK)
- A slice index (e.g., 0, 1, 2, ...)
- A side face (one of the 4 faces perpendicular to L1)

**What we want to know:**
- Which center positions (row, col) on that side face belong to this slice?

### Sub-questions to Answer

1. **Which 4 faces are the "side faces"?**
   - The 4 faces perpendicular to Layer 1
   - Excludes: Layer 1 face and its opposite

2. **Is the slice a "row" or "column" on each side face?**
   - Depends on the relationship between L1 and the side face
   - Example: If L1=DOWN, on FRONT face the slices are horizontal rows
   - Example: If L1=LEFT, on FRONT face the slices are vertical columns

3. **Which row/column index corresponds to slice index N?**
   - Slice 0 should be closest to Layer 1
   - But face coordinate systems vary (some count up, some count down)
   - Need to know: does row 0 touch L1, or does row (n-1) touch L1?

### What I Think I Need

```python
def get_slice_centers_on_face(
    layer1_face: FaceName,
    side_face: FaceName,
    slice_index: int,
    n_slices: int
) -> list[tuple[int, int]]:
    """
    Return the (row, col) positions of centers on side_face that belong to slice_index.

    Args:
        layer1_face: The face where Layer 1 is located
        side_face: One of the 4 faces perpendicular to layer1_face
        slice_index: 0 = closest to L1, n_slices-1 = farthest
        n_slices: Total number of slices (cube_size - 2)

    Returns:
        List of (row, col) tuples in LTR coordinates for the side face
    """
```

### Alternative: Decompose Into Smaller Questions

Maybe instead of one big method, we need:

```python
def get_side_faces(layer1_face: FaceName) -> list[FaceName]:
    """Return the 4 side faces (perpendicular to L1)."""

def does_slice_affect_rows_or_cols(layer1_face: FaceName, side_face: FaceName) -> Literal["row", "col"]:
    """Does the slice cut through rows or columns on this side face?"""

def get_row_or_col_for_slice(layer1_face: FaceName, side_face: FaceName, slice_index: int, n_slices: int) -> int:
    """Which row/column index on side_face corresponds to slice_index?"""
```

---

## Refined Understanding

### The Real Question

Actually, `Slice._get_slices_by_index(slice_index)` already returns exactly which
centers belong to a given slice! It returns `(edges, centers)` for any slice index.

The problem is:
- `Slice` objects are M, E, or S (fixed axis)
- Layer 1 can be on any face
- "Slice 0 relative to L1" is NOT the same as "M[0]" or "E[0]"

**What I really want to know:**

Given Layer 1 is on face X, and I want "slice index N relative to L1":
1. Which physical slice type (M, E, or S) is parallel to L1?
2. What is the physical slice index? (accounting for direction)

### Final Method Signature

**Classification: `COMPUTED`** - Derived from BOY reference layout

```python
@staticmethod
def iterate_orthogonal_face_center_pieces(
    cube: "Cube",
    layer1_face: Face,
    side_face: Face,           # must be orthogonal to layer1_face
    layer_slice_index: int,    # 0 = closest to L1
) -> Iterator[tuple[int, int]]:
    """
    Yield (row, col) positions on side_face for the given layer slice.

    Args:
        cube: The cube (for n_slices and geometry reference)
        layer1_face: The Layer 1 face (base layer, e.g., white face)
        side_face: A face orthogonal to layer1_face
        layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

    Yields:
        (row, col) in LTR coordinates on side_face
        Order is unspecified (may be LTR in future)

    Raises:
        ValueError: if side_face is not orthogonal to layer1_face

    Example:
        L1=DOWN, side_face=FRONT, layer_slice_index=0, n_slices=3
        → Yields positions for bottom row on FRONT: (0,0), (0,1), (0,2)

        L1=LEFT, side_face=FRONT, layer_slice_index=0, n_slices=3
        → Yields positions for left column on FRONT: (0,0), (1,0), (2,0)
    """
```

**Usage:**
```python
for row, col in cube.layout.iterate_orthogonal_face_center_pieces(
    cube, layer1_face, front_face, layer_slice_index=0
):
    center = front_face.center.get_center_slice((row, col))
    if center.color != expected_color:
        return False
```

### How to Derive This

**Sub-question 1.1: Which slice is parallel to L1?**

Classification: `COMPUTED` - derived from slice axis definitions

| L1 Face | Parallel Slice | Why |
|---------|---------------|-----|
| U or D | E | E axis is U-D |
| L or R | M | M axis is L-R |
| F or B | S | S axis is F-B |

**Sub-question 1.2: Is L1 on the reference face or opposite?**

Classification: `HARDCODED` - the reference face for each slice is a convention

| Slice | Reference Face | Source |
|-------|---------------|--------|
| M | L | Slice.py docs: "M rotates like L" |
| E | D | Slice.py docs: "E rotates like D" |
| S | F | Slice.py docs: "S rotates like F" |

**Sub-question 1.3: Index direction conversion**

Classification: `COMPUTED` - follows from 1.1 and 1.2

```
If L1 == reference_face:
    physical_index = layer_slice_index
Else:  # L1 == opposite of reference
    physical_index = n_slices - 1 - layer_slice_index
```

---

## Architecture

The geometry methods are organized as follows:

- **Private implementation:** `_CubeLayoutGeometry` (in `_CubeLayoutGeometry.py`)
- **Public API via protocols:**
  - `SliceLayout` protocol: slice-related methods (`does_slice_cut_rows_or_columns`, `does_slice_of_face_start_with_face`)
  - `CubeLayout` protocol: face relationship methods (`iterate_orthogonal_face_center_pieces`)

## Methods in SliceLayout Protocol

### `slice_layout.does_slice_cut_rows_or_columns(face_name)`

Returns whether this slice cuts through rows or columns on a given face.

- M slice: always cuts rows (vertical slice)
- E slice: always cuts columns (horizontal slice)
- S slice: depends on face (R/L = rows, others = columns)

**Usage:**
```python
slice_layout = cube.layout.get_slice(SliceName.M)
if slice_layout.does_slice_cut_rows_or_columns(FaceName.F) == CLGColRow.ROW:
    ...
```

### `slice_layout.does_slice_of_face_start_with_face(face_name)`

Returns whether slice[0] starts at the "natural" beginning of the face coordinate.

Used to determine if slice indices go in same direction as face coordinates.

## Methods in CubeLayout Protocol

### `layout.iterate_orthogonal_face_center_pieces(cube, layer1_face, side_face, layer_slice_index)`

Yields (row, col) positions on side_face for the given layer slice.

