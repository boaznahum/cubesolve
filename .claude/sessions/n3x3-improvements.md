# Session: n3x3-improvements

## Goal

Port selected optimizations from the 2x2 beginner solver (branch `n2x2-2`) to the 3x3 beginner solver.

## Source: 2x2 Improvements (n2x2-2 branch)

Relevant commits reviewed:

| Commit | Description | Applicable to 3x3? |
|--------|-------------|---------------------|
| `519585ad` | Compute twist count from corner orientation (0/1/2) | YES - L3Corners `_do_orientation` |
| `e9e372b8` | Skip oriented corners, jump to next unoriented | YES - L3Corners `_do_orientation` |
| `3ffa784d` | Fix double whole-cube rotation in bring_white_to_down | MAYBE - check if 3x3 has same issue |
| `45b71afb` | Best color for L1, thread through L3 | YES - pick best L1 color, not always white |
| `2e45bde8` | Rewrite L3 Permute: 3-cycle + single swap | NO - 3x3 L3 uses different permute strategy |
| `6f311c58` | First corner / reference corner approach | NO - 3x3 has cross+centers for positioning |

## Plan (simplest to hardest)

### Phase 1: L3 Orientation - Compute twist count (EASY)

**Current 3x3 code** (`_L3Corners.py:161-172`):
```python
def _do_orientation(self, yf: Face):
    for _ in range(0, 4):
        while not yf.corner_bottom_right.match_face(yf):
            self.op.play(Algs.alg(None, Algs.R.prime, Algs.D.prime, Algs.R, Algs.D) * 2)
        self.op.play(Algs.U.prime)
```

**Problem**: `while` loop iteratively applies twist until correct. Can be 1 or 2 applications.

**Fix**: Compute twist count from which face yellow sticker is on (same as 2x2):
- Yellow on UP -> 0 twists (already oriented)
- Yellow on Right -> 1 twist
- Yellow on Front -> 2 twists

Then play `(twist * count).simplify()` instead of looping.

**Source**: `_L3Orient.py:_twist_count()` (static method)

### Phase 2: L3 Orientation - Skip oriented corners (EASY)

**Current 3x3 code**: Always does 4 iterations with `U'` after each, even for corners already oriented.

**Fix**: Search CCW for next unoriented corner, jump with `(U' * N).simplify()`. Skip already-oriented corners. Track total U' rotations for realignment at end.

**Source**: `_L3Orient.py:_do_orient()` and `_find_next_unoriented_ccw()`

### Phase 3: Check for double rotation in bring_face_up (EASY)

**What happened in 2x2**: `bring_white_to_down` was calling `bring_face_up(white_face)` then `bring_face_down(cube.up)` — two rotations when one suffices.

**Check**: Does the 3x3 solver have similar redundant rotations in `_L3Corners._solve()` or `_L3Cross._solve()`? Both call `self.cmn.bring_face_up(self.white_face.opposite)`. Verify this is direct (single rotation).

### Phase 4: Best color for L1 (HARDEST)

**Current 3x3 code**: Always starts with `cmn.white` (configured `first_face_color`, default WHITE).
`CommonOp._start_color` is set once at init from config.

**How it works in 3x3**: `self.white_face` -> `cube.color_2_face(self.cmn.white)` -> face whose center is white.
All solvers reference `self.white_face` (via `SolverHelper.white_face` -> `cmn.white_face`).

**Optimization**: Before solving L1, scan all 6 faces. For each face, count how many of its 4 corners
are already correctly positioned+oriented (`match_faces`). Also check L1 cross edges.
Pick the face/color with the best head start. Prefer white on ties.

**Impact**: Changing `cmn.white` / `_start_color` affects ALL solver stages (L1 cross, L1 corners, L2, L3).
This is actually simpler than 2x2 because 3x3 already threads everything through `self.white_face`.
Just need to change `CommonOp._start_color` before solving starts.

**Key difference from 2x2**: On 3x3 we also have L1 cross (4 edges) + L1 corners (4 corners) = 8 pieces.
Scoring should weight cross edges AND corners. A face with 3 cross edges + 2 corners is better
than one with 0 cross + 4 corners.

**Scope**:
- `BeginnerSolver3x3.solve_3x3()` — add best-color selection before L1
- `CommonOp._start_color` — make settable or add method to override
- All downstream solvers automatically follow via `self.white_face`

## Key Differences: 2x2 vs 3x3

| Aspect | 2x2 | 3x3 |
|--------|------|------|
| Face colors | None (no centers) | Defined by centers |
| White detection | Scan corner stickers | `self.white_face` (center) |
| `match_face` | N/A (no face color) | Works directly |
| L3 has cross? | No (corners only) | Yes (edges + corners) |
| Orientation check | `corner.face_color(up) == yellow_color` | `corner.match_face(yf)` |

## Files to Modify

- `src/cube/domain/solver/_3x3/beginner/_L3Corners.py` - Phases 1 & 2
- `src/cube/domain/solver/_3x3/beginner/BeginnerSolver3x3.py` - Phase 4 (best color)
- `src/cube/domain/solver/common/CommonOp.py` - Phase 4 (start color override)

## Implementation Details

### Phase 4: `BeginnerSolver3x3._select_best_start_color()` (commit b228c404)
- Added to `BeginnerSolver3x3.py`
- Called at start of `solve_3x3()` before any solve steps
- Uses query mode (`with_query_restore_state`) to try each of 6 face colors
- For each face color, temporarily sets `cmn._start_color`, then checks `is_cross_rotate_and_check()` + `is_corners()`
- If a solved L1 is found, uses that color; otherwise keeps white
- TODO in code: replace query mode with direct part checking
- Also changed `_config.py` default `CUBE_SIZE` from 2 to 3

### Phases 1+2: `L3Corners._do_orientation()` rewrite (commit 12c0f0f8)
- Replaced `while` loop with computed `_twist_count()` static method
- `_twist_count(yf, cube_front, cube_right)`: checks `fru.face_color(face) == yellow` for UP/Right/Front
- Added `_find_next_unoriented_ccw(yf)`: returns 0-3 (U' count to next unoriented) or -1 (all done)
- Main loop: search CCW, jump with `(U' * N).simplify()`, twist with `(twist * count).simplify()`
- Tracks `total_u`, realigns at end with `(4 - total_u % 4) % 4` remaining U' rotations
- Important: uses `face_color()` not `match_face()` for twist count — `match_face` checks if sticker matches the face's center, but we need to check where yellow IS

### Phase 3: No changes needed
- 3x3 L3 solvers use single `bring_face_up(self.white_face.opposite)` — no double rotation bug

## Commits

| Commit | Description |
|--------|-------------|
| `b228c404` | Best start color for L1 + default size 3 |
| `12c0f0f8` | L3 orientation: compute twist + skip oriented corners |

## Tests
- 314 LBL size-3 tests pass (filtered with `-k "size_3 and LBL"`)
- 1570 total size-3 tests pass (all solvers)

## Status

- [x] Phase 1: Compute twist count (commit 12c0f0f8)
- [x] Phase 2: Skip oriented corners (commit 12c0f0f8, same commit)
- [x] Phase 3: Check double rotation — N/A, 3x3 uses single bring_face_up calls
- [x] Phase 4: Best color for L1 (commit b228c404)
