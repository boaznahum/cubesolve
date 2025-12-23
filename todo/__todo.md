# Project TODO

## Open Tasks Summary

| ID | Category | Priority | Title                                                   | Status |
|----|----------|----------|---------------------------------------------------------|--------|
| B1 | Bug | HIGH | GUI Animation Solver Bug (Lazy Cache Initialization)    | Investigating |
| B5 | Bug | MEDIUM | Missing debug output when running with `--debug-all`    | Open |
| B6 | Bug | MEDIUM | Celebration effect triggers on reset/resize             | Open |
| B8 | Bug | MEDIUM | Default texture shows wrong face colors                 | Open |
| B9 | Bug | MEDIUM | Solve completes instantly (animation skipped)           | Open |
| B10 | Bug | MEDIUM | Markers don't show source/destination during commutator | Open |
| B11 | Bug | MEDIUM | Axes disapeared when moving to pyglet2                  | Open |
| G2 | GUI | LOW | Investigate pyopengltk for tkinter backend              | Open |
| G5 | GUI | MEDIUM | Comprehensive Command Testing Plan                      | Open |
| G6 | GUI | LOW | Additional lighting improvements (pyglet2)              | Open |
| G7 | GUI | IN PROGRESS | Texture mapping for cube faces                          | In Progress |
| G8 | GUI | IN PROGRESS | 3D Arrows for solver annotations                        | In Progress |
| A7 | Architecture | MEDIUM | Investigate circular import issues                      | Open |
| A8 | Architecture | MEDIUM | No code leak outside backends layer                     | Open |
| A10 | Architecture | HIGH | Check for _config direct imports in presentation layer  | Open |
| A9 | Architecture | MEDIUM | Centralize animation handling                           | Done |
| D1 | Documentation | LOW | Improve keyboard_and_commands.md diagram                | Open |
| Q5 | Quality | LOW | Review all `# type: ignore` comments                    | Open |
| Q6 | Quality | LOW | Evaluate `disable_error_code = import-untyped`          | Open |
| Q7 | Quality | LOW | Add type annotations to lambda callbacks                | Open |
| Q9 | Quality | LOW | Clean up dead code debug prints in solver               | Open |
| Q10 | Quality | LOW | Relocate `debug_dump()` to better location              | Open |
| Q13 | Quality | LOW | Evaluate pyright strict mode                            | Open |
| Q14 | Quality | MEDIUM | Fix vs.debug() performance issue                        | Open |
| Q15 | Quality | LOW | Clean up protected member access warnings               | Open |
| Q16 | Quality | MEDIUM | Clean up all dead code (vulture)                        | Open |
| S1 | Solver | MEDIUM | Unify tracker cleanup code                              | Open |
| S2 | Solver | LOW | Cage face creation duplication                          | Open |
| S3 | Solver | HIGH | OpAnnotation marker cleanup fails during OpAborted      | Open |

---

> **Instructions for updating this file:**
>
> **Symbols (Windows: `Win + .` to open emoji picker):**
> - ❌ Not started - search "cross" or "x mark"
> - ♾️ In progress - search "infinity"
> - ✅ Completed - search "check"
>
> **Related files:**
> - `todo/todo_completed.md` - Completed tasks history
> - `todo/todo_open.md` - Master list of all open tasks (detailed)
> - `todo/todo_code_comments.md` - TODO comments found in source code
> - `todo/__dead_code.md` - Dead code cleanup list
>
> **Claude instructions:**
> - Update the summary table above when adding/completing tasks
> - When starting work, change status to ♾️ BEFORE beginning
> - When done, move task to `todo/todo_completed.md`, preserving ID
> - Check existing IDs (including completed) to avoid duplicates
> - After code changes: run mypy, pyright, then tests

---

## Bugs

- ❌ **B1.** GUI Animation Solver Bug (Lazy Cache Initialization) [HIGH]
  - **Status:** Investigating (2025-11-28)
  - **Skipped Test:** `test_multiple_scrambles` in `tests/gui/test_gui.py`
  - **Root Cause:** Lazy initialization of `colors_id`/`position_id` + timing issues during animation
  - **Workaround:** Use `--speed-up 5` in tests
  - **Key Files:** `Part.py:221-273`, `_part_slice.py:213-245`, `L3Cross.py:178`

- ❌ **B5.** Missing debug output when running with `--debug-all`
  - **Status:** Open (2025-12-02)
  - **Files:** `config.py`, `Command.py`, `Operator.py`

- ❌ **B6.** Celebration effect triggers on reset/resize
  - **Status:** Open (2025-12-02)
  - **Root Cause:** Triggers when `cube.is_solved` becomes True, not checking if scrambled first

- ❌ **B8.** Default texture shows wrong face colors (YELLOW on front instead of WHITE)
  - **Status:** Open
  - **Related to:** G7 texture work

- ❌ **B9.** Solve completes instantly (animation skipped)
  - **Status:** Open (2025-12-23)
  - **Symptom:** Sometimes when solving, cube goes directly to solved state without animation
  - **Likely cause:** Animation not enabled or DualOperator/shadow cube issue

- ❌ **B10.** Markers don't show source/destination during commutator
  - **Status:** Open (2025-12-23)
  - **Symptom:** During commutator algorithm, markers should show which pieces are source/destination
  - **Related to:** OpAnnotation, DualAnnotation, marker rendering

- ❌ **B11.** Axes disappeared when moving to pyglet2
  - **Status:** Open (2025-12-23)
  - **Symptom:** Axes visual display disappeared when using pyglet2 modern GL backend
  - **Related to:** pyglet2 modernGL renderer, axis rendering

