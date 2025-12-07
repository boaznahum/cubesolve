# Project TODO

## Open Tasks Summary

| ID | Category | Priority | Title |
|----|----------|----------|-------|
| B1 | Bug | HIGH | GUI Animation Solver Bug (Lazy Cache Initialization) |
| B5 | Bug | - | Missing debug output when running with `--debug-all` |
| B6 | Bug | - | Celebration effect triggers on reset/resize |
| G2 | GUI | - | Investigate pyopengltk for tkinter backend |
| G5 | GUI | - | Comprehensive Command Testing Plan |
| G6 | GUI | - | Additional lighting improvements (pyglet2) |
| G7 | GUI | IN PROGRESS | Texture mapping for cube faces |
| A7 | Architecture | - | Investigate and document circular import issues |
| D1 | Documentation | - | Improve keyboard_and_commands.md diagram |
| Q5 | Quality | - | Review all `# type: ignore` comments |
| Q6 | Quality | - | Evaluate `disable_error_code = import-untyped` |
| Q7 | Quality | - | Add type annotations to lambda callbacks |
| Q9 | Quality | - | Clean up dead code debug prints in solver |
| Q10 | Quality | - | Relocate `debug_dump()` to better location |
| Q13 | Quality | - | Evaluate pyright strict mode (1905 errors) |
| Q14 | Quality | - | Fix vs.debug() performance (avoid template strings) |

---

> **Instructions for updating this file:**
>
> **Symbols (Windows: `Win + .` to open emoji picker):**
> - ❌ Not started - search "cross" or "x mark"
> - ♾️ In progress - search "infinity"
> - ✅ Completed - search "check"
>
> **Claude instructions:**
> - Update the summary table above when adding/completing tasks
> - When starting work, change status to ♾️ BEFORE beginning
> - When done, move task to "Done Tasks" section, preserving ID
> - Check existing IDs (including Done) to avoid duplicates
> - After code changes: run mypy, pyright, then tests

---

## Bugs

- ❌ **B6.** Celebration effect triggers on reset/resize, not just actual solves
  - **Status:** New (2025-12-02)
  - **Symptom:** Celebration effect (confetti, victory spin, etc.) triggers when:
    - Resetting the cube (Escape key)
    - Changing cube size (+/- size commands)
    - Other scenarios where cube becomes "solved" without actually solving
  - **Expected:** Celebration should ONLY trigger when user solves a scrambled cube
  - **Root Cause:** Effect triggers whenever `cube.is_solved` becomes True, not checking if it was actually scrambled first
  - **Fix Ideas:**
    - Track "was_scrambled" state, only celebrate if transitioning from scrambled→solved
    - Add "solve_count" or "last_scramble_time" to detect real solves
  - **Files to investigate:**
    - `src/cube/application/commands/Operator.py` - where solve detection happens
    - Celebration effect trigger location (needs investigation)

- ❌ **B5.** Missing debug output when running with `--debug-all`
  - **Status:** New (2025-12-02)
  - **Symptom:** When running with `debug=True` or `--debug-all`, many expected debug messages are missing:
    - Algorithm execution (e.g., R, L, U face rotations)
    - Command execution (which command was triggered by which key)
    - Keyboard input events (KEYBOAD_INPUT_DEBUG flag exists but is never used)
  - **Expected:** Debug mode should show full trace of user actions and cube operations
  - **Related:** `config.KEYBOAD_INPUT_DEBUG` is defined but never checked anywhere
  - **Files to investigate:**
    - `src/cube/application/config.py` - KEYBOAD_INPUT_DEBUG flag
    - `src/cube/presentation/gui/Command.py` - command execution
    - `src/cube/application/commands/Operator.py` - algorithm execution

