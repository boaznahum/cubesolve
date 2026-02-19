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

## Application Creation Flow (Updated 2026-02-19)

**Design principle:** App is always born without animation. Backend injects animation if it supports it. No circular dependency.

### Entry Points

| Entry Point | Function | Animation? | Used By |
|---|---|---|---|
| **Tests/scripts** | `AbstractApp.create_app(cube_size, solver=...)` | Never | All non-GUI tests (~50 files) |
| **GUI app** | `create_app_window(backend, cube_size=..., animation=True, ...)` | Backend injects if supported | `run_with_backend()`, CLI |
| **GUI tests** | `create_app_window(backend, cube_size=..., animation=True, ...)` | Backend injects if supported | `GUITestRunner` |

### How Tests Get Noop (non-GUI tests)

```
Test calls:  AbstractApp.create_app(cube_size=3)
                    │
                    ▼
          _App.__init__(config, vs, cube_size)
              ├── _am = None
              ├── NoopMarkerFactory()
              ├── NoopMarkerManager()
              └── Operator(cube, vs) → NoopAnnotation()
```

### How GUI App Gets Real Objects (backend owns animation)

```
CLI/main → create_app_window("pyglet2", animation=True)
                    │
                    ▼
          app = AbstractApp.create_app(...)       ← always Noop
                    │
                    ▼
          backend.create_app_window(app)          ← BACKEND IS AUTHORITY
              │
              ├── if animation_factory is not None:
              │     am = AnimationManager(app.vs)
              │     app.enable_animation(am)      ← swaps Noop → real
              │     am.set_event_loop(event_loop)
              │
              └── AppWindow(app, ...)
                    │
                    ▼
          if not animation:                       ← caller opt-out
              app.op.toggle_animation_on(False)
```

### enable_animation() Injection Chain

```
app.enable_animation(am)
  ├── assert _am is None          (guard: one-shot only)
  ├── _am              = am
  ├── _marker_factory  = MarkerFactory()       (was NoopMarkerFactory)
  ├── _marker_manager  = MarkerManager()       (was NoopMarkerManager)
  └── _op.enable_animation(am, config.animation_enabled)
        ├── assert _animation_manager is None  (guard)
        ├── _animation_manager = am
        ├── _animation_enabled = animation_enabled
        └── _annotation        = OpAnnotation  (was NoopAnnotation)
```

### Summary Table

| Scenario | AnimationManager | MarkerFactory | MarkerManager | Annotation |
|---|---|---|---|---|
| `create_app()` (tests) | None | NoopMarkerFactory | NoopMarkerManager | NoopAnnotation |
| `create_app_window("headless")` | None | NoopMarkerFactory | NoopMarkerManager | NoopAnnotation |
| `create_app_window("console")` | None | NoopMarkerFactory | NoopMarkerManager | NoopAnnotation |
| `create_app_window("pyglet2")` | AnimationManager | MarkerFactory | MarkerManager | OpAnnotation |

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

- ~~**DONE: Single coordination point is not enforced.** Resolved by "backend owns animation" refactor — `_create_app()` removed, app always born without animation, backend injects via `enable_animation()`.~~
- ~~**DONE: GUITestRunner bypasses coordination point.** Resolved — GUITestRunner now uses `create_app_window()` which delegates to backend.~~
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
