# Completed Tasks

This file contains all tasks that have been completed. Moved from `__todo.md`.

---

## Bugs (Completed)

### B2. Fix mypy -p cube errors after Q3.2 file renames
- **Status:** COMPLETED
- Fixed import ambiguity: module names vs class names (e.g., `from cube.model import PartEdge`)
- Solution: use explicit imports from files (e.g., `from cube.model.PartEdge import PartEdge`)
- Fixed imports in: Part.py, Face.py, Edge.py, Corner.py, Center.py, _part.py, _part_slice.py
- Fixed Renderer imports in: TextureData.py, ApplicationAndViewState.py, GCubeViewer.py
- Fixed AnnotationAlg import in Inv.py
- Fixed type errors in: Command.py, AnimationManager.py, HeadlessAppWindow.py

### B3. Shift+/ (solve without animation) no longer works after command refactoring
- **Status:** COMPLETED
- Added `SOLVE_ALL_NO_ANIMATION` command and mapped Shift+/ to it
- Key binding updated in `key_bindings.py:104`
- New command in `Command.py:552`

### B4. Mouse zoom (scroll wheel) and Ctrl+Up/Down zoom crash in pyglet2 backend
- **Status:** COMPLETED (2025-12-02)
- **Root Cause:** Zoom commands called `renderer.view.set_projection()` which used legacy `gluPerspective()` not available in OpenGL core profile
- **Solution:** Created `ModernGLViewStateManager` and `ModernGLRendererAdapter` to provide modern GL compatible `set_projection()`
- **Files:** `backends/pyglet2/ModernGLRenderer.py`, `backends/pyglet2/PygletAppWindow.py`

### B7. Commands accessing ctx.viewer fail in pyglet2 backend
- **Status:** COMPLETED (2025-12-07)

---

## GUI & Testing (Completed)

### G1. Make sure all test_gui run with all backends
- **Status:** COMPLETED
- Added `--backend` pytest option (default: "all" runs pyglet, headless, console, tkinter)
- Tests use `Command` enum instead of string key sequences
- `BackendRegistry.ensure_registered()` ensures backend is loaded
- Animation manager gracefully handles backends without viewers

### G3. Add keyboard controls for lighting adjustment (pyglet2 backend)
- **Status:** COMPLETED (2025-12-02)
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

### G4. F10/F11/F12 shadow modes don't work in pyglet2 backend
- **Status:** COMPLETED (2025-12-02)
- **Root Cause:** `ModernGLCubeViewer._rebuild_geometry()` only drew 6 main faces, didn't check shadow mode or create offset duplicates
- **Solution:**
  - Added `vs` parameter to `ModernGLCubeViewer.__init__()`
  - Refactored geometry generation into `_generate_face_geometry()` helper
  - When shadow mode enabled for L/D/B faces, generates duplicate face at offset position
  - Shadow offsets match legacy `_board.py`: L=-75 (x), D=-50 (y), B=-200 (z)
- **Files:** `backends/pyglet2/ModernGLCubeViewer.py`, `backends/pyglet2/PygletAppWindow.py`

---

## Architecture (Completed)

### A1. Move main window factory to backend, not a special factory in main_any
- **Status:** COMPLETED
- Added `app_window_factory` to `_BackendEntry` and `GUIBackend.create_app_window()`
- Animation manager wiring is now in `GUIBackend.create_app_window()`

### A2. Introduce commands injecting instead of keys, simplify key handling
- **A2.0.** COMPLETED - Unify keyboard handling across all backends (prerequisite)
  - Created `handle_key_with_error_handling()` - unified error handling
  - All backends now use `handle_key(symbol, modifiers)` as the **protocol method**
  - Each backend has its own **native handler** that converts and calls `handle_key()`:
    - Pyglet: `on_key_press()` -> `handle_key()`
    - Tkinter: `_on_tk_key_event()` -> `handle_key()`
    - Console: `_on_console_key_event()` -> `handle_key()`
    - Headless: `inject_key()` -> `handle_key()`
  - See `docs/design/keyboard_and_commands.md` for details
- **A2.1.** COMPLETED - Create Command enum and inject_command() mechanism in AppWindow
  - Created `Command` enum with ~100 self-executing commands (gui/command.py)
  - Created `key_bindings.py` with KEY_BINDINGS_NORMAL and KEY_BINDINGS_ANIMATION tables
  - Added `lookup_command()` for O(1) key->command lookup
  - Added `inject_command()` to AppWindow protocol
  - Wired `handle_key()` to use `lookup_command()` + `command.execute()`
  - **DELETED** `main_g_keyboard_input.py` (~600 lines of legacy code)
  - See `docs/design/keyboard_and_commands.md` for architecture details
