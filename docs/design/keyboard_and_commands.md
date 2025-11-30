# Keyboard Handling and Command System

## 1. Architecture (Current)

> **Last Updated:** 2025-11-30 (A2.1 Complete)

### 1.1 Overview

All backends use a **unified flow** for keyboard handling with the **Command pattern**:

```
User Input → Backend Native Event → Native Handler (converts) → handle_key(symbol, modifiers)
           → lookup_command() → command.execute(ctx) → Action
```

**Key principle:** All backends have the same **protocol method** `handle_key(symbol, modifiers)` that:
1. Takes abstract `Keys` values (not native keys)
2. Calls `lookup_command()` to find the Command for the key+modifiers
3. Calls `command.execute(ctx)` to perform the action

Each backend has its own native handler that receives native events, converts to abstract keys, and calls `handle_key()`.

### 1.2 Command Pattern Architecture

The Command pattern separates **key binding** from **command execution**:

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Key Bindings      │     │     Command Enum     │     │  Command Handlers   │
│  (key_bindings.py)  │────▶│    (command.py)      │────▶│   (command.py)      │
├─────────────────────┤     ├──────────────────────┤     ├─────────────────────┤
│ KEY_BINDINGS_NORMAL │     │ Command.ROTATE_R     │     │ _rotate("R", False) │
│ KEY_BINDINGS_ANIM   │     │ Command.SCRAMBLE_1   │     │ _scramble(1)        │
│ lookup_command()    │     │ Command.SOLVE_ALL    │     │ _solve(...)         │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
```

### 1.3 Why All Backends Use the Same Abstract Keys

The `Keys` class in `gui/types.py` uses **ASCII-like values** by design:

```python
class Keys:
    # Letters use ASCII values
    R = 82  # ord('R')
    L = 76  # ord('L')

    # Numbers use ASCII values
    _0 = 48  # ord('0')
    _1 = 49  # ord('1')
