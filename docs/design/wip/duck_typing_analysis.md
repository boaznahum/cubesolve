
# Duck Typing Analysis

> **Date:** 2025-12-04 (Updated: 2025-12-05)
> **Purpose:** Identify all classes implementing protocols without explicit inheritance ("duck typing")
> **Violation of:** CLAUDE.md rule: "When implementing protocols, always inherit from them for PyCharm visibility"
> **Status:** ✅ ALL fixable items complete. Only acceptable duck typing remains (metaclass conflicts, external libs).

---

## Claude Instructions

> **When working on fixes from this document:**
> 1. When starting a fix, change the checkbox from `[ ]` to `[♾️]` (in progress)
> 2. When the fix is complete and tested, change it to `[✅]` (done)
> 3. Update the status in Part 5 "Recommended Actions" section
> 4. After ALL fixes in a priority group are done, add completion date
> 5. Whenever you change in presentation elements and GUI, update the UML diagrams
> 6. Protocols should be named with `I` prefix (like Java interfaces), e.g., `IWindow` instead of `Window`
> 7. In UML diagrams, show duck typing with bold red dashed lines labeled "duck" to visualize the full picture
>
> **Status symbols:**
> - `[ ]` - Not started
> - `[♾️]` - In progress
> - `[✅]` - Completed

---

## Executive Summary

This analysis identifies **two categories** of duck typing issues in the codebase:

1. **Protocol Implementation Without Inheritance** - Classes that implement all methods of a protocol but don't inherit from it
2. **Runtime Duck Typing** - Use of `getattr()`/`hasattr()` to check for optional features instead of protocol methods

### Key Findings

| Category                                        | Count | Risk Level | Status    | Details Section |
|-------------------------------------------------|-------|------------|-----------|-----------------|
| Classes missing protocol inheritance            | 6     | HIGH       | ✅ FIXED  | Part 2          |
| `hasattr()`/`getattr()` for optional features   | 1     | HIGH       | ✅ FIXED  | Part 3.1        |
| `hasattr()`/`getattr()` for lazy initialization | 0     | MEDIUM     | ✅ N/A    | Part 3.2        |
| Acceptable duck typing (external libs, debug)   | 6     | LOW        | OK        | Part 3.3        |
| PygletAppWindow metaclass conflict              | 2     | LOW        | OK        | Documented      |

---

## Part 1: Protocol Definitions

The codebase defines **10 protocols** in `src/cube/presentation/gui/protocols/`:

| Protocol             | File                      | Methods | @runtime_checkable |
|----------------------|---------------------------|---------|:------------------:|
| `Renderer`           | `Renderer.py:16`          | 12      | ✅                 |
| `ShapeRenderer`      | `ShapeRenderer.py:13`     | 14      | ✅                 |
| `DisplayListManager` | `DisplayListManager.py:13`| 7       | ✅                 |
| `ViewStateManager`   | `ViewStateManager.py:13`  | 10      | ✅                 |
| `TextRenderer`       | `TextRenderer.py:13`      | 2       | ✅                 |
| `EventLoop`          | `EventLoop.py:11`         | 12      | ✅                 |
| `Window`             | `Window.py:14`            | 18      | ✅                 |
| `AppWindow`          | `AppWindow.py:20`         | 16      | ✅                 |
| `AnimationBackend`   | `AnimationBackend.py:16`  | 8       | ✅                 |
| `AnimatableViewer`   | `AnimatableViewer.py:21`  | 3       | ✅                 |

---

## Part 2: Classes Missing Protocol Inheritance (HIGH RISK)

These classes implement all required protocol methods but **do NOT inherit** from the protocol:

### 2.1 Web Backend (All 3 classes are ducks!)