- **A2.2.** COMPLETED - Update GUI tests to use inject_command() instead of inject_key_sequence()
  - Created `CommandSequence` class with `+` and `*` operators for fluent API
  - Updated `GUITestRunner` to accept `Command | CommandSequence` and `backend` parameter
  - Added `--backend` pytest fixture (default: all 4 backends)
  - Added `BackendRegistry.ensure_registered()` helper
  - Deleted `tests/gui/keys.py` (GUIKeys no longer needed)
  - Tests now use: `Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT`

### A3. Consider moving animation manager wiring from GUIBackend to elsewhere
- **Status:** COMPLETED (closed as "by design")
- **Decision:** Keep as-is
- **Rationale:**
  - The coupling is benign - it's just wiring, not business logic
  - `create_app_window()` is a natural injection point for animation setup
  - This is cohesive: factory creates window and wires its animation system
  - Alternatives add boilerplate without practical benefit
  - A1 intentionally consolidated this wiring into GUIBackend - that was correct

### A4. Fix AppWindowBase / AbstractWindow inheritance mess
- **Status:** COMPLETED (2025-12-07)
- **Solution:**
  - Centralized `AppWindowBase` in `protocols/` (was duplicated in backends)
  - Deleted backend-specific `AbstractWindow.py` files
  - All backends now properly inherit: `PygletAppWindow(AppWindowBase, AnimationWindow, AppWindow)`
  - No more metaclass conflicts - pyglet2 uses composition via `PygletWindow`
- **Files:** `protocols/AppWindowBase.py`, all `*AppWindow.py` files

### A5. Pyglet 2.0 Backend with Modern OpenGL
- **Status:** COMPLETED (2025-12-02)
- **Solution:** Created `pyglet2` backend with VBO-based rendering and animation
- **Key components:**
  - `ModernGLCubeViewer` - Shader-based cube rendering with animation support
  - `ModernGLRenderer` - Modern GL with GLSL shaders and matrix stack emulation
  - Ray-plane intersection for mouse face picking (replaces gluUnProject)
  - VBO-based animation via `draw_animated()` method
- **Tests:** 126 non-GUI passed, 11 GUI passed (2 pyglet2, 9 other backends)
- **Files:** `src/cube/presentation/gui/backends/pyglet2/`
- **Docs:** `docs/design/migration_state.md` (A5 section)

### A6. AnimationManager layer violation (application layer knowing presentation details)
- **Status:** COMPLETED (2025-12-02)
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

---

## Code Quality (Completed)

### Q1. Refactor too many packages under `src/cube`
- **Status:** COMPLETED
- **New structure:**
  - `domain/` - Pure business logic (algs, model, solver with beginner typo fixed)
  - `application/` - Orchestration (commands, animation, config, exceptions, state)
  - `presentation/` - View/UI (viewer, gui with backends)
  - `utils/` - Utility functions (unchanged)
  - `main_*.py` - Entry points (stay at cube/ root)
- **Files moved:** ~150 files across 12 packages into 3 layer packages
- **Fixed:** solver/begginer -> solver/beginner (typo)
- **All tests pass:** 126 non-GUI tests, 8 GUI tests (4 skipped for B1)

### Q2. Add typing to all code, make sure mypy is green
- **Status:** COMPLETED
- 0 errors in 141 source files (down from 57 errors)
- Fixed: protocol signatures, abstract class implementations, None/Optional narrowing,
  wrong argument types, variable/import conflicts, missing protocol members
- Added `disable_error_code = import-untyped` to `mypy.ini` for pyglet (no type stubs)

### Q3. File naming convention: single class per file with case-sensitive filename matching class name
- **Status:** COMPLETED
- When implementing a protocol or base class, the implementation class name should differ from the base
- Example: Protocol `Renderer` implemented by `PygletRenderer`, `HeadlessRenderer` (not just `Renderer`)
- Example: `class MyClass` should be in `MyClass.py` (not `my_class.py`)
- **Q3.1.** COMPLETED - Audit and fix all protocol classes and their implementations
  - Split protocol files to PascalCase (ShapeRenderer.py, EventLoop.py, etc.)
  - Renamed all backend implementation files to PascalCase
  - Updated all __init__.py files and imports
- **Q3.2.** COMPLETED - Audit and fix all other classes in the codebase
  - Renamed 45 files to match class names (PascalCase)
  - Split 6 multi-class files with backward-compatible re-export modules
  - Left 3 complex files unsplit due to tight coupling: `_elements.py`, `_part.py`, `_part_slice.py`

### Q4. Create `/mytodo` slash command to read and manage `__todo.md`
- **Status:** COMPLETED
- Created `.claude/commands/mytodo.md`

### Q8. Code cleanup: remove unused code and consolidate console backend
- **Status:** COMPLETED
- Deleted `main_c.py` (old standalone console app) and `tests/console/`
- Removed unused imports and dead functions
- Moved `main_console/` code to `gui/backends/console/`
- Deleted `main_console/` folder

