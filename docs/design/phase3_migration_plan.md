# Phase 3 Migration Plan: Abstract Window Layer

**Branch:** `claude/new-gui-phase-3-01X4mUeuJiPgg79XX6ZyvaS6`
**Created:** 2025-11-29
**Status:** Planning

---

## Executive Summary

Phase 3 aims to create an **AppWindow abstraction layer** that allows both Pyglet and Tkinter backends to share the same application logic. Currently, `main_pyglet.py` (42 lines) uses the full `AbstractApp` + `Window` infrastructure, while `main_tkinter.py` (180 lines) bypasses it entirely with a custom implementation.

**Goal:** Make `main_tkinter.py` as simple as `main_pyglet.py` by:
1. Creating an `AppWindow` protocol
2. Implementing `TkinterAnimation` backend
3. Refactoring `Window.py` to use composition instead of inheritance

---

## Current State Analysis

### The Asymmetry Problem

| Aspect | main_pyglet.py | main_tkinter.py |
|--------|----------------|-----------------|
| Lines of code | 42 | 180 |
| Uses AbstractApp | ✅ Yes | ❌ No |
| Uses Window class | ✅ Yes | ❌ Custom TkinterCubeApp |
| Has Operator | ✅ Yes | ❌ No |
| Has Solver | ✅ Yes | ❌ No |
| Has Animation | ✅ Yes | ❌ No |
| Keyboard handling | ✅ Shared infrastructure | ❌ Duplicated locally |

### Root Cause

`Window` class in `src/cube/main_window/Window.py` **inherits directly from `pyglet.window.Window`**:

```python
class Window(pyglet.window.Window, AnimationWindow):  # Line 22
```

This tight coupling prevents Tkinter from reusing the same application logic.

### Pyglet Dependencies in Window.py

| Category | Count | Complexity |
|----------|-------|------------|
| Pyglet imports | 3 modules | CRITICAL |
| Class inheritance | 1 (pyglet.window.Window) | CRITICAL |
| Event handlers | 7 methods | CRITICAL |
| GL calls (draw_text) | 22 calls | HIGH |
| pyglet.text.Label | ~15 instances | HIGH |
| Key constants | 30+ symbols | MEDIUM |

### Tkinter Backend Gaps

| Feature | Pyglet | Tkinter | Gap |
|---------|--------|---------|-----|
| AnimationBackend | ✅ PygletAnimation | ❌ None | **CRITICAL** |
| 3D Rendering | ✅ OpenGL | 2D Isometric | Architectural |
| Texture support | ✅ Yes | ❌ No | Medium |
| Full app integration | ✅ Yes | ❌ No | **CRITICAL** |

---

## Migration Steps

### Step 18: Create AppWindow Protocol
**Status:** ⬜ Pending
**Estimated effort:** Medium
**Files to create:**
- `src/cube/gui/protocols/app_window.py`

**Description:**
Define the `AppWindow` protocol that abstracts window functionality for both backends.

```python
@runtime_checkable
class AppWindow(Protocol):
    """Protocol for application window combining GUI and app logic."""

    @property
    def app(self) -> AbstractApp: ...

    @property
    def viewer(self) -> GCubeViewer: ...

    @property
    def renderer(self) -> Renderer: ...

    @property
    def animation_running(self) -> bool: ...

    def update_gui_elements(self) -> None: ...
    def close(self) -> None: ...
```

**Acceptance criteria:**
- [ ] Protocol defined with all required methods
- [ ] Protocol exported from `src/cube/gui/protocols/__init__.py`
- [ ] Type hints work correctly

---

### Step 19: Create AppWindowBase Shared Logic
**Status:** ⬜ Pending
**Estimated effort:** High
**Files to create:**
- `src/cube/main_window/app_window_base.py`

**Description:**
Extract shared logic from `Window.py` into a base class that both backends can use.

**Shared logic to extract:**
- `update_text()` - Build status text (convert from pyglet.text.Label to TextRenderer)
- `update_animation_text()` - Build animation text
- `update_gui_elements()` - Coordinate updates
- Key sequence injection logic
- Error handling patterns

