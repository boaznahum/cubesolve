# Hardcoded Geometry - Issue #55 Status

## Architecture

Two-layer architecture (see `GEOMETRY_LAYERS.md`):
- **Layout Layer** (size-independent): `CubeLayout`, `SliceLayout` - accessed via `cube.layout`
- **Geometric Layer** (size-dependent): `CubeGeometric` - accessed via `cube.geometric`

---

## Status Summary

| ID | Table/Constant | Location | Status | Notes |
|----|----------------|----------|--------|-------|
| 1.1 | `_TRANSFORMATION_TABLE` | Face2FaceTranslator.py:174 | **DONE** | Derived via `layout.derive_transform_type()` |
| 1.2 | `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py:346 | TODO | 12 entries, derive from edge geometry |
| 1.3 | `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` | Face2FaceTranslator.py:431 | TODO | Can derive from rotation faces |
| 2.1 | `does_slice_cut_rows_or_columns` | slice_layout.py | OK | Already derived from slice axis |
| 2.2 | `does_slice_of_face_start_with_face` | _CubeGeometric.py | OK | Minimal hardcoding, edge-based |
| 3.1 | `_SLICE_ROTATION_FACE` | _CubeGeometric.py:48 | FUNDAMENTAL | M→L, E→D, S→F (definition) |
| 3.2 | `_AXIS_ROTATION_FACE` | _CubeGeometric.py:55 | FUNDAMENTAL | M→R, E→U, S→F (definition) |
| 3.3 | `_SLICE_FACES` | _CubeGeometric.py:41 | OK | Could derive from rotation faces |
| 4.1 | `_OPPOSITE` | cube_layout.py:40 | FUNDAMENTAL | F↔B, U↔D, L↔R (definition) |
| 4.2 | `_ADJACENT` | cube_layout.py:50 | OK | Derived from `_OPPOSITE` |
| 5.1 | BOY layout | cube_boy.py | FUNDAMENTAL | Color scheme definition |
| 5.2 | `_UNIT_ROTATIONS` | FRotation.py:171 | FUNDAMENTAL | 4 rotation transforms |

---

## Remaining Work

### High Priority
- **1.2 `_SLICE_INDEX_TABLE`** - 12 entries mapping (SliceName, FaceName) → formula
  - Derive from: `does_slice_cut_rows_or_columns()` + `does_slice_of_face_start_with_face()`

### Medium Priority
- **1.3 Rotation Cycles** - `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE`
  - Derive from: slice traversal around axis faces

### Low Priority
- **3.3 `_SLICE_FACES`** - Which faces each slice affects
  - Derive from: faces adjacent to the slice's rotation face

---

## Fundamental Definitions (Cannot Derive)

These are the irreducible definitions everything else derives from:

```
_OPPOSITE           : F↔B, U↔D, L↔R
_SLICE_ROTATION_FACE: M→L, E→D, S→F
_AXIS_ROTATION_FACE : M→R, E→U, S→F
BOY layout          : Face→Color mapping
_UNIT_ROTATIONS     : 4 coordinate transform functions
```

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
