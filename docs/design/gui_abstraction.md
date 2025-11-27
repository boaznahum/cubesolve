# GUI Abstraction Layer Design Document

## 1. Overview

This document describes the design for a GUI abstraction layer that allows the Rubik's cube solver to support multiple rendering backends beyond the current OpenGL/pyglet implementation.

### Goals

1. **Backend Independence** - Any main/test can choose its GUI system
2. **Tkinter Support** - Primary alternative backend (built-in, no dependencies)
3. **Headless Mode** - Enable fast testing without GUI overhead
4. **Incremental Migration** - Don't break existing functionality during transition
5. **Clean Separation** - Clear boundary between model and view layers

---

## 2. Current Architecture Analysis

### 2.1 Model Layer (Clean - No Changes Needed)

The model layer is well-designed with no GUI dependencies:

```
Cube
├── Face (6 faces: F, B, L, R, U, D)
│   ├── Part (Edge, Corner, Center) - shared between faces
│   │   └── PartSlice (EdgeWing, CornerSlice, CenterSlice)
│   │       └── PartEdge (individual sticker with color)
│   └── Slices for NxN cubes
├── Operator - mediates algorithms and cube mutations
└── CubeQueries2 - query interface for solvers
```

**Key Design Principle:** Parts never move in 3D space - only their colors change.

**Model Files:**
- `src/cube/model/cube.py` - Root Cube class
- `src/cube/model/cube_face.py` - Face rotation logic
- `src/cube/model/Part.py`, `Edge.py`, `Corner.py`, `Center.py` - Piece types
- `src/cube/operator/cube_operator.py` - Move execution

### 2.2 View Layer (Tightly Coupled to pyglet/OpenGL)

| Component | Location | OpenGL Coupling |
|-----------|----------|-----------------|
| Window | `main_window/Window.py` | Extends `pyglet.window.Window` |
| Cell rendering | `viewer/_cell.py` | `glBegin`, `glVertex3f`, `glGenLists`, `glCallList` |
| Board | `viewer/_board.py` | Display lists, texture binding |
| Face board | `viewer/_faceboard.py` | GL vertex arrays |
| Shapes | `viewer/shapes.py` | `GL_QUADS`, `gluSphere`, `gluCylinder` |
| View state | `app/app_state.py` | `glPushAttrib`, `glRotatef`, `gluPerspective` |
| Animation | `animation/animation_manager.py` | `pyglet.app.event_loop`, `pyglet.clock` |

### 2.3 Existing Console Viewer (Reference Pattern)

The console viewer (`src/cube/main_console/viewer.py`) provides a useful pattern:
- Has its own `_Cell`, `_FaceBoard`, `_Board` classes
- Text-based rendering with colorama
- No OpenGL dependencies
- Shows that alternative renderers are feasible

---

## 3. Proposed Architecture

### 3.1 Package Structure

```
src/cube/gui/
    __init__.py                 # Public API exports
    types.py                    # Common types (Point3D, Color3, events)
    factory.py                  # BackendRegistry and create_gui()

    protocols/
        __init__.py
        renderer.py             # ShapeRenderer, DisplayListManager, ViewStateManager
        window.py               # Window, TextRenderer protocols
        event_loop.py           # EventLoop protocol
        animation.py            # AnimationBackend protocol

    backends/
        __init__.py
        pyglet/                 # Wraps existing OpenGL code
            __init__.py
            renderer.py
            window.py
            event_loop.py
            animation.py
        headless/               # No-op for testing
            __init__.py
            renderer.py
            window.py
            event_loop.py
        tkinter/                # Future: Canvas-based rendering
            __init__.py
            renderer.py
            window.py
            event_loop.py
```

### 3.2 Core Protocols

#### 3.2.1 Common Types (`types.py`)

