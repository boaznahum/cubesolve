# Hardcoded Values Analysis - Issue #55

This document analyzes all hardcoded values related to face names, axis names, slice names, and geometric logic in the codebase. The goal is to identify candidates for refactoring to derive values mathematically instead of using hardcoded tables.

## Overview

The codebase has multiple hardcoded lookup tables and conditional logic based on specific face/slice names. These are scattered across several files, primarily in:

1. `src/cube/domain/geometric/` - Core geometry implementations
2. `src/cube/domain/model/` - Domain model classes
3. `src/cube/domain/solver/` - Solver algorithms

---

## Category 1: Face-to-Face Transformation Tables

### 1.1 `_TRANSFORMATION_TABLE` in `Face2FaceTranslator.py` (lines 164-206)

**Location:** `src/cube/domain/geometric/Face2FaceTranslator.py:164-206`

**Type:** Hardcoded 30-entry dict mapping `(source_face, target_face) -> TransformType`

```python
_TRANSFORMATION_TABLE: dict[tuple[FaceName, FaceName], TransformType] = {
    # B face transitions
    (FaceName.B, FaceName.D): TransformType.ROT_180,
    (FaceName.B, FaceName.F): TransformType.ROT_180,
    (FaceName.B, FaceName.L): TransformType.IDENTITY,
    # ... 25 more entries
}
```

**Purpose:** Maps how coordinates transform when moving content between faces via whole-cube rotation.

**Source:** Empirically derived by `tests/model/test_empirical_transforms.py`

**Could be derived from:**
- Slice traversal geometry
- Rotation cycle analysis (X, Y, Z cycles)

---

### 1.2 `_SLICE_INDEX_TABLE` in `Face2FaceTranslator.py` (lines 336-354)

**Location:** `src/cube/domain/geometric/Face2FaceTranslator.py:336-354`

**Type:** Hardcoded 12-entry dict mapping `(SliceName, FaceName) -> SliceIndexFormula`

```python
_SLICE_INDEX_TABLE: dict[tuple[SliceName, FaceName], str] = {
    # M slice (affects F, U, D, B)
    (SliceName.M, FaceName.F): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.U): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.D): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.B): _SliceIndexFormula.INV_COL,
    # E slice (affects F, L, R, B)
    (SliceName.E, FaceName.F): _SliceIndexFormula.ROW,
    # ... 8 more entries
}
```

**Purpose:** Determines how to compute slice index from (row, col) coordinates on each face.

**Source:** Empirically derived by `tests/model/derive_slice_index_table.py`

**Could be derived from:**
- Edge orientation on each face
- Slice geometry (does_slice_cut_rows_or_columns + does_slice_of_face_start_with_face)

---

### 1.3 Rotation Cycles in `Face2FaceTranslator.py` (lines 421-423)

**Location:** `src/cube/domain/geometric/Face2FaceTranslator.py:421-423`

**Type:** Hardcoded lists defining face order during rotation

```python
_X_CYCLE: list[FaceName] = [FaceName.D, FaceName.F, FaceName.U, FaceName.B]
_Y_CYCLE: list[FaceName] = [FaceName.R, FaceName.F, FaceName.L, FaceName.B]
_Z_CYCLE: list[FaceName] = [FaceName.L, FaceName.U, FaceName.R, FaceName.D]
```

**Purpose:** Defines content flow direction during X, Y, Z whole-cube rotations.

**Could be derived from:**
- Slice traversal starting from each axis face
- The relationship between slice rotation face and whole-cube rotation face

---

## Category 2: Slice-to-Face Geometry Tables

### 2.1 `does_slice_cut_rows_or_columns` in `_CubeLayoutGeometry.py` (lines 40-64)

**Location:** `src/cube/domain/geometric/_CubeLayoutGeometry.py:40-64`

**Type:** Hardcoded conditional logic

```python
if slice_name == SliceName.M:
    return CLGColRow.ROW  # M always cuts rows (forms vertical strips)

elif slice_name == SliceName.E:
    return CLGColRow.COL  # E always cuts columns (forms horizontal strips)

elif slice_name == SliceName.S:
    if face_name in [FaceName.R, FaceName.L]:
        return CLGColRow.ROW
    else:
        return CLGColRow.COL
```

**Purpose:** Determines whether a slice cuts rows or columns on a given face.

