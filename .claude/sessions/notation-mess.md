# Session: notation-mess branch

## Goal
Overhaul the summary table in `docs/algorithm_notation.md` to be the definitive reference, cross-referenced against 3 standard sources (Twizzle, MZRG, SS Wiki) and verified with tests.

## Commits (in order)
- `46b6e833` — Add verified summary table with standard sources and test coverage
- `b8801f01` — Fix parser column to show input strings, add F1-F5 debug logging
- `eadd0f03` — Add equivalent decompositions, logger.error(), wide bracket bugs
- `0f5c7c72` — Add opposite face span tests and WIP rows
- `8929b97e` — Consolidate 3-4R/Rw/r rows in Inner Slices
- `af47c355` — Make WideLayerAlg sliceable, add SiGN range parser, fix animation DRY

## What Was Done

### Summary Table
- Single HTML table in `docs/algorithm_notation.md` with 6 groups: Face Moves, Inner Slices, Wide Moves, Slice Moves, Slice Range & Indexing, Whole Cube Rotations
- Columns: Description/Effect | Twizzle | MZRG | SS Wiki | Code | str() | Parser | Parser (3×3 mode)
- Cross-referenced against 3 standard sources (Twizzle manually verified by user, MZRG/SS Wiki from web research)
- ✅/❌ markers on verified/broken items, footnotes ①-⑩

### Fixes Implemented
1. **Opposite face spanning** — `4R` on 4×4 = `L'`. Fixed `FaceAlgBase._resolve_slices()` with `n_max=cube.size`. Tested all 6 faces × 3 sizes.
2. **DRY refactor** — `FaceAlgBase._resolve_slices()` shared by `play()` and `get_animation_objects()`. `Cube._classify_layers()` shared by rotation and parts collection.
3. **WideLayerAlg sliceable** — inherits `SliceAbleAlg`, `__getitem__` returns `SlicedFaceAlg`. `Rw[3:4]` == `R[3:4]`.
4. **SiGN range parser** — `3-4R`, `3-4Rw`, `3-4r` now parsed (regex in `_parser.py`).
5. **Scramble** — WideLayerAlg now included in slice generation.
6. **F1-F5 debug logging** — split `load_file_content`/`parse_file_content`, logs raw content before parsing, errors via `logger.error()` (bypasses quiet_all).
7. **WebGL animation fix** — `ClientSession` n_max patched to `cube.size`.

### Tests: 161 passed, 32 skipped, 1 xfailed
- `TestDocTable` — code vs parser, str round-trip, equivalent decomposition, compat_3x3
- `TestSpecialCases` — opposite face all 6 faces × 3 sizes, Rw≡r, [1:2]R≡Rw, 2L≡M, M≡MM on 3x3, clamping, wide slicing, SiGN range parsing
- Equivalents use `Algs.parse()` for decomposition (independent code path, not same slicing mechanism)

## Known Bugs (remaining)
1. **`[:]R` returns just `R`** — should be all layers (≡ X). xfail test exists. Next session fix.
2. **#141: n_max duplication** — WebGL `ClientSession` calls `normalize_slice_index` directly instead of using `_resolve_slices()`. Patched but not DRY.
3. **SiGN range on M/E/S** — `2-3M` not tested, may or may not work.

## Twizzle Verification Status
- ✅ Rw, r, 3Rw, 3r, R, 3-4R, 3-4Rw, 3-4r
- ❌ 3Rw/3r: no span in Twizzle (error on 3×3)
- ? remaining rows (M, m, 2R, 3R, X/Y/Z, [3:]R, [:3]R, etc.)

## Current Session (2026-03-22) — Putting Order in the Table

### Row Numbers Added
Added WIP row numbers (#) column to summary table for easy reference during cleanup.
Can use non-whole numbers (e.g., 6.5) to insert rows between existing ones.

| # | Group | Description |
|---|-------|-------------|
| 1 | Face Moves | R CW |
| 2 | Face Moves | R' CCW |
| 3 | Face Moves | R2 180° |
| 4 | Inner Slices | 2R (2nd layer) |
| 5 | Inner Slices | 3R (3rd layer) |
| 6 | Inner Slices | 4R on 4×4 ≡ L' (opposite face) |
| 7 | Inner Slices | 3-4R SiGN range |
| 8 | Inner Slices | [3:]R (3rd to last) |
| 9 | Inner Slices | [:]R = all layers ≡ X |
| 10 | Inner Slices | [:3]R (layers 1-3) |
| 11 | Wide Moves | Rw/r (2 layers) |
| 12 | Wide Moves | 3Rw/3r (3 layers) |
| 13 | Wide Moves | [:-1]Rw adaptive (all-but-last) |
| 14 | Slice Moves | M single center slice |
| 15 | Slice Moves | [:]M all inner slices |
| 16 | Slice Range | [1:2]R = Rw |
| 17 | Slice Range | [2:3]R |
| 18 | Slice Range | [1]M single slice |
| 19 | Slice Range | [1:2]M |
| 20 | Slice Range | [1:]M = [:]M |
| 21 | Whole Cube | X (like R) |
| 22 | Whole Cube | Y (like U) |
| 23 | Whole Cube | Z (like F) |

### TODO — Table Cleanup
- Reorganize/reorder rows as needed
- Fix any mess/inconsistencies user wants addressed
- Continue Twizzle verification
- Fix `[:]R` bug (already done in `1d91b16f`)
- Consider DRY cleanup for #141