### Q8.2. Centralized debug output control
- **Status:** COMPLETED
- Added `debug_all` and `quiet_all` flags to `ApplicationAndViewState`
- Added `debug()`, `debug_lazy()`, `is_debug()`, `debug_prefix()` methods
- Migrated solver debug prints to use `vs.debug()` system
- Added `--debug-all` and `--quiet` CLI flags

### Q11. Clean up ModernGLCubeViewer.py code quality
- **Status:** COMPLETED (2025-12-07)
- **Problem:** 1210-line monolith with magic numbers, no documentation, duplicate code
- **Solution:** Refactored to match legacy `GCubeViewer` -> `_Board` -> `_FaceBoard` -> `_Cell` architecture
- **New files created:**
  - `_modern_gl_constants.py` - Named constants with comments (HALF_CUBE_SIZE, CELL_GAP_RATIO, etc.)
  - `_modern_gl_board.py` - Manages all 6 faces, ASCII coordinate diagrams
  - `_modern_gl_face.py` - Manages cells on one face, cell layout documentation
  - `_modern_gl_cell.py` - Vertex generation for one cell
- **Improvements:**
  - Main file reduced from 1210 -> 657 lines
  - ASCII diagrams documenting coordinate systems (like legacy)
  - Named booleans (`is_bottom_row`, `is_left_col`) instead of raw comparisons
  - `_get_cell_color` now delegates to `_get_cell_part_slice` (no duplicate logic)
  - All magic numbers documented in `_modern_gl_constants.py`
- **Files:** `src/cube/presentation/gui/backends/pyglet2/`

### Q12. Fix AppWindow.viewer type mismatch
- **Status:** COMPLETED (2025-12-07)
- **Problem:** Protocol declared `viewer -> GCubeViewer` but implementations returned `GCubeViewer | ModernGLCubeViewer | None`
- **Solution:** Updated `AppWindow.viewer` to return `AnimatableViewer` protocol type
- `AnimatableViewer` is implemented by both `GCubeViewer` and `ModernGLCubeViewer`
- **Files:** `src/cube/presentation/gui/protocols/AppWindow.py:50`

---

## Solver Tasks (Completed)

### Dead code removed (2025-12-16)
- Removed `detect_edge_parity()` and `detect_corner_parity()` from:
  - `Solver3x3Protocol` (never called)
  - `BeginnerSolver3x3` (never called)
  - `CFOP3x3` (never called, and would never return True anyway since OLL/PLL silently fix)
  - `Kociemba3x3` (never called, always returned None)
- Removed error-masking fallback code in `NxNSolverOrchestrator` (lines 287-290)
  - Now properly raises `InternalSWError` if edge parity detected twice
- Deleted stale `__branch_state.md` WIP documentation

### Corner swap vs edge parity asymmetry (2025-12-16)
- Unified Pattern implemented:
  - Both parities now follow: Detector raises exception -> Orchestrator catches -> Reducer fixes
- Changes Made:
  - `L3Corners.py`: Removed `_do_corner_swap()` call before throwing exception
  - `NxNSolverOrchestrator.py`: Always calls `reducer.fix_corner_parity()` when catching exception
  - `Cube.py`: Removed `dont_fix_corner_parity` flag and `with_dont_fix_corner_parity()` context manager

### SolverElementsProvider Refactoring (2025-12-17)
- Created minimal protocol and abstract base class
- New Files:
  - `protocols/SolverElementsProvider.py` - New protocol
  - `reducers/AbstractReducer.py` - New base class
  - `SOLVER_ARCHITECTURE.md` - Class hierarchy documentation
- Eliminated `_ReducerSolverFacade` hack
- Clear separation between solver and reducer hierarchies

---

## Cage Solver Tasks (Completed)

### Phase 1a: Edge Solving
- Reuses `NxNEdges` from beginner solver
- Edge parity handled inside `NxNEdges.solve()`
- Works for both odd and even cubes

### Phase 1b: Corner Solving
- Uses shadow cube approach for both odd and even cubes
- Odd cubes: Use face center color for face color mapping
- Even cubes: Use `FaceTracker` to establish face colors from majority colors
- Even cube solver: Uses beginner solver (not CFOP) to avoid parity oscillation

### Phase 2: Center Solving
- Uses `CageCenters` which wraps `NxNCenters`
- Face color mapping from Phase 1b trackers
- Preserves edges and corners

### Even Cube Support
- Face color mapping: Uses `FaceTracker` pattern to establish colors
- Shadow cube approach: Same as odd cubes but with tracked colors
- Parity handling: Uses beginner solver to avoid OLL/PLL parity oscillation

### CFOP Solver for Odd Cubes
- Added `ignore_center_check=True` parameter to `Solvers3x3.by_name()`
- CFOP's F2L uses `Part.match_faces` instead of `Face.solved` for validation