**Acceptance criteria:**
- [ ] AppWindowBase contains all backend-agnostic logic
- [ ] Text rendering uses TextRenderer protocol (not pyglet.text.Label)
- [ ] No pyglet imports in AppWindowBase

---

### Step 20: Implement TkinterAnimation Backend
**Status:** ⬜ Pending
**Estimated effort:** High
**Files to create:**
- `src/cube/gui/backends/tkinter/animation.py`

**Description:**
Implement `AnimationBackend` protocol for Tkinter using `tk.after()` for scheduling.

```python
class TkinterAnimation(AnimationBackend):
    def __init__(self):
        self._running = False
        self._speed = 1.0
        self._root: tk.Tk | None = None
        self._after_id: str | None = None

    def set_root(self, root: tk.Tk) -> None:
        self._root = root

    @property
    def supported(self) -> bool:
        return True

    def run_animation(self, update_func, on_complete, interval):
        # Use self._root.after() for scheduling
        ...
```

**Acceptance criteria:**
- [ ] TkinterAnimation implements AnimationBackend protocol
- [ ] Supports run_animation, cancel, pause, resume, skip
- [ ] Speed multiplier works correctly
- [ ] Registered in `backends/tkinter/__init__.py` with `animation_factory=TkinterAnimation`

---

### Step 21: Create PygletAppWindow Wrapper
**Status:** ⬜ Pending
**Estimated effort:** High
**Files to modify:**
- `src/cube/main_window/Window.py` → Refactor
**Files to create:**
- `src/cube/gui/backends/pyglet/app_window.py`

**Description:**
Refactor `Window.py` to separate pyglet-specific code into `PygletAppWindow`.

**Architecture:**
```
AppWindowBase (shared logic)
    ↓
PygletAppWindow (pyglet-specific)
    ├── Inherits from pyglet.window.Window
    ├── Implements pyglet event handlers
    └── Uses AppWindowBase for business logic
```

**Key changes:**
1. Move pyglet inheritance to PygletAppWindow
2. Move GL text rendering to PygletAppWindow
3. Keep shared logic in AppWindowBase
4. PygletAppWindow delegates to AppWindowBase

**Acceptance criteria:**
- [ ] PygletAppWindow inherits from both pyglet.window.Window and AppWindowBase
- [ ] All pyglet-specific code isolated in PygletAppWindow
- [ ] main_pyglet.py continues to work unchanged
- [ ] All tests pass

---

### Step 22: Create TkinterAppWindow
**Status:** ⬜ Pending
**Estimated effort:** High
**Files to create:**
- `src/cube/gui/backends/tkinter/app_window.py`

**Description:**
Create `TkinterAppWindow` that uses AppWindowBase with Tkinter backend.

```python
class TkinterAppWindow(AppWindowBase):
    def __init__(self, app: AbstractApp, width: int, height: int,
                 title: str, backend: GUIBackend):
        # Create TkinterWindow
        self._tk_window = TkinterWindow(width, height, title)

        # Get renderer and configure
        self._renderer = backend.renderer
        self._renderer.set_canvas(self._tk_window.canvas)

        # Initialize base class
        super().__init__(app, backend)

        # Set up event handlers
        self._tk_window.set_draw_handler(self._on_draw)
        self._tk_window.set_key_press_handler(self._on_key_press)
        # ... etc
```

**Acceptance criteria:**
- [ ] TkinterAppWindow implements AppWindow protocol
- [ ] Uses shared logic from AppWindowBase
- [ ] Integrates with TkinterAnimation
- [ ] Supports all keyboard/mouse handlers

---

### Step 23: Simplify main_tkinter.py
**Status:** ⬜ Pending
**Estimated effort:** Low
**Files to modify:**
- `src/cube/main_tkinter.py`

**Description:**
Rewrite `main_tkinter.py` to match `main_pyglet.py` structure.

**Target (should be ~45 lines):**
```python
def main():
    # Get the tkinter backend
    backend = BackendRegistry.get_backend("tkinter")

    # Create app with full infrastructure
    app = AbstractApp.create()

    # Set the event loop on the animation manager
    if app.am is not None:
        app.am.set_event_loop(backend.event_loop)

    # Create window using TkinterAppWindow
    win = TkinterAppWindow(app, 720, 720, "Cube", backend=backend)

    try:
        backend.event_loop.run()
    finally:
        win.viewer.cleanup()
```

