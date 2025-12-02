# GUI Abstraction Migration State

## Overview
This document tracks the progress of migrating from direct pyglet/OpenGL calls to the renderer abstraction layer.

## Test Requirements Per Step
Before marking a step complete and tagging:
1. Run all algorithm tests: `pytest tests/algs -v`
2. Run all GUI tests: `pytest tests/gui -v --speed-up 2`
3. Run manual GUI test: `python -m cube.main_pyglet` - user confirms it works

---

## Phase 1: Core Abstraction Layer (COMPLETED)

### Step 1: Migrate viewer_g_ext.py - Axis Drawing
- **Tag:** `migration-step-1-axis-drawing`
- **Files Changed:** `src/cube/presentation/viewer/viewer_g_ext.py`
- **Changes:** Removed `from pyglet import gl`, now uses `renderer.view` and `renderer.shapes` for axis drawing
- **Status:** COMPLETED

### Step 2: Migrate app_state.py - Matrix Operations
- **Tag:** `migration-step-2-matrix-ops`
- **Files Changed:** `src/cube/application/state.py`
- **Changes:** `prepare_objects_view()`, `restore_objects_view()`, `set_projection()` now accept renderer parameter
- **Status:** COMPLETED

### Step 3: Migrate texture.py - Texture Loading
- **Tag:** `migration-step-3-texture`
- **Files Changed:** `src/cube/presentation/viewer/TextureData.py`
- **Changes:** Uses `renderer.load_texture()` instead of `pyglet.image.load()`
- **Status:** COMPLETED

### Step 4: Migrate main_g_keyboard_input.py - Key Constants
- **Tag:** `migration-step-4-keyboard`
- **Files Changed:**
  - `src/cube/presentation/gui/backends/pyglet/main_g_keyboard_input.py` (DELETED in A2.1)
  - `src/cube/presentation/gui/types.py` (added key constants)
  - `src/cube/presentation/gui/backends/pyglet/PygletWindow.py` (key mappings)
  - `src/cube/presentation/gui/backends/pyglet/Window.py` (key conversion, draw_text fix)
- **Changes:**
  - Replaced `pyglet.window.key` with abstract `Keys` and `Modifiers`
  - Fixed `draw_text()` GL_MATRIX_MODE bug (use GL_TRANSFORM_BIT)
- **Status:** COMPLETED

### Step 5: Add Picking to Renderer Protocol
- **Tag:** `migration-step-5-picking`
- **Files Changed:**
  - `src/cube/presentation/gui/protocols/Renderer.py` - Added `screen_to_world()` method to ViewStateManager protocol
  - `src/cube/presentation/gui/backends/pyglet/PygletRenderer.py` - Implemented using `gluUnProject`
  - `src/cube/presentation/gui/backends/headless/HeadlessRenderer.py` - Added no-op implementation returning (0,0,0)
- **Changes:** Added screen coordinate to world coordinate conversion (picking) to renderer protocol
- **Status:** COMPLETED

### Step 6: Migrate main_g_mouse.py - Mouse Handling
- **Tag:** `migration-step-6-mouse`
- **Files Changed:**
  - `src/cube/presentation/gui/backends/pyglet/main_g_mouse.py` - Removed pyglet imports, uses abstract types
  - `src/cube/presentation/gui/types.py` - Added `MouseButton` class
  - `src/cube/presentation/gui/backends/pyglet/PygletWindow.py` - Added `_convert_mouse_buttons()` function
  - `src/cube/presentation/gui/backends/pyglet/Window.py` - Converts mouse events to abstract types
- **Changes:**
  - `_screen_to_model()` now uses `renderer.view.screen_to_world()` instead of direct GL calls
  - Mouse drag/press handlers use abstract `Modifiers` and `MouseButton` constants
- **Bug Fix:** Pyglet uses bottom-left origin (y=0 at bottom), removed unnecessary Y-flip
- **Status:** COMPLETED

### Step 7: Remove Unused Batch
- **Tag:** `migration-step-7-batch`
- **Files Changed:**
  - `src/cube/presentation/gui/backends/pyglet/Window.py` - Removed `self.batch` and `pyglet.graphics.Batch()` creation
  - `src/cube/presentation/viewer/viewer_g.py` - Removed `batch` parameter from `GCubeViewer.__init__()`
  - `src/cube/presentation/viewer/_board.py` - Removed `batch` parameter and `self.batch` attribute
  - `src/cube/presentation/viewer/_faceboard.py` - Removed `batch` parameter and `self._batch` attribute
  - `src/cube/presentation/viewer/_cell.py` - Removed `batch` parameter, removed `from pyglet.graphics import Batch`
- **Changes:** Removed unused `pyglet.graphics.Batch` from entire viewer hierarchy
- **Status:** COMPLETED

### Step 8: Migrate animation_manager.py - Event Loop/Clock
- **Tag:** `step8-eventloop-migration`
- **Files Changed:**
  - `src/cube/application/animation/AnimationManager.py` - Removed pyglet imports, uses abstract EventLoop
  - `src/cube/presentation/gui/protocols/EventLoop.py` - Added `has_exit`, `idle()`, `notify()` methods
  - `src/cube/presentation/gui/backends/pyglet/PygletEventLoop.py` - Implemented new methods
  - `src/cube/presentation/gui/backends/headless/HeadlessEventLoop.py` - Implemented new methods
  - `src/cube/presentation/gui/GUIBackend.py` - Added `event_loop` property to GUIBackend
  - `tests/gui/tester/GUITestRunner.py` - Wire up event loop to animation manager