```
┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/web/WebAppWindow.py:25                           │
│ CLASS: WebAppWindow                                             │
│ SHOULD INHERIT: AppWindow                                       │
│ ACTUALLY INHERITS: AppWindowBase (ABC only, not protocol)       │
│                                                                 │
│ EVIDENCE: Has all AppWindow methods:                            │
│   - app, viewer, renderer, animation_running (properties)       │
│   - run(), close(), cleanup(), update_gui_elements()            │
│   - inject_key(), inject_command(), set_mouse_visible()         │
│   - get_opengl_info(), adjust_brightness(), get_brightness()    │
│   - adjust_background(), get_background()                       │
│   - cycle_texture_set(), load_texture_set()                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/web/WebWindow.py:15                              │
│ CLASS: WebTextRenderer                                          │
│ SHOULD INHERIT: TextRenderer                                    │
│ ACTUALLY INHERITS: (nothing)                                    │
│                                                                 │
│ EVIDENCE: Has all TextRenderer methods:                         │
│   - draw_label(), clear_labels()                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/web/WebWindow.py:56                              │
│ CLASS: WebWindow                                                │
│ SHOULD INHERIT: Window                                          │
│ ACTUALLY INHERITS: (nothing)                                    │
│                                                                 │
│ EVIDENCE: Has all Window methods:                               │
│   - width, height, text, closed (properties)                    │
│   - set_title(), set_visible(), set_size(), close()             │
│   - request_redraw(), set_mouse_visible()                       │
│   - set_draw_handler(), set_resize_handler()                    │
│   - set_key_press_handler(), set_key_release_handler()          │
│   - set_mouse_press_handler(), set_mouse_release_handler()      │
│   - set_mouse_drag_handler(), set_mouse_scroll_handler()        │
│   - set_close_handler()                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Pyglet2 Backend Adapters

```
┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/pyglet2/ModernGLRenderer.py:1082                 │
│ CLASS: ModernGLViewStateManager                                 │
│ SHOULD INHERIT: ViewStateManager                                │
│ ACTUALLY INHERITS: (nothing)                                    │
│                                                                 │
│ DOCSTRING SAYS: "This adapter implements the ViewStateManager   │
│                  protocol" - but doesn't inherit!               │
│                                                                 │
│ EVIDENCE: Has all ViewStateManager methods:                     │
│   - set_projection(), push_matrix(), pop_matrix()               │
│   - load_identity(), translate(), rotate(), scale()             │
│   - multiply_matrix(), look_at(), screen_to_world()             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/pyglet2/ModernGLRenderer.py:1172                 │
│ CLASS: ModernGLShapeAdapter                                     │
│ SHOULD INHERIT: ShapeRenderer                                   │
│ ACTUALLY INHERITS: (nothing)                                    │
│                                                                 │
│ EVIDENCE: Has ShapeRenderer methods:                            │
│   - quad(), line(), box_with_lines()                            │
│   (May be missing some methods - partial implementation?)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FILE: backends/pyglet2/ModernGLRenderer.py:1197                 │
│ CLASS: ModernGLRendererAdapter                                  │
│ SHOULD INHERIT: Renderer                                        │
│ ACTUALLY INHERITS: (nothing)                                    │
│                                                                 │
│ DOCSTRING SAYS: "This adapter makes ModernGLRenderer compatible │
│                  with code that expects the legacy Renderer     │
│                  protocol" - but doesn't inherit!               │
│                                                                 │
│ EVIDENCE: Has Renderer properties:                              │
│   - view, shapes, display_lists (properties)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Is Bad

1. **No IDE autocomplete** - PyCharm/VSCode can't know these classes satisfy protocols
2. **No static type checking** - mypy won't catch missing methods
3. **No runtime verification** - `isinstance(obj, Protocol)` won't work
4. **Violates project rules** - CLAUDE.md explicitly requires protocol inheritance

### Fix Pattern

```python
# BEFORE (duck typing):
class WebTextRenderer:
    def draw_label(self, text: str, ...) -> None: ...
    def clear_labels(self) -> None: ...

# AFTER (explicit inheritance):
from cube.presentation.gui.protocols.TextRenderer import TextRenderer

class WebTextRenderer(TextRenderer):
    def draw_label(self, text: str, ...) -> None: ...
    def clear_labels(self) -> None: ...
```

### Fix Pattern for Partial Implementations

When a class only implements a subset of protocol methods, create an abstract base class
with default no-op implementations for all methods. This allows partial implementations
to inherit and only override what they need.

```python
# STEP 1: Create AbstractShapeRenderer with no-op defaults
from cube.presentation.gui.protocols.ShapeRenderer import ShapeRenderer

class AbstractShapeRenderer(ShapeRenderer):
    """Abstract base class providing default no-op implementations."""

    def quad(self, vertices, color) -> None:
        pass  # No-op default

    def quad_with_border(self, vertices, face_color, line_width, line_color) -> None:
        pass  # No-op default

    def triangle(self, vertices, color) -> None:
        pass  # No-op default

    # ... all other methods with no-op defaults ...

# STEP 2: Partial implementation inherits from abstract class
class ModernGLShapeAdapter(AbstractShapeRenderer):
    """Only implements quad, triangle, line - inherits no-ops for rest."""

    def quad(self, vertices, color) -> None:
        # Real implementation
        self._renderer.set_color(*color)
        self._renderer.quad(vertices)

    def triangle(self, vertices, color) -> None:
        # Real implementation
        ...

    def line(self, p1, p2, width, color) -> None:
        # Real implementation
        ...
    # Other methods inherited as no-ops from AbstractShapeRenderer
```

