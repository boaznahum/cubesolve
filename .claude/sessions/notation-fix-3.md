# Notation Fix 3

## Goal
Introduce proper M notation: `Algs.M` = single middle slice (MiddleSliceAlg), `Algs.MM` = all middle slices (_M).

## Completed Steps

### Phase 1: Remove deprecated MM() method
- Removed `_MM` field, `MM()` static method, unused `warnings` import from `Algs.py`
- Replaced `Algs.MM()` -> `Algs.M.prime` in `NxNCenters.py`

### Phase 2: Rename M -> MM (all middle slices)
- `Algs.M` (type `_M`) renamed to `Algs.MM` throughout codebase
- `_M._add_to_str` overridden to display `[:]M` instead of `M`
- `_M.get_base_alg()` updated to return `Algs.MM`
- All usages across solver, GUI, tests updated: `Algs.M` -> `Algs.MM`
- Parser handles `[:]M` -> `Algs.MM` (unsliced, all middle slices)

### Phase 3: New MiddleSliceAlg class
- Created `src/cube/domain/algs/MiddleSliceAlg.py` - single middle slice, `str()` = `"M"`
- `Algs.M = MiddleSliceAlg()` added to `Algs.py`
- NOT added to `Algs.Simple` list (would break seeded scrambles)
- Parser behavior:
  - bare `"M"` -> `MiddleSliceAlg` (single middle slice)
  - `"[1]M"` -> `Algs.MM[1]` (SlicedSliceAlg)
  - `"[:]M"` -> `Algs.MM` (unsliced, all middle slices)

### Phase 4: Fix solver test failures (compat_3x3 flag)
- **Root cause:** CFOP OLL/PLL algorithms contain "M" in parsed strings (e.g. Ua Perm: `"M2' U M U2 M' U M2'"`). On big cubes (4x4+), MiddleSliceAlg picks only 1 middle slice instead of all slices, breaking the solver.
- **Fix:** Added `compat_3x3` flag (default `False`) to `parse_alg()` and `Algs.parse()`. When `True`, bare "M" stays as `_M` (all middle slices).
- Applied `compat_3x3=True` to:
  - `_OLL.py` - OLL algorithm parsing
  - `_PLL.py` - PLL algorithm parsing (2 call sites)
  - `Kociemba3x3.py` - kociemba solution parsing

## Files Modified

### New files
- `src/cube/domain/algs/MiddleSliceAlg.py`

### Core alg changes
- `src/cube/domain/algs/Algs.py` - MM field, M field, parse() flag, Simple list
- `src/cube/domain/algs/SliceAlg.py` - _M._add_to_str override, get_base_alg
- `src/cube/domain/algs/SlicedSliceAlg.py` - get_base_alg returns Algs.MM
- `src/cube/domain/algs/_parser.py` - compat_3x3 flag, MiddleSliceAlg handling

### Solver changes (Algs.M -> Algs.MM rename)
- `src/cube/domain/solver/common/big_cube/NxNCenters.py`
- `src/cube/domain/solver/common/big_cube/NxNEdges.py`
- `src/cube/domain/solver/common/big_cube/NxNEdgesCommon.py`
- `src/cube/domain/solver/_3x3/cfop/_OLL.py` - compat_3x3=True
- `src/cube/domain/solver/_3x3/cfop/_PLL.py` - compat_3x3=True
- `src/cube/domain/solver/_3x3/kociemba/Kociemba3x3.py` - compat_3x3=True

### GUI changes (Algs.M -> Algs.MM rename)
- `src/cube/presentation/gui/commands/registry.py`
- `src/cube/presentation/gui/backends/webgl/ClientSession.py`
- `src/cube/presentation/gui/backends/pyglet2/PygletAppWindow.py`
- `src/cube/presentation/gui/backends/pyglet2/main_g_mouse.py`
- `src/cube/presentation/gui/protocols/AppWindowBase.py`
- `src/cube/application/Scrambler.py`

### Other source changes
- `src/cube/domain/geometric/Face2FaceTranslator.py`
- `src/cube/domain/model/Slice.py`
- `src/cube/domain/solver/direct/cage/DESIGN.md`

### Test changes (Algs.M -> Algs.MM rename only, no test logic changed)
- `tests/algs/test_cube.py`
- `tests/algs/test_simplify.py`
- `tests/backends/conftest.py`
- `tests/backends/README.md`
- `tests/geometry/test_commutator_blocks.py`
- `tests/parsing/test_indexes_slices.py`
- `tests/parsing/test_slice_notation_display.py`
- `tests/performance/test_slice_cache_perf.py`

## Test Status
- Non-GUI, non-WebGL tests: **9737 passed, 64 skipped, 0 failed**

## Future Tasks
- **TODO:** Eliminate `Algs.parse()` usages in solver code - replace parsed algorithm strings with programmatic alg construction. This removes the need for `compat_3x3` flag.
- **TODO:** Add MiddleSliceAlg (Algs.M) to scrambler (carefully, don't change Simple list length)
- **TODO:** Consolidate `DoubleLayerAlg` (Rw) and `WideFaceAlg` (r) — they use different slice indexing but may produce the same cube state. Investigate whether they are truly identical, then remove one class.
- **TODO:** Create new standard-compliant `Algs.Rw` and `Algs.r` (WCA standard: 2 outermost layers)
  - `Rw` = `r` = 2 layers (identical per WCA standard, `Rw` is official WCA form)
  - Support `nRw` / `nr` prefix for n layers (e.g., `3Rw` = `3r` = 3 layers)
  - Support all slice forms: `Rw'`, `Rw2`, `3Rw'`, `3r2`, etc.
  - Same for all 6 faces: L, U, D, F, B
  - Add to `Algs.Simple` list and scrambler
  - Add to parser tests (bring back `Rw`, `r`, `3Rw`, `3r` etc.)
  - Parser: bare `Rw`/`r` → new standard 2-layer (non-compat mode)
  - Parser: bare `Rw`/`r` → `Algs.RRw`/`Algs.rr` all-but-last (compat mode)
  - Document everything in `algorithm_notation.md` and `README.md`
