# Notation Fix 3

## Goal
Align algorithm notation with WCA standards. Introduce proper M/E/S notation and standard wide moves.

## Completed Steps

### Phase 1: Remove deprecated MM() method
- Removed `_MM` field, `MM()` static method, unused `warnings` import from `Algs.py`
- Replaced `Algs.MM()` -> `Algs.M.prime` in `NxNCenters.py`

### Phase 2: Rename M -> MM (all middle slices)
- `Algs.M` (type `_M`) renamed to `Algs.MM` throughout codebase
- `_M._add_to_str` overridden to display `[:]M` instead of `M`
- Parser handles `[:]M` -> `Algs.MM` (unsliced, all middle slices)

### Phase 3: New MiddleSliceAlg class
- Created `src/cube/domain/algs/MiddleSliceAlg.py` - single middle slice, `str()` = `"M"`
- `Algs.M = MiddleSliceAlg()` added to `Algs.py`
- Parser: bare `"M"` -> MiddleSliceAlg, `"[:]M"` -> `Algs.MM`

### Phase 4: Fix solver test failures (compat_3x3 flag)
- Added `compat_3x3` flag to `parse_alg()` and `Algs.parse()`
- When `True`, bare "M" stays as `_M` (all slices), bare "Rw"/"r" -> all-but-last

### Phase 5A: Rename Rw -> RRw, r -> rr (all-but-last)
- Renamed all 12 adaptive wide moves: `Algs.Rw` -> `Algs.RRw`, `Algs.r` -> `Algs.rr`, etc.
- `str()` now outputs `[:-1]Rw` / `[:-1]r` (Python-style all-but-last notation)
- Parser handles `[:-1]Rw` -> all-but-last, compat mode maps bare `Rw`/`r` -> all-but-last

### Phase 5B: New WideLayerAlg class (WCA standard)
- Created `src/cube/domain/algs/WideLayerAlg.py` for standard `nRw`/`nr` notation
- `Rw`/`r` = 2 outermost layers (WCA default), `3Rw`/`3r` = 3 layers, `nRw`/`nr` = n layers
- Added `Algs.Rw`, `Algs.r` etc. as WideLayerAlg instances (12 total)
- Added to `Algs.Simple` list and parser

### Phase 5C: Scrambler nRw support
- Scrambler randomly varies WideLayerAlg layer count on cubes > 3x3
- Fixed parser `[` heuristic: `re.match(r'^[\d:,\-]+$')` distinguishes slice `[1:2]M` from sequence `[3Rw ...]`
- Fixed `_Mul.atomic_str()` digit ambiguity: `(r'3)2` not `r'32`

### Phase 5D: Consolidate DoubleLayerAlg + WideFaceAlg -> WideLayerAlg
- Added `ALL_BUT_LAST = -1` sentinel to WideLayerAlg
- `_effective_layers()`: returns `cube.size - 1` when `layers == ALL_BUT_LAST`
- `atomic_str()`: returns `[:-1]Rw` / `[:-1]r` when `layers == ALL_BUT_LAST`
- Replaced all `DoubleLayerAlg` and `WideFaceAlg` instances with `WideLayerAlg`
- Deleted `DoubleLayerAlg.py` and `WideFaceAlg.py` (8 classes eliminated)
- `_wide_to_all_but_last()` simplified to `wide.with_layers(ALL_BUT_LAST)`
- Updated `_F2L.py` and `ClientSession.py` to use WideLayerAlg

### Phase 6: Documentation
- Rewrote `docs/algorithm_notation.md` - comprehensive guide with all notation forms
- Updated `README.md` - corrected wide rotation descriptions in keyboard help and command table

## Files Modified

### Deleted
- `src/cube/domain/algs/DoubleLayerAlg.py` (replaced by WideLayerAlg)
- `src/cube/domain/algs/WideFaceAlg.py` (replaced by WideLayerAlg)

### New
- `src/cube/domain/algs/WideLayerAlg.py` - unified wide move class

### Core alg changes
- `src/cube/domain/algs/Algs.py` - all wide move instances now WideLayerAlg
- `src/cube/domain/algs/_parser.py` - nRw prefix, [:-1] handling, compat_3x3
- `src/cube/domain/algs/Mul.py` - digit ambiguity fix in atomic_str()
- `src/cube/domain/algs/Scramble.py` - nRw layer randomization

### Solver/GUI changes
- `src/cube/domain/solver/_3x3/cfop/_F2L.py` - WideLayerAlg import
- `src/cube/presentation/gui/commands/registry.py` - Algs.RRw references
- `src/cube/presentation/gui/backends/webgl/ClientSession.py` - unified WideLayerAlg handling

### Documentation
- `docs/algorithm_notation.md` - full rewrite
- `README.md` - updated keyboard/command descriptions

### Tests
- `tests/parsing/test_parser.py` - nRw, [:-1], default layer count tests (832 total)

## Test Status
- CFOP: 1571 passed
- Parser: 832 passed
- All non-GUI/WebGL: 10035 passed
- GUI: 36 passed
- Static checks: ruff, mypy, pyright all clean

## Future Tasks
- **TODO:** Eliminate `Algs.parse()` usages in solver code - replace with programmatic alg construction
- ~~**TODO:** Add M/E/S to scrambler~~ — done, added to `Algs.Simple` list
- ~~**TODO:** Document E/S notation~~ — already done, E/S use MiddleSliceAlg same as M
