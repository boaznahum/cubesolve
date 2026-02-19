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
| 2 | `87d512b3` | Add Noop classes + conditional wiring (NoopMarkerFactory, NoopMarkerManager, NoopAnnotation) | All tests pass |
| 3 | `501817f4` | Remove redundant animation disable from ConsoleAppWindow + add assertions | All tests pass |
| 4 | `1fb2bb19` | Remove dead marker rendering methods from _cell.py and _modern_gl_cell.py (~650 lines) | All tests pass |

### Current State (2026-02-19)

- Branch: `fix-marker-refactor` (pushed to origin, 4 commits)
- Parent branch: based on `8d3f8fa6` (parent of bad commit)
- All tests pass (non-GUI and GUI)
- **Next:** Find the breaking change in the remaining diff

---

## Application Creation Flow

### Entry Points (where applications are created)

| Entry Point | Function | Animation? | Used By |
|---|---|---|---|
| **Tests/scripts** | `AbstractApp.create_app(cube_size, solver=...)` | Never | All non-GUI tests (~50 files) |
| **GUI app** | `create_app_window(backend, cube_size=..., animation=True, ...)` | If backend supports it | `run_with_backend()`, CLI |
| **GUI tests** | `AbstractApp._create_app(cube_size, animation=enable_animation)` | **Yes by default** (`--animate` defaults True) | `GUITestRunner` |
| **Special tests** | `AbstractApp._create_app(cube_size=3, animation=True)` | Yes (explicit) | `test_query_restore_state` |

### How Tests Get Noop (non-GUI tests)

```
Test calls:  AbstractApp.create_app(cube_size=3)
                    │
                    ▼
          _create_app(cube_size=3, animation=False)  ← hardcoded False
                    │
                    ▼
          animation=False → am = None
                    │
                    ▼
          _App.__init__(am=None)
              ├── NoopMarkerFactory()
              ├── NoopMarkerManager()
              └── Operator(am=None) → NoopAnnotation()
```

### How GUI App Gets Real Objects

```
CLI/main → create_app_window("pyglet2", animation=True)
                    │
                    ▼
          effective_animation = True AND backend.supports_animation
              ├── pyglet2: supports=True  → effective=True
              ├── console: supports=False → effective=False
              ├── headless: supports=False → effective=False
                    │
                    ▼
          _create_app(animation=True)
                    │
                    ▼
          am = AnimationManager(vs)
                    │
                    ▼
          _App.__init__(am=AnimationManager)
              ├── MarkerFactory()        (real)
              ├── MarkerManager()        (real)
              └── Operator(am=am) → OpAnnotation()  (real)
```

### How GUI Tests Get Real Objects (important!)

```
GUITestRunner.run_test(enable_animation=True)  ← default from --animate flag
                    │
                    ▼
          AbstractApp._create_app(animation=True)  ← bypasses create_app_window!
                    │
                    ▼
          am = AnimationManager(vs)  → real MarkerFactory, MarkerManager, OpAnnotation
```

**Note:** GUI tests bypass `create_app_window()` and call `_create_app()` directly.
This means they get real marker objects when `enable_animation=True`.

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
| `_create_app(animation=True)` (GUI tests) | AnimationManager | MarkerFactory | MarkerManager | OpAnnotation |

---

## What's Left on Bad Branch (`6d73535f`)

### Already Cherry-Picked

| Change | Commit |
|---|---|
| Rename `create_non_default()` → `create_app()` / `_create_app()` | `e17cd6a8` |
| `create_app_window()` as single coordination point | `e17cd6a8` |
| Update ~30 test files to use `create_app()` | `e17cd6a8` |
| Noop classes (NoopMarkerFactory, NoopMarkerManager, NoopAnnotation) | `87d512b3` |
| Conditional wiring in `_App.__init__` and `Operator.__init__` | `87d512b3` |
| `OpAnnotation` inherits `AnnotationProtocol` | `87d512b3` |
| ConsoleAppWindow assertions (was: remove redundant animation disable) | `501817f4` |
| Remove dead marker rendering from `_cell.py` (~196 lines) | `1fb2bb19` |
| Remove dead marker rendering from `_modern_gl_cell.py` (~450 lines) | `1fb2bb19` |

