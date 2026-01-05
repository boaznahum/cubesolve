# Session Notes: Face2FaceTranslator & Coordinate Translation

This document captures all work done on branch `claude/create-transforms-8ecXU`.

## Overview

The goal was to implement geometric coordinate translation between cube faces
using pure geometric analysis (like Slice.py) instead of prebuilt lookup tables.

---

## 1. FRotation Singleton Fix

**File**: `FRotation.py`

Changed `FRotation.unit` property to return singleton constants instead of
creating new instances:

```python
@property
def unit(self) -> FUnitRotation:
    """The unit rotation (size-independent), returns singleton constant."""
    return _UNIT_ROTATIONS[self.n_rotation % 4]


_UNIT_ROTATIONS: tuple[FUnitRotation, ...] = (
    FUnitRotation.CW0,
    FUnitRotation.CW1,
    FUnitRotation.CW2,
    FUnitRotation.CW3,
)
```

---

## 2. Face2FaceTranslator Moved to geometric Package

**Location**: `src/cube/domain/model/geometric/Face2FaceTranslator.py`

Moved from `src/cube/domain/model/Face2FaceTranslator.py`.

**Note**: NOT exported from `geometric/__init__.py` to avoid circular imports.
Import directly:
```python
from cube.domain.model.geometric.Face2FaceTranslator import Face2FaceTranslator
```

---

## 3. translate_target_from_source with Slice Geometry

### The Problem

The original implementation used a loop to translate coordinates through
intermediate faces, but it didn't correctly handle **axis exchange** when
edge type changes (horizontal ↔ vertical).

### The Solution: Composition Design

Split coordinate translation into two functions:

1. **`_translate_adjacent`**: Handles ONE edge crossing between adjacent faces
2. **`_translate_via_slice_geometry`**: Composes adjacent transforms

For opposite faces (2 steps apart in cycle):
```
F → B = adjacent(F → intermediate) × adjacent(intermediate → B)
```

### Key Concepts

#### Two Coordinates to Track

When a slice crosses a face, each point has two components:

1. **current_index**: WHICH slice (0, 1, 2, ...)
   - Translates through edges using `get_slice_index_from_ltr_index()` and
     `get_ltr_index_from_slice_index()`

2. **slot_along**: WHERE on the slice (position 0, 1, 2, ...)
   - Physical position along the slice strip
   - PRESERVED across faces (slot 0 stays slot 0)
   - But mapping to (row, col) depends on edge type

#### Slot Ordering (from Slice._get_slices_by_index)

```
HORIZONTAL EDGES (top/bottom):
┌─────────────────────────────┬─────────────────────────────┐
│  Bottom edge:               │   Top edge:                 │
│  slot 0 → (row=0, col=idx)  │   slot 0 → (row=n-1, col=idx)
│  slot 1 → (row=1, col=idx)  │   slot 1 → (row=n-2, col=idx)
│                             │                             │
│  current_index = col        │   current_index = col       │
│  slot = row                 │   slot = inv(row)           │
└─────────────────────────────┴─────────────────────────────┘

VERTICAL EDGES (left/right):
┌─────────────────────────────┬─────────────────────────────┐
│  Left edge:                 │   Right edge:               │
│  slot 0 → (row=idx, col=0)  │   slot 0 → (row=idx, col=n-1)
│  slot 1 → (row=idx, col=1)  │   slot 1 → (row=idx, col=n-2)
│                             │                             │
│  current_index = row        │   current_index = row       │
│  slot = col                 │   slot = inv(col)           │
└─────────────────────────────┴─────────────────────────────┘
```

#### Axis Exchange

When edge type changes (horizontal ↔ vertical), the coordinate axes swap:

```
Example: S slice traversal U(edge_left) → R(edge_top)

On U (vertical edge):          On R (horizontal edge):
┌─────────────────┐            ┌─────────────────┐
│ ↓               │            │  ←←←←←←←←←←←←←  │
│ │  current_index│            │  current_index  │
│ │  = row        │            │  = col          │
│ ↓               │            │                 │
│ slot = col      │            │  slot = inv(row)│
│ (left-to-right) │            │  (top-to-bottom)│
└─────────────────┘            └─────────────────┘
```

### Slice Cycles

Built by `_build_slice_cycle()`:

```
M: F(edge_bottom) → U → B → D
E: R(edge_left) → B → L → F
S: U(edge_left) → R → D → L
```

---

## 4. get_slices_between_faces Method

**Added to**: `CubeLayout` protocol and `_CubeLayout` implementation

Returns the slice(s) that connect two faces:
- Adjacent faces: returns 1 slice
- Opposite faces: returns 2 slices

```python
def get_slices_between_faces(
        self,
        source_face: "Face",
        target_face: "Face",
) -> list[SliceName]:
    """
    TODO: This is a patch implementation using translate_source_from_target.
          Consider deriving this directly from slice geometry.
    """
```

---

## 5. TestSliceMovementPrediction (WIP)

**File**: `tests/model/test_face2face_translator.py`

**Status**: 12 pass, 18 fail

### Test Design

For each (source, target) face pair:
1. Put unique marker on each center piece of source face
2. Get slice algorithm from `translate_source_from_target` (includes direction)
3. Predict target positions using `translate_target_from_source`
4. Apply `whole_slice_alg`
5. Verify markers appear at predicted positions on target_face

### Current Issue

18 tests failing. The predictions from `translate_target_from_source` don't
match where pieces actually end up after applying the slice algorithm.

Possible causes to investigate:
1. `translate_target_from_source` returning wrong predictions
2. Mismatch between slice direction in algorithm vs prediction
3. The `whole_slice_alg` behavior

### Test Convention

Face pairs are `(target, source)`. Test ID `F<-U` means target=F, source=U.

```python
# Correct unpacking:
target_name, source_name = face_pair
```

---

## 6. LTR Coordinate System

Each face uses LTR (Left-to-Right) coordinates:
- (0, 0) at bottom-left when viewing face from outside
- row increases upward, col increases rightward

```
        col: 0   1   2
           ┌───┬───┬───┐
    row 2  │   │   │   │
           ├───┼───┼───┤
    row 1  │   │   │   │
           ├───┼───┼───┤
    row 0  │   │   │   │
           └───┴───┴───┘
```

See: `docs/face-coordinate-system/edge-face-coordinate-system.md`

---

## 7. Edge Translation Functions

```python
# Face LTR → Edge internal index
edge.get_slice_index_from_ltr_index(face, ltr_i)

# Edge internal index → Face LTR
edge.get_ltr_index_from_slice_index(face, slice_i)
```

The `same_direction` flag determines if f2 sees inverted indices.

---

## 8. Commits on Branch

```
1da50b9 Add TestSliceMovementPrediction test class (WIP - 18 tests failing)
b304444 Add get_slices_between_faces method to CubeLayout
e1f5780 Refactor translate_via_slice_geometry with composition design
1df124a Document _translate_via_slice_geometry with detailed diagrams
12cd178 Move Face2FaceTranslator to geometric package
d523c98 Require slice_name parameter in translate_target_from_source
97ca7f7 Use Slice traversal logic for translate_target_from_source
e60191f Return singleton constants from FRotation.unit property
```

---

## 9. Key Files Modified

1. `src/cube/domain/model/FRotation.py` - Singleton unit rotations
2. `src/cube/domain/model/geometric/Face2FaceTranslator.py` - Main translator
3. `src/cube/domain/model/geometric/cube_layout.py` - Protocol with new method
4. `src/cube/domain/model/geometric/_CubeLayout.py` - Implementation
5. `src/cube/domain/model/geometric/__init__.py` - Updated exports note
6. `tests/model/test_face2face_translator.py` - Tests including WIP

---

## 10. Next Steps

1. **Debug failing tests**: Investigate why `translate_target_from_source`
   predictions don't match actual piece movement

2. **Verify slice direction**: Ensure the algorithm direction matches what
   `translate_target_from_source` expects

3. **Consider**: The test applies `whole_slice_alg` once, but
   `translate_target_from_source` may assume multiple rotations for opposite faces

4. **Issue #55**: Continue reducing assumptions by using geometric derivation
   instead of prebuilt tables

---

## 11. Related Documentation

- `docs/face-coordinate-system/edge-face-coordinate-system.md`
- `docs/face-coordinate-system/Face2FaceTranslator.md`
- `docs/face-coordinate-system/face-slice-rotation.md`
- `src/cube/domain/model/Slice.py` (single source of truth for slice geometry)