**Note:** S slice has special handling because it affects L/R differently than U/D.

**Could be derived from:**
- The axis of each slice (M=L-R axis, E=U-D axis, S=F-B axis)
- Face orientation relative to the slice axis

---

### 2.2 `does_slice_of_face_start_with_face` in `_CubeLayoutGeometry.py` (lines 66-133)

**Location:** `src/cube/domain/geometric/_CubeLayoutGeometry.py:66-133`

**Type:** Hardcoded conditional logic

```python
if slice_name == SliceName.S:
    if face_name in [FaceName.L, FaceName.D]:
        return False  # S[1] is on L[last]

elif slice_name == SliceName.M:
    if face_name in [FaceName.B]:
        return False

return True
```

**Purpose:** Determines if slice index 0 aligns with face's coordinate origin or is inverted.

**Could be derived from:**
- The relationship between slice reference face and the face in question
- Edge shared between the face and the slice's reference face

---

### 2.3 `iterate_orthogonal_face_center_pieces` in `_CubeLayoutGeometry.py` (lines 231-247)

**Location:** `src/cube/domain/geometric/_CubeLayoutGeometry.py:231-247`

**Type:** Hardcoded face-to-slice mapping

```python
if l1_name in [FaceName.U, FaceName.D]:
    slice_name = SliceName.E
    reference_face = FaceName.D
elif l1_name in [FaceName.L, FaceName.R]:
    slice_name = SliceName.M
    reference_face = FaceName.L
else:  # F or B
    slice_name = SliceName.S
    reference_face = FaceName.F
```

**Purpose:** Maps layer1 face to the parallel slice type and its reference face.

**Could be derived from:**
- Slice definitions (M parallel to L-R, E parallel to U-D, S parallel to F-B)

---

## Category 3: Slice Definition Tables

### 3.1 `get_face_name()` in `slice_layout.py` (lines 144-156)

**Location:** `src/cube/domain/geometric/slice_layout.py:144-156`

**Type:** Hardcoded mapping

```python
match self._slice_name:
    case SliceName.S:  # over F
        return FaceName.F
    case SliceName.M:  # over L
        return FaceName.L
    case SliceName.E:  # over D
        return FaceName.D
```

**Purpose:** Returns the face that defines the positive rotation direction for each slice.

**Note:** This is a fundamental definition - M rotates like L, E rotates like D, S rotates like F.

---

### 3.2 `_build_slice_cycle` in `Face2FaceTranslator.py` (lines 774-799)

**Location:** `src/cube/domain/geometric/Face2FaceTranslator.py:774-799`

**Type:** Hardcoded starting face/edge for each slice

```python
match slice_name:
    case SliceName.M:
        start_face = cube.front
        start_edge = start_face.edge_bottom
    case SliceName.E:
        start_face = cube.right
        start_edge = start_face.edge_left
    case SliceName.S:
        start_face = cube.up
        start_edge = start_face.edge_left
```

**Purpose:** Defines the starting point for building slice traversal cycles.

**Could be derived from:**
- Slice rotation face via `get_face_name()`
- Clockwise edge order around the rotation face

---

## Category 4: Face Property Checks

### 4.1 Face property checks in `Face.py` (lines 611-647)

**Location:** `src/cube/domain/model/Face.py:611-647`

**Type:** Hardcoded boolean properties

```python
@property
def is_front(self):
    return self.name is FaceName.F

@property
def is_back(self):
    return self.name is FaceName.B

@property
def is_down(self):
    return self.name is FaceName.D
# ... etc
```

**Purpose:** Quick checks for face identity.

**Note:** These are convenience properties, unlikely candidates for derivation.

---

## Category 5: Layout Geometry Tables

### 5.1 `_OPPOSITE` in `cube_layout.py` (lines 39-43)

**Location:** `src/cube/domain/geometric/cube_layout.py:39-43`

**Type:** Fundamental definition

```python
_OPPOSITE: Mapping[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R
}
```

**Purpose:** Defines which faces are opposite to each other.

**Note:** This is a fundamental geometric property of a cube - cannot be derived further.

---

### 5.2 `_rotate_x`, `_rotate_y`, `_rotate_z` in `_CubeLayout.py` (lines 352-401)

**Location:** `src/cube/domain/geometric/_CubeLayout.py:352-401`