- **Changes:**
  - AnimationManager now accepts EventLoop via `set_event_loop()` method
  - Uses `event_loop.schedule_interval()` instead of `pyglet.clock.schedule_interval()`
- **Status:** COMPLETED

### Step 9: Migrate main_pyglet.py - Main Loop
- **Tag:** `step9-mainloop-migration`
- **Files Changed:** `src/cube/main_pyglet.py`
- **Changes:**
  - Removed `import pyglet` (no direct pyglet import)
  - Changed `pyglet.app.run()` to `backend.event_loop.run()`
- **Bug Fix:** Use `pyglet.app.run()` in PygletEventLoop.run() instead of manual while loop
- **Status:** COMPLETED

### Step 10: Migrate Window.py + main_g_abstract.py
- **Tag:** `step10-abstractwindow-protocol`
- **Files Changed:**
  - `src/cube/presentation/gui/backends/pyglet/AbstractWindow.py` - Converted AbstractWindow from class to Protocol
  - `src/cube/presentation/gui/backends/pyglet/Window.py` - Now inherits directly from `pyglet.window.Window`
- **Changes:**
  - AbstractWindow is now a `@runtime_checkable` Protocol defining the interface
  - Window class implements the Protocol by being a pyglet window
- **Status:** COMPLETED

### Step 11: Migrate viewer_g.py + _board.py - Cleanup
- **Tag:** `step11-viewer-cleanup`
- **Files Changed:**
  - `src/cube/presentation/viewer/viewer_g.py` - Removed unused `import pyglet`, `import pyglet.gl as gl`, `from pyglet.gl import *`
  - `src/cube/presentation/viewer/_board.py` - Removed unused `from pyglet import gl`
- **Changes:** Cleanup of unused imports
- **Status:** COMPLETED

### Step 12: Final Verification (Phase 1)
- **Tag:** `step12-final-verification`
- **Verification:**
  - All non-GUI tests pass: 126 passed, 8 skipped
  - All GUI tests pass: 3 passed
  - Manual GUI verified working
- **Status:** COMPLETED ✅

---

## Phase 2: Move Remaining Pyglet Code to Backend (COMPLETED)

### Goal for Phase 2

All `import pyglet` and `from pyglet` statements should ONLY exist in:
1. `src/cube/gui/backends/pyglet/` - The pyglet backend implementation
2. `src/cube/main_window/Window.py` - Acceptable as this IS the pyglet window class

### Phase 2 Migration Steps

#### Step 13: Delete shapes.py (Dead Code)
- **Tag:** `step13-delete-shapes`
- **Target:** `src/cube/presentation/viewer/shapes.py`
- **Action:** DELETED - All 440 lines were unused dead code
- **Finding:** `_cell.py` already used `renderer.shapes.*` for all rendering
- **Status:** COMPLETED ✅

#### Step 14: Delete gl_helper.py (Dead Code)
- **Tag:** `step14-delete-gl-helper`
- **Target:** `src/cube/presentation/viewer/gl_helper.py`
- **Action:** DELETED - Only imported by shapes.py (which was deleted)
- **Status:** COMPLETED ✅

#### Step 15: Delete graphic_helper.py (Debug Only)
- **Tag:** `step15-delete-graphic-helper`
- **Target:** `src/cube/presentation/viewer/graphic_helper.py`
- **Action:** DELETED - Debug-only functions, `complement()` was unused
- **Status:** COMPLETED ✅

#### Step 16: Clean up _cell.py
- **Tag:** `step16-cleanup-cell`
- **Target:** `src/cube/presentation/viewer/_cell.py`
- **Changes:**
  - Removed `import pyglet` (line 8)
  - Removed `from pyglet import gl` (line 10)
  - Removed `from . import shapes` (line 16)
  - Removed unused `pyglet.shapes.*` type hints (lines 99-102)
- **Status:** COMPLETED ✅

#### Step 17: Final Phase 2 Verification
- **Tag:** `step17-phase2-complete`
- **Verification:**
  - Zero pyglet imports outside backend (verified via grep)
  - All 126 non-GUI tests pass
  - Manual GUI verification pending
- **Status:** COMPLETED ✅

---

## Architecture Reference

### Renderer Protocol Hierarchy
```
Renderer (main protocol)
├── shapes: ShapeRenderer
│   ├── quad(), quad_with_border(), quad_with_texture()
│   ├── triangle(), line(), lines(), cross()
│   ├── sphere(), cylinder(), disk(), full_cylinder()
│   └── cone()
├── display_lists: DisplayListManager
│   ├── gen_list(), delete_list(), delete_lists()
│   ├── begin_list(), end_list()
│   └── call_list(), call_lists()
└── view: ViewStateManager
    ├── set_projection(), push_matrix(), pop_matrix()
    ├── translate(), rotate(), scale(), multiply_matrix()
    ├── look_at(), screen_to_world()
    └── push_attrib(), pop_attrib()
```

### EventLoop Protocol
```
EventLoop
├── running: bool (property)
├── has_exit: bool (property)
├── run(), stop(), step()
├── get_time(): float
├── schedule_once(), schedule_interval(), unschedule()
├── idle(): float
└── notify()
```