**Benefits:**
1. Partial implementations satisfy the protocol via inheritance
2. No repeated stub methods in each partial class
3. `isinstance(obj, ShapeRenderer)` works correctly
4. IDE autocomplete and type checking work

---

## Part 3: Runtime Duck Typing (`hasattr`/`getattr`)

### 3.1 HIGH RISK - Optional Feature Detection ✅ FIXED 2025-12-05

```python
# FILE: backends/pyglet2/PygletAppWindow.py:391
# WAS:
if hasattr(self, '_renderer_adapter') and self._renderer_adapter:
    self._renderer_adapter.update_window_size(width, height)

# NOW FIXED - initialize attribute before super().__init__():
self._renderer_adapter: ModernGLRendererAdapter | None = None
# ...
if self._renderer_adapter:  # No more hasattr()
    self._renderer_adapter.update_window_size(width, height)
```

**Problem:** Used duck typing to check for optional feature.

**Fix Applied:** Initialize `_renderer_adapter = None` before `super().__init__()` so the attribute always exists.

### 3.2 MEDIUM RISK - Lazy Attribute Initialization ✅ N/A

**Status:** No issues remaining. The `PygletWindow.py` files no longer exist - window functionality was refactored into `PygletAppWindow` and `WindowBase`.

| File                     | Line(s)       | Pattern                                   | Status                   |
|--------------------------|---------------|-------------------------------------------|--------------------------|
| `pyglet/PygletWindow.py` | N/A           | File removed                              | ✅ N/A                   |
| `pyglet2/PygletWindow.py`| N/A           | File removed                              | ✅ N/A                   |
| `RenderingContext.py`    | 56, 70        | `getattr(self._local, 'renderer', None)`  | ✅ Acceptable (thread-local) |

**Note:** `RenderingContext.py` uses `getattr(self._local, 'renderer', None)` which is the standard Python pattern for thread-local storage. This is acceptable because `threading.local()` doesn't have a predefined schema - attributes are created dynamically per thread.

### 3.3 LOW RISK - Acceptable Duck Typing

These patterns are acceptable because they handle external library interop or debug-only code:

| File                 | Line            | Pattern                                  | Why Acceptable                   |
|----------------------|-----------------|------------------------------------------|----------------------------------|
| `debug.py`           | 51-52, 96-97    | `slice_._colors_id_by_colors` (direct)   | Debug-only, inspecting internals |
| `Command.py`         | 175, 186, 196   | `getattr(Algs, alg_name)`                | Idiomatic enum lookup            |
| `common_gl_utils.py` | 32              | `hasattr(value, 'contents')`             | ctypes pointer detection         |
| `TkinterWindow.py`   | 312             | `hasattr(event, 'delta')`                | Platform-specific tkinter        |
| `shaders.py`         | 290             | `hasattr(matrix, 'ctypes')`              | numpy vs ctypes dispatch         |
| `RenderingContext.py`| 56, 70          | `getattr(self._local, 'renderer', None)` | Thread-local storage pattern     |

**Note:** `state.py:548` was fixed - removed unnecessary getattr (2025-12-05)

---

## Part 4: Classes That Correctly Inherit Protocols

For comparison, these classes follow the correct pattern:

### Pyglet Backend (Legacy)
```python
# PygletRenderer.py
class PygletShapeRenderer(ShapeRenderer): ...
class PygletDisplayListManager(DisplayListManager): ...
class PygletViewStateManager(ViewStateManager): ...
class PygletRenderer(Renderer): ...

# PygletEventLoop.py
class PygletEventLoop(EventLoop): ...

# PygletAnimation.py
class PygletAnimationBackend(AnimationBackend): ...
```

### Headless Backend
```python
class HeadlessRenderer(Renderer): ...
class HeadlessEventLoop(EventLoop): ...
class HeadlessAppWindow(AppWindowBase, AppWindow): ...
```

### Console Backend
```python
class ConsoleRenderer(Renderer): ...
class ConsoleEventLoop(EventLoop): ...
class ConsoleAppWindow(AppWindowBase, AppWindow): ...
```

### Tkinter Backend
```python
class TkinterRenderer(Renderer): ...
class TkinterEventLoop(EventLoop): ...
class TkinterAppWindow(AppWindowBase, AnimationWindow, AppWindow): ...
```

