# Phase 3 Migration Plan: Unified Backend Architecture

**Branch:** `claude/new-gui-phase-3-01X4mUeuJiPgg79XX6ZyvaS6`
**Created:** 2025-11-29
**Last Updated:** 2025-11-29
**Status:** In Progress (Steps 18-26 Complete)

---

## Executive Summary

Phase 3 creates a **unified backend architecture** enabling a single entry point (`main_any_backend.py`) to run the cube solver with ANY backend. This includes:

- **Pyglet** - 3D OpenGL rendering
- **Tkinter** - 2D isometric rendering
- **Console** - Text-based terminal rendering
- **Headless** - No rendering (for testing)

### Primary Goals

1. **`main_any_backend.py`** - Single entry point with configurable backend
2. **Console as a Backend** - Convert `main_c.py` to use the same architecture
3. **Abstract Test Sequences** - Test sequences work across ALL backends
4. **Unified AppWindow Protocol** - All backends share application logic

### Target State

```bash
# All of these should work with identical application logic:
python -m cube.main_any_backend --backend=pyglet    # 3D OpenGL
python -m cube.main_any_backend --backend=tkinter   # 2D Canvas
python -m cube.main_any_backend --backend=console   # Text terminal
python -m cube.main_any_backend --backend=headless  # Testing only
```

---

## Current State Analysis

### The Fragmentation Problem

| Entry Point | Lines | Uses AbstractApp | Uses AppWindow | Backend |
|-------------|-------|------------------|----------------|---------|
| `main_pyglet.py` | 42 | ✅ Yes | ✅ Window | pyglet |
| `main_tkinter.py` | 180 | ❌ No | ❌ Custom | tkinter |
| `main_console/main_c.py` | 234 | ❌ No | ❌ Custom | console |

### Root Causes

1. **Window.py inherits from pyglet.window.Window** - Other backends can't reuse it
2. **Console has its own key handling** - Duplicates logic from main_g_keyboard_input
3. **No common AppWindow protocol** - Each backend implements its own initialization
4. **Test sequences tied to specific backends** - Can't run same tests across backends

### Backend Feature Matrix

| Feature | Pyglet | Tkinter | Console | Headless |
|---------|--------|---------|---------|----------|
| Renderer | ✅ 3D OpenGL | ✅ 2D Canvas | ❌ Text only | ✅ No-op |
| EventLoop | ✅ pyglet.app | ✅ tk.mainloop | ❌ keyboard lib | ✅ Manual |
| Animation | ✅ Full | ❌ Missing | ❌ None | ✅ Instant |
| AppWindow | ✅ Window | ❌ Custom | ❌ Custom | ❌ None |
| Test sequences | ✅ inject_key | ❌ Manual | ✅ key_sequence | ✅ queue |

---

## Architecture Vision

### Unified Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     main_any_backend.py                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  backend = BackendRegistry.get_backend(args.backend)    │    │
│  │  app = AbstractApp.create()                              │    │
│  │  win = backend.create_app_window(app, 720, 720, "Cube") │    │
│  │  win.run()                                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AbstractApp                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Cube │ Operator │ Solver │ AnimationManager │ ViewState │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AppWindow Protocol                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ AppWindowBase (shared: keyboard handling, text updates)  │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │              │              │              │         │
│    ┌──────┴──────┐ ┌─────┴─────┐ ┌─────┴─────┐ ┌──────┴──────┐ │
│    │   Pyglet    │ │  Tkinter  │ │  Console  │ │  Headless   │ │
│    │ AppWindow   │ │ AppWindow │ │ AppWindow │ │  AppWindow  │ │
│    └─────────────┘ └───────────┘ └───────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Protocols                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Renderer  │ │ EventLoop  │ │  Window    │ │ Animation  │   │
│  │  Protocol  │ │  Protocol  │ │  Protocol  │ │  Protocol  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Test Sequence Abstraction

