# Session: lbl-crash (Issue #119)

## Task
Fix GitHub issue #119: Big LBL solver crashes with "Shadow cube L1 cross not solved after solve_3x3" assertion on certain scrambles.

## Root Cause

The `BeginnerSolver3x3._select_best_start_color()` auto-detects which face to use as L1 by grading all 6 faces. When called on a **shadow 3x3 cube** (created by the Big LBL solver for NxN cubes), it may pick a **non-white** start color if another face has a higher L1 grade.

The Big LBL solver (`DirectLayerByLayerNxNSolver._solve_layer1_with_shadow`) then checks:
```python
shadow_l1 = shadow_cube.color_2_face(self.cmn.white)  # expects WHITE
assert all(e.match_faces for e in shadow_l1.edges)      # but beginner solved BLUE
```
This assertion fails because the beginner solver solved a different face's cross.

### Why it was hard to reproduce

1. The bug only triggers when `_select_best_start_color` picks non-white, which depends on the shadow cube's scramble state
2. With only 300 seeds in the test suite, the probability of hitting a failing configuration was low
3. Running individual tests in isolation passes -- the bug is more likely with xdist where `CommutatorHelper._test_result_index` (a class-level variable) can get corrupted by geometry tests on the same worker, changing which translation path the solver takes

### Key insight: `cmn.white` is misleading

In the solver codebase, `cmn.white` doesn't mean the color white -- it means "the start color" (L1 face color). The Big LBL solver's `cmn.white` is actual white, but the beginner solver's `cmn.white` can be overridden by `_select_best_start_color()`. Two different `cmn` instances, two different "white" values.

## Fix

Added `forced_start_color` attribute to `BeginnerSolver3x3`:
- When set (non-None), `_select_best_start_color()` skips auto-detection and uses the forced color
- `_solve_layer1_with_shadow()` sets `shadow_solver.forced_start_color = self.cmn.white` before running

This ensures the shadow solver always solves the face the Big LBL solver expects.

### Files modified
- `src/cube/domain/solver/_3x3/beginner/BeginnerSolver3x3.py` -- added `forced_start_color` slot and parameter
- `src/cube/domain/solver/direct/lbl/DirectLayerByLayerNxNSolver.py` -- sets forced color on shadow solver
- `tests/sequences/s1_3000.txt` -- new 3000-seed file (extends s1_1000.txt with same base seed)
- `tests/solvers/conftest.py` -- increased seed count from 300 to 3000

## Coverage

`_solve_layer1_with_shadow` is the single entry point for ALL shadow solving:
- `SolveStep.L1x` (L1 cross)
- `SolveStep.L1` (L1 cross + corners)
- `SolveStep.L3x` (L3 cross -- calls through same method)
- `SolveStep.L3` (L3 corners -- calls through same method)

L3 = opposite of L1, so forcing L1 = white means L3 = yellow (correct).

## Test results

- Before fix: 2 failures in 78K tests with xdist + 1000 seeds
- After fix: **78,965 passed, 0 failed** with xdist + 3000 seeds (15 min run)

## Note: CageNxNSolver may have the same issue

`CageNxNSolver._solve_3x3_with_shadow()` also uses `Solvers3x3.beginner()` / `Solvers3x3.by_name()` on a shadow cube without forcing the start color. Same bug could manifest there. Not addressed in this session.

## Status: IN PROGRESS
- Fix implemented and verified with 3000 seeds
- User is running their own test pass
- Not yet committed
