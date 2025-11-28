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

## Pending Steps

### Step 5: Add Picking to Renderer Protocol
- **Tag:** `migration-step-5-picking`
- **Files to Change:**
  - `src/cube/gui/protocols/renderer.py`
  - `src/cube/gui/backends/pyglet/renderer.py`
  - `src/cube/main_window/main_g_mouse.py`
- **Changes Needed:** Add `screen_to_world()` method to renderer protocol

### Step 6: Migrate main_g_mouse.py - Mouse Handling
- **Tag:** `migration-step-6-mouse`
- **Files to Change:** `src/cube/main_window/main_g_mouse.py`
- **Changes Needed:** Replace direct GL calls with renderer methods

### Step 7: Add Batch Protocol
- **Tag:** `migration-step-7-batch`
- **Files to Change:** TBD
- **Changes Needed:** Abstract pyglet.graphics.Batch

### Step 8: Migrate animation_manager.py - Event Loop/Clock
- **Tag:** `migration-step-8-animation`
- **Files to Change:** `src/cube/animation/animation_manager.py`
- **Changes Needed:** Abstract pyglet.app.event_loop and pyglet.clock

### Step 9: Migrate main_pyglet.py - Main Loop
- **Tag:** `migration-step-9-main-loop`
- **Files to Change:** `src/cube/main_pyglet.py`
- **Changes Needed:** Abstract main application entry point

### Step 10: Migrate Window.py + main_g_abstract.py
- **Tag:** `migration-step-10-window`
- **Files to Change:**
  - `src/cube/main_window/Window.py`
  - `src/cube/main_window/main_g_abstract.py`
- **Changes Needed:** Remove remaining direct pyglet imports

### Step 11: Migrate viewer_g.py + _faceboard.py - Cleanup
- **Tag:** `migration-step-11-viewer-cleanup`
- **Files to Change:**
  - `src/cube/viewer/viewer_g.py`
  - `src/cube/viewer/_faceboard.py`
- **Changes Needed:** Remove remaining direct pyglet imports

### Step 12: Final Verification
- **Tag:** `migration-step-12-complete`
- **Verification:** All pyglet imports removed from application code (only in backends)

## Manual Testing Instructions

After each step, run the GUI manually and verify:
1. Start: `python main_pyglet.py`
2. Test cube rotations with mouse drag
3. Test keyboard shortcuts (R, L, U, D, F, B for face rotations)
4. Test scramble (press 1, 2, or 3)
5. Test solve (press /)
6. Test animation speed (+/- keys)
7. Close window (press q or Escape)

Report any visual glitches, crashes, or unexpected behavior.

## Current Migration Status

**Last Completed Step:** Step 4 - Keyboard Input Migration
**Next Step:** Step 5 - Add Picking to Renderer Protocol
**Tests Passing:** 126 non-GUI tests, 3 GUI tests