```python
# Abstract test sequence that works with ANY backend
class TestSequence:
    """Backend-agnostic test sequence."""

    def __init__(self, keys: str):
        self.keys = keys  # e.g., "R U R' U'"

    def run(self, app_window: AppWindow) -> TestResult:
        """Execute sequence on any backend."""
        for key in self._parse_keys():
            app_window.inject_key(key)
        return TestResult(...)

# Usage in tests:
def test_scramble_solve():
    backend = BackendRegistry.get_backend("headless")
    app = AbstractApp.create()
    win = backend.create_app_window(app, 720, 720, "Test")

    # Same sequence works for ANY backend
    result = TestSequence("1?Q").run(win)  # scramble, solve, quit
    assert result.cube.solved
```

---

## Migration Steps

### Phase 3A: Core Protocol Layer (Steps 18-19)

#### Step 18: Create AppWindow Protocol
**Status:** ⬜ Pending
**Effort:** Medium
**Files:**
- Create: `src/cube/gui/protocols/app_window.py`
- Modify: `src/cube/gui/protocols/__init__.py`

```python
@runtime_checkable
class AppWindow(Protocol):
    """Protocol for application window - works with any backend."""

    @property
    def app(self) -> AbstractApp: ...

    @property
    def viewer(self) -> GCubeViewer: ...

    @property
    def renderer(self) -> Renderer: ...

    @property
    def animation_running(self) -> bool: ...

    def run(self) -> None:
        """Run the main event loop."""
        ...

    def close(self) -> None:
        """Close the window and stop the event loop."""
        ...

    def update_gui_elements(self) -> None:
        """Update text, status, and redraw."""
        ...

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a key press (for testing and automation)."""
        ...

    def inject_key_sequence(self, sequence: str) -> None:
        """Inject a sequence of keys."""
        ...
```

**Acceptance Criteria:**
- [ ] Protocol defined with all required methods
- [ ] Supports key injection for testing
- [ ] Protocol exported from protocols package

---

#### Step 19: Create AppWindowBase Shared Logic
**Status:** ⬜ Pending
**Effort:** High
**Files:**
- Create: `src/cube/main_window/AppWindowBase.py`

**Shared Logic to Extract:**
- Keyboard input handling (delegate to `main_g_keyboard_input`)
- Mouse input handling (delegate to `main_g_mouse`)
- Text updates (`update_text()`, `update_animation_text()`)
- GUI element coordination (`update_gui_elements()`)
- Key sequence injection
- Error handling patterns

**Key Design:**
```python
class AppWindowBase:
    """Shared application window logic for all backends."""

    def __init__(self, app: AbstractApp, backend: GUIBackend):
        self._app = app
        self._backend = backend
        self._viewer: GCubeViewer | None = None

    def handle_key_press(self, symbol: int, modifiers: int) -> None:
        """Delegate to shared keyboard handler."""
        main_g_keyboard_input.handle_keyboard_input(self, symbol, modifiers)

    def handle_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        """Delegate to shared mouse handler."""
        main_g_mouse.on_mouse_drag(self, x, y, dx, dy, buttons, modifiers)

    def build_status_text(self) -> list[TextLabel]:
        """Build status text labels (backend renders them)."""
        ...
```

**Acceptance Criteria:**
- [ ] No pyglet imports in AppWindowBase
- [ ] Uses TextRenderer protocol for all text
- [ ] Keyboard/mouse handling reuses existing infrastructure

---

### Phase 3B: Animation Support (Step 20)

#### Step 20: Implement TkinterAnimation Backend
**Status:** ⬜ Pending
**Effort:** High
**Files:**
- Create: `src/cube/gui/backends/tkinter/animation.py`
- Modify: `src/cube/gui/backends/tkinter/__init__.py`

```python
class TkinterAnimation(AnimationBackend):
    """Animation backend using tk.after() for scheduling."""

    def __init__(self):
        self._running = False
        self._speed = 1.0
        self._root: tk.Tk | None = None
        self._after_id: str | None = None

    @property
    def supported(self) -> bool:
        return True

    def run_animation(self, update_func, on_complete, interval):
        def tick():
            if self._running:
                continue_anim = update_func(interval * self._speed)
                if continue_anim:
                    self._after_id = self._root.after(
                        int(interval * 1000), tick
                    )
                else:
                    if on_complete:
                        on_complete()
        tick()
```

