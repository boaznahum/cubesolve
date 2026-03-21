# Session: notation-mess branch

## Goal
Overhaul the summary table in `docs/algorithm_notation.md` to be the definitive reference, cross-referenced against 3 standard sources (Twizzle, MZRG, SS Wiki) and verified with tests.

## Key Files Modified
- `docs/algorithm_notation.md` — single HTML summary table
- `tests/parsing/test_doc_table.py` — 144 tests verifying every row
- `src/cube/domain/algs/FaceAlgBase.py` — play() n_max fix for opposite face
- `src/cube/domain/model/Cube.py` — rotate_face_and_slice handles opposite face index
- `src/cube/presentation/gui/commands/concrete.py` — F1-F5 debug logging + error logging
- `src/cube/resources/algs/__init__.py` — split load_file_content / parse_file_content
- `src/cube/utils/logger.py` — added logger.error() bypasses quiet_all
- `src/cube/utils/logger_protocol.py` — error() method in protocol

## Fixes Implemented

### Opposite face spanning (⑨⑩ — FIXED)
- `4R` on 4×4 now equals `L'` (opposite face rotated in R direction)
- `[3:4]R` on 4×4 now works: decomposes to `3R + L'`
- Fixed in `FaceAlgBase.play()`: `n_max=cube.size` instead of `1+n_slices`
- Fixed in `Cube.rotate_face_and_slice()`: handles `i == size-1` as opposite face
- Fixed in `Cube.get_rotate_face_and_slice_involved_parts()`: same
- Assertion in `get_face_and_rotation_info` updated to `0 <= i <= size-1`
- Tested for ALL 6 faces × 3 sizes (3×3, 4×4, 5×5)

### F1-F5 debug logging
- `load_file_alg` split into `load_file_content` + `parse_file_content`
- Logs raw file content BEFORE parsing (so you see it even on parse errors)
- Uses `solver_debug` flag (not hardcoded True)
- Errors use `logger.error()` which bypasses `quiet_all`
- Format: `--- BEGIN f1.txt ---\n<content>\n--- END f1.txt ---\nParsed: <alg>`

### logger.error()
- New method on Logger and LoggerProtocol
- Always prints to console AND webgl streams
- Ignores `quiet_all` — errors should never be suppressed

## Table Structure
Single HTML table. Columns: Description/Effect | Twizzle | MZRG | SS Wiki | Code | str() | Parser (input) | Parser (3×3 mode)

6 groups:
1. **Face Moves** — R, R', R2
2. **Inner Slices** — 2R, 3R, 4R(=L'), [3:4]R, [3:]R, [:4]R + range rows
3. **Wide Moves** — Rw/r, 3Rw/3r, [:-1]Rw/rr, 3-4Rw, 3-4r
4. **Slice Moves** — M, [:]M
5. **Slice Range & Indexing** — [1:2]R, [2:3]R, [1]M, [1:2]M, [1:]M
6. **Whole Cube Rotations** — X, Y, Z

## Tests (144 passed, 27 skipped, 2 xfailed)
- `TestDocTable.test_code_vs_parser` — code API vs parser equivalence
- `TestDocTable.test_str_round_trip` — str(code) == str(parsed) == expected
- `TestDocTable.test_equivalent_decomposition` — range/wide moves verified against primitive decomposition (e.g. [3:4]R == 3R+4R)
- `TestDocTable.test_compat_3x3_str` — compat_3x3 mode produces expected str
- `TestSpecialCases` — Rw≡r, [1:2]R≡Rw, 2L≡M, M≡MM on 3x3, M≠MM on 5x5, 3Rw clamping, Rw vs adaptive, opposite face for all 6 faces × 3 sizes, [3:4]R spans opposite on 4×4

## Twizzle Verification (user manually checking)
- ✅ `Rw`, `r` — verified (Twizzle also supports spanning)
- ✅ `3Rw`, `3r` — verified (Twizzle also supports spanning)
- ✅ `R` — verified
- ✅ `3-4R`, `3-4Rw`, `3-4r` — verified on Twizzle
- Remaining rows NOT yet verified

## Remaining Bugs (❌ in table)
- ❌⑦ Parser doesn't support SiGN range syntax (`3-4R`). Use bracket `[3:4]R` instead.
- ❌⑧ Bracket slicing on wide moves (`[3:4]Rw`, `[3:4]r`) not supported. Parser throws InternalSWError. Twizzle supports this.
- Missing `Algs` constants for 3-layer wide moves (table shows `WideLayerAlg(R,3)`)

## Commits
- `46b6e833` — Add verified summary table with standard sources and test coverage
- `b8801f01` — Fix parser column to show input strings, add F1-F5 debug logging
- `eadd0f03` — Add equivalent decompositions, logger.error(), wide bracket bugs
- `0f5c7c72` — Add opposite face span tests and WIP rows
- (pending) — Fix opposite face spanning, update table ✅⑨⑩