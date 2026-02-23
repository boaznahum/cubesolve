# claude: entries in this table should be nicely analyzed fromatted and moved to relevant todo file, including this comment

## New Entries

### A1: Revisit CacheManager design - name parameter seems redundant

**Category:** Architecture / Refactoring
**Priority:** Low
**Status:** New

**Summary:**
The current CacheManager design requires a `name` parameter when getting a cache, but this seems redundant. A simpler design with a single key might be sufficient.

**Current Usage:**

```python
cache = self._cube_layout.cache_manager.get("SliceLayout.does_slice_cut_rows_or_columns", CLGColRow)
return cache.compute(cache_key, compute)
```

**Proposed:**
Consider whether the name parameter is needed, or if a single-key cache would be simpler and sufficient.

**Context:**
Discovered while working on Issue #55 (geometry cleanup).

---

### A2: Remove duplicate face→name mappings in _part.py

**Category:** Architecture / Refactoring
**Priority:** Low
**Status:** Partially done

**Summary:**
`_part.py` has `_faces_2_edge_name()` and `_faces_2_corner_name()` with lazy-init dicts mapping `frozenset[FaceName]` → `EdgeName`/`CornerName`. `schematic_cube.py` has `_derive_edge_name()` and `_derive_corner_name()` doing the same thing. Consolidate into one place.

**Callers of `_part.py` functions:**
- `Cube.py`, `Corner.py`, `Edge.py` use `_faces_2_edge_name` / `_faces_2_corner_name`

**Approach:**
Either make `_part.py` functions delegate to `schematic_cube.py`, or move the canonical lookup into `part_names.py` and have both use it.

**Progress (2026-02-24):**
- Hardcoded edge table eliminated — edges now derived from corners in `schematic_cube.py`
- Hardcoded wiring in `Cube._reset()` replaced with loops over schematic data
- Still remaining: `_part.py` functions duplicate `schematic_cube.py` name derivation

**Context:**
Discovered while creating `part_names.py` to centralize `EdgeName`, `CornerName`, `EdgePosition`, `CornerPosition`.

---

### A3: Cube._reset() wiring now uses schematic loops (DONE)

**Category:** Architecture / Refactoring
**Priority:** N/A
**Status:** Done (2026-02-24)

**Summary:**
Replaced 20 hardcoded edge/corner assignment lines in `Cube._reset()` with loops
over `_SCHEMATIC_EDGES` / `_SCHEMATIC_CORNERS`. Added `Face.set_edge()` and
`Face.set_corner()` with match/case and `_init_finished` guard.
The edge table itself is now derived from the corner table — corners are the
single source of truth.

**Commits:**
- `60b1bf17` — Replace hardcoded wiring with schematic loops, add Face.set_edge/set_corner
- `5c229d7f` — Derive edge table from corners, eliminate hardcoded _SCHEMATIC_EDGES

---