**Type:** Hardcoded face swap sequences

```python
def _rotate_x(self, n: int) -> None:
    for _ in range(n % 4):
        f = faces[FaceName.F]
        faces[FaceName.F] = faces[FaceName.D]
        faces[FaceName.D] = faces[FaceName.B]
        faces[FaceName.B] = faces[FaceName.U]
        faces[FaceName.U] = f
```

**Purpose:** Implements layout rotation for layout comparison.

**Could be derived from:**
- `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` cycles

---

## Category 6: BOY Color Scheme

### 6.1 BOY Layout in `cube_boy.py` (lines 113-120)

**Location:** `src/cube/domain/geometric/cube_boy.py:113-120`

**Type:** Fundamental definition

```python
_boy_layout = create_layout(True, {
    FaceName.F: Color.BLUE,
    FaceName.R: Color.RED,
    FaceName.U: Color.YELLOW,
    FaceName.L: Color.ORANGE,
    FaceName.D: Color.WHITE,
    FaceName.B: Color.GREEN,
}, sp)
```

**Purpose:** Defines the standard Rubik's cube color scheme.

**Note:** This is the reference definition - cannot be derived.

---

## Category 7: Communicator Support Tables

### 7.1 `s2_rotation_table.yaml` loaded in `CommunicatorHelper.py`

**Location:** `src/cube/domain/solver/common/big_cube/commun/CommunicatorHelper.py:100-111`

**Type:** External YAML table

```python
def _load_s2_rotation_table(self) -> dict:
    table_file = Path(__file__).parent / "s2_rotation_table.yaml"
```

**Purpose:** Lookup table for s2 rotation direction per face pair.

**Could be derived from:**
- Slice geometry and intersection analysis

---

### 7.2 `_supported_faces.py`

**Location:** `src/cube/domain/solver/common/big_cube/commun/_supported_faces.py`

**Type:** List of supported face pairs

**Purpose:** Defines which (source, target) pairs the communicator supports.

---

## Summary Table

| ID | File | Line | Type | Derivable? | Priority |
|----|------|------|------|------------|----------|
| 1.1 | Face2FaceTranslator.py | 164-206 | Transformation table | Yes - from slice geometry | High |
| 1.2 | Face2FaceTranslator.py | 336-354 | Slice index formula | Yes - from edge orientation | High |
| 1.3 | Face2FaceTranslator.py | 421-423 | Rotation cycles | Yes - from slice traversal | Medium |
| 2.1 | _CubeLayoutGeometry.py | 40-64 | Slice cut direction | Yes - from slice axis | Medium |
| 2.2 | _CubeLayoutGeometry.py | 66-133 | Slice start alignment | Yes - from edge position | Medium |
| 2.3 | _CubeLayoutGeometry.py | 231-247 | Face-to-slice mapping | Yes - trivial | Low |
| 3.1 | slice_layout.py | 144-156 | Slice rotation face | No - fundamental def | N/A |
| 3.2 | Face2FaceTranslator.py | 774-799 | Slice start face/edge | Yes - from rotation face | Medium |
| 4.1 | Face.py | 611-647 | Face property checks | No - convenience | N/A |
| 5.1 | cube_layout.py | 39-43 | Opposite faces | No - fundamental def | N/A |
| 5.2 | _CubeLayout.py | 352-401 | Layout rotation | Yes - from cycles | Low |
| 6.1 | cube_boy.py | 113-120 | BOY colors | No - fundamental def | N/A |
| 7.1 | CommunicatorHelper.py | 100+ | S2 rotation table | Yes - from geometry | Medium |

---

## Recommended Refactoring Order

### Phase 1: High Priority (Tables that are actively maintained)
1. `_TRANSFORMATION_TABLE` - Derive from slice traversal
2. `_SLICE_INDEX_TABLE` - Derive from edge geometry

### Phase 2: Medium Priority (Logic that could be simplified)
3. `does_slice_cut_rows_or_columns` - Derive from slice axis
4. `does_slice_of_face_start_with_face` - Derive from edge sharing
5. `_build_slice_cycle` - Derive from rotation face
6. Rotation cycles (`_X_CYCLE`, etc.) - Derive from slice traversal

### Phase 3: Low Priority (Working well, low maintenance)
7. `_rotate_x/y/z` - Could use cycles
8. Face-to-slice mapping - Simple to derive