**Acceptance Criteria:**
- [ ] Implements AnimationBackend protocol
- [ ] Supports pause, resume, cancel, skip
- [ ] Speed multiplier works
- [ ] Registered with `animation_factory=TkinterAnimation`

---

### Phase 3C: Backend AppWindows (Steps 21-24)

#### Step 21: Create PygletAppWindow
**Status:** ⬜ Pending
**Effort:** High
**Files:**
- Refactor: `src/cube/main_window/Window.py`
- Create: `src/cube/gui/backends/pyglet/app_window.py`

**Architecture:**
```python
class PygletAppWindow(pyglet.window.Window, AppWindowBase):
    """Pyglet-specific AppWindow implementation."""

    def __init__(self, app: AbstractApp, width, height, title, backend):
        AppWindowBase.__init__(self, app, backend)
        pyglet.window.Window.__init__(self, width, height, title)

        # Create viewer with pyglet renderer
        self._viewer = GCubeViewer(app.cube, app.vs, backend.renderer)

    def on_key_press(self, symbol, modifiers):
        # Convert pyglet keys and delegate to base
        abstract_key = _PYGLET_TO_KEYS.get(symbol, symbol)
        abstract_mods = _convert_modifiers(modifiers)
        self.handle_key_press(abstract_key, abstract_mods)

    def on_draw(self):
        self.clear()
        self._viewer.draw()
        self._draw_text()
```

**Acceptance Criteria:**
- [ ] Inherits from both pyglet.window.Window and AppWindowBase
- [ ] All pyglet-specific code in PygletAppWindow
- [ ] main_pyglet.py continues to work

---

#### Step 22: Create TkinterAppWindow
**Status:** ⬜ Pending
**Effort:** High
**Files:**
- Create: `src/cube/gui/backends/tkinter/app_window.py`

```python
class TkinterAppWindow(AppWindowBase):
    """Tkinter-specific AppWindow implementation."""

    def __init__(self, app: AbstractApp, width, height, title, backend):
        super().__init__(app, backend)

        # Create tkinter window
        self._tk_window = TkinterWindow(width, height, title)

        # Configure renderer with canvas
        self._renderer = backend.renderer
        self._renderer.set_canvas(self._tk_window.canvas)

        # Create viewer
        self._viewer = GCubeViewer(app.cube, app.vs, self._renderer)

        # Set up event handlers
        self._tk_window.set_key_press_handler(self._on_key_press)
        self._tk_window.set_draw_handler(self._on_draw)

    def _on_key_press(self, event: KeyEvent):
        self.handle_key_press(event.symbol, event.modifiers)
```

**Acceptance Criteria:**
- [ ] Implements AppWindow protocol
- [ ] Uses AppWindowBase for shared logic
- [ ] Integrates with TkinterAnimation

---

#### Step 23: Create ConsoleAppWindow
**Status:** ⬜ Pending
**Effort:** High
**Files:**
- Create: `src/cube/gui/backends/console/__init__.py`
- Create: `src/cube/gui/backends/console/app_window.py`
- Create: `src/cube/gui/backends/console/renderer.py`
- Create: `src/cube/gui/backends/console/event_loop.py`

**Console Backend Architecture:**
```python
class ConsoleRenderer(Renderer):
    """Text-based renderer using colorama."""

    def render_cube(self, cube: Cube) -> str:
        """Return text representation of cube."""
        # Reuse logic from main_console/viewer.py
        ...

class ConsoleEventLoop(EventLoop):
    """Keyboard-based event loop."""

    def run(self):
        while not self._should_stop:
            key = keyboard.read_event()
            if self._key_handler:
                self._key_handler(self._convert_key(key))

class ConsoleAppWindow(AppWindowBase):
    """Console-specific AppWindow implementation."""

    def __init__(self, app: AbstractApp, width, height, title, backend):
        super().__init__(app, backend)
        self._console_renderer = backend.renderer

    def run(self):
        self._render()
        self._backend.event_loop.run()

    def _render(self):
        # Clear screen and print cube
        print("\033[2J\033[H")  # ANSI clear
        print(self._console_renderer.render_cube(self._app.cube))
        print(f"Status: {self._app.slv.status}")
```

