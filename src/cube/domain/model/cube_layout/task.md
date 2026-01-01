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
| Opposite face pairs (F↔B, U↔D, L↔R) | HARDCODED | cube_layout.py:36 | Fundamental cube topology |
| Adjacent faces | COMPUTED | cube_layout.py:46 | Derived: all except self and opposite |

### 3.2 Color Scheme (BOY Layout)

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| F=Blue, R=Red, U=Yellow, L=Orange, D=White, B=Green | HARDCODED | cube_boy.py:106 | Western standard convention |
| Opposite colors (Blue↔Green, etc.) | COMPUTED | - | Follows from face opposites + color mapping |

### 3.3 Slice Definitions

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| M/E/S slice names | HARDCODED | SliceName.py | Convention from speedcubing |
| M axis = L↔R | HARDCODED | - | "M rotates like L" convention |
| E axis = U↔D | HARDCODED | - | "E rotates like D" convention |
| S axis = F↔B | HARDCODED | - | "S rotates like F" convention |
| M reference face = L | HARDCODED | Face2FaceTranslator | Could have been R |
| E reference face = D | HARDCODED | Face2FaceTranslator | Could have been U |
| S reference face = F | HARDCODED | Face2FaceTranslator | Could have been B |

### 3.4 Rotation Cycles

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| X cycle: D→F→U→B | HARDCODED | Face2FaceTranslator:420 | "X rotates like R" |
| Y cycle: R→F→L→B | HARDCODED | Face2FaceTranslator:421 | "Y rotates like U" |
| Z cycle: L→U→R→D | HARDCODED | Face2FaceTranslator:422 | "Z rotates like F" |
| Clockwise direction | HARDCODED | - | Viewer-facing convention |

### 3.5 Coordinate Systems

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| LTR (left-to-right, top-to-bottom) | HARDCODED | Face.py | Viewer perspective |
| Row 0 = top, Col 0 = left | HARDCODED | Face.py | Screen coordinate convention |
| B face 180° rotated | COMPUTED? | Issue #55 | Follows from LTR + cube topology |

### 3.6 Transformation Tables

| Decision | Classification | Location | Notes |
|----------|---------------|----------|-------|
| 30 face-pair transformations | COMPUTED | Face2FaceTranslator:162 | Derived from whole-cube rotations |
| 12 slice-index formulas | UNKNOWN | Face2FaceTranslator:335 | Empirically derived, may be computable |

---

## 4. KEY GEOMETRIC INSIGHTS

### 4.1 The B-Face Asymmetry

When viewing the cube from the front:
- F, U, D, L, R faces all have "natural" LTR coordinates
- B face appears "upside down" (180° rotated) when unfolded

This explains many special cases in the code:
```python
# Examples of B-face special handling:
if face_name == FaceName.B:
    return False  # Inverted index
```

### 4.2 Slice-Face Relationships

Each slice intersects 4 faces and is parallel to 2 faces:
- M: parallel to L,R; intersects F,U,B,D
- E: parallel to U,D; intersects F,R,B,L
- S: parallel to F,B; intersects U,R,D,L

The slice "cuts" rows on some faces and columns on others:
- M: vertical on F,B (columns), but seen as rows from face perspective
- E: horizontal on all 4 faces (rows)
- S: varies by face (R,L = rows; U,D = columns)

### 4.3 Index Alignment

Slice index 0 is closest to the "reference face":
- M[0] closest to L (not R)
- E[0] closest to D (not U)
- S[0] closest to F (not B)

When iterating a slice on a face, indices may or may not align:
- If face is on "same side" as reference: aligned
- If face is on "opposite side": inverted (n-1-i)

---

## 5. PLACES ASKING GEOMETRY QUESTIONS

### 5.1 In Code Comments

*(To be filled by exploration agents)*

### 5.2 In _CubeLayoutGeometry

| Method | Question Asked |
|--------|---------------|
| `does_slice_cut_rows_or_columns` | Does slice M/E/S cut rows or columns on face X? |
| `does_slice_of_face_start_with_face` | Does slice[0] align with face's row/col 0? |
| `iterate_orthogonal_face_center_pieces` | Which centers on side_face belong to layer slice N? |