```python
from typing import TypeAlias, Tuple, NewType, Sequence
from dataclasses import dataclass
import numpy as np

# Geometric types
Point3D: TypeAlias = np.ndarray  # Shape (3,) - [x, y, z]
Matrix4x4: TypeAlias = np.ndarray  # Shape (4, 4) column-major

# Color types
Color3: TypeAlias = Tuple[int, int, int]  # RGB 0-255
Color4: TypeAlias = Tuple[int, int, int, int]  # RGBA 0-255

# Display list handle (opaque type)
DisplayList = NewType('DisplayList', int)

@dataclass
class KeyEvent:
    """Backend-independent keyboard event."""
    symbol: int      # Key code (use Keys constants)
    modifiers: int   # Modifier flags
    char: str | None = None  # Character if printable

@dataclass
class MouseEvent:
    """Backend-independent mouse event."""
    x: int
    y: int
    dx: int = 0      # Delta for drag events
    dy: int = 0
    button: int = 0
    modifiers: int = 0

class Keys:
    """Backend-independent key constants."""
    # Letters
    A, B, C, D, E, F = 1, 2, 3, 4, 5, 6
    G, H, I, J, K, L = 7, 8, 9, 10, 11, 12
    M, N, O, P, Q, R = 13, 14, 15, 16, 17, 18
    S, T, U, V, W, X = 19, 20, 21, 22, 23, 24
    Y, Z = 25, 26

    # Numbers
    _0, _1, _2, _3, _4 = 30, 31, 32, 33, 34
    _5, _6, _7, _8, _9 = 35, 36, 37, 38, 39

    # Special keys
    ESCAPE = 100
    SPACE = 101
    RETURN = 102
    TAB = 103
    BACKSPACE = 104
    DELETE = 105

    # Arrow keys
    LEFT = 110
    RIGHT = 111
    UP = 112
    DOWN = 113

    # Modifiers
    MOD_SHIFT = 1
    MOD_CTRL = 2
    MOD_ALT = 4
```

#### 3.2.2 Renderer Protocol (`protocols/renderer.py`)

```python
from typing import Protocol, Sequence, runtime_checkable
from cube.gui.types import Point3D, Color3, Color4, DisplayList, Matrix4x4

@runtime_checkable
class ShapeRenderer(Protocol):
    """Protocol for rendering geometric primitives."""

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Render a filled quadrilateral.

        Args:
            vertices: 4 points in counter-clockwise order
            color: RGB fill color
        """
        ...

    def quad_with_border(self, vertices: Sequence[Point3D],
                         face_color: Color3,
                         line_width: float,
                         line_color: Color3) -> None:
        """Render a quadrilateral with colored border.

        Args:
            vertices: 4 points in counter-clockwise order
            face_color: RGB fill color
            line_width: Border line width in pixels
            line_color: RGB border color
        """
        ...

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """Render a sphere (or circle in 2D backends)."""
        ...

    def cylinder(self, p1: Point3D, p2: Point3D,
                 radius1: float, radius2: float, color: Color3) -> None:
        """Render a cylinder between two points (or line in 2D backends)."""
        ...


@runtime_checkable
class DisplayListManager(Protocol):
    """Protocol for managing compiled display lists.

    Display lists are pre-compiled rendering commands that can be
    executed efficiently. For backends without display list support
    (e.g., Tkinter), this can store callable objects instead.
    """

    def create_list(self) -> DisplayList:
        """Create a new display list and return its handle."""
        ...

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling rendering commands into the list."""
        ...

    def end_compile(self) -> None:
        """End compilation and finalize the list."""
        ...

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a single display list."""
        ...

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists."""
        ...

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list and free resources."""
        ...


@runtime_checkable
class ViewStateManager(Protocol):
    """Protocol for managing view transformations.

    Handles projection setup, model-view matrix stack, and
    coordinate transformations.
    """

    def set_projection(self, width: int, height: int, fov_y: float = 50.0) -> None:
        """Set up projection matrix for the viewport.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            fov_y: Field of view in degrees (for 3D backends)
        """
        ...

    def push_model_view(self) -> None:
        """Save current model-view matrix to stack."""
        ...

    def pop_model_view(self) -> None:
        """Restore model-view matrix from stack."""
        ...

    def load_identity(self) -> None:
        """Reset model-view matrix to identity."""
        ...

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation to current matrix."""
        ...

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation around axis to current matrix."""
        ...

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scaling to current matrix."""
        ...

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply current matrix by given 4x4 matrix (column-major)."""
        ...


@runtime_checkable
class Renderer(Protocol):
    """Main renderer protocol combining all rendering capabilities."""

    @property
    def shapes(self) -> ShapeRenderer:
        """Access shape rendering methods."""
        ...

    @property
    def display_lists(self) -> DisplayListManager:
        """Access display list management."""
        ...

    @property
    def view(self) -> ViewStateManager:
        """Access view transformation methods."""
        ...

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Clear the rendering surface."""
        ...

    def setup(self) -> None:
        """Initialize renderer (called once at startup)."""
        ...

    def cleanup(self) -> None:
        """Release renderer resources (called at shutdown)."""
        ...

    def begin_frame(self) -> None:
        """Begin a new frame (called before drawing)."""
        ...

    def end_frame(self) -> None:
        """End frame and present (called after drawing)."""
        ...
```