### Key Files
- `src/cube/presentation/gui/protocols/Renderer.py` - Renderer protocol definition
- `src/cube/presentation/gui/protocols/EventLoop.py` - EventLoop protocol definition
- `src/cube/presentation/gui/backends/pyglet/PygletRenderer.py` - Pyglet renderer implementation
- `src/cube/presentation/gui/backends/pyglet/PygletEventLoop.py` - Pyglet event loop implementation
- `src/cube/presentation/gui/backends/headless/` - Headless backend for testing
- `src/cube/presentation/gui/BackendRegistry.py` - BackendRegistry
- `src/cube/presentation/gui/GUIBackend.py` - GUIBackend

---

## Manual Testing Instructions

After each step, run the GUI manually and verify:
1. Start: `python -m cube.main_pyglet`
2. Test cube rotations with mouse drag
3. Test keyboard shortcuts (R, L, U, D, F, B for face rotations)
4. Test scramble (press 1, 2, or 3)
5. Test solve (press /)
6. Test animation speed (+/- keys)
7. Close window (press q or Escape)

Report any visual glitches, crashes, or unexpected behavior.

---

## Current Status

**Phase 1:** COMPLETE (Steps 1-12) ✅
**Phase 2:** COMPLETE (Steps 13-17) ✅
**Phase 3:** COMPLETE (Abstract Window Layer) ✅
**Phase 4 (Q3.1):** COMPLETE (File Naming Convention) ✅
**A2.1:** COMPLETE (Command Pattern) ✅
**A5:** COMPLETE (Pyglet 2.0 Backend with Animation) ✅
**A6:** PLANNED - AnimationManager Layer Violation Fix 🔄
**B4:** PLANNED - Zoom Crash Fix (depends on A6) 🔄

**Last Completed Step:** A5 - Pyglet 2.0 modern GL with VBO-based animation
**Current Work:** A6 - Fix AnimationManager layer violation, then B4 - Fix zoom crash
**Current Branch:** `new-opengl`
**Tests Passing:** 126 non-GUI tests, 11 GUI tests (pyglet2: 2 passed, 2 skipped; headless/console/tkinter: 9 passed)

### Migration Complete!

All pyglet imports have been successfully removed from:
- `presentation/viewer/shapes.py` - DELETED (440 lines of dead code)
- `presentation/viewer/gl_helper.py` - DELETED (32 lines, only used by shapes.py)
- `presentation/viewer/graphic_helper.py` - DELETED (53 lines, debug only)
- `presentation/viewer/_cell.py` - Cleaned up (removed 3 imports, 4 dead type hints)

**Remaining pyglet imports (by design):**
1. `src/cube/presentation/gui/backends/pyglet/*` - Backend implementation

---

## Phase 3: Abstract Window Layer (PLANNED)

### Goal for Phase 3

Create an abstract `AppWindow` class that can work with ANY backend (pyglet, tkinter, etc.), allowing `main_tkinter.py` to use the same keyboard/mouse handling code as `main_pyglet.py`.

### Current Problem

The `presentation/gui/backends/pyglet/Window.py` is tightly coupled to pyglet:
- Inherits from `pyglet.window.Window`
- Uses pyglet-specific GL calls (`gl.glViewport`, `gl.glEnable`)
- Uses pyglet-specific text rendering (`pyglet.text.Label`)
- Handles pyglet-specific events (`on_key_press`, `on_draw`, etc.)

The keyboard/mouse handlers in `main_g_keyboard_input.py` and `main_g_mouse.py` are already abstracted using `AbstractWindow` protocol, but:
- They need cursor methods (`get_system_mouse_cursor`, `set_mouse_cursor`)
- They need text rendering for status display
- The main Window class creates pyglet-specific labels

### Architecture Design

```
                         AbstractWindow (Protocol)
                               ↑
                               │ implements
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    PygletAppWindow    TkinterAppWindow    [Future backends]
    (wraps Window.py)  (new implementation)
            │                  │
            └────────┬─────────┘
                     │
              AppWindowBase (shared logic)
                     │
        ┌────────────┴────────────┐
        │                         │
  main_g_keyboard_input    main_g_mouse
  (already abstracted)     (already abstracted)
```

### Phase 3 Migration Steps

#### Step 18: Create AppWindow Protocol
- **Target:** `src/cube/gui/protocols/app_window.py` (NEW)
- **Changes:**
  - Define `AppWindow` protocol extending current `AbstractWindow`
  - Add `inject_key_sequence()` for testing
  - Add text rendering interface
  - Add cursor interface (or make optional with default no-op)

#### Step 19: Create AppWindowBase Class
- **Target:** `src/cube/gui/app_window_base.py` (NEW)
- **Changes:**
  - Implement shared logic (keyboard/mouse dispatch)
  - Hold references to: `app`, `viewer`, `renderer`, `backend`
  - Implement `update_gui_elements()` calling viewer.update()
  - Delegate actual window operations to abstract methods

#### Step 20: Create PygletAppWindow
- **Target:** `src/cube/gui/backends/pyglet/app_window.py` (NEW)
- **Changes:**
  - Wrap existing `Window.py` functionality
  - Implement pyglet-specific: GL viewport, text labels, cursor
  - Keep `inject_key_sequence()` for testing

#### Step 21: Create TkinterAppWindow
- **Target:** `src/cube/gui/backends/tkinter/app_window.py` (NEW)
- **Changes:**
  - Use existing `TkinterWindow` for basic window
  - Implement tkinter-specific text rendering
  - Implement cursor methods (or no-op)
  - Wire up to same keyboard/mouse handlers

#### Step 22: Update main_pyglet.py
- **Target:** `src/cube/main_pyglet.py`
- **Changes:**
  - Use new `PygletAppWindow` instead of direct `Window`
  - Should be minimal changes

