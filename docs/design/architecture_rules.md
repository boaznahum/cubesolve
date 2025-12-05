# Architecture Rules

> **Purpose:** Consolidated architecture rules for this codebase.
> **Maintained by:** Human architect + Claude
> **Last Updated:** 2025-12-05

---

## Claude Instructions
> 1. Whenever you change in presentation elements and GUI, update the UML diagrams
> 2. Protocols should be named with `I` prefix (like Java interfaces), e.g., `IWindow` instead of `Window`
> 3. In UML diagrams, show duck typing with bold red dashed lines labeled "duck" to visualize the full picture
>

## 1. Four-Level Class Hierarchy

All protocol implementations should follow this 4-level architecture pattern:

```
Level 1: Interface (Protocol)     - Defines the contract
Level 2: Abstract (Abstract*)     - No-op default implementations
Level 3: Base (*Base)             - Real shared implementation
Level 4: Concrete                 - Backend-specific implementation
```

### Example: Window Protocol Hierarchy

```
Window (Protocol)                 ← Level 1: Interface/contract
    └── AbstractWindow            ← Level 2: No-op defaults (all methods do nothing)
        └── WindowBase            ← Level 3: Real shared implementation
            └── HeadlessWindow    ← Level 4: Concrete implementation
```

### When to Use Each Level

| Level | Name Pattern | Purpose | Example |
|-------|--------------|---------|---------|
| 1 | `Protocol` | Define the contract (what methods exist) | `Window`, `Renderer` |
| 2 | `Abstract*` | Provide empty/no-op implementations | `AbstractWindow`, `AbstractRenderer` |
| 3 | `*Base` | Provide real shared code that multiple backends use | `WindowBase`, `AppWindowBase` |
| 4 | (varies) | Backend-specific implementation | `PygletWindow`, `HeadlessWindow` |

### Rules

1. **Level 2 (Abstract)** classes MUST inherit from Level 1 (Protocol)
2. **Level 3 (Base)** classes MUST inherit from Level 2 (Abstract)
3. **Level 4 (Concrete)** classes SHOULD inherit from Level 3 (Base) when possible
4. If metaclass conflicts prevent inheritance, use duck typing and document it

---

## 2. Protocol Implementation

### Rule: Always Inherit from Protocols

When implementing a protocol, the class MUST inherit from it for:
- IDE autocomplete and navigation
- Static type checking (mypy)
- Runtime `isinstance()` checks

```python
# CORRECT:
from cube.presentation.gui.protocols.Renderer import Renderer

class PygletRenderer(Renderer):
    """Implements Renderer protocol."""
    ...

# WRONG (duck typing):
class PygletRenderer:  # Missing inheritance!
    """Implements Renderer protocol."""
    ...
```

---

## 3. No Runtime Duck Typing

### Rule: No `getattr()`/`hasattr()` for Optional Features

**PROHIBITED:** Using `getattr()` or `hasattr()` to check for optional features.

```python
# WRONG:
modern_renderer = getattr(ctx.window, 'modern_renderer', None)
if modern_renderer is not None:
    modern_renderer.adjust_ambient(0.05)
```

**REQUIRED:** Add optional methods to the protocol with `None` return for unsupported:

```python
# In Protocol:
def adjust_brightness(self, delta: float) -> float | None:
    """Returns new brightness or None if not supported."""
    ...

# In usage:
new_level = ctx.window.adjust_brightness(0.05)
if new_level is not None:
    # Feature is supported
    ...
```

### Exception: Acceptable Duck Typing

These patterns are acceptable:
- External library interop (ctypes, numpy type detection)
- Debug-only code inspecting internals
- Platform-specific feature detection (tkinter event.delta)

---

## 4. Type Annotations for Protocols

### Rule: Use Protocols for Type Hints, Not Abstract/Base Classes

**CRITICAL:** When declaring types for parameters, return values, or variables, always use the **Protocol** (interface), never the Abstract or Base class.

Abstract and Base classes exist for **inheritance only**, not for typing. Using them as types defeats the purpose of the abstraction layer.

```python
# WRONG - Using abstract/base class as type:
def create_viewer(renderer: AbstractRenderer) -> None:  # BAD!
    ...

def process_window(window: WindowBase) -> None:  # BAD!
    ...

# CORRECT - Using protocol as type:
def create_viewer(renderer: Renderer) -> None:  # GOOD - Renderer is the protocol
    ...

def process_window(window: Window) -> None:  # GOOD - Window is the protocol
    ...
```

### Why This Matters

1. **Liskov Substitution Principle** - Code should depend on abstractions (protocols), not implementations
2. **Flexibility** - Any class implementing the protocol can be passed, not just subclasses of a specific base
3. **Decoupling** - Reduces dependencies on internal implementation hierarchy
4. **Testing** - Makes mocking easier since any protocol-compliant object works

