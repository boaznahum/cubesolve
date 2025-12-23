# Open Tasks

This is the master list of all open tasks. Last updated: 2025-12-23

---

## Summary Table

| ID | Category | Priority | Title | Status |
|----|----------|----------|-------|--------|
| B1 | Bug | HIGH | GUI Animation Solver Bug (Lazy Cache) | Investigating |
| B5 | Bug | MEDIUM | Missing debug output with `--debug-all` | Open |
| B6 | Bug | MEDIUM | Celebration effect triggers incorrectly | Open |
| B8 | Bug | MEDIUM | Default texture shows wrong face colors | Open |
| G2 | GUI | LOW | Investigate pyopengltk for tkinter | Open |
| G5 | GUI | MEDIUM | Comprehensive Command Testing Plan | Open |
| G6 | GUI | LOW | Additional lighting improvements (pyglet2) | Open |
| G7 | GUI | IN PROGRESS | Texture mapping for cube faces | In Progress |
| A7 | Architecture | MEDIUM | Circular import investigation | Open |
| A8 | Architecture | MEDIUM | No code leak outside backends layer | Open |
| A9 | Architecture | MEDIUM | Centralize animation handling | Open |
| D1 | Documentation | LOW | Improve keyboard_and_commands.md diagram | Open |
| Q5 | Quality | LOW | Review all `# type: ignore` comments | Open |
| Q6 | Quality | LOW | Evaluate `disable_error_code = import-untyped` | Open |
| Q7 | Quality | LOW | Add type annotations to lambda callbacks | Open |
| Q9 | Quality | LOW | Clean up dead code debug prints in solver | Open |
| Q10 | Quality | LOW | Relocate `debug_dump()` to better location | Open |
| Q13 | Quality | LOW | Evaluate pyright strict mode | Open |
| Q14 | Quality | MEDIUM | Fix vs.debug() performance issue | Open |
| Q15 | Quality | LOW | Clean up protected member access warnings | Open |
| Q16 | Quality | MEDIUM | Clean up all dead code (vulture) | Open |
| S1 | Solver | LOW | CFOP parity detection | Open |
| S2 | Solver | LOW | advanced_edge_parity flag evaluation | Open |
| S3 | Solver | MEDIUM | Unify tracker cleanup code | Open |
| S4 | Solver | LOW | Cage face creation duplication | Open |

---

## Bugs

### B1. GUI Animation Solver Bug (Lazy Cache Initialization) [HIGH]
- **Status:** Investigating (2025-11-28)
- **Skipped Test:** `test_multiple_scrambles` in `tests/gui/test_gui.py` (re-enable when fixed)
- **Symptom:** GUI tests fail with `AssertionError` when running with animation at default speed (`--speed-up 0`), but pass when `+` (speed-up) keys are pressed first.
- **Reproduce:**
  ```bash
  # FAILS:
  pytest tests/gui/test_gui.py::test_scramble_and_solve -v --speed-up 0 --backend pyglet
  # PASSES:
  pytest tests/gui/test_gui.py::test_scramble_and_solve -v --speed-up 5 --backend pyglet
  ```
- **Root Cause:** Lazy initialization and caching of cube piece properties (`colors_id`, `position_id` in `Part` and `PartSlice` classes) combined with timing issues during animation.
- **Key Files:**
  - `src/cube/domain/model/Part.py` lines 221-273
  - `src/cube/domain/model/_part_slice.py` lines 213-245
  - `src/cube/domain/model/cube_slice.py` line 230
  - `src/cube/domain/solver/beginner/L3Cross.py` line 178
- **Workaround:** Use `--speed-up 5` in tests

### B5. Missing debug output when running with `--debug-all` [MEDIUM]
- **Status:** Open (2025-12-02)
- **Symptom:** When running with `debug=True` or `--debug-all`, many expected debug messages are missing:
  - Algorithm execution (e.g., R, L, U face rotations)
  - Command execution (which command was triggered by which key)
  - Keyboard input events (KEYBOAD_INPUT_DEBUG flag exists but is never used)
- **Files to investigate:**
  - `src/cube/application/config.py` - KEYBOAD_INPUT_DEBUG flag
  - `src/cube/presentation/gui/Command.py` - command execution
  - `src/cube/application/commands/Operator.py` - algorithm execution

### B6. Celebration effect triggers on reset/resize [MEDIUM]
- **Status:** Open (2025-12-02)
- **Symptom:** Celebration effect triggers when:
  - Resetting the cube (Escape key)
  - Changing cube size (+/- size commands)
  - Other scenarios where cube becomes "solved" without actually solving
- **Expected:** Celebration should ONLY trigger when user solves a scrambled cube
- **Root Cause:** Effect triggers whenever `cube.is_solved` becomes True, not checking if it was actually scrambled first
- **Fix Ideas:**
  - Track "was_scrambled" state, only celebrate if transitioning from scrambled->solved
  - Add "solve_count" or "last_scramble_time" to detect real solves
