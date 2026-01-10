# Hardcoded Geometry - Issue #55 Status

## Architecture

Two-layer architecture (see `GEOMETRY_LAYERS.md`):
- **Layout Layer** (size-independent): `CubeLayout`, `SliceLayout` - accessed via `cube.layout`
- **Geometric Layer** (size-dependent): `CubeGeometric` - accessed via `cube.geometric`

### Constants Location Rule

**All constants must be in exactly two places:**
1. **`cube_layout.py`** - Topology constants (opposite faces, adjacent faces, slice definitions)
2. **`cube_boy.py`** - BOY color scheme

No other file should define constants. `_CubeGeometric.py`, `_CubeLayout.py`, etc. must derive values from these two sources.

---

## Status Summary

| ID | Table/Constant | Current Location | Status | Action |
|----|----------------|------------------|--------|--------|
| 1.1 | `_TRANSFORMATION_TABLE` | Face2FaceTranslator.py | **DONE** | Derived via `layout.derive_transform_type()` |
| 1.2 | `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py | TODO | Derive from edge geometry |
| 1.3 | `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` | Face2FaceTranslator.py | TODO | Derive from slice rotation faces |
| 2.1 | `_SLICE_ROTATION_FACE` | cube_layout.py | **DONE** | Fundamental constant |
| 2.2 | `_AXIS_ROTATION_FACE` | cube_layout.py | **DONE** | Moved to cube_layout.py |
| 2.3 | `_SLICE_FACES` | (removed) | **DONE** | Derived on demand from _SLICE_ROTATION_FACE + _ADJACENT |
| 2.4 | `_OPPOSITE_FACES` | (deleted) | **DONE** | Removed - was duplicate of `_ALL_OPPOSITE` |
| 3.1 | `_OPPOSITE` | cube_layout.py | OK | Fundamental - correct location |
| 3.2 | `_ADJACENT` | cube_layout.py | OK | Derived from `_OPPOSITE` |
| 4.1 | BOY layout | cube_boy.py | OK | Fundamental - correct location |
| 4.2 | `_UNIT_ROTATIONS` | FRotation.py | OK | Mathematical constants |

---

## Remaining Work

### High Priority
- **1.2 `_SLICE_INDEX_TABLE`** - 12 entries mapping (SliceName, FaceName) → formula
  - Derive from: `does_slice_cut_rows_or_columns()` + `does_slice_of_face_start_with_face()`

### Medium Priority
- **1.3 Rotation Cycles** - `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE`
  - Derive from: slice rotation faces in cube_layout.py

---

## Fundamental Definitions

All in **cube_layout.py** (except BOY):

```
cube_layout.py:
  _OPPOSITE           : F↔B, U↔D, L↔R (fundamental)
  _ALL_OPPOSITE       : Bidirectional (derived)
  _ADJACENT           : Adjacent faces (derived from _OPPOSITE)
  _SLICE_ROTATION_FACE: M→L, E→D, S→F (fundamental)
  _AXIS_ROTATION_FACE : M→R, E→U, S→F (fundamental)

cube_boy.py:
  BOY layout          : Face→Color mapping
```

Note: `_SLICE_FACES` was removed - now derived on demand in `get_slice_for_faces()`.

---

## Completed Work

### Task 1.1: `_TRANSFORMATION_TABLE` (30 entries) - DONE

**Solution:** Added `derive_transform_type()` to `CubeLayout` protocol

**Location:** `_CubeLayout.py:501-568`

**Method:** Symbolic corner analysis using edge properties:
1. Get edge connecting source and target faces
2. Extract properties: `is_horizontal`, `is_slot_inverted`, `is_index_inverted`
3. Map properties to corner index (0-3)
4. Lookup transform from corner pair

**Tests:** `tests/geometry/test_derive_transformation_table.py` - validates all 30 entries

---

## File Organization

```
src/cube/domain/geometric/
├── HARDCODED_ANALYSIS.md   # This file - task status
├── GEOMETRY_LAYERS.md      # Architecture documentation
│
├── cube_layout.py          # CubeLayout protocol (Layout layer)
├── _CubeLayout.py          # Implementation + derive_transform_type
├── slice_layout.py         # SliceLayout protocol
│
├── cube_geometric.py       # CubeGeometric protocol (Geometric layer)
├── _CubeGeometric.py       # Implementation
│
├── Face2FaceTranslator.py  # Contains remaining hardcoded tables
├── FRotation.py            # Rotation transforms
└── cube_walking.py         # Slice traversal utilities
```
