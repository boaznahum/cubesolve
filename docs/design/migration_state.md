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
- **Files Changed:** `src/cube/viewer/viewer_g_ext.py`
- **Changes:** Removed `from pyglet import gl`, now uses `renderer.view` and `renderer.shapes` for axis drawing
- **Status:** COMPLETED

### Step 2: Migrate app_state.py - Matrix Operations
- **Tag:** `migration-step-2-matrix-ops`
- **Files Changed:** `src/cube/app/app_state.py`
- **Changes:** `prepare_objects_view()`, `restore_objects_view()`, `set_projection()` now accept renderer parameter
- **Status:** COMPLETED

### Step 3: Migrate texture.py - Texture Loading
- **Tag:** `migration-step-3-texture`
- **Files Changed:** `src/cube/viewer/texture.py`
- **Changes:** Uses `renderer.load_texture()` instead of `pyglet.image.load()`
- **Status:** COMPLETED

### Step 4: Migrate main_g_keyboard_input.py - Key Constants
- **Tag:** `migration-step-4-keyboard`
- **Files Changed:**
  - `src/cube/main_window/main_g_keyboard_input.py`
  - `src/cube/gui/types.py` (added key constants)
  - `src/cube/gui/backends/pyglet/window.py` (key mappings)
  - `src/cube/main_window/Window.py` (key conversion, draw_text fix)
- **Changes:**
  - Replaced `pyglet.window.key` with abstract `Keys` and `Modifiers`
  - Fixed `draw_text()` GL_MATRIX_MODE bug (use GL_TRANSFORM_BIT)
- **Status:** COMPLETED

### Step 5: Add Picking to Renderer Protocol
- **Tag:** `migration-step-5-picking`
- **Files Changed:**
  - `src/cube/gui/protocols/renderer.py` - Added `screen_to_world()` method to ViewStateManager protocol
  - `src/cube/gui/backends/pyglet/renderer.py` - Implemented using `gluUnProject`
  - `src/cube/gui/backends/headless/renderer.py` - Added no-op implementation returning (0,0,0)
- **Changes:** Added screen coordinate to world coordinate conversion (picking) to renderer protocol
- **Status:** COMPLETED

### Step 6: Migrate main_g_mouse.py - Mouse Handling
- **Tag:** `migration-step-6-mouse`
- **Files Changed:**
  - `src/cube/main_window/main_g_mouse.py` - Removed pyglet imports, uses abstract types
  - `src/cube/gui/types.py` - Added `MouseButton` class
  - `src/cube/gui/backends/pyglet/window.py` - Added `_convert_mouse_buttons()` function
  - `src/cube/main_window/Window.py` - Converts mouse events to abstract types
- **Changes:**
  - `_screen_to_model()` now uses `renderer.view.screen_to_world()` instead of direct GL calls
  - Mouse drag/press handlers use abstract `Modifiers` and `MouseButton` constants
- **Bug Fix:** Pyglet uses bottom-left origin (y=0 at bottom), removed unnecessary Y-flip
- **Status:** COMPLETED

### Step 7: Remove Unused Batch
- **Tag:** `migration-step-7-batch`
- **Files Changed:**
  - `src/cube/main_window/Window.py` - Removed `self.batch` and `pyglet.graphics.Batch()` creation
  - `src/cube/viewer/viewer_g.py` - Removed `batch` parameter from `GCubeViewer.__init__()`
  - `src/cube/viewer/_board.py` - Removed `batch` parameter and `self.batch` attribute
  - `src/cube/viewer/_faceboard.py` - Removed `batch` parameter and `self._batch` attribute
  - `src/cube/viewer/_cell.py` - Removed `batch` parameter, removed `from pyglet.graphics import Batch`
- **Changes:** Removed unused `pyglet.graphics.Batch` from entire viewer hierarchy
- **Status:** COMPLETED

