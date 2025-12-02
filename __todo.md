# Project TODO

> **How to enter symbols in PyCharm (Windows):**
> - ❌ (red X) - Not started: `Win + .` → search "cross" or "x mark" → select ❌
> - ♾️ (infinity) - In progress: `Win + .` → search "infinity" → select ♾️
> - ✅ (green V) - Completed: `Win + .` → search "check" → select ✅
> - Or copy/paste from here: `❌` `♾️` `✅`
>
> **Claude:**
> - When starting work on a task, change its status to ♾️ (in progress) BEFORE beginning work.
> - When reading this file, look for unformatted entries at the bottom and ask user to reformat or not.
> - When a task is done, move it to the "Done Tasks" section at the bottom, preserving its ID number.
> - When adding new tasks, check existing IDs (including Done) to avoid duplicates (e.g., if A1, A2 exist, new is A3).
> - If reopening a done task, mention "Reopened from Done" in the description.
> - After refactoring run mypy -p cube, if change need to be done run tests only and so on


---

## Bugs

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

- ❌ **G3.** Add keyboard controls for lighting adjustment (pyglet2 backend)
  - **Current state:** Lighting parameters are hardcoded in `ModernGLRenderer.__init__()`
  - **Goal:** Allow user to adjust brightness/ambient during runtime
  - **Proposed keys:** `[` / `]` for brightness down/up, or similar
  - **Parameters to control:**
    - Ambient light (currently 0.65)
    - Light position
    - Shininess
  - **Files:** `src/cube/presentation/gui/backends/pyglet2/ModernGLRenderer.py`
  - **Added:** 2025-12-02

- ❌ **G4.** F10/F11/F12 shadow modes don't work in pyglet2 backend
  - These keys control shadow/lighting modes in legacy backend
  - Need to investigate and implement for modern GL
  - **Added:** 2025-12-02


## Architecture

- ❌ **A6.** CRITICAL: AnimationManager should not know about pyglet2/ModernGLCubeViewer
  - **Problem:** `AnimationManager._op_and_play_animation()` uses duck-typing to detect ModernGLCubeViewer:
    ```python
    is_modern_gl = hasattr(viewer, 'draw_animated') and hasattr(viewer, 'is_animating')
    if is_modern_gl:
        animation = _create_modern_gl_animation(...)
    ```
  - **Violation:** Application layer (AnimationManager) knows about presentation layer implementation details
  - **Solution Options:**
    1. Add animation creation to a protocol that viewers implement
    2. Move animation creation to the viewer itself (viewer.create_animation())
    3. Use a factory/strategy pattern injected from the backend
  - **Files:** `src/cube/application/animation/AnimationManager.py` lines 230-237
  - **Added:** 2025-12-02

- ❌ **A4.** PygletAppWindow cannot inherit from AppWindow protocol due to metaclass conflict
  - `pyglet.window.Window` has its own metaclass that conflicts with Protocol
  - Tried `TYPE_CHECKING` trick - didn't work in PyCharm
  - Options: composition pattern, wrapper class, or accept docstring-only documentation


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

---
# New entries below - Claude will reformat and move above this line

---

## Done Tasks

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
  - **Note:** A6 tracks remaining architectural issue with AnimationManager coupling

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