- ❌ **B1.** GUI Animation Solver Bug (Lazy Cache Initialization)
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
  - **Error:** `AssertionError` at `L3Cross.py:178` (`assert top.match`)
  - **Root Cause:** Lazy initialization and caching of cube piece properties (`colors_id`, `position_id` in `Part` and `PartSlice` classes) combined with timing issues during animation.
  - **Mechanism:**
    1. `Part.colors_id` and `Part.position_id` are lazily initialized (cached on first access)
    2. Cache is reset via `reset_after_faces_changes()` after each cube rotation
    3. Pressing `+` triggers `update_gui_elements()` → `cube.is_sanity(force_check=True)`
    4. Sanity check accesses `colors_id` for all parts, forcing cache initialization
    5. Without this initialization, cache state becomes inconsistent during animation
  - **Key Files:**
    - `src/cube/domain/model/Part.py` lines 221-273 - Lazy cache properties
    - `src/cube/domain/model/_part_slice.py` lines 213-245 - Similar lazy caching
    - `src/cube/domain/model/cube_slice.py` line 230 - `reset_after_faces_changes()` call
    - `src/cube/domain/solver/beginner/L3Cross.py` line 178 - Failing assertion
  - **Workaround:** Press `+` key before scramble (or use `--speed-up 5` in tests)


## GUI & Testing

- ❌ **G2.** Investigate pyopengltk as alternative to pure Canvas rendering for tkinter backend
  - Would allow reusing OpenGL code from pyglet backend
  - True 3D rendering instead of 2D isometric projection
  - Adds external dependency (`pip install pyopengltk`)


- ❌ **G5.** Comprehensive Command Testing Plan
  - **Goal:** Create automated tests for ALL keyboard commands and document mouse commands for manual testing
  - **Phase 1: Automated keyboard command tests**
    - Each command can be tested by checking state changes after `inject_command()`
    - Create `tests/gui/test_all_commands.py` with comprehensive coverage
    - See `docs/design/command_test_mapping.md` for command→state mapping
  - **Phase 2: Manual mouse testing documentation**
    - Mouse commands require visual verification (drag, click, scroll)
    - Document test procedures in `docs/design/mouse_testing.md`
  - **Added:** 2025-12-02

- ❌ **G6.** Additional lighting improvements (pyglet2 backend)
  - **Current state:** G3 implemented brightness (10%-150%) and background (0%-50%)
  - **Future enhancements:**
    - Add fill light from below/behind to reduce dark shadows
    - Boost base colors in shader for more vivid appearance
    - Add light position control (move light source around cube)
    - Add specular/shininess control
  - **Added:** 2025-12-02

- ♾️ **G7.** Texture mapping for cube faces (custom images)
  - **Goal:** Allow user to put images (photos, logos) on cube faces
  - **Use case:** Personal photos, educational content, branded cubes
  - **Status:** In progress (2025-12-02)
  - **Implementation considerations:**
    - Load images as OpenGL textures
    - Map UV coordinates for each facelet
    - Handle different image aspect ratios
    - Add command to toggle texture mode on/off
    - Store texture file paths in config
  - **Approach:** Hardcoded sample images first, animated cells keep textures
  - **Files:** `ModernGLRenderer.py`, `ModernGLCubeViewer.py`
  - **Added:** 2025-12-02


## Architecture

- ❌ **A7.** Investigate and document circular import issues
  - **Status:** New (2025-12-07)
  - **Context:** Discovered during pyright fixes - some `__init__.py` files cannot re-export symbols
  - **Circular chain found:**
    ```
    application.__init__ → app → domain.algs → domain.__init__ → solver →
    application.commands.Operator → application.state → application.animation →
    AnimationManager → application.state ← CIRCULAR!
    ```
  - **Affected files:**
    - `src/cube/application/__init__.py` - cannot import App, AbstractApp, etc.
    - `src/cube/application/animation/__init__.py` - cannot import AnimationManager
    - `src/cube/domain/__init__.py` - cannot import subpackages
  - **Goal:** Document why these exist and evaluate if architecture can be improved


## Documentation

- ❌ **D1.** Improve keyboard_and_commands.md diagram clarity
  - Current diagram in section 1.4 is confusing - shows separate flows for each backend
  - Goal: Make it visually clear that Part 1 (native handlers) is different, Part 2 (unified path) is identical
  - Consider: Use actual colors/formatting that renders in markdown, or restructure as separate diagrams

## Code Quality

- ❌ **Q5.** Review all `# type: ignore` comments and document why they're needed
  - Audit added during Q2 mypy fixes
  - Some are for protocol compliance with concrete classes (AnimationWindow, AbstractWindow)
  - Some are for method overrides with different signatures