### Not Derivable (Fundamental Definitions)
- `_OPPOSITE` - Cube geometry definition
- `get_face_name()` - Slice definition
- BOY layout - Color scheme definition
- Face property checks - Convenience methods

---

## Key Insight: The Derivation Chain

Most hardcoded values can be derived from a small set of fundamental definitions:

```
Fundamental Definitions (Cannot derive):
├── Opposite faces: F↔B, U↔D, L↔R
├── Slice rotation faces: M→L, E→D, S→F
└── BOY color scheme

Derivable from fundamentals:
├── Rotation cycles (_X_CYCLE, etc.)
│   └── From slice traversal starting at rotation face
├── _TRANSFORMATION_TABLE
│   └── From rotation cycles + coordinate system
├── does_slice_cut_rows_or_columns
│   └── From slice axis vs face orientation
├── does_slice_of_face_start_with_face
│   └── From edge shared with slice reference face
└── _SLICE_INDEX_TABLE
    └── From cut direction + start alignment
```

---

## Files to Modify

1. `src/cube/domain/geometric/Face2FaceTranslator.py`
2. `src/cube/domain/geometric/_CubeLayoutGeometry.py`
3. `src/cube/domain/geometric/slice_layout.py`
4. `src/cube/domain/geometric/_CubeLayout.py`

---

## Notes

- The codebase already has good documentation explaining WHY these values exist
- The test files (`derive_slice_index_table.py`, `test_empirical_transforms.py`) show how values were derived empirically
- Issue #55 goal: Replace empirical derivation with mathematical derivation from fundamentals

---

## Derivation Approach: Detailed Steps

This section documents HOW to derive each hardcoded table from fundamental definitions.

### Step 1: Understanding the Existing Infrastructure

Before deriving new values, we must understand what already exists:

#### 1.1 `CubeWalkingInfo` - Already Computes Transforms!

**Location:** `_CubeLayoutGeometry.create_walking_info()` (lines 380-583)

This method ALREADY derives transforms dynamically by walking through slice cycles. It:
1. Gets the rotation face for a slice (e.g., M → L)
2. Finds edges clockwise around the rotation face
3. Walks through 4 faces, computing reference points
4. Stores `FaceWalkingInfo` with precomputed point functions

**Key insight:** `CubeWalkingInfo.get_transform(source, target)` returns an `FUnitRotation` that transforms coordinates from source to target.

#### 1.2 `FUnitRotation` to `TransformType` Mapping

The `FUnitRotation` class uses clockwise quarter turns:
- `CW0` (n_rotation=0): (r, c) → (r, c)
- `CW1` (n_rotation=1): (r, c) → (inv(c), r)
- `CW2` (n_rotation=2): (r, c) → (inv(r), inv(c))
- `CW3` (n_rotation=3): (r, c) → (c, inv(r))

These map directly to `TransformType`:
```
FUnitRotation.CW0 → TransformType.IDENTITY
FUnitRotation.CW1 → TransformType.ROT_90_CW
FUnitRotation.CW2 → TransformType.ROT_180
FUnitRotation.CW3 → TransformType.ROT_90_CCW
```

#### 1.3 Slice Cycles = Whole-Cube Cycles (Same Faces!)

The slice cycles and whole-cube cycles use the same 4 faces:
- **M slice** affects: F, U, B, D (same as X rotation)
- **E slice** affects: F, R, B, L (same as Y rotation)
- **S slice** affects: U, R, D, L (same as Z rotation)

The only difference is **direction**:
- M rotates like L, X rotates like R (opposite!)
- E rotates like D, Y rotates like U (opposite!)
- S rotates like F, Z rotates like F (same!)

---

### Step 2: Deriving `_TRANSFORMATION_TABLE` (High Priority)

**Goal:** Replace 30-entry hardcoded table with dynamic computation.

**Approach:**

```
For any (source_face, target_face) pair:
1. Find which slice connects them (M, E, or S)
2. Use CubeWalkingInfo to get reference points for both faces
3. Compute FUnitRotation from reference points
4. Map FUnitRotation → TransformType
```

**Detailed Algorithm:**

