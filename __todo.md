# Project TODO

> **How to enter symbols in PyCharm (Windows):**
> - ❌ (red X): `Win + .` → search "cross" or "x mark" → select ❌
> - ✅ (green V): `Win + .` → search "check" → select ✅
> - Or copy/paste from here: `❌` `✅`

---

## GUI & Testing

- ❌ **G1.** Make sure all test_gui run with all backends
  - Need an abstract mechanism of key sequences that alternates to the keys that the backend understands
  - The backend will be a pytest fixture, the default should be "all" meaning all backends

- ❌ **G2.** Investigate pyopengltk as alternative to pure Canvas rendering for tkinter backend
  - Would allow reusing OpenGL code from pyglet backend
  - True 3D rendering instead of 2D isometric projection
  - Adds external dependency (`pip install pyopengltk`)

## Architecture

- ❌ **A1.** Move main window factory to backend, not a special factory in main_any

- ❌ **A2.** Introduce commands injecting instead of keys, simplify key handling

## Code Quality

- ❌ **Q1.** Refactor too many packages under `src/cube`
  - Ask Claude architects to rearrange them by layers

- ❌ **Q2.** Add typing to all code, make sure mypy is green