#### 3.2.3 Window Protocol (`protocols/window.py`)

```python
from typing import Protocol, Callable, runtime_checkable
from cube.gui.types import KeyEvent, MouseEvent, Color4

@runtime_checkable
class TextRenderer(Protocol):
    """Protocol for text rendering."""

    def draw_label(self, text: str, x: int, y: int,
                   font_size: int = 12,
                   color: Color4 = (255, 255, 255, 255),
                   bold: bool = False,
                   anchor_x: str = 'left',
                   anchor_y: str = 'bottom') -> None:
        """Draw text at the specified position.

        Args:
            text: Text string to render
            x, y: Position in window coordinates
            font_size: Font size in points
            color: RGBA text color
            bold: Whether to use bold font
            anchor_x: Horizontal anchor ('left', 'center', 'right')
            anchor_y: Vertical anchor ('top', 'center', 'bottom')
        """
        ...


@runtime_checkable
class Window(Protocol):
    """Protocol for window management."""

    @property
    def width(self) -> int:
        """Window width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Window height in pixels."""
        ...

    @property
    def text(self) -> TextRenderer:
        """Access text rendering."""
        ...

    def set_title(self, title: str) -> None:
        """Set window title."""
        ...

    def set_visible(self, visible: bool) -> None:
        """Show or hide the window."""
        ...

    def close(self) -> None:
        """Close the window."""
        ...

    def request_redraw(self) -> None:
        """Request window redraw on next frame."""
        ...

    # Event handler registration
    def set_draw_handler(self, handler: Callable[[], None]) -> None:
        """Set the draw callback."""
        ...

    def set_resize_handler(self, handler: Callable[[int, int], None]) -> None:
        """Set the resize callback."""
        ...

    def set_key_handler(self, handler: Callable[[KeyEvent], None]) -> None:
        """Set the key press callback."""
        ...

    def set_mouse_drag_handler(self, handler: Callable[[MouseEvent], None]) -> None:
        """Set the mouse drag callback."""
        ...

    def set_mouse_press_handler(self, handler: Callable[[MouseEvent], None]) -> None:
        """Set the mouse press callback."""
        ...

    def set_mouse_scroll_handler(self, handler: Callable[[int, int, float, float], None]) -> None:
        """Set the mouse scroll callback."""
        ...
```

#### 3.2.4 Event Loop Protocol (`protocols/event_loop.py`)

```python
from typing import Protocol, Callable, runtime_checkable

@runtime_checkable
class EventLoop(Protocol):
    """Protocol for the main event loop."""

    @property
    def running(self) -> bool:
        """Whether the event loop is currently running."""
        ...

    def run(self) -> None:
        """Start the event loop (blocking)."""
        ...

    def stop(self) -> None:
        """Request the event loop to stop."""
        ...

    def step(self, timeout: float = 0.0) -> None:
        """Process pending events without blocking.

        Args:
            timeout: Maximum time to wait for events (0 = non-blocking)
        """
        ...

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay.

        Args:
            callback: Function receiving elapsed time since scheduling
            delay: Delay in seconds
        """
        ...

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly at interval.

        Args:
            callback: Function receiving time since last call
            interval: Interval in seconds
        """
        ...

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback."""
        ...
```

#### 3.2.5 Animation Backend Protocol (`protocols/animation.py`)

```python
from typing import Protocol, Callable, Collection, runtime_checkable
from cube.model import PartSlice
from cube.model.cube import Cube
from cube.model.cube_boy import FaceName

@runtime_checkable
class AnimationBackend(Protocol):
    """Protocol for animation support.

    Animation backends handle the visual interpolation of cube rotations.
    Not all backends need to support animation (e.g., headless mode).
    """

    @property
    def supported(self) -> bool:
        """Whether this backend supports animation."""
        ...

    @property
    def running(self) -> bool:
        """Whether an animation is currently in progress."""
        ...

    def run_animation(self,
                      cube: Cube,
                      rotate_face: FaceName,
                      slices: Collection[int],
                      n_quarter_turns: int,
                      on_complete: Callable[[], None]) -> None:
        """Start an animation for a cube rotation.

        Args:
            cube: The cube being rotated
            rotate_face: Face/axis of rotation
            slices: Which slices are rotating (for NxN cubes)
            n_quarter_turns: Number of 90-degree turns (1-3)
            on_complete: Callback when animation finishes
        """
        ...

    def cancel(self) -> None:
        """Cancel the current animation immediately."""
        ...

    def set_speed(self, speed: float) -> None:
        """Set animation speed multiplier (1.0 = normal)."""
        ...
```

