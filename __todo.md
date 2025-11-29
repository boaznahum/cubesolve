# Project TODO

> **How to enter symbols in PyCharm (Windows):**
> - ❌ (red X) - Not started: `Win + .` → search "cross" or "x mark" → select ❌
> - ♾️ (infinity) - In progress: `Win + .` → search "infinity" → select ♾️
> - ✅ (green V) - Completed: `Win + .` → search "check" → select ✅
> - Or copy/paste from here: `❌` `♾️` `✅`

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

- ❌ **Q2.** Add typing to all code, make sure mypy is green

---
# New entries below - Claude will reformat and move above this line

i want files with single class and name of file is case sentive as class name, ask claude architects if it is good pracice and whay 
it doesnt do it, if yes instruct clause to follow this rules in the future


use claude mecanims to add new slash commd to add new command mytodo to read __todo.md . reformat it according to the rules