- ❌ **Q6.** Evaluate if `disable_error_code = import-untyped` hides real problems
  - Currently disabled globally in `mypy.ini` to suppress pyglet stub warnings
  - Risk: May hide issues with other untyped third-party libraries
  - Alternative: Use per-module `[mypy-pyglet.*]` with `ignore_missing_imports = True`
  - Investigate: Are there other libraries being silently ignored?

- ❌ **Q7.** Add type annotations to untyped lambda callbacks in tkinter backend
  - Files: `tkinter/event_loop.py:34-35`, `tkinter/renderer.py:580`
  - Currently triggers mypy `annotation-unchecked` notes
  - Would allow using `--check-untyped-defs` for stricter checking

- ❌ **Q9.** Clean up dead code debug prints in solver
  - `L1Cross.py:__print_cross_status()` - has `return` guard making code unreachable
  - `NxnCentersFaceTracker.py:_debug_print_track_slices()` - has `if True: return` guard
  - These are intentionally disabled debug functions - decide whether to:
    - Remove them entirely, or
    - Migrate to use `vs.debug()` system and remove the guards

- ❌ **Q10.** Relocate `debug_dump()` from `main_any_backend.py` to a better location
  - **Status:** New (2025-12-02)
  - **Problem:** `debug_dump()` is in `main_any_backend.py` which is not called by tests or other entry points
  - **Goal:** Debug dump should be available to any code that creates an application (tests, scripts, etc.)
  - **Needs:** Architecture review to determine proper location (maybe `AbstractApp` or `ApplicationAndViewState`)

- ❌ **Q13.** Evaluate pyright strict mode (1905 errors to fix)
  - **Status:** New (2025-12-07)
  - **Context:** Changed pyright from "basic" to "standard" mode, which catches method override issues
  - **Strict mode analysis:** Running with `typeCheckingMode = "strict"` reveals 1905 errors:
    - 741 `reportUnknownMemberType` - Missing type info from libraries (numpy, pyglet)
    - 216 `reportPrivateUsage` - Accessing `_private` members
    - 199 `reportUnknownArgumentType` - Args with unknown types
    - 188 `reportMissingParameterType` - Missing param type hints
    - 176 `reportUnknownParameterType` - Params with unknown types
    - 170 `reportUnknownVariableType` - Variables with unknown types
    - 92 `reportUnusedImport` - Unused imports
    - 30 `reportUnusedVariable` - Unused variables
    - Others: unused classes/functions, unnecessary isinstance, etc.
  - **Decision:** Stay with "standard" mode for now (catches real bugs without noise)
  - **Future:** Consider enabling individual strict rules incrementally

- ❌ **Q14.** Fix vs.debug() performance issue with template strings
  - **Status:** New (2025-12-07)
  - **Problem:** Calls like `vs.debug(flag, f"value={expensive_call()}")` evaluate the f-string even when debug is off
  - **Rule:** Always use constant strings or `vs.debug_lazy()` for expensive computations
  - **Action needed:**
    - Find all usages of `vs.debug()` with non-constant strings
    - Add warning comment to `debug()` method docstring
    - Update CLAUDE.md with instructions

---

## Done Tasks

### Bugs

- ✅ **B4.** Mouse zoom (scroll wheel) and Ctrl+Up/Down zoom crash in pyglet2 backend
  - **Fixed:** 2025-12-02
  - **Root Cause:** Zoom commands called `renderer.view.set_projection()` which used legacy `gluPerspective()` not available in OpenGL core profile
  - **Solution:** Created `ModernGLViewStateManager` and `ModernGLRendererAdapter` to provide modern GL compatible `set_projection()`
  - **Files:** `backends/pyglet2/ModernGLRenderer.py`, `backends/pyglet2/PygletAppWindow.py`

### GUI & Testing