### 3.3 Backend Factory (`factory.py`)

```python
from typing import Type, Dict, Any, Callable
from cube.gui.protocols import Renderer, Window, EventLoop, AnimationBackend

class BackendRegistry:
    """Registry for GUI backends."""

    _backends: Dict[str, Dict[str, Type]] = {}
    _default: str | None = None

    @classmethod
    def register(cls, name: str, *,
                 renderer_class: Type[Renderer],
                 window_class: Type[Window],
                 event_loop_class: Type[EventLoop],
                 animation_class: Type[AnimationBackend] | None = None) -> None:
        """Register a new backend.

        Args:
            name: Backend identifier (e.g., 'pyglet', 'tkinter', 'headless')
            renderer_class: Class implementing Renderer protocol
            window_class: Class implementing Window protocol
            event_loop_class: Class implementing EventLoop protocol
            animation_class: Optional class implementing AnimationBackend
        """
        cls._backends[name] = {
            'renderer': renderer_class,
            'window': window_class,
            'event_loop': event_loop_class,
            'animation': animation_class,
        }

    @classmethod
    def set_default(cls, name: str) -> None:
        """Set the default backend."""
        if name not in cls._backends:
            raise ValueError(f"Unknown backend: {name}")
        cls._default = name

    @classmethod
    def get_default(cls) -> str:
        """Get the default backend name."""
        if cls._default:
            return cls._default
        # Auto-detect available backend
        if 'pyglet' in cls._backends:
            return 'pyglet'
        if 'tkinter' in cls._backends:
            return 'tkinter'
        if 'headless' in cls._backends:
            return 'headless'
        raise RuntimeError("No GUI backend registered")

    @classmethod
    def available(cls) -> list[str]:
        """List available backends."""
        return list(cls._backends.keys())

    @classmethod
    def create_renderer(cls, backend: str | None = None) -> Renderer:
        """Create a renderer instance."""
        name = backend or cls.get_default()
        return cls._backends[name]['renderer']()

    @classmethod
    def create_window(cls, width: int, height: int, title: str,
                      backend: str | None = None) -> Window:
        """Create a window instance."""
        name = backend or cls.get_default()
        return cls._backends[name]['window'](width, height, title)

    @classmethod
    def create_event_loop(cls, backend: str | None = None) -> EventLoop:
        """Create an event loop instance."""
        name = backend or cls.get_default()
        return cls._backends[name]['event_loop']()

    @classmethod
    def create_animation(cls, backend: str | None = None) -> AnimationBackend | None:
        """Create an animation backend instance (may be None)."""
        name = backend or cls.get_default()
        anim_class = cls._backends[name]['animation']
        return anim_class() if anim_class else None


def create_gui(backend: str | None = None,
               width: int = 720,
               height: int = 720,
               title: str = "Cube") -> tuple[Renderer, Window, EventLoop, AnimationBackend | None]:
    """Create all GUI components for a backend.

    Args:
        backend: Backend name, or None for default
        width: Window width
        height: Window height
        title: Window title

    Returns:
        Tuple of (renderer, window, event_loop, animation_backend)
    """
    return (
        BackendRegistry.create_renderer(backend),
        BackendRegistry.create_window(width, height, title, backend),
        BackendRegistry.create_event_loop(backend),
        BackendRegistry.create_animation(backend),
    )
```

---

## 4. Backend Implementations

### 4.1 Pyglet Backend

Wraps the existing OpenGL code:

