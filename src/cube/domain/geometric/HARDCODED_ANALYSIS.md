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
| 1.1 | `_TRANSFORMATION_TABLE` | ~~Face2FaceTranslator.py~~ | **REMOVED** | Was dead code - transforms via CubeWalkingInfo |
| 1.2 | `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py | TODO | 12 entries - derive from edge geometry |
| 1.3 | `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` | Face2FaceTranslator.py | TODO | 12 entries total - derive from slice rotation faces |
| 1.4 | `slice_to_axis` dict | Face2FaceTranslator.py | TODO | Duplicates `_AXIS_ROTATION_FACE` |
| 1.5 | `slice_name_to_alg` dict | Face2FaceTranslator.py | TODO | Map via `Algs.M/E/S` |
| 2.1 | `_SLICE_ROTATION_FACE` | cube_layout.py | **OK** | Fundamental constant |
| 2.2 | `_AXIS_ROTATION_FACE` | cube_layout.py | **OK** | Fundamental constant |
| 2.3 | `_SLICE_FACES` | (removed) | **REMOVED** | Derived on demand |
| 2.4 | `_OPPOSITE_FACES` | (deleted) | **REMOVED** | Was duplicate |
| 3.1 | `_OPPOSITE` | cube_layout.py | **OK** | Fundamental |
| 3.2 | `_ADJACENT` | cube_layout.py | **OK** | Derived from `_OPPOSITE` |
| 4.1 | BOY layout | cube_boy.py | **OK** | Fundamental |
| 4.2 | `_UNIT_ROTATIONS` | FRotation.py | **OK** | Mathematical constants |
| 5.1 | `_build_slice_cycle` start faces | Face2FaceTranslator.py | TODO | Hardcoded M/E/S start faces |
| 5.2 | `get_start_face()` | slice_layout.py | TODO | Hardcoded face returns |
| 6.1 | `iterate_orthogonal_face_center_pieces` | _CubeGeometric.py | TODO | Hardcoded face checks |
| 6.2 | `_compute_source_coord_via_slice` | _CubeGeometric.py | TODO | Hardcoded SliceName checks |
| 7.1 | `get_face_from_f_layout` | _CubeLayout.py | TODO | Hardcoded rotation logic |
| 7.2 | `get_funitrot_to_face` | _CubeLayout.py | TODO | Hardcoded rotation logic |
| 7.3 | `_rotate_dict_x/y/z` | _CubeLayout.py | TODO | Hardcoded cycles (derive from fundamental) |

---

## Completed Work

### Session 2025-01 (Current)

**Removed dead code:**
- `TransformType` enum - never used in production
- `derive_transform_type()` - never called from solver/presentation
- `_TRANSFORMATION_TABLE` - was dead, transforms use CubeWalkingInfo
- ~891 lines removed

**Fixed bugs:**
- `_compute_slice_algorithms` now returns ALL algorithms for opposite faces (was returning early)
- `FaceTranslationResult` API changed: `slice_algorithms: list` → `slice_algorithm: SliceAlgorithmResult`
- `translate_source_from_target` returns `list[FaceTranslationResult]` (1 for adjacent, 2 for opposite)

### Previous Sessions

- `_SLICE_FACES` table removed - derived on demand from `_SLICE_ROTATION_FACE + _ADJACENT`
- `_OPPOSITE_FACES` removed - was duplicate of `_ALL_OPPOSITE`
- Constants consolidated in `cube_layout.py`

---

## Remaining Work

### High Priority (Duplicated Constants)

**1.4 `slice_to_axis` dict in Face2FaceTranslator.py:488**
```python
slice_to_axis: dict[SliceName, FaceName] = {
    SliceName.M: FaceName.R,  # M -> X
    SliceName.E: FaceName.U,  # E -> Y
    SliceName.S: FaceName.F,  # S -> Z
}
```
This duplicates `_AXIS_ROTATION_FACE` in cube_layout.py. Should use `cube.layout._AXIS_ROTATION_FACE[slice_name]` or add accessor method.

**1.2 `_SLICE_INDEX_TABLE` - 12 entries**
```python
_SLICE_INDEX_TABLE: dict[tuple[SliceName, FaceName], str] = {
    (SliceName.M, FaceName.F): _SliceIndexFormula.COL,
    (SliceName.M, FaceName.U): _SliceIndexFormula.COL,
    ...
}
```
Can derive from: `does_slice_cut_rows_or_columns()` + `does_slice_of_face_start_with_face()`

### Medium Priority (Hardcoded Logic)

**1.3 Rotation Cycles** - `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE`
Can derive from `_SLICE_ROTATION_FACE` + `_ADJACENT`:
- X cycle = faces affected by M slice (opposite of L: not L or R)
- Y cycle = faces affected by E slice (opposite of D: not U or D)
- Z cycle = faces affected by S slice (opposite of F: not F or B)

**5.1 `_build_slice_cycle` start faces** (Face2FaceTranslator.py:693)
```python
case SliceName.M:
    start_face = cube.front
    start_edge = start_face.edge_bottom
```
Should derive from `_SLICE_ROTATION_FACE` and `get_start_edge_for_slice()`.

**6.1/6.2 _CubeGeometric hardcoded checks**
```python
if l1_name in [FaceName.U, FaceName.D]:
    slice_name = SliceName.E
    reference_face = FaceName.D
```
Should use `get_slice_for_faces()` pattern.

**7.1/7.2/7.3 _CubeLayout rotation logic**
Complex rotation code that should eventually be derived from fundamental constants.

---

## Fundamental Definitions

All in **cube_layout.py** (except BOY):

```
cube_layout.py:
  _OPPOSITE           : F↔B, U↔D, L↔R (3 entries - fundamental)
  _ALL_OPPOSITE       : Bidirectional (6 entries - derived)
  _ADJACENT           : Adjacent faces (derived from _OPPOSITE)
  _SLICE_ROTATION_FACE: M→L, E→D, S→F (3 entries - fundamental)
  _AXIS_ROTATION_FACE : M→R, E→U, S→F (3 entries - fundamental)

cube_boy.py:
  BOY layout          : Face→Color mapping (6 entries - fundamental)
```

**Total fundamental constants: 15 entries** (3+3+3+6)

---

## File Organization

```
src/cube/domain/geometric/
├── HARDCODED_ANALYSIS.md   # This file - task status
├── GEOMETRY_LAYERS.md      # Architecture documentation
│
├── cube_layout.py          # CubeLayout protocol + FUNDAMENTAL CONSTANTS
├── _CubeLayout.py          # Implementation (contains hardcoded rotation logic)
├── slice_layout.py         # SliceLayout protocol (contains hardcoded get_start_face)
│
├── cube_geometric.py       # CubeGeometric protocol
├── _CubeGeometric.py       # Implementation (contains hardcoded face checks)
│
├── Face2FaceTranslator.py  # Contains: _SLICE_INDEX_TABLE, cycles, slice_to_axis
├── FRotation.py            # Rotation transforms (mathematical - OK)
└── cube_walking.py         # Slice traversal (docstring examples only)
```

---

## Quick Reference: Where to Look

| To derive... | Look at... |
|--------------|------------|
| Which faces are opposite | `cube_layout._OPPOSITE` |
| Which faces are adjacent | `cube_layout._ADJACENT` |
| Which face a slice rotates like | `cube_layout._SLICE_ROTATION_FACE` |
| Which axis a slice aligns with | `cube_layout._AXIS_ROTATION_FACE` |
| Which slices connect two faces | `_CubeGeometric.get_slice_for_faces()` |
| Face traversal for a slice | `CubeWalkingInfo` via `create_walking_info()` |