- ✅ **G3.** Add keyboard controls for lighting adjustment (pyglet2 backend)
  - **Completed:** 2025-12-02
  - **Keys:** `Ctrl+[` / `Ctrl+]` for brightness down/up
  - **Features:**
    - Adjusts ambient light from 10% to 100%
    - Persisted in `ApplicationAndViewState.brightness`
    - Displayed in status bar as "Light:XX%"
    - Works during animation
  - **Implementation:**
    - Added `adjust_brightness()` / `get_brightness()` to `AppWindow` protocol
    - Default implementation in `AppWindowBase` (returns None for unsupported backends)
    - Added `BRIGHTNESS_UP` / `BRIGHTNESS_DOWN` commands
  - **Files:** `ModernGLRenderer.py`, `Command.py`, `key_bindings.py`, `AppWindow.py`, `state.py`

- ✅ **G4.** F10/F11/F12 shadow modes don't work in pyglet2 backend
  - **Fixed:** 2025-12-02
  - **Root Cause:** `ModernGLCubeViewer._rebuild_geometry()` only drew 6 main faces, didn't check shadow mode or create offset duplicates
  - **Solution:**
    - Added `vs` parameter to `ModernGLCubeViewer.__init__()`
    - Refactored geometry generation into `_generate_face_geometry()` helper
    - When shadow mode enabled for L/D/B faces, generates duplicate face at offset position
    - Shadow offsets match legacy `_board.py`: L=-75 (x), D=-50 (y), B=-200 (z)
  - **Files:** `backends/pyglet2/ModernGLCubeViewer.py`, `backends/pyglet2/PygletAppWindow.py`

### Architecture

- ✅ **A1.** Move main window factory to backend, not a special factory in main_any
  - Added `app_window_factory` to `_BackendEntry` and `GUIBackend.create_app_window()`
  - Animation manager wiring is now in `GUIBackend.create_app_window()`

- ✅ **A2.** Introduce commands injecting instead of keys, simplify key handling
  - **A2.0.** ✅ Unify keyboard handling across all backends (prerequisite)
    - Created `handle_key_with_error_handling()` - unified error handling
    - All backends now use `handle_key(symbol, modifiers)` as the **protocol method**
    - Each backend has its own **native handler** that converts and calls `handle_key()`:
      - Pyglet: `on_key_press()` → `handle_key()`
      - Tkinter: `_on_tk_key_event()` → `handle_key()`
      - Console: `_on_console_key_event()` → `handle_key()`
      - Headless: `inject_key()` → `handle_key()`
    - See `docs/design/keyboard_and_commands.md` for details
  - **A2.1.** ✅ Create Command enum and inject_command() mechanism in AppWindow
    - Created `Command` enum with ~100 self-executing commands (gui/command.py)
    - Created `key_bindings.py` with KEY_BINDINGS_NORMAL and KEY_BINDINGS_ANIMATION tables
    - Added `lookup_command()` for O(1) key→command lookup
    - Added `inject_command()` to AppWindow protocol
    - Wired `handle_key()` to use `lookup_command()` + `command.execute()`
    - **DELETED** `main_g_keyboard_input.py` (~600 lines of legacy code)
    - See `docs/design/keyboard_and_commands.md` for architecture details
  - **A2.2.** ✅ Update GUI tests to use inject_command() instead of inject_key_sequence()
    - Created `CommandSequence` class with `+` and `*` operators for fluent API
    - Updated `GUITestRunner` to accept `Command | CommandSequence` and `backend` parameter
    - Added `--backend` pytest fixture (default: all 4 backends)
    - Added `BackendRegistry.ensure_registered()` helper
    - Deleted `tests/gui/keys.py` (GUIKeys no longer needed)
    - Tests now use: `Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT`

- ✅ **A3.** Consider moving animation manager wiring from GUIBackend to elsewhere
  - **Decision:** Keep as-is (closed as "by design")
  - **Rationale:**
    - The coupling is benign - it's just wiring, not business logic
    - `create_app_window()` is a natural injection point for animation setup
    - This is cohesive: factory creates window and wires its animation system
    - Alternatives add boilerplate without practical benefit
    - A1 intentionally consolidated this wiring into GUIBackend - that was correct

