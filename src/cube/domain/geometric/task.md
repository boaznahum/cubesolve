# Cube Geometry Analysis - Task Document

**Related:** Issue #55 - Replace hard-coded lookup tables with mathematical derivation

## Executive Summary

This document analyzes all geometric decisions in the cubesolve codebase,
distinguishing between **HARDCODED** (arbitrary conventions) and **COMPUTED**
(mathematically derivable) facts. The goal is to understand what CAN be
derived mathematically vs what MUST remain as conventions.

---

## 1. THE FUNDAMENTAL QUESTION

Issue #55 asks: Can we replace empirically-derived lookup tables with
mathematically-computed values?

**Key Insight from Issue #55:**
> "L, F, R, U, D faces all have aligned coordinate systems (they agree)"
> while "B face has a 180-degree rotated coordinate system."

This suggests a **fundamental asymmetry** in the cube's geometry that
may explain many of the lookup tables.

---

## 2. CLASSIFICATION FRAMEWORK

### HARDCODED (Arbitrary Convention)
- Could have been defined differently
- No mathematical reason for this specific choice
- Examples: color scheme, naming conventions, reference directions

### COMPUTED (Derivable)
- Follows logically from other facts
- Can be calculated mathematically
- Examples: opposite faces, adjacent faces, traversal paths

### UNKNOWN
- Not yet analyzed
- May be either hardcoded or computed

---

## 3. INVENTORY OF GEOMETRIC DECISIONS

### 3.1 Face Relationships

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| Opposite face pairs (F-B, U-D, L-R) | HARDCODED | cube_layout.py:36 | Fundamental cube topology |
| Adjacent faces | COMPUTED | cube_layout.py:46 | Derived: all except self and opposite |

### 3.2 Color Scheme (BOY Layout)

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| F=Blue, R=Red, U=Yellow, L=Orange, D=White, B=Green | HARDCODED | cube_boy.py:106 | Western standard convention |
| Opposite colors (Blue-Green, etc.) | COMPUTED | - | Follows from face opposites + color mapping |

### 3.3 Slice Definitions

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| M/E/S slice names | HARDCODED | SliceName.py | Convention from speedcubing |
| M axis = L-R | HARDCODED | - | "M rotates like L" convention |
| E axis = U-D | HARDCODED | - | "E rotates like D" convention |
| S axis = F-B | HARDCODED | - | "S rotates like F" convention |
| M reference face = L | HARDCODED | Face2FaceTranslator | Could have been R |
| E reference face = D | HARDCODED | Face2FaceTranslator | Could have been U |
| S reference face = F | HARDCODED | Face2FaceTranslator | Could have been B |

### 3.4 Rotation Cycles

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| X cycle: D-F-U-B | **COMPUTED** | `get_face_neighbors_cw_names()` | Derived from AXIS_FACE + adjacency |
| Y cycle: R-F-L-B | **COMPUTED** | `get_face_neighbors_cw_names()` | Derived from AXIS_FACE + adjacency |
| Z cycle: L-U-R-D | **COMPUTED** | `get_face_neighbors_cw_names()` | Derived from AXIS_FACE + adjacency |
| Clockwise direction | HARDCODED | - | Viewer-facing convention |

### 3.5 Coordinate Systems

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| LTR (left-to-right, top-to-bottom) | HARDCODED | Face.py | Viewer perspective |
| Row 0 = top, Col 0 = left | HARDCODED | Face.py | Screen coordinate convention |
| B face 180 rotated | COMPUTED? | Issue #55 | Follows from LTR + cube topology |

### 3.6 Transformation Tables

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| 30 face-pair transformations | **REMOVED** | ~~Face2FaceTranslator~~ | Was dead code, transforms computed dynamically |
| 12 slice-index formulas | **COMPUTED** | `_derive_slice_index_formula()` | Derived from `does_slice_cut_rows_or_columns()` + `does_slice_of_face_start_with_face()` |

---

## 4. COMPREHENSIVE CODE INVENTORY

### 4.1 All Geometry Questions Found in Comments

| Location | Question/Comment |
|----------|-----------------|
| `Face2FaceTranslator.py` | Various coordinate translation comments |
| `Face.py:305-306` | `# TODO [#10]: Unclear why these copies are needed` |
| `docs/design2/my_questions.md` | Various rendering/texture questions |