---

## GUI & Testing

- ❌ **G2.** Investigate pyopengltk as alternative to pure Canvas rendering for tkinter backend
  - Would allow reusing OpenGL code from pyglet backend

- ❌ **G5.** Comprehensive Command Testing Plan
  - **Phase 1:** Automated keyboard command tests (`test_all_commands.py`)
  - **Phase 2:** Manual mouse testing documentation

- ❌ **G6.** Additional lighting improvements (pyglet2 backend)
  - Fill light, specular control, light position control

- ♾️ **G7.** Texture mapping for cube faces (custom images)
  - **Status:** In progress (2025-12-02)
  - **Approach:** Hardcoded sample images first
  - **Files:** `ModernGLRenderer.py`, `ModernGLCubeViewer.py`

- ♾️ **G8.** 3D Arrows for solver annotations
  - **Status:** In progress (2025-12-23)
  - **Current State:** Basic implementation complete but needs improvement
    - Arrows show source-to-destination direction during solve
    - Bright gold color (configurable via ArrowConfig)
    - Grow animation from source to destination
    - Source position updates during piece rotation
    - ArrowConfigProtocol defined in config_protocol.py (architecture-compliant)
  - **Known Issues:**
    - Arrow endpoints may not connect properly in all cases
    - Need to verify arrow is visible above cube surface
    - Animation timing may need tuning
  - **Future Improvements:**
    - Curved arrow style (Bezier)
    - Compound arrow style (multiple segments)
    - Better endpoint matching (by part_slice identity)
    - Fade/pulse animation options
    - Read config values dynamically from ArrowConfigProtocol in _modern_gl_arrow.py
  - **Config:** `_config.py` has `ArrowConfig` dataclass, accessed via `config.arrow_config`
  - **Files:** `_modern_gl_arrow.py`, `_modern_gl_board.py`, `ModernGLCubeViewer.py`, `config_protocol.py`

---

## Architecture

- ❌ **A7.** Investigate and document circular import issues
  - **Status:** Open (2025-12-07)
  - **Affected:** `application/__init__.py`, `animation/__init__.py`, `domain/__init__.py`

- ❌ **A8.** Ensure no code leaks outside backends layer
  - **Status:** Open
  - All backend-specific code should be in backends folder

- ❌ **A10.** Check for _config direct imports in presentation layer [HIGH]
  - **Status:** Open (2025-12-23)
  - **Rule:** `_config.py` must ONLY be accessed via ConfigProtocol
  - **Check:** `grep -r "from cube.application import _config" src/cube/presentation`
  - **Check:** `grep -r "from cube.application._config" src/cube/presentation`
  - Any matches are architecture violations that must be fixed

- ✅ **A9.** Centralize animation handling
  - **Status:** Done (2025-12-23)
  - Implemented Template Method pattern in `AbstractSolver.solve()`
  - All solvers now inherit `with_animation()` wrapper and `OpAborted` handling
  - Solvers implement `_solve_impl()` instead of `solve()`

---

## Documentation

- ❌ **D1.** Improve keyboard_and_commands.md diagram clarity
  - Make Part 1 (native handlers) vs Part 2 (unified path) visually clear

---

## Code Quality

- ❌ **Q5.** Review all `# type: ignore` comments and document why they're needed

- ❌ **Q6.** Evaluate if `disable_error_code = import-untyped` hides real problems

- ❌ **Q7.** Add type annotations to untyped lambda callbacks
  - Files: `tkinter/event_loop.py:34-35`, `tkinter/renderer.py:580`

- ❌ **Q9.** Clean up dead code debug prints in solver
  - `L1Cross.py:__print_cross_status()`, `NxnCentersFaceTracker.py:_debug_print_track_slices()`

- ❌ **Q10.** Relocate `debug_dump()` from `main_any_backend.py` to better location

- ❌ **Q13.** Evaluate pyright strict mode (1905 errors)
  - **Decision:** Stay with "standard" mode for now

- ❌ **Q14.** Fix vs.debug() performance issue with template strings
  - Use constant strings or `vs.debug_lazy()` for expensive computations

- ❌ **Q15.** Clean up protected member access warnings in CageNxNSolver.py
  - **Status:** Open (2025-12-20)

- ❌ **Q16.** Clean up all dead code using vulture
  - **Status:** Open (2025-12-21)
  - **See:** `todo/__dead_code.md` for detailed list

---

## Solver

- ❌ **S1.** Unify tracker cleanup code
  - **See:** `docs/design/TODO_tracker_cleanup.md`
  - Unify `NxNCentersFaceTrackers` and `FaceTrackerHolder`

- ❌ **S2.** Cage face creation duplication
  - Code duplicated in reducer, uses tracer methods
  - Ensure third center uses majority

- ❌ **S3.** OpAnnotation marker cleanup fails during OpAborted [HIGH]
  - **Status:** Open (2025-12-23)
  - **File:** `src/cube/application/commands/OpAnnotation.py:169`
  - **Repro:** Scramble → Solve with animation → Press ESC mid-solve
  - **See:** `src/cube/domain/solver/__todo_solvers.md` for details and solutions

---

## Completed Tasks

**See:** `todo/todo_completed.md` for all completed tasks with details.

Quick reference (recent completions):
- A1-A6: Architecture improvements (all done)
- B2-B4, B7: Bug fixes (all done)
- G1, G3-G4: GUI improvements (all done)
- Q1-Q4, Q8, Q11-Q12: Quality improvements (all done)
