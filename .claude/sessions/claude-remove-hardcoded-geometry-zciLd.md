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
| 2 | Remove DEBUG print statements | Pending | See details below |
| 3 | Update documentation | Pending | Document the geometry derivation |
| 4 | Derive `is_slot_inverted` logic | Pending | Currently computed per-iteration |
| 5 | Derive `is_index_inverted` logic | Pending | Currently computed per-iteration |

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
