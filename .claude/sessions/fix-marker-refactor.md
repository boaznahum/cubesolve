# fix-marker-refactor Branch Session Notes

## How This Session Started

### Background

Branch `gui-improvements` had a bad commit `6d73535f` ("Replace MarkerConfig god-class with concrete MarkerCreator per shape") that caused GUI tests run from PyCharm to get stuck.

User ran `git bisect` and identified:
- **Last good commit:** `8d3f8fa6` ("Add MarkerCreator/MarkerToolkit architecture for self-drawing markers")
- **First bad commit:** `6d73535f` (the one above)

### What We Did

1. `git bisect reset` to exit bisect mode
2. Created branch `fix-marker-refactor` starting from the last good commit `8d3f8fa6`
3. Cherry-picked **safe parts** of the bad commit incrementally (not the risky rendering changes)
4. Disabled `git config core.autocrlf false` to avoid line-ending noise

### Commits on This Branch

| # | Hash | Description | Status |
|---|---|---|---|
| 1 | `e17cd6a8` | Rename `create_non_default()` → `create_app()` / `_create_app()`, single factory coordination, update ~30 test files | All tests pass |
| 2 | pending | Add Noop classes + conditional wiring (NoopMarkerFactory, NoopMarkerManager, NoopAnnotation) | All tests pass |

### Current State (2026-02-19)

- Branch: `fix-marker-refactor` (pushed to origin)
- Parent branch: based on `8d3f8fa6` (parent of bad commit)
- All tests pass (non-GUI and GUI)
- Commit 1 pushed, commit 2 staged but not yet committed

---

## Application Creation Flow

### Entry Points (where applications are created)

| Entry Point | Function | Animation? | Used By |
|---|---|---|---|
| **Tests/scripts** | `AbstractApp.create_app(cube_size, solver=...)` | Never | All non-GUI tests (~50 files) |
| **GUI app** | `create_app_window(backend, cube_size=..., animation=True, ...)` | If backend supports it | `run_with_backend()`, CLI |
| **GUI tests** | `AbstractApp._create_app(cube_size, animation=enable_animation)` | Variable | `GUITestRunner` |
| **Special tests** | `AbstractApp._create_app(cube_size=3, animation=True)` | Yes (explicit) | `test_query_restore_state` |

### Internal Factory: `AbstractApp._create_app()`

```
_create_app(cube_size, animation=False, ...)
    │
    ├── Creates AppConfig, ApplicationAndViewState
    │
    ├── animation=True?
    │   ├── YES → AnimationManager(vs)  →  am = AnimationManager
    │   └── NO  → am = None
    │
    └── _App(config, vs, am, cube_size, solver)
```

### Wiring Inside `_App.__init__(am)`

```
am is not None (animation)?
├── YES (GUI with animation):
│   ├── MarkerFactory()        ← real factory, creates MarkerConfig objects
│   ├── MarkerManager()        ← real manager, writes markers to PartEdge attributes
│   └── Operator(am=am)
│       └── OpAnnotation(self) ← real annotation, draws solver steps on cube
│
└── NO (tests, scripts, headless):
    ├── NoopMarkerFactory()    ← returns _NOOP singleton for all methods
    ├── NoopMarkerManager()    ← all add/remove/get are silent no-ops
    └── Operator(am=None)
        └── NoopAnnotation()   ← annotate() returns nullcontext()
```

### Single Coordination Point: `create_app_window()`

```python
# src/cube/main_any_backend.py
def create_app_window(backend_name, *, cube_size, animation=True, ...):
    backend = BackendRegistry.get_backend(backend_name)
    effective_animation = animation and backend.supports_animation  # ← key line
    app = AbstractApp._create_app(cube_size, animation=effective_animation, ...)
    return backend.create_app_window(app, width, height, title)
```

This ensures animation is only enabled when **both** the caller wants it **and** the backend supports it.

### Summary Table

| Scenario | AnimationManager | MarkerFactory | MarkerManager | Annotation |
|---|---|---|---|---|
| `create_app()` (tests) | None | NoopMarkerFactory | NoopMarkerManager | NoopAnnotation |
| `create_app_window("headless")` | None | NoopMarkerFactory | NoopMarkerManager | NoopAnnotation |
| `create_app_window("pyglet2")` | AnimationManager | MarkerFactory | MarkerManager | OpAnnotation |
| `_create_app(animation=True)` | AnimationManager | MarkerFactory | MarkerManager | OpAnnotation |

---

## What's Left on Bad Branch (`6d73535f`)

### Already Cherry-Picked

| Change | Commit |
|---|---|
| Rename `create_non_default()` → `create_app()` / `_create_app()` | `e17cd6a8` |
| `create_app_window()` as single coordination point | `e17cd6a8` |
| Update ~30 test files to use `create_app()` | `e17cd6a8` |
| Noop classes (NoopMarkerFactory, NoopMarkerManager, NoopAnnotation) | commit 2 |
| Conditional wiring in `_App.__init__` and `Operator.__init__` | commit 2 |
| `OpAnnotation` inherits `AnnotationProtocol` | commit 2 |

### NOT Taken — Marker Creator Refactor (the risky part)

| Change | Files | Lines | Risk |
|---|---|---|---|
| Delete `MarkerShape` enum | `MarkerShape.py` | -27 | Low |
| Delete `MarkerConfig` dispatch (`if shape==`) | `_marker_config.py` | -115 | **High** — this is the god-class removal |
| New concrete MarkerCreator classes (Ring, FilledCircle, Cross, Arrow, Checkmark, BoldCross, Character) | `_marker_creators.py` | +125 | **High** — new drawing code |
| Slim down `MarkerFactory` to use concrete creators | `MarkerFactory.py` | net -100 | Medium |
| Remove `isinstance(MarkerConfig)` rendering from `_cell.py` | `_cell.py` | -200 | **High** — rendering pipeline |
| Remove `isinstance(MarkerConfig)` rendering from `_modern_gl_cell.py` | `_modern_gl_cell.py` | -450 | **High** — rendering pipeline |
| `MarkerConfig` → `MarkerCreator` type hints in `OpAnnotation.py` | `OpAnnotation.py` | ~20 | Low |
| `ConsoleAppWindow` cleanup | `ConsoleAppWindow.py` | -4 | Low |
| Design doc updates | `gui_abstraction.md`, `gui_components.puml` | minor | Low |

### Why It's Risky

The rendering removal in `_cell.py` and `_modern_gl_cell.py` is **~650 lines** of `isinstance(MarkerConfig)` dispatch code deleted and replaced by the `MarkerCreator.draw(toolkit)` pattern. This is the most likely cause of the PyCharm test hang — the new `draw()` methods interact with the OpenGL rendering pipeline differently.

### Key Files Reference

- `src/cube/application/AbstractApp.py` — `create_app()`, `_create_app()`
- `src/cube/main_any_backend.py` — `create_app_window()`, `run_with_backend()`
- `src/cube/application/app.py` — `_App.__init__()` wiring
- `src/cube/application/commands/Operator.py` — annotation wiring
- `src/cube/application/markers/` — factory/manager + Noop variants
- `src/cube/domain/solver/protocols/NoopAnnotation.py`
- `tests/gui/tester/GUITestRunner.py` — GUI test app creation
