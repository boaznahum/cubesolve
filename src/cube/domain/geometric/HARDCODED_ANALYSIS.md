# Hardcoded Geometry - Issue #55 Status

## Architecture

Two-layer architecture (see `GEOMETRY_LAYERS.md`):
- **Layout Layer** (size-independent): `CubeLayout`, `SliceLayout` - accessed via `cube.layout`
- **Geometric Layer** (size-dependent): `SizedCubeLayout` - accessed via `cube.sized_layout`

### Constants Location Rule

**Fundamental constants should be in:**
1. **`cube_layout.py`** - Topology constants (opposite faces, slice definitions)
2. **`cube_boy.py`** - BOY color scheme
3. **`_part.py`** - Part definitions (edge/corner names)
4. **`CubeSanity.py`** - Valid color combinations

---

## TODO - Remaining Hardcoded Items

| What | Location | Entries | How to Derive |
|------|----------|---------|---------------|
| `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py | 12 | From edge geometry |
| `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` | Face2FaceTranslator.py | 12 | From `_SLICE_ROTATION_FACE` |
| `slice_to_axis` dict | Face2FaceTranslator.py:488 | 3 | Use `_AXIS_ROTATION_FACE` directly |
| `get_start_face()` | slice_layout.py | 3 | Derive from slice definitions |
| `_rotate_dict_x/y/z` | _CubeLayout.py | 12 | From rotation cycles |

---

## Status Summary - Geometry Package (Full Details)

| ID | Table/Constant | Location | Status | Action |
|----|----------------|----------|--------|--------|
| 1.1 | `_TRANSFORMATION_TABLE` | ~~Face2FaceTranslator.py~~ | **REMOVED** | Was dead code |
| 1.2 | `_SLICE_INDEX_TABLE` | Face2FaceTranslator.py | TODO | 12 entries - derive from edge geometry |
| 1.3 | `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` | Face2FaceTranslator.py | TODO | 12 entries - derive from slice faces |
| 1.4 | `slice_to_axis` dict | Face2FaceTranslator.py:488 | TODO | Duplicates `_AXIS_ROTATION_FACE` |
| 1.5 | `_build_slice_cycle` start faces | Face2FaceTranslator.py:693 | **FIXED** | Uses `resolve_cube_cycle()` |
| 2.1 | `_SLICE_ROTATION_FACE` | cube_layout.py | **OK** | Fundamental |
| 2.2 | `_AXIS_ROTATION_FACE` | cube_layout.py | **OK** | Fundamental |
| 2.3 | `_OPPOSITE` | cube_layout.py | **OK** | Fundamental |
| 2.4 | `get_slice_for_faces()` | cube_layout.py | **ADDED** | Derives slices from constants |
| 2.5 | `get_all_slices_for_faces()` | cube_layout.py | **ADDED** | Derives all connecting slices |
| 2.6 | `get_slice_parallel_to_face()` | cube_layout.py | **ADDED** | Derives parallel slice for face |
| 2.7 | `get_face_neighbor()` | cube_layout.py | **ADDED** | Gets neighbor face by EdgePosition |
| 2.8 | `get_face_neighbors_cw()` | cube_layout.py | **ADDED** | Gets 4 neighbors in CW order |
| 3.1 | `get_start_face()` | slice_layout.py | TODO | Hardcoded face returns |
| 3.2 | face checks | ~~_SizedCubeLayout.py~~ | **FIXED** | Now uses `get_slice_parallel_to_face()` |
| 3.3 | `does_slice_of_face_start_with_face()` | slice_layout.py | **MOVED** | Moved from _SizedCubeLayout |
| 3.4 | rotation logic | _CubeLayout.py | TODO | `_rotate_dict_x/y/z` cycles |
| 4.1 | `EdgePosition` enum | _elements.py | **ADDED** | LEFT/RIGHT/TOP/BOTTOM positions |
| 4.2 | `Face.get_edge()` | Face.py | **ADDED** | Get edge by EdgePosition |

---

## Codebase-Wide Hardcoded Constants

### FUNDAMENTAL - Should Stay

| File | What | Count | Notes |
|------|------|-------|-------|
| `cube_layout.py` | `_OPPOSITE`, `_SLICE_ROTATION_FACE`, `_AXIS_ROTATION_FACE` | 9 | Topology definitions |
| `cube_boy.py` | BOY color mapping | 6 | Color scheme |
| `_part.py` | Edge/corner name definitions | 24 | Part structure |
| `Cube.py:374-387` | Face object creation | 6 | Uses BOY layout |
| `Cube.py:451-472` | Slice object creation | 3 | Initialization |
| `Cube3x3Colors.py` | Edge/corner color init | 18 | Initial state |
| `CubeSanity.py` | Valid color combinations | 24 | Validation data |
| `FRotation.py` | `_UNIT_ROTATIONS` | 4 | Mathematical |

### TODO - Should Be Derived

| File | What | Count | How to Derive |
|------|------|-------|---------------|
| `Face2FaceTranslator.py` | `_SLICE_INDEX_TABLE` | 12 | From edge geometry |
| `Face2FaceTranslator.py` | `_X/Y/Z_CYCLE` | 12 | From `_SLICE_ROTATION_FACE` |
| `Face2FaceTranslator.py` | `slice_to_axis` | 3 | Use `_AXIS_ROTATION_FACE` |
| `_supported_faces.py` | Face transform table | 41 | From face relationships |
| `FaceAlg.py` | Subclass constructors | 6 | Factory pattern |
| `WideFaceAlg.py` | Subclass constructors | 6 | Factory pattern |
| `SliceAlg.py` | Subclass constructors | 3 | Factory pattern |
| `WholeCubeAlg.py` | Subclass constructors + dispatch | 9 | Factory pattern |

### ACCEPTABLE - Switch/Dispatch Logic

These are inherently tied to enum values and are acceptable:

| File | What | Notes |
|------|------|-------|
| `Cube.py` | `rotate_face_and_slice()` dispatch | ~20 cases |
| `CommonOp.py` | Face manipulation logic | ~35 references |
| `Algs.py` | Move notation dispatch | ~15 cases |
| `Face.py` | `is_front()`, `is_back()` etc. | Properties |
| Solver files | Assertions and sanity checks | Validation |

---

## Completed Work

### Session 2026-01-15

**Added EdgePosition enum and Face navigation:**
- `EdgePosition` enum in `_elements.py` - LEFT/RIGHT/TOP/BOTTOM positions
- `Face.get_edge(position)` - Get edge at specific position on face
- `Face._edge_by_position` mapping built in `finish_init()`

**Added CubeLayout methods for face neighbors:**
- `get_face_neighbor(face_name, position)` - Get neighboring FaceName at EdgePosition
- `get_face_neighbors_cw(face)` - Get 4 neighboring Face objects in clockwise order

**Fixed Face2FaceTranslator:**
- `_build_slice_cycle` now uses `resolve_cube_cycle()` instead of hardcoded start faces

**Object Ownership Pattern documented:**
- Methods with `resolve_cube` prefix accept Cube parameter and return objects from SAME cube
- Added TODO in `CubeWalkingInfoUnit` to audit all geometry classes for this pattern
- Pattern ensures no internal cube objects are leaked to callers

**Import cleanup:**
- Removed `FaceName` re-export from `cube_boy.py` `__all__`
- Fixed `cube.domain.model.__init__.py` to import `FaceName` directly from `FaceName.py`

### Session 2026-01-11 (continued)

**Moved methods to layout layer:**
- `get_slice_for_faces()` - moved from `_SizedCubeLayout` to `cube_layout.py`
- `get_all_slices_for_faces()` - moved from `_SizedCubeLayout` to `cube_layout.py`
- `get_slice_parallel_to_face()` - new function in `cube_layout.py`
- `_does_slice_of_face_start_with_face()` - moved from `_SizedCubeLayout` to `_SliceLayout`

**Fixed hardcoded logic:**
- `iterate_orthogonal_face_center_pieces` - removed hardcoded face checks, now uses `get_slice_parallel_to_face()`

**Removed claude: comments** from `_SizedCubeLayout.py`

### Session 2025-01-11

**Removed dead code (-891 lines):**
- `TransformType` enum - never used in production
- `derive_transform_type()` - never called from solver/presentation
- `_TRANSFORMATION_TABLE` - was dead, transforms use CubeWalkingInfo
- Related test files and helper methods

**Fixed bugs:**
- `_compute_slice_algorithms` returns ALL algorithms for opposite faces
- `FaceTranslationResult` API: `slice_algorithms: list` → `slice_algorithm: SliceAlgorithmResult`
- `translate_source_from_target` returns `list[FaceTranslationResult]`

### Previous Sessions

- `_SLICE_FACES` table removed - derived on demand
- `_OPPOSITE_FACES` removed - was duplicate
- Constants consolidated in `cube_layout.py`

---

## Priority Order for Remaining Work

### High Priority (Duplicated Constants)
1. **`slice_to_axis` in Face2FaceTranslator.py** - Direct duplicate of `_AXIS_ROTATION_FACE`
2. **`_supported_faces.py` table** - 41 entries that could be derived

### Medium Priority (Derivable Tables)
3. **`_SLICE_INDEX_TABLE`** - 12 entries, derive from `does_slice_cut_rows_or_columns()`
4. **`_X/Y/Z_CYCLE`** - 12 entries, derive from `_SLICE_ROTATION_FACE + _ADJACENT`
5. **`_build_slice_cycle` start faces** - 3 cases, derive from slice definitions

### Low Priority (Factory Pattern Refactoring)
6. **Alg subclass constructors** - Use factory/registry pattern instead of explicit classes

---

## File Organization

```
src/cube/
├── domain/
│   ├── geometric/           # ANALYZED - see table above
│   │   ├── cube_layout.py   # FUNDAMENTAL CONSTANTS HERE
│   │   ├── cube_boy.py      # BOY COLOR SCHEME HERE
│   │   └── ...
│   │
│   ├── model/
│   │   ├── _part.py         # FUNDAMENTAL - Part definitions
│   │   ├── Cube.py          # Mixed: init (OK) + dispatch (acceptable)
│   │   ├── CubeSanity.py    # FUNDAMENTAL - Valid combinations
│   │   └── Slice.py         # Acceptable dispatch logic
│   │
│   ├── algs/
│   │   ├── FaceAlg.py       # TODO - Factory pattern
│   │   ├── SliceAlg.py      # TODO - Factory pattern
│   │   ├── WholeCubeAlg.py  # TODO - Factory pattern
│   │   └── Algs.py          # Acceptable dispatch
│   │
│   └── solver/
│       └── common/
│           └── big_cube/
│               └── commun/
│                   └── _supported_faces.py  # TODO - Derive from relationships
```

---

## Quick Reference

| To derive... | Look at... |
|--------------|------------|
| Opposite faces | `cube_layout._OPPOSITE` |
| Adjacent faces | `cube_layout._ADJACENT` |
| Slice rotation face | `cube_layout._SLICE_ROTATION_FACE` |
| Slice axis face | `cube_layout._AXIS_ROTATION_FACE` |
| Slices connecting faces | `cube_layout.get_slice_for_faces()` |
| All slices connecting faces | `cube_layout.get_all_slices_for_faces()` |
| Slice parallel to a face | `cube_layout.get_slice_parallel_to_face()` |
| Slice alignment with face | `slice_layout.does_slice_of_face_start_with_face()` |
| Face traversal | `CubeWalkingInfo` via `create_walking_info()` |
| Neighbor face by position | `cube_layout.get_face_neighbor(face_name, EdgePosition)` |
| 4 neighbors clockwise | `cube_layout.get_face_neighbors_cw(face)` |
| Edge at face position | `face.get_edge(EdgePosition)` |
| Resolve names to objects | `CubeWalkingInfoUnit.resolve_cube_cycle(cube)` |

---

## Object Ownership Pattern

Methods that return Face/Edge/Part objects must follow this pattern:

1. **Accept cube parameter** → return objects from that cube
2. **Accept Face/Edge objects** → return objects from the same cube
3. **No cube parameter** → return only names/enums, NOT objects

Methods with `resolve_cube` prefix explicitly follow this pattern.

**TODO:** Audit all geometry classes to ensure compliance.