```python
def derive_transform_type(source: FaceName, target: FaceName, cube: Cube) -> TransformType:
    # Step 1: Find which slice(s) connect source and target
    for slice_name in [SliceName.M, SliceName.E, SliceName.S]:
        walk_info = create_walking_info(cube, slice_name)
        if walk_info.has_face(source_face) and walk_info.has_face(target_face):
            # Step 2: Get transform from walking info
            unit_rotation = walk_info.get_transform(source_face, target_face)

            # Step 3: Map to TransformType
            return unit_rotation_to_transform_type(unit_rotation)

    raise ValueError(f"No slice connects {source} and {target}")

def unit_rotation_to_transform_type(unit: FUnitRotation) -> TransformType:
    mapping = {
        0: TransformType.IDENTITY,
        1: TransformType.ROT_90_CW,
        2: TransformType.ROT_180,
        3: TransformType.ROT_90_CCW,
    }
    return mapping[unit._n_rotation % 4]
```

**Why This Works:**

The coordinate transformation when content moves from face A to face B is the same regardless of whether we use:
- A slice rotation (M, E, S), or
- A whole-cube rotation (X, Y, Z)

Because they move content through the same cycle of faces!

**Implementation Strategy:**

Option A: Generate table at module load time
```python
# Generate _TRANSFORMATION_TABLE dynamically at import
_TRANSFORMATION_TABLE = _generate_transformation_table()
```

Option B: Compute on-demand with caching
```python
def get_transformation(source: FaceName, target: FaceName) -> TransformType:
    return cache.compute((source, target), lambda: derive_transform_type(...))
```

---

### Step 3: Deriving `_SLICE_INDEX_TABLE` (High Priority)

**Goal:** Replace 12-entry hardcoded table with derivation from geometry.

**Current Logic:** For each (SliceName, FaceName), the table says which formula to use:
- ROW: slice_index = row + 1
- COL: slice_index = col + 1
- INV_ROW: slice_index = n_slices - row
- INV_COL: slice_index = n_slices - col

**Derivation Approach:**

The formula depends on two things:
1. **Does the slice cut rows or columns?** → `does_slice_cut_rows_or_columns(slice, face)`
2. **Is slice index aligned or inverted?** → `does_slice_of_face_start_with_face(slice, face)`

```python
def derive_slice_index_formula(slice_name: SliceName, face_name: FaceName) -> str:
    # Step 1: Does slice cut rows or columns?
    cut_type = does_slice_cut_rows_or_columns(slice_name, face_name)

    # Step 2: Is slice index aligned with face coordinates?
    aligned = does_slice_of_face_start_with_face(slice_name, face_name)

    # Step 3: Combine to get formula
    if cut_type == CLGColRow.ROW:  # slice cuts rows → use column
        return _SliceIndexFormula.COL if aligned else _SliceIndexFormula.INV_COL
    else:  # slice cuts columns → use row
        return _SliceIndexFormula.ROW if aligned else _SliceIndexFormula.INV_ROW
```

**Note:** This requires first deriving `does_slice_cut_rows_or_columns` and `does_slice_of_face_start_with_face` from fundamentals.

---

### Step 4: Deriving `does_slice_cut_rows_or_columns` (Medium Priority)

**Goal:** Remove hardcoded conditionals, derive from slice axis.

**Key Insight:** A slice cuts rows or columns based on its axis relative to the face.

Slice axes:
- M: axis between L and R (vertical when viewing F)
- E: axis between U and D (horizontal when viewing F)
- S: axis between F and B (perpendicular to F)

**Derivation Algorithm:**

```python
def derive_slice_cut_type(slice_name: SliceName, face_name: FaceName) -> CLGColRow:
    # Get the two faces that define the slice axis
    slice_axis_faces = get_slice_axis_faces(slice_name)  # e.g., M → (L, R)

    # Get the face's orientation (which edges are horizontal/vertical)
    # A slice cuts ROWS if it's parallel to the face's vertical edges
    # A slice cuts COLS if it's parallel to the face's horizontal edges

    # If face is one of the axis faces, slice doesn't affect it
    if face_name in slice_axis_faces:
        raise ValueError(f"Slice {slice_name} doesn't cut face {face_name}")

    # Determine if slice axis is vertical or horizontal relative to face
    # ... (requires understanding face edge orientations)
```

**Alternative:** Use the slice walking info - the entry edge determines cut direction:
- Horizontal entry edge (top/bottom) → slice cuts columns (ROW)
- Vertical entry edge (left/right) → slice cuts rows (COL)