**Acceptance criteria:**
- [ ] main_tkinter.py reduced from 180 to ~45 lines
- [ ] Uses AbstractApp.create()
- [ ] Uses TkinterAppWindow
- [ ] Has full feature parity with main_pyglet.py (within 2D limitations)

---

### Step 24: Update Factory and Registration
**Status:** ⬜ Pending
**Estimated effort:** Low
**Files to modify:**
- `src/cube/gui/factory.py`
- `src/cube/gui/backends/pyglet/__init__.py`
- `src/cube/gui/backends/tkinter/__init__.py`

**Description:**
Update BackendRegistry to support AppWindow factory.

```python
BackendRegistry.register(
    "tkinter",
    renderer_factory=TkinterRenderer,
    window_factory=lambda w, h, t: TkinterWindow(w, h, t),
    event_loop_factory=TkinterEventLoop,
    animation_factory=TkinterAnimation,  # NEW
    app_window_factory=lambda app, w, h, t, b: TkinterAppWindow(app, w, h, t, b),  # NEW
)
```

**Acceptance criteria:**
- [ ] BackendRegistry supports app_window_factory
- [ ] Both backends registered with app_window_factory
- [ ] Existing code continues to work

---

### Step 25: Final Verification and Documentation
**Status:** ⬜ Pending
**Estimated effort:** Medium
**Files to modify:**
- `docs/design/migration_state.md`
- `docs/design/phase3_migration_plan.md`

**Description:**
- Run all tests
- Verify both backends work
- Update documentation
- Create git tag `phase3-complete`

**Acceptance criteria:**
- [ ] All existing tests pass
- [ ] main_pyglet.py works as before
- [ ] main_tkinter.py works with full features
- [ ] Documentation updated
- [ ] Git tag created

---

## Architecture After Migration

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AbstractApp (Cube, Operator, Solver, AnimationMgr)   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AppWindow Protocol                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AppWindowBase (shared: text, updates, handlers)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                     │                    │                   │
│           ┌─────────┴─────────┐ ┌────────┴────────┐        │
│           │ PygletAppWindow   │ │ TkinterAppWindow │        │
│           │ (pyglet-specific) │ │ (tkinter-specific)│        │
│           └───────────────────┘ └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    GUI Backend Layer                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Renderer   │ │  EventLoop   │ │  Animation   │        │
│  │   Protocol   │ │   Protocol   │ │   Protocol   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│         │                │                │                  │
│    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐           │
│    │ Pyglet  │      │ Pyglet  │      │ Pyglet  │           │
│    │ Tkinter │      │ Tkinter │      │ Tkinter │           │
│    │Headless │      │Headless │      │   N/A   │           │
│    └─────────┘      └─────────┘      └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### File Structure After Migration

```
src/cube/
├── gui/
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── renderer.py
│   │   ├── event_loop.py
│   │   ├── window.py
│   │   ├── animation.py
│   │   └── app_window.py          # NEW - Step 18
│   │
│   ├── backends/
│   │   ├── pyglet/
│   │   │   ├── __init__.py
│   │   │   ├── renderer.py
│   │   │   ├── window.py
│   │   │   ├── event_loop.py
│   │   │   ├── animation.py
│   │   │   └── app_window.py      # NEW - Step 21
│   │   │
│   │   ├── tkinter/
│   │   │   ├── __init__.py
│   │   │   ├── renderer.py
│   │   │   ├── window.py
│   │   │   ├── event_loop.py
│   │   │   ├── animation.py       # NEW - Step 20
│   │   │   └── app_window.py      # NEW - Step 22
│   │   │
│   │   └── headless/
│   │       └── ...
│   │
│   ├── factory.py                  # MODIFIED - Step 24
│   └── types.py
│
├── main_window/
│   ├── Window.py                   # REFACTORED - Step 21
│   ├── app_window_base.py          # NEW - Step 19
│   ├── main_g_keyboard_input.py
│   ├── main_g_mouse.py
│   └── main_g_abstract.py
│
├── main_pyglet.py                  # Unchanged
└── main_tkinter.py                 # SIMPLIFIED - Step 23
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing pyglet functionality | Medium | High | Incremental changes, extensive testing |
| Animation timing differences between backends | Medium | Medium | Abstract timing, test both backends |
| 2D/3D rendering differences | Low | Low | Accept as architectural limitation |
| Complex refactoring of Window.py | High | Medium | Clear separation of concerns |

---

## Dependencies

### Step Dependencies
```
Step 18 (AppWindow Protocol)
    ↓