**Acceptance Criteria:**
- [ ] Console backend registered in BackendRegistry
- [ ] Reuses viewer.py rendering logic
- [ ] Supports key injection for testing
- [ ] Works with AbstractApp infrastructure

---

#### Step 24: Create HeadlessAppWindow
**Status:** ⬜ Pending
**Effort:** Medium
**Files:**
- Create: `src/cube/gui/backends/headless/app_window.py`
- Modify: `src/cube/gui/backends/headless/__init__.py`

```python
class HeadlessAppWindow(AppWindowBase):
    """Headless AppWindow for testing - no actual rendering."""

    def __init__(self, app: AbstractApp, width, height, title, backend):
        super().__init__(app, backend)
        self._viewer = GCubeViewer(app.cube, app.vs, backend.renderer)
        self._key_queue: list[tuple[int, int]] = []

    def run(self):
        """Process queued keys then return."""
        while self._key_queue:
            key, mods = self._key_queue.pop(0)
            self.handle_key_press(key, mods)

    def inject_key(self, key: int, modifiers: int = 0):
        self._key_queue.append((key, modifiers))
```

**Acceptance Criteria:**
- [ ] Implements AppWindow protocol
- [ ] Supports key queue for deterministic testing
- [ ] Instant animation (no delays)

---

### Phase 3D: Unified Entry Point (Steps 25-26)

#### Step 25: Create main_any_backend.py
**Status:** ⬜ Pending
**Effort:** Medium
**Files:**
- Create: `src/cube/main_any_backend.py`

```python
"""
Unified entry point for the Cube Solver with any backend.

Usage:
    python -m cube.main_any_backend --backend=pyglet
    python -m cube.main_any_backend --backend=tkinter
    python -m cube.main_any_backend --backend=console
    python -m cube.main_any_backend --backend=headless --keys="1?Q"
"""
import argparse

from cube.app.AbstractApp import AbstractApp
from cube.gui import BackendRegistry

# Import all backends to register them
import cube.gui.backends.pyglet  # noqa: F401
import cube.gui.backends.tkinter  # noqa: F401
import cube.gui.backends.console  # noqa: F401
import cube.gui.backends.headless  # noqa: F401


def main():
    parser = argparse.ArgumentParser(description="Rubik's Cube Solver")
    parser.add_argument(
        "--backend", "-b",
        choices=["pyglet", "tkinter", "console", "headless"],
        default="pyglet",
        help="Rendering backend to use"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        default=3,
        help="Cube size (default: 3)"
    )
    parser.add_argument(
        "--keys", "-k",
        type=str,
        default=None,
        help="Key sequence to inject (for testing)"
    )
    args = parser.parse_args()

    # Get backend
    backend = BackendRegistry.get_backend(args.backend)

    # Create app
    app = AbstractApp.create(cube_size=args.size)

    # Configure animation manager
    if app.am is not None:
        app.am.set_event_loop(backend.event_loop)

    # Create window
    win = backend.create_app_window(app, 720, 720, "Cube")

    # Inject keys if provided
    if args.keys:
        win.inject_key_sequence(args.keys)

    try:
        win.run()
    finally:
        if hasattr(win, 'viewer'):
            win.viewer.cleanup()


if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- [ ] Single entry point works with all 4 backends
- [ ] Command-line arguments for backend selection
- [ ] Key injection for automated testing
- [ ] Cube size configuration

---

#### Step 26: Abstract Test Sequences
**Status:** ⬜ Pending
**Effort:** Medium
**Files:**
- Create: `src/cube/testing/test_sequence.py`
- Modify: `tests/` - Update tests to use abstract sequences

```python
class TestSequence:
    """Backend-agnostic test sequence."""

    # Standard test sequences
    SCRAMBLE_1 = "1"
    SCRAMBLE_SOLVE = "1?"
    FULL_TEST = "T"

    def __init__(self, keys: str, quit_after: bool = True):
        self.keys = keys + ("Q" if quit_after else "")

    def run(self, backend: str = "headless") -> TestResult:
        """Run sequence on specified backend."""
        from cube.gui import BackendRegistry
        from cube.app.AbstractApp import AbstractApp

        backend = BackendRegistry.get_backend(backend)
        app = AbstractApp.create()
        win = backend.create_app_window(app, 720, 720, "Test")

        win.inject_key_sequence(self.keys)
        win.run()

        return TestResult(
            cube=app.cube,
            solved=app.cube.solved,
            operator=app.op,
            solver=app.slv
        )