```

This makes key mapping intuitive:
- **Pyglet**: `pyglet.window.key.R` (some internal value) → `Keys.R` (82)
- **Tkinter**: keysym "r" → `Keys.R` (82)
- **Console**: character 'R' → `Keys.R` (82)
- **Headless**: already uses `Keys.R` directly

### 1.4 Flow Diagram: Native Event → Command Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PART 1: NATIVE HANDLERS (Backend-Specific)                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Each backend receives native key events and converts to abstract Keys.    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pyglet:   on_key_press(symbol=114, mods)                                   │
│            → _PYGLET_TO_KEYS.get(114) → Keys.R (82)                         │
│            → handle_key(82, 0)                                              │
│                                                                             │
│  Tkinter:  _on_tk_key_event(event)                                          │
│            → event already has abstract keys                                │
│            → handle_key(event.symbol, event.modifiers)                      │
│                                                                             │
│  Console:  _on_console_key_event('R')                                       │
│            → _CONSOLE_TO_KEYS.get('R') → Keys.R (82)                        │
│            → handle_key(82, modifiers)                                      │
│                                                                             │
│  Headless: inject_key(Keys.R, 0)                                            │
│            → already abstract keys                                          │
│            → handle_key(82, 0)                                              │
│                                                                             │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PART 2: UNIFIED PATH (100% Identical for ALL Backends)                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  From handle_key() onward, every backend executes the EXACT same code.     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  handle_key(symbol=82, modifiers=0)                                         │
│      │                                                                      │
│      │  [app_window_base.py:159] or [pyglet/PygletAppWindow.py:159]         │
│      │                                                                      │
│      ▼                                                                      │
│  cmd = lookup_command(symbol, modifiers, animation_running)                 │
│      │                                                                      │
│      │  [key_bindings.py:274]                                               │
│      │  - Looks up (key, mods) in KEY_BINDINGS_NORMAL or _ANIMATION         │
│      │  - Returns Command enum value or None                                │
│      │                                                                      │
│      ▼                                                                      │
│  if cmd:                                                                    │
│      self.inject_command(cmd)                                               │
│      │                                                                      │
│      │  [app_window_base.py:251]                                            │
│      │  - Creates CommandContext from window                                │
│      │  - Calls cmd.execute(ctx)                                            │
│      │  - Updates GUI if needed                                             │
│      │  - Handles exceptions (AppExit, etc.)                                │
│      │                                                                      │
│      ▼                                                                      │
│  COMMAND EXECUTED (cube rotated, scrambled, solved, etc.)                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Command System

### 2.1 Command Enum (command.py)

Each command is a self-executing enum value with lazy handler creation:

```python
class Command(Enum):
    """Self-executing command enum.

    Each value is a tuple: (handler_factory, *args)
    """
    ROTATE_R = (_rotate, "R", False)
    ROTATE_R_PRIME = (_rotate, "R", True)
    SCRAMBLE_1 = (_scramble, 1)
    SOLVE_ALL = (_solve, None)
    QUIT = (_quit,)
    # ... 100+ commands

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute this command with the given context."""
        handler = self._get_handler()  # Lazy creation
        result = handler(ctx)
        return result if result else CommandResult()
```

### 2.2 CommandContext

Provides access to all application components:

```python
@dataclass
class CommandContext:
    window: "AbstractWindow"

    @property
    def app(self) -> "AbstractApp": return self.window.app

    @property
    def op(self): return self.app.op      # Operator

    @property
    def vs(self): return self.app.vs      # ViewState

    @property
    def slv(self): return self.app.slv    # Solver

    @property
    def cube(self): return self.app.cube  # Cube

    @property
    def viewer(self): return self.window.viewer
```

### 2.3 Key Bindings (key_bindings.py)

Two declarative binding tables:

```python
# Normal mode bindings (when NOT animating)
KEY_BINDINGS_NORMAL: list[KeyBinding] = [
    (Keys.R, 0, Command.ROTATE_R),
    (Keys.R, Modifiers.SHIFT, Command.ROTATE_R_PRIME),
    (Keys._1, 0, Command.SCRAMBLE_1),
    (Keys.SLASH, 0, Command.SOLVE_ALL),
    (Keys.Q, 0, Command.QUIT),
    # ... 60+ bindings
]

# Animation mode bindings (DURING animation)
KEY_BINDINGS_ANIMATION: list[KeyBinding] = [
    (Keys.S, 0, Command.STOP_ANIMATION),  # S = Stop during animation
    (Keys.SPACE, 0, Command.PAUSE_TOGGLE),
    (Keys.NUM_ADD, 0, Command.SPEED_UP),
    (Keys.Q, 0, Command.QUIT),
    # ... limited set of commands
]

def lookup_command(key: int, modifiers: int, animation_running: bool) -> Command | None:
    """O(1) lookup for key binding."""
    table = _ANIMATION_MAP if animation_running else _NORMAL_MAP
    return table.get((key, modifiers))
```

### 2.4 Command Handlers

Handlers are factory functions that create the actual handler:

```python
def _rotate(face: str, inv: bool) -> Handler:
    """Create handler for face rotation."""
    def handler(ctx: CommandContext) -> CommandResult:
        from cube.algs import Algs
        alg = getattr(Algs, face)
        ctx.op.play(ctx.vs.slice_alg(ctx.cube, alg), inv)
        return CommandResult()
    return handler

def _scramble(seed: int | None) -> Handler:
    """Create handler for scramble."""
    def handler(ctx: CommandContext) -> CommandResult:
        from cube.algs import Algs
        ctx.op.play(Algs.scramble(ctx.cube.size, seed))
        return CommandResult()
    return handler

def _quit(ctx: CommandContext) -> None:
    """Handler for quit command."""
    from cube.app.app_exceptions import AppExit
    ctx.op.abort()
    ctx.window.close()
    raise AppExit
```

---

## 3. Key Injection Methods

### 3.1 inject_command() - Preferred

Type-safe command injection with IDE autocomplete:

```python
window.inject_command(Command.SCRAMBLE_1)
window.inject_command(Command.SOLVE_ALL)
window.inject_command(Command.QUIT)
```

### 3.2 inject_key_sequence() - Legacy

String-based key injection (DEPRECATED):

```python
window.inject_key_sequence("1/Q")  # Scramble, solve, quit
```

### 3.3 inject_key() - Low-level

Single key injection:

```python
window.inject_key(Keys.R, Modifiers.SHIFT)  # R' (R inverse)
```

---

## 4. Backend Implementation Details

### 4.1 Base Class (app_window_base.py)

```python
class AppWindowBase(ABC):
    def handle_key(self, symbol: int, modifiers: int) -> None:
        """Protocol method - lookup command and execute."""
        cmd = lookup_command(symbol, modifiers, self.animation_running)
        if cmd:
            self.inject_command(cmd)

    def inject_command(self, command: Command) -> None:
        """Execute a command with error handling."""
        try:
            ctx = CommandContext.from_window(self)
            result = command.execute(ctx)
            if not result.no_gui_update:
                self.update_gui_elements()
        except AppExit:
            # Handle quit...
```

### 4.2 Backend Inheritance

| Backend | Inherits from | handle_key() |
|---------|---------------|--------------|
| **Tkinter** | `AppWindowBase` | Overrides (adds `_draw()`) |
| **Console** | `AppWindowBase` | Inherited from base |
| **Headless** | `AppWindowBase` | Inherited from base |
| **Pyglet** | `pyglet.window.Window` | Own implementation (metaclass conflict) |

**Note:** PygletAppWindow cannot inherit from AppWindowBase because `pyglet.window.Window` has a metaclass that conflicts with `ABCMeta`.

---

## 5. Key Files

| File | Purpose |
|------|---------|
| `gui/command.py` | Command enum with 100+ self-executing commands |
| `gui/key_bindings.py` | Key→Command binding tables, lookup_command() |
| `gui/types.py` | Abstract `Keys` class with ASCII-like values |
| `main_window/app_window_base.py` | Base class with handle_key(), inject_command() |
| `gui/backends/pyglet/PygletWindow.py` | `_PYGLET_TO_KEYS` mapping |
| `gui/backends/tkinter/TkinterWindow.py` | `_TK_KEY_MAP` mapping |
| `gui/backends/console/ConsoleAppWindow.py` | `_CONSOLE_TO_KEYS` mapping |

---

## 6. Migration History

### Completed (2025-11-30)

#### A2.0: Unified Keyboard Handling
1. ✅ Created `handle_key_with_error_handling()` in `app_window_base.py`
2. ✅ Unified inheritance - Tkinter, Console, Headless all inherit from `AppWindowBase`
3. ✅ Removed duplicate code - `handle_key()`, `inject_key()` in base class

#### A2.1: Command Pattern Implementation
1. ✅ Created `Command` enum with ~100 self-executing commands
2. ✅ Created `key_bindings.py` with `KEY_BINDINGS_NORMAL` and `KEY_BINDINGS_ANIMATION`
3. ✅ Created `lookup_command()` for O(1) key→command lookup
4. ✅ Implemented lazy handler creation with caching
5. ✅ Added `inject_command()` to AppWindow protocol
6. ✅ Wired `handle_key()` to use `lookup_command()` + `command.execute()`
7. ✅ **Removed `main_g_keyboard_input.py`** (~600 lines of legacy match/case)
8. ✅ Updated `GUITestRunner` to handle `AppExit` as success

#### Q3.1: File Naming Convention (PascalCase)
All backend implementation files renamed to match class names:
- `pyglet/app_window.py` → `pyglet/PygletAppWindow.py`
- `pyglet/renderer.py` → `pyglet/PygletRenderer.py`
- `headless/app_window.py` → `headless/HeadlessAppWindow.py`
- etc.

### Architecture Before/After

**Before (A2.0):**
```
handle_key() → handle_key_with_error_handling() → main_g_keyboard_input.handle_keyboard_input()
                                                   └── 600 lines of match/case
```

**After (A2.1):**
```
handle_key() → lookup_command() → command.execute(ctx)
               └── O(1) dict lookup    └── Self-contained handler
```

---

## 7. Benefits of Command Pattern

1. **Single Source of Truth** - Key bindings in one place (`key_bindings.py`)
2. **Self-Documenting** - `Command.ROTATE_R_PRIME` vs magic `Keys.R + SHIFT`
3. **Type-Safe** - IDE autocomplete for commands
4. **Testable** - `inject_command()` bypasses key handling
5. **Extensible** - Add commands without modifying key handler
6. **Context-Aware** - Different commands during animation vs normal mode
7. **Lazy Loading** - Handlers created on first use, reducing startup time