```python
# backends/pyglet/renderer.py
from pyglet import gl
from cube.gui.protocols.renderer import ShapeRenderer, DisplayListManager, ViewStateManager

class PygletShapeRenderer:
    """Wraps existing shapes.py functions."""

    def quad(self, vertices, color):
        gl.glColor3ub(*color)
        gl.glBegin(gl.GL_QUADS)
        for v in vertices:
            gl.glVertex3f(*v)
        gl.glEnd()

    def quad_with_border(self, vertices, face_color, line_width, line_color):
        # Existing quad_with_line() implementation
        ...

class PygletDisplayListManager:
    """Wraps OpenGL display list functions."""

    def create_list(self):
        return DisplayList(gl.glGenLists(1))

    def begin_compile(self, list_id):
        gl.glNewList(list_id, gl.GL_COMPILE)

    def end_compile(self):
        gl.glEndList()

    def call_list(self, list_id):
        gl.glCallList(list_id)

    # ... etc

class PygletRenderer:
    """Main pyglet renderer combining all components."""

    def __init__(self):
        self._shapes = PygletShapeRenderer()
        self._display_lists = PygletDisplayListManager()
        self._view = PygletViewStateManager()

    @property
    def shapes(self): return self._shapes

    @property
    def display_lists(self): return self._display_lists

    @property
    def view(self): return self._view

    # ... etc
```

### 4.2 Headless Backend

No-op implementations for testing:

```python
# backends/headless/renderer.py
class HeadlessShapeRenderer:
    """No-op shape renderer."""
    def quad(self, vertices, color): pass
    def quad_with_border(self, vertices, face_color, line_width, line_color): pass
    def sphere(self, center, radius, color): pass
    def cylinder(self, p1, p2, r1, r2, color): pass

class HeadlessDisplayListManager:
    """In-memory display list tracking."""
    def __init__(self):
        self._next_id = 1
        self._lists: dict[int, list] = {}

    def create_list(self):
        id = DisplayList(self._next_id)
        self._next_id += 1
        self._lists[id] = []
        return id

    # ... minimal implementations

class HeadlessRenderer:
    # ... combines headless components
```

### 4.3 Tkinter Backend (Future)

Canvas-based 2D rendering:

```python
# backends/tkinter/renderer.py
import tkinter as tk
from cube.gui.types import Point3D, Color3

class TkinterShapeRenderer:
    """2D canvas-based rendering with isometric projection."""

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas

    def quad(self, vertices: Sequence[Point3D], color: Color3):
        # Project 3D to 2D isometric
        points_2d = [self._project(v) for v in vertices]
        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        self._canvas.create_polygon(
            *[coord for p in points_2d for coord in p],
            fill=color_hex, outline='black'
        )

    def _project(self, point: Point3D) -> tuple[float, float]:
        """Isometric projection from 3D to 2D."""
        x, y, z = point
        # Simple isometric: x' = x - z, y' = y + (x + z) / 2
        return (x - z) * 30 + 360, (y + (x + z) * 0.5) * 30 + 360
```

---

## 5. Migration Strategy

### Phase 1: Create Protocol Definitions (Non-breaking)

**Files to create:**
- `src/cube/gui/__init__.py`
- `src/cube/gui/types.py`
- `src/cube/gui/factory.py`
- `src/cube/gui/protocols/__init__.py`
- `src/cube/gui/protocols/renderer.py`
- `src/cube/gui/protocols/window.py`
- `src/cube/gui/protocols/event_loop.py`
- `src/cube/gui/protocols/animation.py`

**Impact:** None - new code only

### Phase 2: Implement Pyglet Backend

**Files to create:**
- `src/cube/gui/backends/__init__.py`
- `src/cube/gui/backends/pyglet/__init__.py`
- `src/cube/gui/backends/pyglet/renderer.py`
- `src/cube/gui/backends/pyglet/window.py`
- `src/cube/gui/backends/pyglet/event_loop.py`
- `src/cube/gui/backends/pyglet/animation.py`

**Impact:** Wraps existing code, no changes to existing files

### Phase 3: Implement Headless Backend

**Files to create:**
- `src/cube/gui/backends/headless/__init__.py`
- `src/cube/gui/backends/headless/renderer.py`
- `src/cube/gui/backends/headless/window.py`
- `src/cube/gui/backends/headless/event_loop.py`

**Impact:** Enables fast testing without GUI

### Phase 4: Refactor Viewer to Use Protocols

**Files to modify:**
- `src/cube/viewer/_cell.py` - Accept `Renderer`, use `renderer.display_lists` and `renderer.shapes`
- `src/cube/viewer/_board.py` - Accept and pass `Renderer`
- `src/cube/viewer/_faceboard.py` - Accept and pass `Renderer`
- `src/cube/viewer/viewer_g.py` - Accept `Renderer`

**Impact:** Internal refactoring, API unchanged

### Phase 5: Refactor ApplicationAndViewState