- ✅ **A5.** Pyglet 2.0 Backend with Modern OpenGL
  - **Completed:** 2025-12-02
  - **Solution:** Created `pyglet2` backend with VBO-based rendering and animation
  - **Key components:**
    - `ModernGLCubeViewer` - Shader-based cube rendering with animation support
    - `ModernGLRenderer` - Modern GL with GLSL shaders and matrix stack emulation
    - Ray-plane intersection for mouse face picking (replaces gluUnProject)
    - VBO-based animation via `draw_animated()` method
  - **Tests:** 126 non-GUI passed, 11 GUI passed (2 pyglet2, 9 other backends)
  - **Files:** `src/cube/presentation/gui/backends/pyglet2/`
  - **Docs:** `docs/design/migration_state.md` (A5 section)

- ✅ **A4.** Fix AppWindowBase / AbstractWindow inheritance mess
  - **Fixed:** 2025-12-07 (discovered during V5 layer fixes)
  - **Solution:**
    - Centralized `AppWindowBase` in `protocols/` (was duplicated in backends)
    - Deleted backend-specific `AbstractWindow.py` files
    - All backends now properly inherit: `PygletAppWindow(AppWindowBase, AnimationWindow, AppWindow)`
    - No more metaclass conflicts - pyglet2 uses composition via `PygletWindow`
  - **Files:** `protocols/AppWindowBase.py`, all `*AppWindow.py` files

- ✅ **A6.** AnimationManager layer violation (application layer knowing presentation details)
  - **Completed:** 2025-12-02
  - **Problem:** `AnimationManager` (application layer) used duck-typing to detect viewer type:
    ```python
    is_modern_gl = hasattr(viewer, 'draw_animated') and hasattr(viewer, 'is_animating')
    ```
  - **Solution:** Created `AnimatableViewer` protocol in presentation layer
    - Viewers implement `create_animation()` method polymorphically
    - AnimationManager uses protocol, not concrete types
    - Removed ~270 lines of `_create_animation()` and `_create_modern_gl_animation()` functions
  - **Files:**
    - `protocols/AnimatableViewer.py` (NEW)
    - `viewer/GCubeViewer.py` - inherits from AnimatableViewer, adds `create_animation()`
    - `backends/pyglet2/ModernGLCubeViewer.py` - inherits from AnimatableViewer, adds `create_animation()`
    - `application/animation/AnimationManager.py` - now uses `viewer.create_animation()` polymorphically

### Bugs

- ✅ **B2.** Fix mypy -p cube errors after Q3.2 file renames
  - Fixed import ambiguity: module names vs class names (e.g., `from cube.model import PartEdge`)
  - Solution: use explicit imports from files (e.g., `from cube.model.PartEdge import PartEdge`)
  - Fixed imports in: Part.py, Face.py, Edge.py, Corner.py, Center.py, _part.py, _part_slice.py
  - Fixed Renderer imports in: TextureData.py, ApplicationAndViewState.py, GCubeViewer.py
  - Fixed AnnotationAlg import in Inv.py
  - Fixed type errors in: Command.py, AnimationManager.py, HeadlessAppWindow.py

- ✅ **B3.** Shift+/ (solve without animation) no longer works after command refactoring
  - **Fixed:** Added `SOLVE_ALL_NO_ANIMATION` command and mapped Shift+/ to it
  - Key binding updated in `key_bindings.py:104`
  - New command in `Command.py:552`

- ✅ **B7.** Commands accessing ctx.viewer fail in pyglet2 backend
  - **Fixed:** 2025-12-07 (details not recorded)

### GUI & Testing

- ✅ **G1.** Make sure all test_gui run with all backends
  - Added `--backend` pytest option (default: "all" runs pyglet, headless, console, tkinter)
  - Tests use `Command` enum instead of string key sequences
  - `BackendRegistry.ensure_registered()` ensures backend is loaded
  - Animation manager gracefully handles backends without viewers

### Code Quality

- ✅ **Q1.** Refactor too many packages under `src/cube`
  - **Completed:** Full layered architecture restructuring
  - **New structure:**
    - `domain/` - Pure business logic (algs, model, solver with beginner typo fixed)
    - `application/` - Orchestration (commands, animation, config, exceptions, state)
    - `presentation/` - View/UI (viewer, gui with backends)
    - `utils/` - Utility functions (unchanged)
    - `main_*.py` - Entry points (stay at cube/ root)
  - **Files moved:** ~150 files across 12 packages into 3 layer packages
  - **Fixed:** solver/begginer → solver/beginner (typo)
  - **All tests pass:** 126 non-GUI tests, 8 GUI tests (4 skipped for B1)