- **Files to investigate:**
  - `src/cube/application/commands/Operator.py` - where solve detection happens

### B8. Default texture shows wrong face colors [MEDIUM]
- **Status:** Open
- **Symptom:** YELLOW on front instead of WHITE
- **Related to:** G7 texture mapping work

---

## GUI & Testing

### G2. Investigate pyopengltk for tkinter backend [LOW]
- **Status:** Open
- Would allow reusing OpenGL code from pyglet backend
- True 3D rendering instead of 2D isometric projection
- Adds external dependency (`pip install pyopengltk`)

### G5. Comprehensive Command Testing Plan [MEDIUM]
- **Status:** Open (2025-12-02)
- **Goal:** Create automated tests for ALL keyboard commands and document mouse commands for manual testing
- **Phase 1:** Automated keyboard command tests
  - Each command can be tested by checking state changes after `inject_command()`
  - Create `tests/gui/test_all_commands.py` with comprehensive coverage
  - See `docs/design/command_test_mapping.md` for command->state mapping
- **Phase 2:** Manual mouse testing documentation
  - Mouse commands require visual verification (drag, click, scroll)
  - Document test procedures in `docs/design/mouse_testing.md`

### G6. Additional lighting improvements (pyglet2 backend) [LOW]
- **Status:** Open (2025-12-02)
- **Current state:** G3 implemented brightness (10%-150%) and background (0%-50%)
- **Future enhancements:**
  - Add fill light from below/behind to reduce dark shadows
  - Boost base colors in shader for more vivid appearance
  - Add light position control (move light source around cube)
  - Add specular/shininess control

### G7. Texture mapping for cube faces [IN PROGRESS]
- **Status:** In progress (2025-12-02)
- **Goal:** Allow user to put images (photos, logos) on cube faces
- **Use case:** Personal photos, educational content, branded cubes
- **Implementation considerations:**
  - Load images as OpenGL textures
  - Map UV coordinates for each facelet
  - Handle different image aspect ratios
  - Add command to toggle texture mode on/off
  - Store texture file paths in config
- **Approach:** Hardcoded sample images first, animated cells keep textures
- **Files:** `ModernGLRenderer.py`, `ModernGLCubeViewer.py`

---

## Architecture

### A7. Investigate and document circular import issues [MEDIUM]
- **Status:** Open (2025-12-07)
- **Context:** Discovered during pyright fixes - some `__init__.py` files cannot re-export symbols
- **Circular chain found:**
  ```
  application.__init__ -> app -> domain.algs -> domain.__init__ -> solver ->
  application.commands.Operator -> application.state -> application.animation ->
  AnimationManager -> application.state <- CIRCULAR!
  ```
- **Affected files:**
  - `src/cube/application/__init__.py` - cannot import App, AbstractApp, etc.
  - `src/cube/application/animation/__init__.py` - cannot import AnimationManager
  - `src/cube/domain/__init__.py` - cannot import subpackages
- **Goal:** Document why these exist and evaluate if architecture can be improved

### A8. Ensure no code leaks outside backends layer [MEDIUM]
- **Status:** Open (from __todo.md new entries)
- **Goal:** All backend-specific code (pyglet, etc.) should be contained within the backends folder

### A9. Centralize animation handling [MEDIUM]
- **Status:** Open (from __todo.md new entries)
- **Problem:** Solvers need to wrap operations with `with_animation()` themselves
- **Goal:** Handle animation at a higher level so solvers don't need to care

---

## Documentation

### D1. Improve keyboard_and_commands.md diagram clarity [LOW]
- **Status:** Open
- Current diagram in section 1.4 is confusing - shows separate flows for each backend
- Goal: Make it visually clear that Part 1 (native handlers) is different, Part 2 (unified path) is identical
- Consider: Use actual colors/formatting that renders in markdown, or restructure as separate diagrams

---

## Code Quality

### Q5. Review all `# type: ignore` comments [LOW]
- **Status:** Open
- Audit added during Q2 mypy fixes
- Some are for protocol compliance with concrete classes
- Some are for method overrides with different signatures

### Q6. Evaluate if `disable_error_code = import-untyped` hides real problems [LOW]
- **Status:** Open
- Currently disabled globally in `mypy.ini` to suppress pyglet stub warnings
- Risk: May hide issues with other untyped third-party libraries
- Alternative: Use per-module `[mypy-pyglet.*]` with `ignore_missing_imports = True`

### Q7. Add type annotations to untyped lambda callbacks [LOW]
- **Status:** Open
- Files: `tkinter/event_loop.py:34-35`, `tkinter/renderer.py:580`
- Currently triggers mypy `annotation-unchecked` notes
- Would allow using `--check-untyped-defs` for stricter checking