---

## Part 5: Recommended Actions

### Priority 1: Fix Web Backend (3 classes) ✅ Done 2025-12-04
- [✅] `WebAppWindow` - add `AppWindow` to inheritance
- [✅] `WebTextRenderer` - add `TextRenderer` to inheritance
- [✅] `WebWindow` - add `Window` to inheritance

### Priority 2: Fix Pyglet2 Adapters (3 classes) ✅ Done 2025-12-04
- [✅] `ModernGLViewStateManager` - add `ViewStateManager` to inheritance (full implementation)
- [✅] `ModernGLShapeAdapter` - created `AbstractShapeRenderer` with no-op defaults, inherits from it
- [✅] `ModernGLRendererAdapter` - created `AbstractRenderer` with no-op defaults, inherits from it

### Priority 3: Move AppWindowBase to protocols package ✅ Done 2025-12-05
- [✅] Move `AppWindowBase` to `protocols/AppWindowBase.py`
- [✅] Update all backends to import from `protocols.AppWindowBase`
- [✅] Delete duplicate `AppWindowBase` files from backend folders

### Priority 4: Create AbstractWindow and WindowBase for Window protocol ✅ Done 2025-12-05
- [✅] Create `protocols/AbstractWindow.py` with no-op defaults for Window
- [✅] Create `protocols/WindowBase.py` with shared Window implementation
- [✅] HeadlessWindow inherits from WindowBase

### Priority 5: Standardize naming conventions (OPTIONAL - LOW VALUE)
- [ ] Rename protocols to use `I` prefix (e.g., `Window` → `IWindow`)
- [ ] Verify 4-level architecture: Interface (`I*`) → Abstract (`Abstract*`) → Base (`*Base`) → Concrete
- **Note:** This is a cosmetic change with significant churn. Current naming works fine.

### Priority 6: Fix Lazy Initialization ✅ N/A - Files removed
- [✅] `PygletWindow.py` files no longer exist - refactored into PygletAppWindow
- [✅] `_key_event_queue` is now properly initialized in `WindowBase.__init__`

### Priority 7: Fix Optional Feature Detection (1 file) ✅ Done 2025-12-05
- [✅] `pyglet2/PygletAppWindow.py:391` - initialize `_renderer_adapter = None` before `super().__init__()`

### Priority 8: Fix debug.py type annotations ✅ Done 2025-12-05
- [✅] Add proper type annotations to `debug.py`
- [✅] Handle Part vs PartSlice correctly (see `docs/design/domain_model.md`)

---

## Appendix: Full Protocol Method Signatures

<details>
<summary>Click to expand all protocol definitions</summary>

### Renderer Protocol
```python
@runtime_checkable
class Renderer(Protocol):
    @property
    def shapes(self) -> ShapeRenderer: ...
    @property
    def display_lists(self) -> DisplayListManager: ...
    @property
    def view(self) -> ViewStateManager: ...
    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None: ...
    def setup(self) -> None: ...
    def cleanup(self) -> None: ...
    def begin_frame(self) -> None: ...
    def end_frame(self) -> None: ...
    def flush(self) -> None: ...
    def load_texture(self, file_path: str) -> TextureHandle | None: ...
    def bind_texture(self, texture: TextureHandle | None) -> None: ...
    def delete_texture(self, texture: TextureHandle) -> None: ...
```

### ShapeRenderer Protocol
```python
@runtime_checkable
class ShapeRenderer(Protocol):
    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None: ...
    def quad_with_border(self, vertices: Sequence[Point3D], face_color: Color3,
                         line_width: float, line_color: Color3) -> None: ...
    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None: ...
    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None: ...
    def sphere(self, center: Point3D, radius: float, color: Color3) -> None: ...
    def cylinder(self, p1: Point3D, p2: Point3D, radius1: float, radius2: float,
                 color: Color3) -> None: ...
    def disk(self, center: Point3D, normal: Point3D, inner_radius: float,
             outer_radius: float, color: Color3) -> None: ...
    def lines(self, points: Sequence[tuple[Point3D, Point3D]], width: float,
              color: Color3) -> None: ...
    def quad_with_texture(self, vertices: Sequence[Point3D], color: Color3,
                          texture: TextureHandle | None,
                          texture_map: TextureMap | None) -> None: ...
    def cross(self, vertices: Sequence[Point3D], line_width: float,
              line_color: Color3) -> None: ...
    def lines_in_quad(self, vertices: Sequence[Point3D], n: int, line_width: float,
                      line_color: Color3) -> None: ...
    def box_with_lines(self, bottom_quad: Sequence[Point3D], top_quad: Sequence[Point3D],
                       face_color: Color3, line_width: float, line_color: Color3) -> None: ...
    def full_cylinder(self, p1: Point3D, p2: Point3D, outer_radius: float,
                      inner_radius: float, color: Color3) -> None: ...
```