Step 19 (AppWindowBase) ──────────────────┐
    ↓                                      │
Step 20 (TkinterAnimation) ───────────────┤
    ↓                                      │
Step 21 (PygletAppWindow) ← depends on ───┤
    ↓                                      │
Step 22 (TkinterAppWindow) ← depends on ──┘
    ↓
Step 23 (Simplify main_tkinter.py)
    ↓
Step 24 (Update Factory)
    ↓
Step 25 (Final Verification)
```

### External Dependencies
- No new external packages required
- Tkinter is stdlib (always available)
- numpy already used for matrix math

---

## Success Criteria

### Functional Requirements
- [ ] main_tkinter.py reduced to ~45 lines
- [ ] main_tkinter.py uses AbstractApp.create()
- [ ] Tkinter backend supports animation
- [ ] All keyboard shortcuts work in Tkinter
- [ ] Mouse rotation works in Tkinter
- [ ] Solver integration works in Tkinter

### Non-Functional Requirements
- [ ] All existing tests pass
- [ ] No performance regression in Pyglet
- [ ] Clean separation of concerns
- [ ] No pyglet imports outside backend directory (except Window.py during transition)

---

## Migration State Tracking

| Step | Description | Status | Date |
|------|-------------|--------|------|
| 18 | Create AppWindow Protocol | ⬜ Pending | - |
| 19 | Create AppWindowBase | ⬜ Pending | - |
| 20 | Implement TkinterAnimation | ⬜ Pending | - |
| 21 | Create PygletAppWindow | ⬜ Pending | - |
| 22 | Create TkinterAppWindow | ⬜ Pending | - |
| 23 | Simplify main_tkinter.py | ⬜ Pending | - |
| 24 | Update Factory | ⬜ Pending | - |
| 25 | Final Verification | ⬜ Pending | - |

**Legend:**
- ⬜ Pending
- 🔄 In Progress
- ✅ Completed
- ❌ Blocked

---

## Git Tags (Planned)

```
step18-app-window-protocol
step19-app-window-base
step20-tkinter-animation
step21-pyglet-app-window
step22-tkinter-app-window
step23-simplify-main-tkinter
step24-update-factory
step25-phase3-complete
```

---

## Notes

### Design Decisions

1. **Composition over Inheritance for AppWindowBase**
   - AppWindowBase will NOT inherit from pyglet.window.Window
   - PygletAppWindow will inherit from both pyglet.window.Window AND use AppWindowBase via composition
   - This allows clean separation while maintaining pyglet's event system

2. **TextRenderer for All Text**
   - Replace all `pyglet.text.Label` usage with `TextRenderer` protocol
   - Each backend implements TextRenderer differently
   - Pyglet: Uses pyglet.text.Label internally
   - Tkinter: Uses canvas.create_text

3. **Animation Protocol Already Exists**
   - `AnimationBackend` protocol is already defined
   - Just need to implement `TkinterAnimation`
   - Registration system already supports `animation_factory`

### Open Questions

1. Should PygletAppWindow remain in `main_window/Window.py` or move to `backends/pyglet/`?
   - **Decision:** Move to backends/pyglet/app_window.py for consistency
   - Keep backward compatibility alias in Window.py during transition

2. How to handle GL state management for text overlay?
   - **Decision:** Add `with_2d_overlay()` context manager to Renderer protocol
   - Pyglet: Sets up orthographic projection with GL
   - Tkinter: No-op (already 2D)

---

## References

- [Phase 1-2 Migration State](migration_state.md)
- [GUI Abstraction Design](gui_abstraction.md)
- [Architecture Documentation](../../arch.md)