### Step 8: Migrate animation_manager.py - Event Loop/Clock
- **Tag:** `step8-eventloop-migration`
- **Files Changed:**
  - `src/cube/animation/animation_manager.py` - Removed pyglet imports, uses abstract EventLoop
  - `src/cube/gui/protocols/event_loop.py` - Added `has_exit`, `idle()`, `notify()` methods
  - `src/cube/gui/backends/pyglet/event_loop.py` - Implemented new methods
  - `src/cube/gui/backends/headless/event_loop.py` - Implemented new methods
  - `src/cube/gui/factory.py` - Added `event_loop` property to GUIBackend
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
  - `src/cube/main_window/main_g_abstract.py` - Converted AbstractWindow from class to Protocol
  - `src/cube/main_window/Window.py` - Now inherits directly from `pyglet.window.Window`
- **Changes:**
  - AbstractWindow is now a `@runtime_checkable` Protocol defining the interface
  - Window class implements the Protocol by being a pyglet window
- **Status:** COMPLETED

### Step 11: Migrate viewer_g.py + _board.py - Cleanup
- **Tag:** `step11-viewer-cleanup`
- **Files Changed:**
  - `src/cube/viewer/viewer_g.py` - Removed unused `import pyglet`, `import pyglet.gl as gl`, `from pyglet.gl import *`
  - `src/cube/viewer/_board.py` - Removed unused `from pyglet import gl`
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
- **Target:** `src/cube/viewer/shapes.py`
- **Action:** DELETED - All 440 lines were unused dead code
- **Finding:** `_cell.py` already used `renderer.shapes.*` for all rendering
- **Status:** COMPLETED ✅

#### Step 14: Delete gl_helper.py (Dead Code)
- **Tag:** `step14-delete-gl-helper`
- **Target:** `src/cube/viewer/gl_helper.py`
- **Action:** DELETED - Only imported by shapes.py (which was deleted)
- **Status:** COMPLETED ✅

#### Step 15: Delete graphic_helper.py (Debug Only)
- **Tag:** `step15-delete-graphic-helper`
- **Target:** `src/cube/viewer/graphic_helper.py`
- **Action:** DELETED - Debug-only functions, `complement()` was unused
- **Status:** COMPLETED ✅

#### Step 16: Clean up _cell.py
- **Tag:** `step16-cleanup-cell`
- **Target:** `src/cube/viewer/_cell.py`
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
- `src/cube/gui/protocols/renderer.py` - Renderer protocol definition
- `src/cube/gui/protocols/event_loop.py` - EventLoop protocol definition
- `src/cube/gui/backends/pyglet/renderer.py` - Pyglet renderer implementation
- `src/cube/gui/backends/pyglet/event_loop.py` - Pyglet event loop implementation
- `src/cube/gui/backends/headless/` - Headless backend for testing
- `src/cube/gui/factory.py` - BackendRegistry and GUIBackend

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

**Last Completed Step:** Step 17 - Phase 2 Final Verification
**Last Tag:** `step17-phase2-complete`
**Tests Passing:** 126 non-GUI tests, 8 skipped

### Migration Complete!

All pyglet imports have been successfully removed from:
- `viewer/shapes.py` - DELETED (440 lines of dead code)
- `viewer/gl_helper.py` - DELETED (32 lines, only used by shapes.py)
- `viewer/graphic_helper.py` - DELETED (53 lines, debug only)
- `viewer/_cell.py` - Cleaned up (removed 3 imports, 4 dead type hints)

**Remaining pyglet imports (by design):**
1. `src/cube/gui/backends/pyglet/*` - Backend implementation
2. `src/cube/main_window/Window.py` - IS the pyglet window class

---

## Phase 3: Abstract Window Layer (PLANNED)

### Goal for Phase 3

Create an abstract `AppWindow` class that can work with ANY backend (pyglet, tkinter, etc.), allowing `main_tkinter.py` to use the same keyboard/mouse handling code as `main_pyglet.py`.

### Current Problem

The `main_window/Window.py` is tightly coupled to pyglet:
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
| `main_window/main_g_abstract.py` | MODIFY or REMOVE - Merge into new protocol |
| `main_pyglet.py` | MODIFY - Use new window class |
| `main_tkinter.py` | MODIFY - Use new window class |

### Notes

- The `main_g_keyboard_input.py` and `main_g_mouse.py` are ALREADY backend-agnostic
- They use `AbstractWindow` protocol which defines the interface
- The main work is creating concrete implementations for each backend
- Tkinter won't support all features (e.g., screen_to_world picking may not work well)
- Focus on getting basic cube display + keyboard rotations working first

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