### The Hierarchy Purpose

| Level | Name Pattern | Purpose | Used For |
|-------|--------------|---------|----------|
| Protocol | `Window`, `Renderer` | Define the contract | **TYPE HINTS** |
| Abstract | `Abstract*` | Provide no-op defaults | **INHERITANCE ONLY** |
| Base | `*Base` | Provide shared implementation | **INHERITANCE ONLY** |
| Concrete | `Pyglet*`, `Headless*` | Backend-specific code | **INSTANTIATION** |

---

## 5. General Type Annotations

### Rule: All Code Must Have Type Annotations

- All function parameters must have type hints
- All function return types must be specified
- Class attributes should be typed
- Use `from __future__ import annotations` for forward references

```python
from __future__ import annotations

def process_commands(
    commands: Command | CommandSequence,
    timeout: float = 30.0,
    debug: bool = False
) -> GUITestResult:
    """Process a sequence of commands."""
    result: GUITestResult | None = None
    # ...
    return result
```

---

## 6. Lazy Initialization

### Rule: Initialize Attributes in `__init__`

**PROHIBITED:** Lazy initialization with `hasattr()`:

```python
# WRONG:
def queue_key_events(self, events):
    if not hasattr(self, '_key_event_queue'):
        self._key_event_queue = []
    self._key_event_queue.extend(events)
```

**REQUIRED:** Initialize in `__init__`:

```python
# CORRECT:
def __init__(self, ...):
    self._key_event_queue: list[KeyEvent] = []

def queue_key_events(self, events):
    self._key_event_queue.extend(events)
```

---

## 7. UML Diagram Rules

### Location

All PlantUML diagrams are in `docs/design/`:
- `protocols_pyglet.puml` - Pyglet (legacy OpenGL) backend
- `protocols_pyglet2.puml` - Pyglet2 (modern OpenGL) backend
- `protocols_headless.puml` - Headless (testing) backend
- `protocols_console.puml` - Console (text-based) backend
- `protocols_tkinter.puml` - Tkinter (2D canvas) backend

### Diagram Requirements

1. **Diagrams MUST reflect actual code** - No TODO items, no planned features
2. **Update diagrams with code changes** - Same commit, same PR
3. **Show all 4 levels** when applicable:
   - Interface (Protocol)
   - Abstract class
   - Base class
   - Concrete implementation

### Duck Typing Visualization

When a class currently uses duck typing (violation to be fixed):

```plantuml
' Use bold red dashed line with "duck" label to mark violations
PygletWindow .[#FF0000,bold,dashed].> Window : <color:red>duck
```

Red lines indicate technical debt that needs to be resolved.

### Proper Inheritance

```plantuml
' Implementation inherits from protocol (dashed line)
PygletRenderer ..|> Renderer

' Class inherits from base class (solid line)
PygletAppWindow --|> AppWindowBase
```

### Layout

- Protocols package should be at TOP
- Backend package should be at BOTTOM
- Use hidden links to enforce layout: `P -[hidden]down- B`

---

## 8. File Naming

### Rule: PascalCase for All Python Files

All Python files in this project use PascalCase naming:
- `Renderer.py` (not `renderer.py`)
- `AppWindow.py` (not `app_window.py`)
- `ModernGLRenderer.py` (not `modern_gl_renderer.py`)

### Directory Structure

```
src/cube/presentation/gui/
├── protocols/           # All protocols and base classes
│   ├── Renderer.py
│   ├── Window.py
│   ├── AbstractWindow.py
│   ├── WindowBase.py
│   ├── AppWindowBase.py
│   └── ...
└── backends/
    ├── pyglet/          # Legacy OpenGL backend
    ├── pyglet2/         # Modern OpenGL backend
    ├── headless/        # Testing backend
    ├── console/         # Text-based backend
    └── tkinter/         # 2D canvas backend
```

---

## 9. Protocol Location

### Rule: All Protocols and Base Classes in `protocols/`

The `protocols/` package contains:
1. **Protocols (Level 1)** - Interface definitions
2. **Abstract classes (Level 2)** - No-op defaults
3. **Base classes (Level 3)** - Shared implementation

Concrete implementations (Level 4) remain in their backend packages.

---

## Summary Checklist

When adding a new class that implements a protocol:

- [ ] Inherit from the protocol (or document why duck typing is required)
- [ ] Add type annotations to all methods
- [ ] Initialize all attributes in `__init__`
- [ ] Update the relevant PlantUML diagram
- [ ] Follow PascalCase file naming
- [ ] Place in correct directory (protocols/ vs backends/)

When modifying existing protocol implementations:

- [ ] Update PlantUML diagrams to reflect changes
- [ ] Verify 4-level hierarchy is maintained
- [ ] Run tests for all backends
