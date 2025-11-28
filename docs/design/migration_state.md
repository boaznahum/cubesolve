# GUI Abstraction Migration State

## Overview
This document tracks the progress of migrating from direct pyglet/OpenGL calls to the renderer abstraction layer.

## Test Requirements Per Step
Before marking a step complete and tagging:
1. Run all algorithm tests: `pytest tests/algs -v`
2. Run all GUI tests: `pytest tests/gui -v`
3. Run manual GUI test: `python main_pyglet.py` - user confirms it works

## Completed Steps

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
- **Manual Test Focus:** Test mouse clicking and dragging on cube faces - should still work correctly
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
- **Bug Fix:** Initial implementation incorrectly assumed pyglet mouse events use top-left origin.
  Pyglet uses OpenGL convention (bottom-left origin, y=0 at bottom). Removed unnecessary Y-flip
  from `screen_to_world()` which was causing mouse picking to select wrong faces.
- **Manual Test Focus:** Right-click drag to rotate view, left-drag on faces to rotate slices, shift/ctrl+click
- **Status:** COMPLETED

### Step 7: Remove Unused Batch
- **Tag:** `migration-step-7-batch`
- **Files Changed:**
  - `src/cube/main_window/Window.py` - Removed `self.batch` and `pyglet.graphics.Batch()` creation
  - `src/cube/viewer/viewer_g.py` - Removed `batch` parameter from `GCubeViewer.__init__()`
  - `src/cube/viewer/_board.py` - Removed `batch` parameter and `self.batch` attribute
  - `src/cube/viewer/_faceboard.py` - Removed `batch` parameter and `self._batch` attribute
  - `src/cube/viewer/_cell.py` - Removed `batch` parameter, removed `from pyglet.graphics import Batch`
- **Changes:**
  - The `pyglet.graphics.Batch` was being passed through the entire viewer hierarchy but never used
  - `self.batch.draw()` in Window was already commented out
  - Removed all Batch-related imports, parameters, and attributes
  - No protocol needed - Batch was dead code
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
  - No direct pyglet imports in animation_manager.py
- **Status:** COMPLETED

### Step 9: Migrate main_pyglet.py - Main Loop
- **Tag:** `step9-mainloop-migration`
- **Files Changed:** `src/cube/main_pyglet.py`
- **Changes:**
  - Removed `import pyglet` (no direct pyglet import)
  - Changed `pyglet.app.run()` to `backend.event_loop.run()`
- **Bug Fix:** Initial implementation used manual stepping loop which didn't trigger window redraws.
  Fixed by using `pyglet.app.run()` in PygletEventLoop.run() instead of manual while loop.
- **Status:** COMPLETED

### Step 10: Migrate Window.py + main_g_abstract.py
- **Tag:** `step10-abstractwindow-protocol`
- **Files Changed:**
  - `src/cube/main_window/main_g_abstract.py` - Converted AbstractWindow from class to Protocol
  - `src/cube/main_window/Window.py` - Now inherits directly from `pyglet.window.Window`
- **Changes:**
  - AbstractWindow is now a `@runtime_checkable` Protocol defining the interface
  - Window class implements the Protocol by being a pyglet window
  - Keyboard/mouse handlers use the Protocol, not concrete Window class
- **Status:** COMPLETED

### Step 11: Migrate viewer_g.py + _board.py - Cleanup
- **Tag:** `step11-viewer-cleanup`
- **Files Changed:**
  - `src/cube/viewer/viewer_g.py` - Removed unused `import pyglet`, `import pyglet.gl as gl`, `from pyglet.gl import *`
  - `src/cube/viewer/_board.py` - Removed unused `from pyglet import gl`
- **Changes:** Cleanup of unused imports - active pyglet code remains in pyglet backend files
- **Status:** COMPLETED

### Step 12: Final Verification
- **Tag:** `step12-final-verification`
- **Verification:**
  - All non-GUI tests pass: 126 passed, 8 skipped
  - All GUI tests pass: 3 passed
  - Manual GUI verified working
- **Status:** COMPLETED ✅

## Migration Complete

The core abstraction layer migration is **COMPLETE**.

### Remaining Direct OpenGL Code (Intentional)

These files contain direct pyglet/OpenGL calls and are part of the **pyglet backend**:

| File | Notes |
|------|-------|
| `viewer/_cell.py` | Low-level GL rendering |
| `viewer/shapes.py` | Shape primitives |
| `viewer/texture.py` | Texture loading |
| `viewer/viewer_g_ext.py` | draw_axis() helper |
| `app/app_state.py` | Matrix operations |
| `main_window/Window.py` | draw_text() orthographic |

These would only need abstraction if adding another 3D backend (e.g., Vulkan).

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

## Current Migration Status

**Last Completed Step:** Step 12 - Final Verification
**Last Tag:** `step12-final-verification`
**Status:** MIGRATION COMPLETE ✅
**Tests Passing:** 126 non-GUI tests, 3 GUI tests, manual GUI verified