# In tests:
def test_scramble_and_solve():
    result = TestSequence("1?").run()
    assert result.solved

def test_manual_moves():
    result = TestSequence("RURU").run()
    assert not result.solved
```

**Acceptance Criteria:**
- [ ] TestSequence class works with any backend
- [ ] Standard test sequences defined
- [ ] Existing tests migrated to use TestSequence

---

### Phase 3E: Cleanup and Verification (Steps 27-28)

#### Step 27: Simplify Legacy Main Files
**Status:** ⬜ Pending
**Effort:** Low
**Files:**
- Modify: `src/cube/main_pyglet.py`
- Modify: `src/cube/main_tkinter.py`
- Modify: `src/cube/main_console/main_c.py`

Convert legacy entry points to thin wrappers:

```python
# main_pyglet.py (simplified)
from cube.main_any_backend import main as any_main
import sys

def main():
    sys.argv.extend(["--backend", "pyglet"])
    any_main()

if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- [ ] Legacy entry points still work
- [ ] Each is < 10 lines
- [ ] All delegate to main_any_backend

---

#### Step 28: Update Factory and Final Verification
**Status:** ⬜ Pending
**Effort:** Medium
**Files:**
- Modify: `src/cube/gui/factory.py`
- Modify: All `backends/*/__init__.py`

**Factory Updates:**
```python
class BackendRegistry:
    @classmethod
    def register(cls, name: str, *,
                 renderer_factory,
                 window_factory,
                 event_loop_factory,
                 animation_factory=None,
                 app_window_factory=None):  # NEW
        ...

    def create_app_window(self, app, width, height, title) -> AppWindow:
        """Create an AppWindow for this backend."""
        return self._entry.app_window_factory(app, width, height, title, self)
```

**Acceptance Criteria:**
- [ ] All 4 backends registered with app_window_factory
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Git tag `phase3-complete` created

---

## File Structure After Migration

```
src/cube/
├── gui/
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── renderer.py
│   │   ├── event_loop.py
│   │   ├── window.py
│   │   ├── animation.py
│   │   └── app_window.py              # NEW - Step 18
│   │
│   ├── backends/
│   │   ├── pyglet/
│   │   │   ├── __init__.py            # MODIFIED - app_window_factory
│   │   │   ├── renderer.py
│   │   │   ├── window.py
│   │   │   ├── event_loop.py
│   │   │   ├── animation.py
│   │   │   └── app_window.py          # NEW - Step 21
│   │   │
│   │   ├── tkinter/
│   │   │   ├── __init__.py            # MODIFIED - animation + app_window
│   │   │   ├── renderer.py
│   │   │   ├── window.py
│   │   │   ├── event_loop.py
│   │   │   ├── animation.py           # NEW - Step 20
│   │   │   └── app_window.py          # NEW - Step 22
│   │   │
│   │   ├── console/                    # NEW - Step 23
│   │   │   ├── __init__.py
│   │   │   ├── renderer.py
│   │   │   ├── event_loop.py
│   │   │   └── app_window.py
│   │   │
│   │   └── headless/
│   │       ├── __init__.py            # MODIFIED
│   │       ├── renderer.py
│   │       ├── event_loop.py
│   │       └── app_window.py          # NEW - Step 24
│   │
│   ├── factory.py                      # MODIFIED - Step 28
│   └── types.py
│
├── main_window/
│   ├── Window.py                       # REFACTORED - Step 21
│   ├── app_window_base.py              # NEW - Step 19
│   ├── main_g_keyboard_input.py
│   ├── main_g_mouse.py
│   └── main_g_abstract.py
│
├── testing/                            # NEW - Step 26
│   ├── __init__.py
│   └── test_sequence.py
│
├── main_any_backend.py                 # NEW - Step 25
├── main_pyglet.py                      # SIMPLIFIED - Step 27
├── main_tkinter.py                     # SIMPLIFIED - Step 27
└── main_console/
    └── main_c.py                       # SIMPLIFIED - Step 27
```