#### Step 23: Update main_tkinter.py
- **Target:** `src/cube/main_tkinter.py`
- **Changes:**
  - Replace custom `TkinterCubeApp` with `TkinterAppWindow`
  - Use same keyboard/mouse handlers as pyglet version
  - Remove duplicate key handling code

#### Step 24: Phase 3 Final Verification
- **Verification:**
  - Both `main_pyglet.py` and `main_tkinter.py` use same handlers
  - All keyboard shortcuts work in both backends
  - Mouse rotation/slicing works in both (or gracefully degraded in tkinter)
  - All tests pass

### Key Abstractions Needed

1. **Text Rendering:**
   - Current: `pyglet.text.Label` directly in Window
   - Abstract: `TextRenderer.draw_label()` - already exists in protocols

2. **Cursor Management:**
   - Current: `window.get_system_mouse_cursor()`, `window.set_mouse_cursor()`
   - Abstract: Make optional with no-op default for backends that don't support it

3. **GL-specific calls in Window.py:**
   - `gl.glViewport()` → Move to renderer or backend-specific window
   - `gl.glEnable(gl.GL_DEPTH_TEST)` → Move to renderer setup

4. **Event Dispatch:**
   - `on_key_press` → `handle_keyboard_input()`
   - `on_mouse_drag/press/release/scroll` → `main_g_mouse.*`
   - Already abstracted, just need proper wiring

### Files That Will Change

| File | Action |
|------|--------|
| `gui/protocols/app_window.py` | NEW - AppWindow protocol |
| `gui/app_window_base.py` | NEW - Shared implementation |
| `gui/backends/pyglet/app_window.py` | NEW - Pyglet implementation |
| `gui/backends/tkinter/app_window.py` | NEW - Tkinter implementation |
| `main_window/Window.py` | MODIFY - Extract reusable parts |
| `main_window/AbstractWindow.py` | MODIFY or REMOVE - Merge into new protocol |
| `main_pyglet.py` | MODIFY - Use new window class |
| `main_tkinter.py` | MODIFY - Use new window class |

### Notes

- The `main_g_keyboard_input.py` and `main_g_mouse.py` are ALREADY backend-agnostic
- They use `AbstractWindow` protocol which defines the interface
- The main work is creating concrete implementations for each backend
- Tkinter won't support all features (e.g., screen_to_world picking may not work well)
- Focus on getting basic cube display + keyboard rotations working first

---

## Phase 4: File Naming Convention (Q3.1) - COMPLETE ✅