### Q9. Clean up dead code debug prints in solver [LOW]
- **Status:** Open
- `L1Cross.py:__print_cross_status()` - has `return` guard making code unreachable
- `NxnCentersFaceTracker.py:_debug_print_track_slices()` - has `if True: return` guard
- Decide: Remove entirely OR migrate to `vs.debug()` system

### Q10. Relocate `debug_dump()` to better location [LOW]
- **Status:** Open (2025-12-02)
- **Problem:** `debug_dump()` is in `main_any_backend.py` which is not called by tests
- **Goal:** Debug dump should be available to any code that creates an application
- **Needs:** Architecture review to determine proper location

### Q13. Evaluate pyright strict mode [LOW]
- **Status:** Open (2025-12-07)
- **Context:** Changed pyright from "basic" to "standard" mode
- **Strict mode analysis:** 1905 errors breakdown:
  - 741 `reportUnknownMemberType` - Missing type info from libraries
  - 216 `reportPrivateUsage` - Accessing `_private` members
  - 199 `reportUnknownArgumentType`
  - 188 `reportMissingParameterType`
  - And more...
- **Decision:** Stay with "standard" mode for now

### Q14. Fix vs.debug() performance issue with template strings [MEDIUM]
- **Status:** Open (2025-12-07)
- **Problem:** Calls like `vs.debug(flag, f"value={expensive_call()}")` evaluate the f-string even when debug is off
- **Rule:** Always use constant strings or `vs.debug_lazy()` for expensive computations
- **Action needed:**
  - Find all usages of `vs.debug()` with non-constant strings
  - Add warning comment to `debug()` method docstring
  - Update CLAUDE.md with instructions

### Q15. Clean up protected member access warnings in CageNxNSolver.py [LOW]
- **Status:** Open (2025-12-20)
- **Problem:** PyCharm reports ~10 "Access to a protected member" warnings
- **Options:**
  1. Add public accessor methods/properties to the domain classes
  2. Use `# noinspection PyProtectedMember` comments
  3. Leave as-is (internal solver code accessing internal model details)
- **Files:** `src/cube/domain/solver/direct/cage/CageNxNSolver.py`

### Q16. Clean up all dead code using vulture [MEDIUM]
- **Status:** Open (2025-12-21)
- **Tool:** `python -m vulture src/cube`
- **Known issues to fix:**
  - Unused `what` parameter in `CageNxNSolver.solve()` (line 189)
  - Unused `_was_partial_edge_parity` attribute
  - Review all 60% confidence findings for real dead code
- **See also:** `todo/__dead_code.md` for detailed list

---

## Solver Tasks

### S1. CFOP parity detection [LOW]
- **Status:** Open
- **Problem:** CFOP doesn't detect and raise parity exceptions like BeginnerSolver3x3 does
- CFOP silently fixes edge parity in `OLL._check_and_do_oll_edge_parity()` instead of raising `EvenCubeEdgeParityException`
- For now, the orchestrator uses BeginnerSolver3x3 as the parity detector
- See: `OLL.py` lines 108-126

### S2. advanced_edge_parity flag evaluation [LOW]
- **Status:** Open
- Currently using `advanced_edge_parity=False` (M-slice algorithm)
- Consider switching to `True` (R/L-slice algorithm) which:
  - Preserves edge pairing better
  - May be better for cage method

### S3. Unify tracker cleanup code [MEDIUM]
- **Status:** Open
- **See:** `docs/design/TODO_tracker_cleanup.md`
- **Problem:** Two separate cleanup mechanisms for face tracker slices:
  - `NxNCentersFaceTrackers` (used by NxNCenters)
  - `FaceTrackerHolder` (used by CageNxNSolver)
- **Goal:** Unify around `FaceTrackerHolder`

### S4. Cage face creation duplication [LOW]
- **Status:** Open (from __todo.md new entries)
- **Problem:** Code in cage used to create faces in case of even is duplicated in reducer
- Uses tracer methods - need to review
- Make sure the third center also uses majority

---

## From Legacy Files

### From `__todo.txt` (legacy notes)
- Generalize slice walking and use in communicator
- Fix scramble to invert and multiple and generate sub lists
- Why big block doesn't cause tracker replacement?
- Feature: swap complete slices (Done, but only destination zero slices)
- Feature: Keyboard history
- Bug: self annotation causes delay in animation?
- Code: Move face trackers to separated file
- Optimize: clone don't need to clone facets attributes
- Feature: viewer should auto-detect shadow mode changes
- Optimize: centers should start with front, minimize movements
- Optimize: improve face tracker (search 4 points only)
- Bug: using texture animation is very slow
- Code: keyboard and solver user directly config for debug

### From `__next_session.md`
- Replace Canvas2D with Three.js WebGL in `static/cube.js` (web backend Phase 2)

### From `__todo_gui_test_bug.md`
- Notes about running tests with debug=true and sequence 1/q for comparison