### NOT Taken — MarkerConfig → MarkerCreator Swap

These are the **only remaining changes** and must contain the breaking change:

| Change | Files | Risk | Notes |
|---|---|---|---|
| New concrete MarkerCreator classes | `_marker_creators.py` (+125 lines, NEW) | Medium | RingMarker, FilledCircleMarker, CrossMarker, ArrowMarker, CheckmarkMarker, BoldCrossMarker, CharacterMarker |
| MarkerFactory returns concrete creators | `MarkerFactory.py` (net -100) | **Suspect** | `MarkerConfig(shape=RING, ...)` → `RingMarker(...)` etc. |
| Delete `MarkerConfig` class body | `_marker_config.py` (-115) | **Suspect** | Removes draw() dispatch method |
| Delete `MarkerShape` enum | `MarkerShape.py` (-27) | Low | Just an enum |
| Type hints: MarkerConfig → MarkerCreator | `IMarkerFactory.py`, `OpAnnotation.py`, `AnnotationProtocol.py` | Low | Pure type changes |
| Docstring update | `_marker_creator_protocol.py` | None | Comment only |
| `__init__.py` export changes | `markers/__init__.py` | Low | Remove MarkerConfig/MarkerShape from exports |

### Analysis: Why These Could Cause a Hang

The draw() logic is **functionally identical**:
- Old: `MarkerConfig.draw(toolkit)` → dispatch by `self.shape` enum → `toolkit.draw_X(...)`
- New: `RingMarker.draw(toolkit)` → directly calls `toolkit.draw_ring(...)`

Same toolkit methods, same arguments. **No behavioral difference in rendering.**

Possible causes to investigate:
1. **Import-time issue** — circular imports when loading `_marker_creators.py`?
2. **Class-level cache** — `MarkerFactory._cache` is class-level dict, shared across instances. Old code cached `MarkerConfig`, new caches concrete creators. Could stale cache entries cause issues?
3. **Hashability difference** — `get_markers_from_part_edge()` deduplicates markers by using them as dict keys. MarkerConfig had ALL fields (shape, direction, character even when unused). Concrete classes only have relevant fields. Different hash = different dedup behavior?
4. **PyCharm-specific** — PyCharm debugger interaction with frozen dataclasses? (user said "from PyCharm")

### TODO / Design Gaps

- **TODO: Single coordination point is not enforced.** `create_app_window()` correctly checks `backend.supports_animation`, but nothing prevents calling `_create_app(animation=True)` and passing the app directly to a non-animation backend. GUITestRunner does exactly this. Consider: (a) making backends assert/validate animation state, or (b) making `_create_app` truly private.
- **TODO: GUITestRunner bypasses coordination point.** It calls `_create_app()` directly, not `create_app_window()`. This means the `backend.supports_animation` check is skipped.
- **TODO: Find the breaking change.** The remaining diff (MarkerConfig→MarkerCreator swap) is the only suspect. Need to apply incrementally and test.

### Key Files Reference

- `src/cube/application/AbstractApp.py` — `create_app()`, `_create_app()`
- `src/cube/main_any_backend.py` — `create_app_window()`, `run_with_backend()`
- `src/cube/application/app.py` — `_App.__init__()` wiring
- `src/cube/application/commands/Operator.py` — annotation wiring
- `src/cube/application/markers/` — factory/manager + Noop variants
- `src/cube/domain/solver/protocols/NoopAnnotation.py`
- `tests/gui/tester/GUITestRunner.py` — GUI test app creation (bypasses create_app_window!)
- `tests/gui/conftest.py` — `--animate` defaults True, `--speed-up` defaults 3
