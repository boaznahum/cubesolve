# Project TODO

> **How to enter symbols in PyCharm (Windows):**
> - ❌ (red X) - Not started: `Win + .` → search "cross" or "x mark" → select ❌
> - ♾️ (infinity) - In progress: `Win + .` → search "infinity" → select ♾️
> - ✅ (green V) - Completed: `Win + .` → search "check" → select ✅
> - Or copy/paste from here: `❌` `♾️` `✅`
>
> **Claude: When starting work on a task, change its status to ♾️ (in progress) BEFORE beginning work.**

---

## Bugs

- ❌ **B1.** Investigate GUI test bug that fails in slow animation
  - See CLAUDE.md "Known Issues" section for details
  - Root cause: Lazy cache initialization in `Part.colors_id` / `Part.position_id`
  - Workaround: Use `--speed-up 5` in tests

## GUI & Testing

- ❌ **G1.** Make sure all test_gui run with all backends
  - Need an abstract mechanism of key sequences that alternates to the keys that the backend understands
  - The backend will be a pytest fixture, the default should be "all" meaning all backends

- ❌ **G2.** Investigate pyopengltk as alternative to pure Canvas rendering for tkinter backend
  - Would allow reusing OpenGL code from pyglet backend
  - True 3D rendering instead of 2D isometric projection
  - Adds external dependency (`pip install pyopengltk`)

## Architecture

- ✅ **A1.** Move main window factory to backend, not a special factory in main_any
  - Added `app_window_factory` to `_BackendEntry` and `GUIBackend.create_app_window()`
  - Animation manager wiring is now in `GUIBackend.create_app_window()`

- ❌ **A2.** Introduce commands injecting instead of keys, simplify key handling

- ❌ **A3.** Consider moving animation manager wiring from GUIBackend to elsewhere
  - Currently `GUIBackend.create_app_window()` wires up `app.am.set_event_loop()`
  - This creates coupling between GUIBackend and AbstractApp
  - Options: move to AbstractApp, make it explicit in main_any, or keep as-is

## Code Quality

- ❌ **Q1.** Refactor too many packages under `src/cube`
  - Ask Claude architects to rearrange them by layers

- ✅ **Q2.** Add typing to all code, make sure mypy is green
  - Completed: 0 errors in 141 source files (down from 57 errors)
  - Fixed: protocol signatures, abstract class implementations, None/Optional narrowing,
    wrong argument types, variable/import conflicts, missing protocol members
  - Added `disable_error_code = import-untyped` to `mypy.ini` for pyglet (no type stubs)

- ❌ **Q3.** File naming convention: single class per file with case-sensitive filename matching class name
  - Example: `class MyClass` should be in `MyClass.py` (not `my_class.py`)
  - Research: Is this good practice? Why doesn't Python community follow this?
  - If approved: Add to CLAUDE.md as coding standard

- ✅ **Q4.** Create `/mytodo` slash command to read and manage `__todo.md`
  - Created `.claude/commands/mytodo.md`

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

---
# New entries below - Claude will reformat and move above this line