# Session Notes: Remove Hardcoded Geometry

**Branch:** `claude/remove-hardcoded-geometry-zciLd`
**Based on:** `geometry_cleanup_issue55_no2`
**Issue:** #55 - Replace hard-coded lookup tables with mathematical derivation
**Status:** In Progress

---

## Overview

Continue the work from `geometry_cleanup_issue55_no2` to remove hardcoded geometry from the cube solver.

---

## Task Table

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Remove hardcoded starting face/edge in `create_walking_info()` | Done | Derived from rotation face geometry |
| 2 | Remove DEBUG print statements | Done | Uses proper config-controlled logging (`solver_debug`) |
| 3 | Update documentation | Pending | Document the geometry derivation |
| 4 | Derive `is_slot_inverted` logic | Pending | Currently computed per-iteration |
| 5 | Derive `is_index_inverted` logic | Pending | Currently computed per-iteration |
| 6 | Fix TestSliceMovementPrediction tests | Pending | 18 tests failing (12 pass) |
| 7 | Debug `translate_target_from_source` predictions | Pending | Predictions don't match actual piece movement |
| 8 | Derive `get_slices_between_faces` directly | Pending | Currently uses patch implementation |

### From HARDCODED_ANALYSIS.md - Phase 1 (High Priority)

| ID | Table/Logic | File:Lines | Status | Notes |
|----|-------------|------------|--------|-------|
| 1.1 | `_TRANSFORMATION_TABLE` | Face2FaceTranslator.py:164-206 | In Progress | 30-entry dict, derive from slice traversal |
| 1.2 | `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py:336-354 | Pending | 12-entry dict, derive from edge geometry |

### From HARDCODED_ANALYSIS.md - Phase 2 (Medium Priority)

| ID | Table/Logic | File:Lines | Status | Notes |
|----|-------------|------------|--------|-------|
| 2.1 | `does_slice_cut_rows_or_columns` | _CubeLayoutGeometry.py:40-64 | Pending | Derive from slice axis |
| 2.2 | `does_slice_of_face_start_with_face` | _CubeLayoutGeometry.py:66-133 | Pending | Derive from edge sharing |
| 2.3 | Face-to-slice mapping | _CubeLayoutGeometry.py:231-247 | Pending | Trivial derivation |
| 1.3 | Rotation cycles `_X/Y/Z_CYCLE` | Face2FaceTranslator.py:421-423 | Pending | Derive from slice traversal |
| 3.2 | `_build_slice_cycle` start face/edge | Face2FaceTranslator.py:774-799 | Done | Was task #1 |

### From HARDCODED_ANALYSIS.md - Phase 3 (Low Priority)

| ID | Table/Logic | File:Lines | Status | Notes |
|----|-------------|------------|--------|-------|
| 5.2 | `_rotate_x/y/z` | _CubeLayout.py:352-401 | Pending | Could use cycles |

### From HARDCODED_ANALYSIS.md - Fundamental Definitions (NOT Derivable)

| ID | Definition | File:Lines | Notes |
|----|------------|------------|-------|
| 5.1 | `_OPPOSITE` faces | cube_layout.py:39-43 | Cube geometry definition |
| 3.1 | `get_face_name()` slice rotation | slice_layout.py:144-156 | M→L, E→D, S→F definition |
| 6.1 | BOY color scheme | cube_boy.py:113-120 | Reference definition |
| 4.1 | Face property checks | Face.py:611-647 | Convenience methods |

### Methods from GEOMETRY.md

| # | Method | Classification | Status | Notes |
|---|--------|---------------|--------|-------|
| 9 | `get_side_faces(layer1_face)` | COMPUTED | Pending | Return 4 faces perpendicular to L1 |
| 10 | `does_slice_affect_rows_or_cols(layer1_face, side_face)` | COMPUTED | Pending | Does slice cut rows or columns? |
| 11 | `get_row_or_col_for_slice(layer1_face, side_face, slice_index, n_slices)` | COMPUTED | Pending | Which row/col for slice index? |
| 12 | `iterate_orthogonal_face_center_pieces(...)` | COMPUTED | Done | In CubeLayout protocol |
| 13 | `does_slice_cut_rows_or_columns(face_name)` | COMPUTED | Done | In SliceLayout protocol |
| 14 | `does_slice_of_face_start_with_face(face_name)` | COMPUTED | Done | In SliceLayout protocol |

---

## Task #2: DEBUG Statements

**File:** `src/cube/domain/geometric/_CubeLayoutGeometry.py`

**Locations:**
- Lines 435-445: Initial debug (slice name, rotation face, cycle faces, starting edge/face)
- Lines 490-506: Per-iteration debug (face, edge position, flags, reference_point)
- Lines 540-542: Movement debug (edge leads to next face)

**Note:** These are NOT simple `print()` statements. They use the proper logging infrastructure:
```python
_log = cube.sp.logger
_dbg = cube.config.solver_debug  # Config flag controls output
if _log.is_debug(_dbg):
    _log.debug(_dbg, f"...")
```

**Decision needed:** Should these be:
1. **Removed entirely** - no longer needed after development
2. **Kept as-is** - useful for future debugging
3. **Converted** - move to a different debug flag (e.g., `geometry_debug`)

---

## Key Files

- `src/cube/domain/geometric/_CubeLayoutGeometry.py` - Main implementation
- `src/cube/domain/geometric/GEOMETRY.md` - Design documentation
- `.claude/sessions/claude-remove-geometry-barcoded-Jy1nL.md` - Previous session notes

---

## Commits on This Branch

(Inherited from `geometry_cleanup_issue55_no2`)
- Core hardcoded geometry removal already complete
- All tests passing (618+)

---

## Next Steps

1. Decide on DEBUG statement handling (task #2)
2. Continue with remaining tasks from table above

---

## Task 1.1: Deriving _TRANSFORMATION_TABLE

### Approach

1. Slice cycles (M, E, S) and whole-cube rotations (X, Y, Z) affect the **same 4 faces**
2. Use `CubeWalkingInfo.get_transform(source, target)` to get coordinate transform
3. Handle direction difference between slice and axis rotation

### Geometric Assumption

**ASSUMPTION:** Opposite faces rotate in opposite directions.

| Slice | Rotation Face | Axis | Axis Face | Relationship |
|-------|---------------|------|-----------|--------------|
| M | L | X | R | Opposite → invert direction |
| E | D | Y | U | Opposite → invert direction |
| S | F | Z | F | Same → same direction |

**Status:** Accepted as geometric fact. If proof needed, see:
- Standard Rubik's cube notation conventions
- TODO: Add link to formal proof if needed

### Algorithm

```
For (source_face, target_face):
1. Find slice that connects them (M, E, or S)
2. Get slice rotation face via SliceLayout.get_face_name()
3. Get axis rotation face (X→R, Y→U, Z→F)
4. Check if opposite via CubeLayout.get_opposite()
5. Get transform from CubeWalkingInfo.get_transform()
6. If opposite faces: invert transform direction
7. Map FUnitRotation → TransformType
```