### ViewStateManager Protocol
```python
@runtime_checkable
class ViewStateManager(Protocol):
    def set_projection(self, width: int, height: int, fov_y: float = 50.0,
                       near: float = 0.1, far: float = 100.0) -> None: ...
    def push_matrix(self) -> None: ...
    def pop_matrix(self) -> None: ...
    def load_identity(self) -> None: ...
    def translate(self, x: float, y: float, z: float) -> None: ...
    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None: ...
    def scale(self, x: float, y: float, z: float) -> None: ...
    def multiply_matrix(self, matrix: Matrix4x4) -> None: ...
    def look_at(self, eye_x: float, eye_y: float, eye_z: float,
                center_x: float, center_y: float, center_z: float,
                up_x: float, up_y: float, up_z: float) -> None: ...
    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]: ...
```

### AppWindow Protocol
```python
@runtime_checkable
class AppWindow(Protocol):
    @property
    def app(self) -> AbstractApp: ...
    @property
    def viewer(self) -> GCubeViewer: ...
    @property
    def renderer(self) -> Renderer: ...
    @property
    def animation_running(self) -> bool: ...
    def run(self) -> None: ...
    def close(self) -> None: ...
    def cleanup(self) -> None: ...
    def update_gui_elements(self) -> None: ...
    def inject_key(self, key: int, modifiers: int = 0) -> None: ...
    def inject_command(self, command: Command) -> None: ...
    def set_mouse_visible(self, visible: bool) -> None: ...
    def get_opengl_info(self) -> str: ...
    def adjust_brightness(self, delta: float) -> float | None: ...
    def get_brightness(self) -> float | None: ...
    def adjust_background(self, delta: float) -> float | None: ...
    def get_background(self) -> float | None: ...
    def cycle_texture_set(self) -> str | None: ...
    def load_texture_set(self, directory: str) -> int: ...
```

</details>

---

## Related Documentation

- `CLAUDE.md` - Protocol Implementation Pattern section
- `docs/design/gui_abstraction.md` - GUI architecture overview
- `docs/design/domain_model.md` - Cube domain model (Part vs PartSlice)
- `__todo.md` - Task A4 (AppWindowBase inheritance mess)

---

## Session Summary (2025-12-05) - DUCK TYPING ANALYSIS COMPLETE ✅

### Status: All Fixable Issues Resolved

All duck typing issues that could be fixed have been fixed. The remaining cases are:

1. **PygletAppWindow (pyglet + pyglet2 backends)** - Cannot inherit from AppWindow due to metaclass conflict with `pyglet.window.Window`. This is documented and visualized in UML with red dashed "duck" lines.

2. **Acceptable patterns** - Thread-local storage (`RenderingContext`), external library interop (ctypes, numpy, tkinter), and enum lookup are all standard Python patterns.

### What Was Fixed (Previous Sessions)

1. **Web Backend Protocol Inheritance** (Priority 1) ✅
2. **Pyglet2 Adapter Protocol Inheritance** (Priority 2) ✅
3. **AppWindowBase moved to protocols** (Priority 3) ✅
4. **AbstractWindow and WindowBase created** (Priority 4) ✅
5. **PygletWindow.py files removed** (Priority 6) - Refactored into PygletAppWindow
6. **hasattr in PygletAppWindow** (Priority 7) ✅
7. **debug.py type annotations** (Priority 8) ✅

### Remaining (Optional/Low Value)

- **Priority 5: I-prefix naming** - Cosmetic change with significant churn. Not recommended.

### Key Architecture Points

1. **4-Level Hierarchy** is in place:
   - Protocol (Window, AppWindow, Renderer, etc.)
   - Abstract (AbstractWindow, AbstractRenderer, AbstractShapeRenderer)
   - Base (WindowBase, AppWindowBase)
   - Concrete (HeadlessWindow, PygletAppWindow, etc.)

2. **PygletAppWindow duck typing is acceptable** due to metaclass conflict - documented in code and UML

3. **No `hasattr(self, ...)` patterns** remain in the codebase (verified via grep)
