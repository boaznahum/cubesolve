
# Duck Typing Analysis

> **Date:** 2025-12-04
> **Purpose:** Identify all classes implementing protocols without explicit inheritance ("duck typing")
> **Violation of:** CLAUDE.md rule: "When implementing protocols, always inherit from them for PyCharm visibility"

---

## Claude Instructions

> **When working on fixes from this document:**
> 1. When starting a fix, change the checkbox from `[ ]` to `[♾️]` (in progress)
> 2. When the fix is complete and tested, change it to `[✅]` (done)
> 3. Update the status in Part 5 "Recommended Actions" section
> 4. After ALL fixes in a priority group are done, add completion date
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

| Category                                        | Count | Risk Level | Details Section |
|-------------------------------------------------|-------|------------|-----------------|
| Classes missing protocol inheritance            | 6     | HIGH       | Part 2          |
| `hasattr()`/`getattr()` for optional features   | 1     | HIGH       | Part 3.1        |
| `hasattr()`/`getattr()` for lazy initialization | 3     | MEDIUM     | Part 3.2        |
| Acceptable duck typing (external libs, debug)   | 6     | LOW        | Part 3.3        |

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

---

## Part 3: Runtime Duck Typing (`hasattr`/`getattr`)

### 3.1 HIGH RISK - Optional Feature Detection

```python
# FILE: backends/pyglet2/PygletAppWindow.py:391
if hasattr(self, '_renderer_adapter') and self._renderer_adapter:
    self._renderer_adapter.update_window_size(width, height)
```

**Problem:** Uses duck typing to check for optional feature instead of protocol method.

**Fix:** Add method to `AppWindow` protocol:
```python
# In AppWindow protocol:
def update_adapter_window_size(self, width: int, height: int) -> bool | None:
    """Returns None if not supported, True if updated."""
    ...
```

### 3.2 MEDIUM RISK - Lazy Attribute Initialization

| File                     | Line(s)       | Pattern                                   | Fix                      |
|--------------------------|---------------|-------------------------------------------|--------------------------|
| `pyglet/PygletWindow.py` | 329, 338, 351 | `hasattr(self, '_key_event_queue')`       | Initialize in `__init__` |
| `pyglet2/PygletWindow.py`| 333, 342, 355 | `hasattr(self, '_key_event_queue')`       | Initialize in `__init__` |
| `RenderingContext.py`    | 56, 70        | `getattr(self._local, 'renderer', None)`  | Use typed wrapper        |

**Fix Pattern:**
```python
# BEFORE:
def queue_key_events(self, events):
    if not hasattr(self, '_key_event_queue'):
        self._key_event_queue = []
    self._key_event_queue.extend(events)

# AFTER:
def __init__(self, ...):
    self._key_event_queue: list[KeyEvent] = []

def queue_key_events(self, events):
    self._key_event_queue.extend(events)
```

### 3.3 LOW RISK - Acceptable Duck Typing

These patterns are acceptable because they handle external library interop or debug-only code:

| File                 | Line            | Pattern                                  | Why Acceptable                   |
|----------------------|-----------------|------------------------------------------|----------------------------------|
| `debug.py`           | 51-52, 96-97    | `getattr(part, '_colors_id_by_colors')`  | Debug-only, inspecting internals |
| `state.py`           | 548             | `getattr(s, '_colors_id_by_colors')`     | Debug-only                       |
| `Command.py`         | 175, 186, 196   | `getattr(Algs, alg_name)`                | Idiomatic enum lookup            |
| `common_gl_utils.py` | 32              | `hasattr(value, 'contents')`             | ctypes pointer detection         |
| `TkinterWindow.py`   | 312             | `hasattr(event, 'delta')`                | Platform-specific tkinter        |
| `shaders.py`         | 290             | `hasattr(matrix, 'ctypes')`              | numpy vs ctypes dispatch         |

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

### Priority 2: Fix Pyglet2 Adapters (3 classes)
- [ ] `ModernGLViewStateManager` - add `ViewStateManager` to inheritance
- [ ] `ModernGLShapeAdapter` - add `ShapeRenderer` to inheritance
- [ ] `ModernGLRendererAdapter` - add `Renderer` to inheritance

### Priority 3: Fix Lazy Initialization (2 files)
- [ ] `pyglet/PygletWindow.py` - initialize `_key_event_queue` in `__init__`
- [ ] `pyglet2/PygletWindow.py` - initialize `_key_event_queue` in `__init__`

### Priority 4: Fix Optional Feature Detection (1 file)
- [ ] `pyglet2/PygletAppWindow.py:391` - add protocol method for adapter

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
- `__todo.md` - Task A4 (AppWindowBase inheritance mess)