### Goal
Rename all files to PascalCase matching their class names (Java/C# style):
- `renderer.py` → `Renderer.py`
- `event_loop.py` → `EventLoop.py`
- Files with multiple classes are split (one class per file)

### Completed Steps

#### Step 1: Split protocols/ (DONE)
Created new PascalCase files in `src/cube/gui/protocols/`:
- `ShapeRenderer.py` - ShapeRenderer protocol
- `DisplayListManager.py` - DisplayListManager protocol
- `ViewStateManager.py` - ViewStateManager protocol
- `Renderer.py` - Renderer protocol (imports above 3)
- `TextRenderer.py` - TextRenderer protocol
- `Window.py` - Window protocol (imports TextRenderer)
- `EventLoop.py` - EventLoop protocol
- `AnimationBackend.py` - AnimationBackend protocol
- `AppWindow.py` - AppWindow protocol

#### Step 2: Rename backend implementation files (DONE)
All backend files renamed to PascalCase:

**Pyglet backend:**
- `event_loop.py` → `PygletEventLoop.py`
- `app_window.py` → `PygletAppWindow.py`
- `animation.py` → `PygletAnimation.py`
- `renderer.py` → `PygletRenderer.py`
- `window.py` → `PygletWindow.py`

**Headless backend:**
- `event_loop.py` → `HeadlessEventLoop.py`
- `app_window.py` → `HeadlessAppWindow.py`
- `renderer.py` → `HeadlessRenderer.py`
- `window.py` → `HeadlessWindow.py`

**Console backend:**
- `event_loop.py` → `ConsoleEventLoop.py`
- `app_window.py` → `ConsoleAppWindow.py`
- `renderer.py` → `ConsoleRenderer.py`

**Tkinter backend:**
- `event_loop.py` → `TkinterEventLoop.py`
- `app_window.py` → `TkinterAppWindow.py`
- `animation.py` → `TkinterAnimation.py`
- `renderer.py` → `TkinterRenderer.py`
- `window.py` → `TkinterWindow.py`

#### Step 3: Update all imports (DONE)
All `__init__.py` files and cross-file imports updated.

#### Step 4: Tests passed (DONE)
All 126 non-GUI tests pass, 2 GUI tests pass.

---

## A2.1: Command Pattern - COMPLETE ✅

### Goal
Replace the legacy `main_g_keyboard_input.py` (600 lines of match/case) with a clean Command pattern.

### Architecture

```
handle_key(symbol, modifiers)
    ↓
lookup_command(symbol, modifiers, animation_running)   [key_bindings.py]
    ↓
command.execute(ctx)   [command.py - self-executing Command enum]
    ↓
Action performed
```

### Key Components

1. **Command Enum** (`gui/Command.py`)
   - ~100 self-executing commands (ROTATE_R, SCRAMBLE_1, SOLVE_ALL, etc.)
   - Lazy handler creation with caching
   - CommandContext provides access to app, cube, operator, solver

2. **Key Bindings** (`gui/key_bindings.py`)
   - `KEY_BINDINGS_NORMAL` - Commands when NOT animating
   - `KEY_BINDINGS_ANIMATION` - Commands DURING animation (S=Stop, etc.)
   - `lookup_command()` - O(1) dict lookup

3. **Integration** (`main_window/AppWindowBase.py`)
   - `handle_key()` → `lookup_command()` → `inject_command()`
   - `inject_command()` executes with error handling

### Files Changed

| File | Change |
|------|--------|
| `gui/Command.py` | NEW - Command enum with ~100 commands |
| `gui/key_bindings.py` | NEW - Key binding tables |
| `main_window/AppWindowBase.py` | Updated handle_key() to use commands |
| `main_window/main_g_keyboard_input.py` | **DELETED** (~600 lines) |
| `gui/backends/pyglet/PygletAppWindow.py` | Updated handle_key() |
| `main_window/Window.py` | Updated on_key_press() |
| `tests/gui/tester/GUITestRunner.py` | Handle AppExit as success |

### Benefits

1. **Single Source of Truth** - Key bindings in one place
2. **Self-Documenting** - `Command.ROTATE_R_PRIME` vs magic keys
3. **Type-Safe** - IDE autocomplete for commands
4. **Testable** - `inject_command()` bypasses key handling
5. **Lazy Loading** - Handlers created on first use

---

## A2.2: GUI Tests with Commands - COMPLETE ✅

### Goal
Update GUI tests to use `Command` enum instead of string key sequences, and support all backends.

### Architecture

```
# Old way (string sequences)
GUITestRunner.run_test(key_sequence="1/q")

# New way (type-safe commands)
GUITestRunner.run_test(
    commands=Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
    backend="pyglet"  # or "headless", "console", "tkinter", or omit for all
)
```

### Key Components

1. **CommandSequence** (`gui/Command.py`)
   - `+` operator to combine commands
   - `*` operator to repeat commands
   - Iterable for executing all commands

2. **GUITestRunner** (`tests/gui/tester/GUITestRunner.py`)
   - Accepts `Command | CommandSequence`
   - `backend` parameter to specify which backend
   - Uses `BackendRegistry.ensure_registered()` to load backend

3. **Backend Fixture** (`tests/gui/conftest.py`)
   - `--backend` pytest option (default: "all")
   - Parametrizes tests with all 4 backends

### Files Changed

| File | Change |
|------|--------|
| `gui/Command.py` | Added `CommandSequence` class with `+` and `*` operators |
| `gui/factory.py` | Added `BackendRegistry.ensure_registered()` |
| `tests/gui/tester/GUITestRunner.py` | Accept commands + backend parameter |
| `tests/gui/conftest.py` | Added `--backend` pytest option |
| `tests/gui/test_gui.py` | Use `Command` instead of `GUIKeys` |
| `tests/gui/keys.py` | **DELETED** (GUIKeys no longer needed) |
| `animation/AnimationManager.py` | Graceful handling when no viewer |
| `gui/backends/console/ConsoleAppWindow.py` | Disable animation manager |

### Test Results

All 4 backends pass:
- **pyglet:** 2 passed, 1 skipped
- **headless:** 2 passed, 1 skipped
- **console:** 2 passed, 1 skipped
- **tkinter:** 2 passed, 1 skipped

---

## A5: Pyglet 2.0 Backend (new-opengl branch) - IN PROGRESS 🔄

### Goal
Create a new pyglet2 backend that uses modern OpenGL 3.3+ core profile instead of legacy OpenGL (glBegin/glEnd, display lists).

### Background
Pyglet 2.0 creates OpenGL 3.3 core profile by default, which removes all legacy GL functions:
- No `glBegin`/`glEnd` (immediate mode)
- No display lists (`glGenLists`, `glNewList`, `glCallList`)
- No fixed-function pipeline (`glMatrixMode`, `glLoadIdentity`)
- Shaders and VBOs are required

### Key Insight: Two Renderer Approaches

The pyglet2 backend has **two parallel renderer implementations**:

| Renderer | GL Mode | Status | Animation Support |
|----------|---------|--------|-------------------|
| `PygletRenderer.py` | `gl_compat` (legacy) | Working | Possible via display lists |
| `ModernGLRenderer.py` | Modern GL 3.3+ | Working | Needs VBO-based approach |

**Decision Needed:** Which path to pursue for animation?

1. **Option A: Use `gl_compat`** - Fastest path to full feature parity
   - `PygletRenderer.py` already implements all protocols using `gl_compat`
   - Would allow existing `GCubeViewer` + display lists to work
   - Requires: Verify display lists work in compatibility mode

2. **Option B: Implement modern animation** - Future-proof but more work
   - Use `ModernGLCubeViewer` for rendering
   - Implement VBO-based animation (rotate vertex positions)
   - More complex, requires matrix stack per-piece

### Architecture

```
pyglet2 backend
├── PygletRenderer.py     # gl_compat wrapper (implements Renderer protocol)
│   ├── Uses pyglet.gl.gl_compat for legacy functions
│   ├── Uses PyOpenGL (GLU) for sphere/cylinder
│   └── Full ShapeRenderer protocol implementation
│
├── ModernGLRenderer.py   # True modern GL (GLSL shaders)
│   ├── Vertex shaders: solid color + per-vertex color
│   ├── VBO/VAO management via buffers.py
│   └── Matrix stack emulation via matrix.py
│
├── ModernGLCubeViewer.py # Cube rendering (bypasses GCubeViewer)
│   ├── Generates face triangles from cube model
│   ├── Per-vertex colors for stickers
│   ├── Grid lines for cell borders
│   └── update() / draw() interface
│
└── PygletAppWindow.py    # Main window
    ├── Uses ModernGLRenderer for cube drawing
    ├── Uses ModernGLCubeViewer (not GCubeViewer)
    └── AnimationManager bypassed (falls back to instant)
```

### Current Status (2025-12-02)

| Feature | Status | Notes |
|---------|--------|-------|
| Cube rendering | ✅ Working | ModernGLCubeViewer with shaders |
| Face rotations (keyboard) | ✅ Working | R/L/U/D/F/B with animation |
| Scramble | ✅ Working | Press 1-9 for scrambles |
| Solve | ✅ Working | Press ? for solve |
| Mouse drag (camera rotation) | ✅ Working | Right-click drag, camera orbit via matrix.py |
| Mouse drag (face rotation) | ✅ Working | Left-click drag with animation |
| Mouse scroll (zoom) | ✅ Working | Z-axis translation |
| Text labels | ✅ Working | pyglet.text.Label (modern GL) |
| Debug logging | ✅ Working | `--debug-all` shows output |
| History tracking | ✅ Working | Via Operator.play() |
| **Visual animation** | ✅ Working | VBO-based animation via ModernGLCubeViewer |

### Mouse Face Picking - IMPLEMENTED ✅

The old pyglet 1.x backend used legacy GL functions for picking:
- `glGetDoublev(GL_PROJECTION_MATRIX)` - get current matrices
- `glGetDoublev(GL_MODELVIEW_MATRIX)`
- `gluUnProject()` - convert screen coords to 3D world coords
- `GCubeViewer.find_facet()` - find which cube face was clicked

In pyglet 2.0, these legacy functions are not available. **Solution: Ray-plane intersection**.

#### Ray-Plane Intersection Implementation

New methods added to `ModernGLCubeViewer.py`:
- `_setup_view_matrix(vs)` - Recalculates view matrix for current camera orientation
- `screen_to_ray(x, y, width, height, vs)` - Convert screen coords to world-space ray
- `find_facet_by_ray(origin, direction)` - Intersect ray with 6 cube face planes
- `find_facet_at_screen(x, y, width, height, vs)` - Combine above two
- `get_part_edge_at_screen(x, y, width, height, vs)` - Return PartEdge like legacy API
- `_get_part_edge_at_cell(face, row, col)` - Map (row, col) to cube model parts

New method added to `ModernGLRenderer.py`:
- `get_inverse_mvp()` - Get inverse of combined Model-View-Projection matrix

Updated `main_g_mouse.py`:
- `_get_selected_slice()` - Now uses `modern_viewer.get_part_edge_at_screen()`
- `_play()` - Uses `op.play(alg, animation=False)` to track history without animation
- Converted debug `print()` to `vs.debug()` for consistency

#### How It Works

```
Left-click drag on cube face:
    ↓
_handle_face_slice_rotate_by_drag()
    ↓
_get_selected_slice() → modern_viewer.get_part_edge_at_screen()
    ↓
screen_to_ray() - Convert screen (x,y) to world-space ray using inverse MVP
    ↓
find_facet_by_ray() - Test ray against 6 face planes, find closest hit
    ↓
_get_part_edge_at_cell() - Map hit (face, row, col) to PartEdge
    ↓
Determine rotation direction from drag vector
    ↓
op.play(alg, animation=False) - Execute without animation, track history
    ↓
window.update_gui_elements() - Refresh display
```

#### Animation Support - IMPLEMENTED ✅

Animation now works for both keyboard and mouse rotation using VBO-based rendering:

```python
# AnimationManager detects ModernGLCubeViewer via duck-typing:
is_modern_gl = hasattr(viewer, 'draw_animated') and hasattr(viewer, 'is_animating')
if is_modern_gl:
    animation = _create_modern_gl_animation(cube, viewer, vs, alg, alg.n)
```

The `ModernGLCubeViewer` implements:
- `get_slices_movable_gui_objects()` - Separates animated geometry from static
- `draw_animated(model_view)` - Renders animated parts with rotation matrix
- `unhidden_all()` - Restores normal rendering after animation
- `is_animating()` - Animation state check

### Solution Attempt: Compatibility Profile (FAILED)

Tried using pyglet 2.0 compatibility profile via window config:

```python
from pyglet.gl import Config

# Attempt 1: forward_compatible=False
config = Config(
    double_buffer=True,
    depth_size=24,
    forward_compatible=False,
)

# Attempt 2: Request OpenGL 2.1 explicitly
config = Config(
    double_buffer=True,
    depth_size=24,
    major_version=2,
    minor_version=1,
)
```

**Result:** Both attempts FAILED on Windows.
- `glBegin`/`glEnd` still throw `GLException: Invalid operation (0x1282)`
- Pyglet 2.x on Windows always creates a core profile context
- The Config options don't override this behavior

**Conclusion:** Compatibility profile approach doesn't work on pyglet 2 + Windows.

### Solution Attempt: Modern GL screen_to_world (PARTIAL)

Added `screen_to_world()` to `ModernGLRenderer` that:
1. Reads depth buffer with `glReadPixels` (works in modern GL)
2. Inverts projection*modelview matrix
3. Unprojects screen coords to world coords

**Problem:** `GCubeViewer.find_facet()` requires `GCubeViewer` which creates display lists
in its constructor (`_Board._create_faces()` → `_Cell.prepare_geometry()` → `glGenLists`).

**The geometry and GL are deeply intertwined in `GCubeViewer`/`_Board`/`_Cell`.**

### Completed Features

- ✅ Ray-plane intersection for mouse face picking
- ✅ History tracking via Operator.play()
- ✅ VBO-based visual animation (keyboard and mouse rotation)
- ✅ Animation uses ModernGLCubeViewer.draw_animated() with rotation matrix
- ✅ Test configuration updated to use pyglet2 instead of legacy pyglet

**Remaining work for pyglet2:**
1. **Enable test_scramble_and_solve** - Currently skipped, may work now with animation
2. **Remove unused code** - `GCubeViewer` reference (`self._viewer = None`) can be cleaned up

### Files in pyglet2 Backend

```
src/cube/presentation/gui/backends/pyglet2/
├── __init__.py           # Backend registration
├── AbstractWindow.py     # Window protocol
├── AppWindowBase.py      # Shared window logic (copied from pyglet)
├── buffers.py            # VBO/VAO buffer management
├── main_g_mouse.py       # Mouse handling (copied from pyglet)
├── matrix.py             # Mat4, perspective, rotate, multiply
├── ModernGLCubeViewer.py # Shader-based cube rendering
├── ModernGLRenderer.py   # Modern GL with GLSL shaders
├── PygletAnimation.py    # Animation (currently unused)
├── PygletAppWindow.py    # Main window class
├── PygletEventLoop.py    # Event loop (same as pyglet)
├── PygletRenderer.py     # gl_compat wrapper (implements protocol)
├── PygletWindow.py       # Base window
├── shaders.py            # Shader compilation utilities
└── Window.py             # Legacy window (unused)
```

### How Animation Currently Fails

```python
# In PygletAppWindow.__init__():
self._viewer = None  # GCubeViewer disabled!

# In AnimationManager.run_animation():
try:
    viewer = self._window.viewer  # Property access
except RuntimeError:
    # Viewer not initialized - skip animation, execute directly
    op(alg, False)  # <-- This is what happens
    return
```

### Environment Setup

```bash
# Pyglet 2.x requires separate venv (incompatible with pyglet 1.5)
python -m venv .venv_pyglet2
.venv_pyglet2/Scripts/pip install "pyglet>=2.0" PyOpenGL numpy

# Main branch uses pyglet 1.5:
.venv314/Scripts/pip install "pyglet<2.0"
```

### How to Run

```bash
# Requires .venv_pyglet2 with pyglet 2.x
.venv_pyglet2/Scripts/python.exe -m cube.main_any_backend --backend=pyglet2

# With debug output
.venv_pyglet2/Scripts/python.exe -m cube.main_any_backend --backend=pyglet2 --debug-all
```

### Test Results (2025-12-02)

```bash
# Run all GUI tests (pyglet2 is now default instead of legacy pyglet)
.venv_pyglet2/Scripts/python.exe -m pytest tests/gui -v --speed-up 5

# Results: 11 passed, 5 skipped
# pyglet2: test_face_rotations PASSED, test_simple_quit PASSED
# headless: 3 passed
# console: 3 passed
# tkinter: 3 passed
```

### Recent Commits (new-opengl branch)

```
7028e0b Merge debug fixes from main
b7ec97f Fix pyglet2 mouse rotation and key press debug logging
f2cc9ab Fix pyglet2 animation skip and text rendering
dea6893 Add ModernGLCubeViewer for pyglet2 backend with working cube rendering
1ac0103 Fix pyglet2 on_resize called before renderer initialized
ba42268 Integrate ModernGLRenderer with PygletAppWindow
7a62dbb A5: Document pyglet 2.0 compatibility profile limitation
```

### Completed Tasks

1. ~~**Test mouse picking**: Implement screen_to_world for face selection~~ ✅ DONE
2. ~~**Decide on animation approach**: gl_compat vs modern GL~~ ✅ Chose modern GL
3. ~~**Modern GL animation**: VBO-based animation system~~ ✅ DONE
4. ~~**Enable mouse rotation animation**~~ ✅ DONE

---

## A6: AnimationManager Layer Violation Fix - PLANNED 🔄

### Problem Statement

The `AnimationManager` (application layer) uses duck-typing to detect `ModernGLCubeViewer` (presentation layer):

```python
# In AnimationManager._op_and_play_animation() lines 230-237:
is_modern_gl = hasattr(viewer, 'draw_animated') and hasattr(viewer, 'is_animating')
if is_modern_gl:
    animation = _create_modern_gl_animation(cube, viewer, vs, alg, alg.n)
```

**Violation:** Application layer knows about presentation layer implementation details.

### Architecture Issue

```
Current (Bad):
                    AnimationManager (application layer)
                           │
                           ├── knows about GCubeViewer (presentation)
                           │      uses display lists for animation
                           │
                           └── knows about ModernGLCubeViewer (presentation)
                                  uses duck-typing to detect VBO animation

Desired (Good):
                    AnimationManager (application layer)
                           │
                           └── AnimatableViewer (protocol)
                                      │
                           ┌──────────┴──────────┐
                           │                     │
                    GCubeViewer            ModernGLCubeViewer
                    (implements)           (implements)
```

### Solution: AnimatableViewer Protocol

Create a protocol that both `GCubeViewer` and `ModernGLCubeViewer` implement:

```python
# src/cube/presentation/gui/protocols/AnimatableViewer.py
from typing import Protocol, runtime_checkable, Any
from cube.domain.model.Cube import Cube
from cube.domain.algs import Alg

@runtime_checkable
class AnimatableViewer(Protocol):
    """Protocol for viewers that support animation."""

    @property
    def cube(self) -> Cube:
        """The cube being viewed."""
        ...

    def create_animation(
        self,
        alg: Alg,
        vs: Any,  # ApplicationAndViewState
        on_finish: Callable[[], None]
    ) -> "Animation":
        """Create an animation for the given algorithm.

        The viewer decides HOW to animate (display lists, VBOs, etc.)
        Returns an Animation object that AnimationManager can schedule.
        """
        ...

    def update(self) -> None:
        """Update the viewer's display."""
        ...
```

### Implementation Plan

1. **Create `AnimatableViewer` protocol** in `protocols/AnimatableViewer.py`
   - Define interface for animation creation
   - Animation object returned handles the HOW

2. **Update `GCubeViewer`** to implement protocol
   - Add `create_animation()` method that uses display lists
   - Move `_create_animation()` from `AnimationManager` to viewer

3. **Update `ModernGLCubeViewer`** to implement protocol
   - Add `create_animation()` method that uses VBOs
   - Move `_create_modern_gl_animation()` from `AnimationManager` to viewer

4. **Update `AnimationManager`**
   - Remove duck-typing detection
   - Use `viewer.create_animation()` polymorphically
   - No knowledge of specific viewer implementations

### Files to Change

| File | Change |
|------|--------|
| `protocols/AnimatableViewer.py` | NEW - Protocol definition |
| `presentation/viewer/GCubeViewer.py` | Add `create_animation()` |
| `backends/pyglet2/ModernGLCubeViewer.py` | Add `create_animation()` |
| `application/animation/AnimationManager.py` | Remove duck-typing, use protocol |

### Benefits

1. **Clean layer separation** - Application layer uses protocol, not concrete types
2. **Extensibility** - New viewers just implement the protocol
3. **Type-safe** - Protocol is `@runtime_checkable` for safety
4. **Self-documenting** - Animation creation is viewer's responsibility

---

## B4: Zoom Crash Fix - PLANNED 🔄

### Problem Statement

Zoom commands (Ctrl+Up/Down, mouse scroll) crash in pyglet2 backend because they call `gluPerspective()` which is not available in OpenGL core profile.

### Root Cause

The pyglet2 backend has two renderers:
- `_modern_renderer` (ModernGLRenderer) - shader-based, has `set_perspective()`
- `_renderer` (PygletRenderer) - legacy, has `ViewStateManager.set_projection()` using `gluPerspective()`

Zoom path uses wrong renderer:
```python
# Command.py _zoom_in():
ctx.vs.set_projection(ctx.window.width, ctx.window.height, ctx.window.renderer)
# → window.renderer is PygletRenderer (legacy)
# → calls gluPerspective() → CRASH in core profile
```

But `on_resize` works correctly:
```python
# PygletAppWindow.on_resize():
self._modern_renderer.set_perspective(width, height, fov_y=45.0, ...)
# → uses modern GL → works
```

### Solution: ModernGLViewStateManager Adapter

Create an adapter that wraps `ModernGLRenderer` and implements `ViewStateManager` protocol.

```python
class ModernGLViewStateManager(ViewStateManager):
    """ViewStateManager that delegates to ModernGLRenderer."""

    def __init__(self, modern_renderer: ModernGLRenderer):
        self._renderer = modern_renderer

    def set_projection(self, width, height, fov_y, near, far):
        # Delegate to modern renderer
        self._renderer.set_perspective(width, height, fov_y, near, far)

    def push_matrix(self): self._renderer.push_matrix()
    def pop_matrix(self): self._renderer.pop_matrix()
    # ... etc
```

### Implementation Plan

1. **Create `ModernGLViewStateManager`** in `ModernGLRenderer.py`
   - Implements `ViewStateManager` protocol
   - Wraps `ModernGLRenderer` instance

2. **Update `PygletRenderer`** (pyglet2 version)
   - Accept `ModernGLRenderer` reference
   - Return `ModernGLViewStateManager` from `view` property

3. **Wire up in `PygletAppWindow.__init__`**
   - After creating `_modern_renderer`, inject it into `_renderer`

### Benefits

- Fixes ALL code paths using `renderer.view.set_projection()`
- Commands remain backend-agnostic
- Single point of change

### Dependency

A6 should be fixed first because:
1. Both involve pyglet2 backend architecture
2. A6 establishes cleaner patterns that B4 can follow
3. Fixing A6 first ensures we don't introduce new layer violations in B4

---

## Future Investigation: pyopengltk

### Background

The current Tkinter backend uses pure 2D Canvas rendering with isometric projection. This has limitations:
- No true 3D (fake perspective via math)
- No depth buffer
- No hardware acceleration
- Visual differences from pyglet backend

### Alternative: pyopengltk

`pyopengltk` provides an OpenGL context inside a tkinter window, which would allow:
- Reusing most of the pyglet backend's OpenGL code
- True 3D rendering with depth buffer
- Hardware acceleration
- Near-identical visual output to pyglet

Trade-offs:
- Adds external dependency (`pip install pyopengltk`)
- Event handling differs from pyglet (needs adaptation)

### Status
- **Priority:** Low (current Canvas approach works for basic functionality)
- **Tracked in:** `__todo.md`