- ✅ **Q2.** Add typing to all code, make sure mypy is green
  - Completed: 0 errors in 141 source files (down from 57 errors)
  - Fixed: protocol signatures, abstract class implementations, None/Optional narrowing,
    wrong argument types, variable/import conflicts, missing protocol members
  - Added `disable_error_code = import-untyped` to `mypy.ini` for pyglet (no type stubs)

- ✅ **Q3.** File naming convention: single class per file with case-sensitive filename matching class name
  - When implementing a protocol or base class, the implementation class name should differ from the base
  - Example: Protocol `Renderer` implemented by `PygletRenderer`, `HeadlessRenderer` (not just `Renderer`)
  - Example: `class MyClass` should be in `MyClass.py` (not `my_class.py`)
  - **Q3.1.** ✅ Audit and fix all protocol classes and their implementations
    - Split protocol files to PascalCase (ShapeRenderer.py, EventLoop.py, etc.)
    - Renamed all backend implementation files to PascalCase
    - Updated all __init__.py files and imports
  - **Q3.2.** ✅ Audit and fix all other classes in the codebase
    - Renamed 45 files to match class names (PascalCase)
    - Split 6 multi-class files with backward-compatible re-export modules
    - Left 3 complex files unsplit due to tight coupling: `_elements.py`, `_part.py`, `_part_slice.py`

- ✅ **Q4.** Create `/mytodo` slash command to read and manage `__todo.md`
  - Created `.claude/commands/mytodo.md`

- ✅ **Q8.** Code cleanup: remove unused code and consolidate console backend
  - Deleted `main_c.py` (old standalone console app) and `tests/console/`
  - Removed unused imports and dead functions
  - Moved `main_console/` code to `gui/backends/console/`
  - Deleted `main_console/` folder

- ✅ **Q8.2.** Centralized debug output control
  - Added `debug_all` and `quiet_all` flags to `ApplicationAndViewState`
  - Added `debug()`, `debug_lazy()`, `is_debug()`, `debug_prefix()` methods
  - Migrated solver debug prints to use `vs.debug()` system
  - Added `--debug-all` and `--quiet` CLI flags

- ✅ **Q11.** Clean up ModernGLCubeViewer.py code quality
  - **Fixed:** 2025-12-07
  - **Problem:** 1210-line monolith with magic numbers, no documentation, duplicate code
  - **Solution:** Refactored to match legacy `GCubeViewer` → `_Board` → `_FaceBoard` → `_Cell` architecture
  - **New files created:**
    - `_modern_gl_constants.py` - Named constants with comments (HALF_CUBE_SIZE, CELL_GAP_RATIO, etc.)
    - `_modern_gl_board.py` - Manages all 6 faces, ASCII coordinate diagrams
    - `_modern_gl_face.py` - Manages cells on one face, cell layout documentation
    - `_modern_gl_cell.py` - Vertex generation for one cell
  - **Improvements:**
    - Main file reduced from 1210 → 657 lines
    - ASCII diagrams documenting coordinate systems (like legacy)
    - Named booleans (`is_bottom_row`, `is_left_col`) instead of raw comparisons
    - `_get_cell_color` now delegates to `_get_cell_part_slice` (no duplicate logic)
    - All magic numbers documented in `_modern_gl_constants.py`
  - **Files:** `src/cube/presentation/gui/backends/pyglet2/`

- ✅ **Q12.** Fix AppWindow.viewer type mismatch
  - **Fixed:** 2025-12-07 (as part of V5b layer fix)
  - **Problem:** Protocol declared `viewer -> GCubeViewer` but implementations returned `GCubeViewer | ModernGLCubeViewer | None`
  - **Solution:** Updated `AppWindow.viewer` to return `AnimatableViewer` protocol type
  - `AnimatableViewer` is implemented by both `GCubeViewer` and `ModernGLCubeViewer`
  - **Files:** `src/cube/presentation/gui/protocols/AppWindow.py:50`