### 5.3 In Face2FaceTranslator

| Method | Question Asked |
|--------|---------------|
| `translate` | Given point on face A, what's the corresponding point on face B? |
| `get_transform_type` | What rotation (0°, 90°, 180°, 270°) relates two faces? |
| `_derive_whole_cube_alg` | What whole-cube rotation brings source face to target position? |

---

## 6. WHAT CAN BE DERIVED MATHEMATICALLY?

### 6.1 Definitely Derivable

1. **Adjacent faces** from opposite faces
2. **Opposite colors** from face colors + opposite faces
3. **Slice traversal paths** from slice axis definitions
4. **Transformation types** from whole-cube rotation sequences

### 6.2 Potentially Derivable (Needs Analysis)

1. **Slice index formulas** - may follow from:
   - LTR coordinate convention
   - Slice reference face convention
   - Face-to-face transformation rules

2. **B-face rotation** - may follow from:
   - Cube unfolding convention
   - LTR coordinate system on all faces

### 6.3 Cannot Be Derived (Must Be Hardcoded)

1. **Color scheme** - arbitrary assignment
2. **Slice naming** (M/E/S) - speedcubing convention
3. **Reference face choice** (M→L, E→D, S→F) - arbitrary
4. **Rotation direction** - clockwise/counterclockwise convention
5. **Coordinate origin** - (0,0) at top-left vs bottom-left

---

## 7. PROPOSED ARCHITECTURE

### 7.1 Layer 0: Fundamental Constants (HARDCODED)

```python
# These MUST be hardcoded - no way to derive them
FACE_NAMES = [F, R, U, L, D, B]
OPPOSITE_PAIRS = [(F,B), (U,D), (L,R)]
SLICE_REFERENCE = {M: L, E: D, S: F}
ROTATION_POSITIVE = "clockwise when facing the reference face"
COORD_ORIGIN = "top-left of face when viewed from outside"
```

### 7.2 Layer 1: Derived Topology (COMPUTED)

```python
# These can be computed from Layer 0
def adjacent_faces(face): ...
def slice_axis(slice): ...  # M → L-R axis, etc.
def rotation_cycle(axis): ...  # X → [D,F,U,B]
```

### 7.3 Layer 2: Coordinate Transformations (COMPUTED)

```python
# These can be computed from Layer 1
def transform_type(source, target): ...  # IDENTITY, ROT_90_CW, etc.
def slice_formula(slice, face): ...  # ROW, COL, INV_ROW, INV_COL
```

### 7.4 Layer 3: High-Level Queries (COMPUTED)

```python
# These use Layer 2
def translate_point(source, target, point): ...
def iterate_slice_on_face(slice, face, index): ...
```

---

## 8. NEXT STEPS

### 8.1 Immediate Tasks

1. [ ] Complete inventory of all hardcoded tables
2. [ ] Document the mathematical relationship between tables
3. [ ] Prototype derivation of transformation table
4. [ ] Verify B-face asymmetry hypothesis

### 8.2 Future Work (Issue #55)

1. [ ] Implement Layer 0 constants module
2. [ ] Implement Layer 1 derived topology
3. [ ] Implement Layer 2 coordinate math
4. [ ] Replace lookup tables with computed values
5. [ ] Add comprehensive tests

---

## 9. APPENDIX: FILE LOCATIONS

| File | Contains |
|------|----------|
| `cube_layout.py` | CubeLayout protocol, opposite/adjacent |
| `_CubeLayout.py` | CubeLayout implementation |
| `_CubeLayoutGeometry.py` | Slice geometry methods |
| `cube_boy.py` | BOY color scheme |
| `slice_layout.py` | SliceLayout protocol |
| `Face2FaceTranslator.py` | Coordinate translation |
| `SliceName.py` | Slice enum |
| `FaceName.py` | Face enum |
| `_part.py` | Edge/Corner definitions |
| `GEOMETRY.md` | Existing geometry documentation |

---

*Document created: Analysis in progress*
*Last updated: Will be updated as agents complete*