**Files to modify:**
- `src/cube/app/app_state.py` - Extract GL code to use `ViewStateManager`

**Impact:** Internal refactoring

### Phase 6: Refactor Animation System

**Files to modify:**
- `src/cube/animation/animation_manager.py` - Use `AnimationBackend` protocol

**Impact:** Internal refactoring

### Phase 7: Refactor Window and Entry Point

**Files to modify:**
- `src/cube/main_window/Window.py` - Use protocols, delegate to backend
- `src/cube/main_g.py` - Use backend factory

**Impact:** Entry point signature may change

### Phase 8: Update AbstractApp Factory

**Files to modify:**
- `src/cube/app/abstract_ap.py` - Add `create_with_gui()` method

**Impact:** New factory method, existing method unchanged

---

## 6. Entry Point Usage

### Current (main_g.py)

```python
def main():
    app = AbstractApp.create()
    win = Window(app, 720, 720, "Cube")
    pyglet.app.run()
```

### After Migration

```python
from cube.gui import create_gui, BackendRegistry
from cube.gui.backends.pyglet import register  # Auto-registers pyglet

def main(backend: str | None = None):
    # Create GUI components
    renderer, window, event_loop, animation = create_gui(
        backend=backend,  # 'pyglet', 'tkinter', 'headless', or None for default
        width=720,
        height=720,
        title="Cube"
    )

    # Create app with GUI components
    app = AbstractApp.create_with_gui(renderer, animation)

    # Set up window handlers
    window.set_draw_handler(lambda: app.draw(renderer))
    window.set_key_handler(lambda e: handle_key(app, e))
    window.set_mouse_drag_handler(lambda e: handle_mouse(app, e))

    # Run event loop
    event_loop.run()

if __name__ == '__main__':
    import sys
    backend = sys.argv[1] if len(sys.argv) > 1 else None
    main(backend)
```

### For Tests

```python
from cube.gui import create_gui

def test_cube_operations():
    # Use headless backend for fast testing
    renderer, window, event_loop, _ = create_gui(backend='headless')

    # Create app
    app = AbstractApp.create_with_gui(renderer, animation=None)

    # Test cube operations without GUI overhead
    app.cube.rotate_face(FaceName.R, 1)
    assert not app.cube.solved
```

---

## 7. Benefits

1. **Backend Flexibility** - Support pyglet, tkinter, headless, and future backends
2. **Testability** - Headless mode enables fast unit testing without GUI
3. **Incremental Migration** - Each phase is independently testable
4. **Type Safety** - Protocols provide clear contracts with static type checking
5. **Backward Compatibility** - Existing code continues to work during migration
6. **Separation of Concerns** - Clear boundary between model and view

---

## 8. Critical Files Reference

| Priority | File | Description |
|----------|------|-------------|
| 1 | `viewer/_cell.py` | Heaviest GL usage - display lists, shape rendering |
| 2 | `app/app_state.py` | View state management - projection, matrix stack |
| 3 | `animation/animation_manager.py` | Animation system - event loop integration |
| 4 | `main_window/Window.py` | Main window - pyglet.window.Window subclass |
| 5 | `viewer/shapes.py` | Primitive rendering functions |
| 6 | `main_g.py` | Entry point |

---

## 9. Appendix: Tkinter Backend Details

Since Tkinter is the priority alternative backend:

### Rendering Approach

- **2D Canvas** - Use `tkinter.Canvas` widget
- **Isometric Projection** - Project 3D cube coordinates to 2D
- **No Display Lists** - Direct draw calls (Canvas maintains item IDs)
- **Colors** - Convert RGB tuples to hex strings

### Animation

- Use `canvas.after(ms, callback)` for scheduling
- Update item positions/colors directly via Canvas API
- Simpler than OpenGL - no matrix transformations needed

### Window Integration

```python
class TkinterWindow:
    def __init__(self, width: int, height: int, title: str):
        self._root = tk.Tk()
        self._root.title(title)
        self._canvas = tk.Canvas(self._root, width=width, height=height, bg='black')
        self._canvas.pack()

        # Bind events
        self._root.bind('<KeyPress>', self._on_key)
        self._canvas.bind('<B1-Motion>', self._on_drag)

    def run(self):
        self._root.mainloop()
```

### Limitations

- 2D only (isometric projection instead of true 3D)
- Simpler visuals (no textures, lighting)
- Suitable for debugging, education, and lightweight usage
