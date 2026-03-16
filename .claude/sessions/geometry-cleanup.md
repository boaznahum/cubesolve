# Session: geometry-cleanup

**Branch:** `geometry-cleanup`
**Base:** `todo-cleanup-2` (which includes `dead-code-cleanup` and `todo-cleanup`)
**Started:** 2026-03-16
**Related Issues:** #121, #126 (closed)

## Goal

Eliminate all hardcoded geometry in the solver layer. Replace `cube.inv()`, hardcoded face/edge position checks, and coordinate assumptions with geometry classes (`Face2FaceTranslator`, `CubeLayout`, `SchematicCube`, `FUnitRotation`).

## Background

Issue #126 (NxNCenters back-face coordinate inversion) was fixed on branch `claude/code-cleanup-4R0LI` and merged. That fix:
- Replaced `_count_colors_on_block` inv() hack with `Block`-based geometry
- Replaced `_get_four_center_points` inv() with `geometry_utils.inv()`
- Fixed `_do_complete_slices` to search ALL source faces

The remaining hardcoded geometry is spread across 6 files.

## Hardcoded Geometry Audit (2026-03-16)

### 1. CommonOp.py — WORST OFFENDER (Issue #121)

**File:** `src/cube/domain/solver/common/CommonOp.py`

**Line 472:** `# claude [#121]: hard coded, find the optimal path to rotate face on edge`
**Line 529:** `# claude: hard coded !!!!!! all information in cube and slice layout`

**Lines 231-343:** Massive block of hardcoded face/edge position checks:
```python
if cube.front.edge_right is edge or cube.front.edge_left is edge:
    ...
if cube.right.edge_right is edge:
    ...
if cube.left.edge_left is edge:
    ...
if edge is cube.back.edge_top:
    ...
```

This is ~100 lines of hardcoded spatial reasoning about which face/edge is where. Should use geometry queries from `CubeLayout` or `SchematicCube`.

### 2. CommutatorHelper.py — 2 spots

**File:** `src/cube/domain/solver/common/big_cube/commutator/CommutatorHelper.py`

**Lines 692-693:**
```python
v1 = self.cube.inv(v1)
v2 = self.cube.inv(v2)
```

Hardcoded coordinate inversion. Should use geometry translation.

### 3. E2ECommutator.py — 1 spot

**File:** `src/cube/domain/solver/common/big_cube/commutator/E2ECommutator.py`

**Line 46:**
```python
required_source_wing_face_column_index = cube.inv(face_row_index_on_target_edge)
```

### 4. _LBLL3Edges.py — 2 spots

**File:** `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py`

**Line 225:** `required_indices = [target_index, cube.inv(target_index)]`
**Line 279:** `return mapped_si == cube.inv(ti)`

Edge index mirroring using `cube.inv()`.

### 5. _LBLNxNEdges.py — 1 spot

**File:** `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py`

**Line 111:** `required_indexes = [target_edge_wing.index, cube.inv(target_edge_wing.index)]`

### 6. NxNCenters.py — 1 remaining spot

**File:** `src/cube/domain/solver/common/big_cube/NxNCenters.py`

**Line 727:** `inv = self.cube.inv`

Used for coordinate inversion in slice swap logic.

## Pattern Summary

| Pattern | Count | Files |
|---------|-------|-------|
| `cube.inv()` coordinate inversion | 7 | CommutatorHelper, E2ECommutator, _LBLL3Edges, _LBLNxNEdges, NxNCenters |
| Hardcoded face/edge position checks | ~15+ | CommonOp |
| **Total** | ~22+ | 6 files |

## Available Geometry Infrastructure

These classes already exist and can replace hardcoded logic:

- **`geometry_utils.inv(n_slices, v)`** — Generic coordinate inversion (no cube dependency)
- **`Face2FaceTranslator`** — Translates coordinates between any two faces
- **`CubeLayout.get_bring_face_alg(target, source)`** — Whole-cube rotation between faces
- **`SchematicCube`** — Face topology (neighbors, opposites, adjacency)
- **`FUnitRotation`** — Face-local coordinate transforms (CW0-CW3)
- **`CubeWalkingInfo`** — Walking paths along slices across faces
- **`Block`** — Rectangular region on a face with proper coordinate handling

## Approach

1. Start with `cube.inv()` usages (7 spots) — replace with `geometry_utils.inv(n, v)`
2. Then tackle CommonOp.py hardcoded face/edge checks — use SchematicCube queries
3. Run solver tests after each file change

## Checklist

- [ ] CommutatorHelper.py lines 692-693
- [ ] E2ECommutator.py line 46
- [ ] _LBLL3Edges.py lines 225, 279
- [ ] _LBLNxNEdges.py line 111
- [ ] NxNCenters.py line 727
- [ ] CommonOp.py lines 231-343 (big refactor — #121)
- [ ] CommonOp.py line 472 (optimal rotation path)
- [ ] CommonOp.py line 529 (hardcoded geometry)

## Test Commands

```bash
# Solver tests
CUBE_QUIET_ALL=1 python -m pytest tests/solvers/ -v --tb=short

# All non-GUI tests
CUBE_QUIET_ALL=1 python -m pytest tests/ -v -m "not gui and not slow"

# Checkers
python -m ruff check src/cube
python -m mypy -p cube
python -m pyright src/cube
```