*Note: `CubeLayout/SizedCubeLayout.py` no longer exists — methods moved to `_CubeLayout.py` and `_SizedCubeLayout.py`.*

### 4.2 Issue References in Code

| Issue | Location | Description |
|-------|----------|-------------|
| #10 | `Face.py:305` | Unclear why edge copies needed during rotation |
| #11 | `Slice.py:378-381` | M slice direction inverted vs standard notation |
| #53 | `Face.py:290, Cube.py:412-413` | Edge orientation system not documented |
| #55 | geometry package | Hardcoded geometry methods — most now derived (see HARDCODED_ANALYSIS.md) |

### 4.3 Magic Numbers and Rotation Constants

| File:Line | Constant | Usage |
|-----------|----------|-------|
| `Cube.py:577-578` | `inv(i) = n_slices - 1 - i` | Index inversion helper |
| `Cube.py:63-64` | 90 rotations | Face.rotate(1) = 90 CW |
| `_elements.py:13-15` | D90, D180, D270 | Degree constants |

### 4.4 Coordinate Inversion Patterns (n - 1 - x)

| Location | Context |
|----------|---------|
| `Face2FaceTranslator.py:444` | `inv(x) = n - 1 - x` |
| `Edge.py:371` | `return n - 1 - slices_indexes` |
| `CubeQueries2.py:171, 178, 188, 198` | Rotation formulas using inv() |
| `Slice.py:266, 272` | Center slice access with inv(i) |
| `NxNCenters.py:1212, 1327, 1341` | `# back is mirrored in both direction` |

---

## 5. FACE2FACE TRANSLATOR - CENTRAL GEOMETRY ENGINE

The `Face2FaceTranslator.py` is the central geometry engine for coordinate
translation between cube faces.

### 5.1 Transformation Table — **REMOVED**

Was a 30-entry lookup `_TRANSFORMATION_TABLE`. Removed as dead code —
transforms are now computed dynamically via `CubeWalkingInfo`.

### 5.2 Slice Index Table — **REMOVED** (Now Derived)

Was a 12-entry lookup `_SLICE_INDEX_TABLE`. Now derived dynamically via
`_derive_slice_index_formula()` using:
- `does_slice_cut_rows_or_columns()` → determines ROW vs COL
- `does_slice_of_face_start_with_face()` → determines direct vs inverted

### 5.3 Rotation Cycles — **REMOVED** (Now Derived)

Were hardcoded `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE`. Now derived via
`get_face_neighbors_cw_names()` from `AXIS_FACE` + adjacency topology.

---

## 6. CUBE CONSTRUCTION ORDER

### 6.1 Initialization Sequence

```
IServiceProvider -> BOY Layout (singleton)
                        |
                    Cube.__init__()
                        |
                    _reset()
                        |-- [1] Create 6 Face objects
                        |       |-- Each Face creates its Center
                        |       |-- Faces stored in _faces dict
                        |
                        |-- [2] Set opposite face relationships
                        |
                        |-- [3] Create 12 Edges (with EdgeWing slices)
                        |       |-- Each EdgeWing creates 2 PartEdges
                        |
                        |-- [4] Create 8 Corners (with CornerSlices)
                        |       |-- Each CornerSlice creates 3 PartEdges
                        |
                        |-- [5] Call finish_init() on each Face
                        |
                        |-- [6] Collect centers: _centers list
                        |
                        |-- [7] Create 3 Slices (M, E, S)
                        |       |-- Reference existing Edge/Center objects
                        |
                        |-- [8] Call finish_init() on each Slice
```

### 6.2 Critical Ordering Constraints

1. **Faces must be created before Edges** - Edges reference Face objects
2. **Edges must be created before Corners** - Some algorithms reference them
3. **Edges and Corners must exist before `face.finish_init()`**
4. **Centers are collected after finish_init()** - Line 445 reads from faces
5. **Slices created last** - They reference edges and centers

### 6.3 Part Sharing (Objects Referenced, Not Duplicated)

- **Edges:** Each Edge object is referenced by 2 Face objects
  - Example: `f._edge_top = u._edge_bottom` (same Edge object)
- **Corners:** Each Corner object is referenced by 3 Face objects
  - Example: `f._corner_top_left = l._corner_top_right = u._corner_bottom_left`
- **Centers:** Each Center object is owned by exactly 1 Face

---

## 7. KEY GEOMETRIC INSIGHTS

### 7.1 The B-Face Asymmetry

