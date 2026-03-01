# Session: centers-alg-align — Direct Source Iteration for NxNCenters

## Goal
Optimize `NxNCenters.__do_center()` to iterate all source faces directly (like `_LBLNxNCenters`) instead of bringing adjacent faces to UP via `B[1:n]` rotations.

## Phase 1 (this session): Commutator/block path + skip empty faces for slices

### Plan Summary
1. Refactor `_block_commutator()` — remove UP/BACK constraint, use CommutatorHelper dry_run for natural source coords
2. Refactor `_search_block()` — use dry_run instead of `_is_block`/`_2d_range_on_source`
3. Refactor `_do_blocks()` — remove `_point_on_source` calls
4. Create `_do_center_from_face_direct()` — accepts any source face for commutator/block path
5. Refactor `__do_center()` — two phases: (a) complete slices with bring-to-UP but skip empty, (b) commutator/block with direct iteration
6. Clean up dead code: `_point_on_source`, `_point_on_target`, `_2d_range_on_source`, `_bring_face_up_preserve_front`
7. Add Phase 2 TODO for complete slice swap with all source faces

### Key Files
- `src/cube/domain/solver/common/big_cube/NxNCenters.py` — main changes
- `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py` — reference patterns
- `__todo.md` — add Phase 2 TODO

### Key Reference Patterns (from _LBLNxNCenters)
- Direct source iteration: `target_face.other_faces()`, skip if `count_color_on_face == 0`
- Dry-run for natural source coords: `execute_commutator(dry_run=True)` → `natural_source_block`
- Rotation search: 4 rotations of source_block with `rotate_clockwise(n_slices)`

### Status
- [x] _block_commutator refactored — uses dry_run, no UP/BACK constraint
- [x] _search_block_via_dry_run created — replaces _search_block, uses natural source coords
- [x] _do_blocks refactored — searches unsolved blocks on target face
- [x] _do_center_from_face_direct created — commutator/block for any source face
- [x] _do_complete_slices_from_face created — slice swap + odd-cube face swap (UP/BACK only)
- [x] __do_center refactored — two-phase: complete slices + direct source iteration
- [x] Dead code removed: _do_center_from_face, _search_block, _execute_commutator, _point_on_source, _2d_range_on_source
- [x] _is_block simplified — removed dont_convert_coordinates parameter
- [x] todo_new_entries.md updated with Phase 2 TODO (A4)
- [x] ruff, mypy, pyright all pass

### Awaiting
- User review of changes before running tests

### Commits
(none yet)
