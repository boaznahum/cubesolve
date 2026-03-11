# Session: credit-and-info branch

## Goal
Add credits/info popup and various UX improvements.

## Completed Work

### Allow solver switch without resetting cube (2026-03-08)
- **Problem:** Changing solver dropdown reset the cube to solved state and cleared all history. Frustrating if you scramble and want to try a different solver.
- **Fix:** Replaced `op.reset()` with `op.clear_redo()` in three places:
  - `src/cube/presentation/gui/commands/concrete.py` — `SwitchSolverCommand` and `SwitchToSolverCommand`
  - `src/cube/presentation/gui/backends/webgl/ClientSession.py` — `_handle_solver()`
- **Result:** Cube state and history preserved, only redo queue cleared (old solver's solution invalid for new solver)
- **Tested in Chrome:** Scramble → Solve → Stop → Switch solver (Beginner Reducer → CFOP) → Solve again → Cube solved successfully
- **Version:** bumped to 1.44
- **Commit:** `6adbe048` — "Allow solver switch without resetting cube"

### Previous commits on this branch
- `058a57ea` — Add author info header to info popup
- `c2befc13` — Rewrite user guide: common/desktop/mobile structure
- `8ae54389` — Add info popup with credits and user guide
- `60da6858` — Fix paint mode state machine bugs and disable buttons during solving

## Key Observations
- Solver select dropdown is properly disabled during solve (confirmed via DOM check)
- `Operator.clear_redo()` already existed at line 266 of `Operator.py` — no new method needed
- Size change, reset button, and reset_session still do full reset (correct behavior)