When viewing the cube from the front:
- F, U, D, L, R faces all have "natural" LTR coordinates
- B face appears "upside down" (180 rotated) when unfolded

This explains many special cases in the code:
```python
# Examples of B-face special handling:
if face_name == FaceName.B:
    return False  # Inverted index

# In slice index derivation:
# M on B face → INV_COL (not COL!) because B is 180° rotated
```

### 7.2 Slice-Face Relationships

Each slice intersects 4 faces and is parallel to 2 faces:
- M: parallel to L,R; intersects F,U,B,D
- E: parallel to U,D; intersects F,R,B,L
- S: parallel to F,B; intersects U,R,D,L

The slice "cuts" rows on some faces and columns on others:
- M: vertical on F,B (columns), but seen as rows from face perspective
- E: horizontal on all 4 faces (rows)
- S: varies by face (R,L = rows; U,D = columns)

### 7.3 Index Alignment

Slice index 0 is closest to the "reference face":
- M[0] closest to L (not R)
- E[0] closest to D (not U)
- S[0] closest to F (not B)

When iterating a slice on a face, indices may or may not align:
- If face is on "same side" as reference: aligned
- If face is on "opposite side": inverted (n-1-i)

### 7.4 Bidirectional Equivalence

All three representations of the same movement are equivalent:

1. **Whole-cube rotation:** X, Y, Z moves
2. **Slice algorithms:** M, E, S moves
3. **Face rotations:** Combinations of L, R, U, D, F, B moves

Example: Moving Right-face content to Front
```
Y'         # Whole-cube: rotate around U-D axis counter-clockwise
E[2]'      # Slice: rotate horizontal slice (for 5x5)
R, U', L', U  # Face algorithms: specific sequence
```

---

## 8. PLACES ASKING GEOMETRY QUESTIONS

### 8.1 In CubeLayout / SizedCubeLayout

| Method | Question Asked | Layer |
|--------|---------------|-------|
| `does_slice_cut_rows_or_columns` | Does slice M/E/S cut rows or columns on face X? | SliceLayout |
| `does_slice_of_face_start_with_face` | Does slice[0] align with face's row/col 0? | SliceLayout |
| `iterate_orthogonal_face_center_pieces` | Which centers on side_face belong to layer slice N? | SizedCubeLayout |

### 8.2 In Face2FaceTranslator

| Method | Question Asked |
|--------|---------------|
| `translate` | Given point on face A, what's the corresponding point on face B? |
| `get_transform_type` | What rotation (0, 90, 180, 270) relates two faces? |
| `_derive_whole_cube_alg` | What whole-cube rotation brings source face to target position? |
| `_compute_slice_index` | What slice index corresponds to this (row, col) coordinate? |
| `_compute_slice_algorithms` | What slice algorithm is equivalent to this whole-cube move? |

### 8.3 Known Bugs Related to Geometry

| Issue | Location | Description |
|-------|----------|-------------|
| #11 | `Slice.py:378-381` | M slice direction inverted vs standard notation |
| 1-based bug | `Face2FaceTranslator.py:270` | Slice index table uses 1-based internally |
| #10 | `Face.py:305` | Edge copies needed during rotation - unclear why |

---

## 9. WHAT CAN BE DERIVED MATHEMATICALLY?

### 9.1 Definitely Derivable

1. **Adjacent faces** from opposite faces
2. **Opposite colors** from face colors + opposite faces
3. **Slice traversal paths** from slice axis definitions
4. **Transformation types** from whole-cube rotation sequences
5. **2D coordinate transformations** from standard rotation matrices

### 9.2 Now Derived (Previously Listed as "Potentially Derivable")

1. **Slice index formulas** — **DONE**: Derived via `_derive_slice_index_formula()` from
   `does_slice_cut_rows_or_columns()` and `does_slice_of_face_start_with_face()`

2. **B-face rotation** — Confirmed as consequence of LTR coordinate convention + cube topology

### 9.3 Cannot Be Derived (Must Be Hardcoded)

1. **Color scheme** - arbitrary assignment
2. **Slice naming** (M/E/S) - speedcubing convention
3. **Reference face choice** (M->L, E->D, S->F) - arbitrary
4. **Rotation direction** - clockwise/counterclockwise convention
5. **Coordinate origin** - (0,0) at top-left vs bottom-left

---

## 10. PROPOSED ARCHITECTURE