---

## Migration State Tracking

| Step | Description | Status | Date | Commit |
|------|-------------|--------|------|--------|
| **Phase 3A: Core Protocol** | | | | |
| 18 | Create AppWindow Protocol | ✅ Completed | 2025-11-29 | `12ad591` |
| 19 | Create AppWindowBase | ✅ Completed | 2025-11-29 | `dbf00c5` |
| **Phase 3B: Animation** | | | | |
| 20 | Implement TkinterAnimation | ✅ Completed | 2025-11-29 | `c0aaa53` |
| **Phase 3C: Backend AppWindows** | | | | |
| 21 | Create PygletAppWindow | ✅ Completed | 2025-11-29 | `081bab8` |
| 22 | Create TkinterAppWindow | ✅ Completed | 2025-11-29 | `f04ad22` |
| 23 | Create ConsoleAppWindow + Backend | ✅ Completed | 2025-11-29 | `e6d542d` |
| 24 | Create HeadlessAppWindow | ✅ Completed | 2025-11-29 | `844c4d4` |
| **Phase 3D: Unified Entry** | | | | |
| 25 | Create main_any_backend.py | ✅ Completed | 2025-11-29 | `4278201` |
| 26 | Abstract Test Sequences | ✅ Completed | 2025-11-29 | `5debedd` |
| **Phase 3E: Cleanup** | | | | |
| 27 | Simplify Legacy Main Files | ⬜ Pending | - | - |
| 28 | Update Factory & Verification | ⬜ Pending | - | - |

**Legend:**
- ⬜ Pending
- 🔄 In Progress
- ✅ Completed
- ❌ Blocked

---

## Step Dependencies

```
Step 18 (AppWindow Protocol)
    │
    ▼
Step 19 (AppWindowBase) ──────────────────────────────┐
    │                                                  │
    ├───────────────┬───────────────┬─────────────────┤
    ▼               ▼               ▼                 ▼
Step 20         Step 21         Step 22           Step 23
(TkinterAnim)   (PygletApp)     (TkinterApp)      (ConsoleApp)
    │               │               │                 │
    └───────────────┴───────────────┴─────────────────┤
                                                      ▼
                                                  Step 24
                                                (HeadlessApp)
                                                      │
                                                      ▼
                                                  Step 25
                                            (main_any_backend)
                                                      │
                                                      ▼
                                                  Step 26
                                            (Test Sequences)
                                                      │
                                                      ▼
                                                  Step 27
                                            (Simplify Legacy)
                                                      │
                                                      ▼
                                                  Step 28
                                            (Final Verification)
```

---

## Success Criteria

### Functional Requirements
- [ ] `main_any_backend.py --backend=pyglet` works
- [ ] `main_any_backend.py --backend=tkinter` works
- [ ] `main_any_backend.py --backend=console` works
- [ ] `main_any_backend.py --backend=headless --keys="1?Q"` works
- [ ] All keyboard shortcuts work across backends
- [ ] Test sequences work across all backends
- [ ] Solver integration works across all backends

### Non-Functional Requirements
- [ ] All existing tests pass
- [ ] No pyglet imports outside pyglet backend
- [ ] No tkinter imports outside tkinter backend
- [ ] Clean separation of concerns
- [ ] Documentation complete

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing pyglet functionality | Medium | High | Incremental changes, extensive testing |
| Console keyboard library compatibility | Medium | Medium | Fallback to stdin input |
| Animation timing differences | Medium | Medium | Abstract timing, backend-specific adjustments |
| Complex refactoring of Window.py | High | Medium | Clear separation, keep backward compat |

---

## Git Tags (Planned)

```
step18-app-window-protocol
step19-app-window-base
step20-tkinter-animation
step21-pyglet-app-window
step22-tkinter-app-window
step23-console-backend
step24-headless-app-window
step25-main-any-backend
step26-test-sequences
step27-simplify-legacy
step28-phase3-complete
```

---

## References

- [Phase 1-2 Migration State](wip/migration_state.md)
- [GUI Abstraction Design](gui_abstraction.md)
- [Architecture Documentation](../../arch.md)
