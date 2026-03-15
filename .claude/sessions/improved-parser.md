# Session: improved-parser

## Goal
Add a multi-line parser preprocessor that supports:
1. **Variable assignments**: `$setup = X Y L R`
2. **Variable references**: `$setup` expands inline
3. **Prime of variables**: `$setup'` → inverse of the expanded alg
4. **Integer variables + expressions**: `$I = 1`, `[$I:$I+1]M2` → `[1:2]M2`
5. **Repetition**: `$corner * $n` or `$corner * 5`

## Architecture
- **Preprocessor layer** — sits between `parse_multiline()` and `parse_alg()`
- Does NOT modify the token-level parser (`_parser.py`)
- New file: `src/cube/domain/algs/_multiline_parser.py`
- Updates `Algs.parse_multiline()` to use the new preprocessor
- WebGL AlgEditor: `<input>` → `<textarea>` for multi-line support
- Server-side: `_handle_parse_alg` / `_handle_edit_play` / `_handle_edit_ok` use `parse_multiline`

## Files to modify
1. `src/cube/domain/algs/_multiline_parser.py` — NEW: preprocessor
2. `src/cube/domain/algs/Algs.py` — update `parse_multiline`
3. `src/cube/presentation/gui/backends/webgl/static/index.html` — textarea
4. `src/cube/presentation/gui/backends/webgl/static/js/AlgEditor.js` — textarea support
5. `src/cube/presentation/gui/backends/webgl/static/styles.css` — textarea styling
6. `src/cube/presentation/gui/backends/webgl/ClientSession.py` — use parse_multiline
7. `tests/parsing/test_multiline_parser.py` — NEW: tests

## Status
- [ ] Preprocessor implementation
- [ ] Algs.parse_multiline update
- [ ] WebGL textarea + server changes
- [ ] Tests
- [ ] All checks pass

## Commits
(none yet)