### 10.1 Layer 0: Fundamental Constants (HARDCODED)

```python
# These MUST be hardcoded - no way to derive them
FACE_NAMES = [F, R, U, L, D, B]
OPPOSITE_PAIRS = [(F,B), (U,D), (L,R)]
SLICE_REFERENCE = {M: L, E: D, S: F}
ROTATION_POSITIVE = "clockwise when facing the reference face"
COORD_ORIGIN = "top-left of face when viewed from outside"
```

### 10.2 Layer 1: Derived Topology (COMPUTED)

```python
# These can be computed from Layer 0
def adjacent_faces(face): ...
def slice_axis(slice): ...  # M -> L-R axis, etc.
def rotation_cycle(axis): ...  # X -> [D,F,U,B]
```

### 10.3 Layer 2: Coordinate Transformations (COMPUTED)

```python
# These can be computed from Layer 1
def transform_type(source, target): ...  # IDENTITY, ROT_90_CW, etc.
def slice_formula(slice, face): ...  # ROW, COL, INV_ROW, INV_COL
```

### 10.4 Layer 3: High-Level Queries (COMPUTED)

```python
# These use Layer 2
def translate_point(source, target, point): ...
def iterate_slice_on_face(slice, face, index): ...
```

---

## 11. SUMMARY TABLE

| Component | Status | Notes |
|-----------|--------|-------|
| **_TRANSFORMATION_TABLE** | **REMOVED** | Was dead code |
| **_SLICE_INDEX_TABLE** | **REMOVED** | Now derived via `_derive_slice_index_formula()` |
| **Rotation Cycles** | **REMOVED** | Now derived via `get_face_neighbors_cw_names()` |
| **_apply_transform()** | Formulas (4 types) | From 2D rotation |
| **_derive_whole_cube_alg()** | Computed | From derived cycles |
| **_compute_slice_index()** | Computed | From derived formula |
| **does_slice_cut_rows_or_columns** | Computed | In SliceLayout |
| **does_slice_of_face_start_with_face** | Computed | In SliceLayout |

---

## 12. NEXT STEPS

### 12.1 Immediate Tasks

1. [x] Complete inventory of all hardcoded tables
2. [x] Document the mathematical relationship between tables
3. [x] Prototype derivation of transformation table (CubeWalkingInfo.get_transform())
4. [x] Verify B-face asymmetry hypothesis (test_cube_walking.py proves it)

### 12.2 Future Work (Issue #55)

1. [x] Implement Layer 0 constants module — `geometry_fundamentals.py`
2. [x] Implement Layer 1 derived topology — `CubeLayout`, `SliceLayout`
3. [x] Implement Layer 2 coordinate math — `SizedCubeLayout`, `_derive_slice_index_formula()`
4. [x] Replace lookup tables with computed values — `_TRANSFORMATION_TABLE`, `_SLICE_INDEX_TABLE`, `_X/Y/Z_CYCLE` all removed
5. [x] Add comprehensive tests — `test_slice_index_derivation.py` and others
6. [ ] Remove hardcoded face-to-slice mapping in mouse handlers (`main_g_mouse.py`, `ClientSession.py`)
7. [ ] Replace `_supported_faces.py` table with derived computation

---

## 13. APPENDIX: FILE LOCATIONS

| File | Contains |
|------|----------|
| `geometry_fundamentals.py` | Axioms: `SLICE_ROTATION_FACE`, `AXIS_FACE` |
| `cube_layout.py` | CubeLayout protocol, opposite/adjacent |
| `_CubeLayout.py` | CubeLayout implementation (includes former `CubeLayout/SizedCubeLayout`) |
| `sized_cube_layout.py` | SizedCubeLayout protocol (size-dependent) |
| `_SizedCubeLayout.py` | SizedCubeLayout implementation |
| `cube_boy.py` | BOY color scheme |
| `slice_layout.py` | SliceLayout protocol + implementation |
| `Face2FaceTranslator.py` | Coordinate translation |
| `FaceName.py` | Face enum |
| `_part.py` | Edge/Corner definitions |
| `HARDCODED_ANALYSIS.md` | Tracking of hardcoded items |
| `GEOMETRY_LAYERS.md` | Two-layer architecture |
| `GEOMETRY.md` | Questions and solutions framework |

---

*Document created: Analysis complete*
*Last updated: 2026-03-15 — removed references to deleted files/tables*