---

### Step 5: Deriving `does_slice_of_face_start_with_face` (Medium Priority)

**Goal:** Remove hardcoded conditionals, derive from edge relationships.

**Key Insight:** Slice[0] is always closest to the slice's rotation face.

For a given face, slice indices align with face coordinates if:
- The rotation face is on the "low" side of that face's coordinate system

**Derivation Algorithm:**

```python
def derive_slice_alignment(slice_name: SliceName, face_name: FaceName) -> bool:
    # Get the slice's rotation face
    rotation_face = get_slice_rotation_face(slice_name)  # M→L, E→D, S→F

    # Find which edge of face_name is adjacent to rotation_face
    # If that edge is at the coordinate origin (left or bottom), return True
    # If that edge is at the coordinate max (right or top), return False

    # Get the edge shared between face and rotation_face
    shared_edge = face.find_shared_edge(rotation_face)

    # Determine if shared_edge is at origin or max
    if face.is_bottom_edge(shared_edge) or face.is_left_edge(shared_edge):
        return True  # aligned
    else:
        return False  # inverted
```

---

### Step 6: Deriving Rotation Cycles (Medium Priority)

**Goal:** Replace `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` with derivation.

**Key Insight:** The cycle is just the faces around the axis, in rotation order.

```python
def derive_rotation_cycle(axis_face: FaceName) -> list[FaceName]:
    """
    Derive the face cycle for whole-cube rotation around axis_face.

    X rotates around R face: cycle = faces clockwise around R
    Y rotates around U face: cycle = faces clockwise around U
    Z rotates around F face: cycle = faces clockwise around F
    """
    # Get all faces adjacent to axis_face
    adjacent = get_adjacent_faces(axis_face)  # 4 faces

    # Order them clockwise when viewing axis_face from outside
    # This can be done by walking edges clockwise around axis_face

    # Use slice walking info for the corresponding slice
    slice_name = axis_face_to_slice(axis_face)  # R→M', U→E', F→S
    walk_info = create_walking_info(cube, slice_name)

    # Return faces in traversal order (but may need direction adjustment)
    return [info.face.name for info in walk_info]
```

---

### Verification Strategy

For each derivation, we need to verify correctness:

1. **Unit Tests:** Compare derived values against hardcoded tables
2. **Integration Tests:** Run existing tests to ensure behavior unchanged
3. **Gradual Replacement:** Keep hardcoded table as fallback during transition

```python
def test_derived_transformation_table():
    """Verify derived transforms match hardcoded table."""
    for (source, target), expected in _TRANSFORMATION_TABLE.items():
        derived = derive_transform_type(source, target)
        assert derived == expected, f"Mismatch for ({source}, {target})"
```

---

### Implementation Order

Based on dependencies:

1. **First:** `unit_rotation_to_transform_type` mapping (trivial)
2. **Second:** `derive_transform_type` using existing `CubeWalkingInfo`
3. **Third:** Verify with tests, then replace `_TRANSFORMATION_TABLE`
4. **Fourth:** `derive_slice_cut_type` (needed for Step 5)
5. **Fifth:** `derive_slice_alignment` (uses Step 4)
6. **Sixth:** `derive_slice_index_formula` (combines Steps 4+5)
7. **Seventh:** Verify with tests, then replace `_SLICE_INDEX_TABLE`
8. **Last:** Rotation cycles (lowest priority, used elsewhere)

---

### Risk Mitigation

**Risk 1:** Random starting face in `create_walking_info`

The walking info uses `random.randint(0, 3)` to pick starting face. This doesn't affect RELATIVE transforms between faces, but we should verify.

**Risk 2:** Performance regression

Dynamic derivation may be slower than table lookup. Mitigate with caching.

**Risk 3:** Subtle bugs in edge cases

The existing tables were empirically verified. We must ensure derived values match exactly.

---

### Session Notes

**Date:** 2026-01-09
**Branch:** `geometry_cleanup_issue55_no2`
**Status:** Analysis complete, derivation approach documented

**Next Steps:**
1. Review derivation approach with user
2. Start with `_TRANSFORMATION_TABLE` derivation
3. Write verification tests first
4. Implement derivation
5. Run all checks to verify no regressions
