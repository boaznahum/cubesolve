# Keyboard Handling and Command System

## 1. Architecture (After Refactoring)

> **Last Updated:** 2025-11-30

### 1.1 Overview

All backends now use a **unified flow** for keyboard handling:

```
User Input → Backend Native Event → Native Handler (converts) → handle_key(symbol, modifiers) → Action
```

**Key principle:** All backends have the same **protocol method** `handle_key(symbol, modifiers)` that:
1. Takes abstract `Keys` values (not native keys)
2. Calls `handle_key_with_error_handling()` for unified error handling
3. Which calls `main_g_keyboard_input.handle_keyboard_input()` for command execution

Each backend has its own native handler that receives native events, converts to abstract keys, and calls `handle_key()`.

### 1.2 Why All Backends Use the Same Abstract Keys

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

All backends convert their native key representation to the same abstract `Keys` values,
which are then passed to `handle_key_with_error_handling()`.

### 1.3 Flow Table: Native Event → handle_key (Protocol Method)

| Backend | Native Event Source | Native Handler | Calls Protocol Method |
|---------|---------------------|----------------|----------------------|
| **Pyglet** | `pyglet.window.Window` → `on_key_press()` | `on_key_press()` converts via `_PYGLET_TO_KEYS` | `handle_key()` |
| **Tkinter** | `TkinterWindow` → `key_press_handler()` | `_on_tk_key_event()` (already converted) | `handle_key()` |
| **Console** | `ConsoleEventLoop` → `key_handler()` | `_on_console_key_event()` converts via `_CONSOLE_TO_KEYS` | `handle_key()` |
| **Headless** | Test calls `inject_key()` | `inject_key()` (already abstract) | `handle_key()` |

**All backends call `handle_key(symbol, modifiers)` → `handle_key_with_error_handling()`**

**File locations:**
- `pyglet/app_window.py:144` - `on_key_press()` native handler
- `pyglet/app_window.py:154` - `handle_key()` protocol method
- `tkinter/app_window.py:163` - `_on_tk_key_event()` native handler
- `tkinter/app_window.py:171` - `handle_key()` protocol method (overrides base)
- `console/app_window.py:146` - `_on_console_key_event()` native handler
- `console/app_window.py` - `handle_key()` inherited from `AppWindowBase`
- `headless/app_window.py` - `inject_key()`, `handle_key()` inherited from `AppWindowBase`
- `app_window_base.py:41` - `handle_key_with_error_handling()` - the single entry point
- `app_window_base.py:214` - `handle_key()` base implementation

### 1.4 Two-Part Architecture: Native Handlers + Unified Path

The keyboard handling has exactly **two parts**:

1. **Native Handlers (DIFFERENT per backend)** - Convert native keys to abstract `Keys`
2. **Unified Path (IDENTICAL for all backends)** - From `handle_key()` to command execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PART 1: NATIVE HANDLERS (Backend-Specific)                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Each backend receives native key events and converts to abstract Keys.    │
│  This is the ONLY code that differs between backends.                       │
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
│      │  [app_window_base.py:214] or [pyglet/app_window.py:154]              │
│      │                                                                      │
│      ▼                                                                      │
│  handle_key_with_error_handling(window, 82, 0)                              │
│      │                                                                      │
│      │  [app_window_base.py:41]                                             │
│      │  - Unified error handling (AppExit, RunStop, OpAborted)              │
│      │  - GUI_TEST_MODE vs normal mode                                      │
│      │                                                                      │
│      ▼                                                                      │
│  main_g_keyboard_input.handle_keyboard_input(window, 82, 0)                 │
│      │                                                                      │
│      │  [main_g_keyboard_input.py:19]                                       │
│      │  - ALL command logic lives here (~600 lines)                         │
│      │  - match value: case Keys.R: op.play(Algs.R, inv) ...                │
│      │                                                                      │
│      ▼                                                                      │
│  COMMAND EXECUTED (cube rotated, scrambled, solved, etc.)                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5 Native Handler Details (Part 1)

These are the **only backend-specific** keyboard handling functions:

| Backend | Native Handler | Location | Converts |
|---------|----------------|----------|----------|
| **Pyglet** | `on_key_press()` | `pyglet/app_window.py:144` | pyglet key codes → `Keys` |
| **Tkinter** | `_on_tk_key_event()` | `tkinter/app_window.py:163` | (already converted) |
| **Console** | `_on_console_key_event()` | `console/app_window.py:146` | characters → `Keys` |
| **Headless** | `inject_key()` | (inherited) | (already abstract) |

### 1.6 Unified Path Details (Part 2)

After native handlers call `handle_key()`, the path is **identical**:

```
handle_key(symbol, modifiers)
    ↓
handle_key_with_error_handling(window, symbol, modifiers)   [app_window_base.py:41]
    ↓
main_g_keyboard_input.handle_keyboard_input(window, symbol, modifiers)   [main_g_keyboard_input.py:19]
    ↓
Command execution (op.play, slv.solve, etc.)
```

**All command logic is in ONE place:** `main_g_keyboard_input.py`

### 1.7 Backend Inheritance Structure

```
AppWindowBase (ABC)                          [app_window_base.py]
    │
    ├── handle_key()          ← Protocol method (calls handle_key_with_error_handling)
    ├── inject_key()          ← Delegates to handle_key()
    ├── inject_key_sequence() ← Parses string and calls inject_key()
    └── [shared: app, viewer, animation_running, status_labels, etc.]

    ▼ Inheritance

┌─────────────────────────────────────────────────────────────────────────┐
│ TkinterAppWindow(AppWindowBase, AnimationWindow, AppWindow)             │
│   - Inherits handle_key(), overrides to add _draw()                     │
│   - Native handler: _on_tk_key_event() → handle_key()                   │
├─────────────────────────────────────────────────────────────────────────┤
│ ConsoleAppWindow(AppWindowBase, AppWindow)                              │
│   - Inherits handle_key(), inject_key() from base                       │
│   - Native handler: _on_console_key_event() → handle_key()              │
├─────────────────────────────────────────────────────────────────────────┤
│ HeadlessAppWindow(AppWindowBase, AppWindow)                             │
│   - Inherits handle_key(), inject_key(), inject_key_sequence() from base│
│   - Native handler: (tests call inject_key() directly)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ PygletAppWindow(pyglet.window.Window, AnimationWindow)  ← NO AppWindowBase│
│   - Cannot inherit from AppWindowBase (metaclass conflict with pyglet)  │
│   - Has its own handle_key() implementation                             │
│   - Native handler: on_key_press() → handle_key()                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Note:** PygletAppWindow cannot inherit from AppWindowBase because `pyglet.window.Window` has a metaclass (`WindowMeta`) that conflicts with `ABCMeta`. The solution is to duplicate the `handle_key()` method in PygletAppWindow.

### 1.8 Backend Implementation Details

All backends implement `handle_key(symbol, modifiers)` - the protocol method.

#### Pyglet Backend (duplicates handle_key - metaclass conflict)
```python
# src/cube/gui/backends/pyglet/app_window.py:144
def on_key_press(self, symbol, modifiers):
    """NATIVE handler - called by pyglet, converts and calls handle_key."""
    abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
    abstract_mods = _convert_modifiers(modifiers)
    self.handle_key(abstract_symbol, abstract_mods)

# src/cube/gui/backends/pyglet/app_window.py:154
def handle_key(self, symbol: int, modifiers: int) -> None:
    """PROTOCOL METHOD - receives abstract Keys."""
    handle_key_with_error_handling(self, symbol, modifiers)
```

#### Tkinter Backend (inherits from AppWindowBase)
```python
# src/cube/gui/backends/tkinter/app_window.py:163
def _on_tk_key_event(self, event) -> None:
    """NATIVE handler - called by TkinterWindow, calls handle_key."""
    self.handle_key(event.symbol, event.modifiers)

# src/cube/gui/backends/tkinter/app_window.py:171
def handle_key(self, symbol: int, modifiers: int) -> None:
    """PROTOCOL METHOD - overrides to add redraw after key press."""
    super().handle_key(symbol, modifiers)  # ← calls AppWindowBase.handle_key()
    self._draw()
```

#### Console Backend (inherits from AppWindowBase)
```python
# src/cube/gui/backends/console/app_window.py:146
def _on_console_key_event(self, key: str) -> bool:
    """NATIVE handler - called by ConsoleEventLoop, converts and calls handle_key."""
    # Handle inverse mode toggle (console-specific)
    if key == ConsoleKeys.INV:
        self._inv_mode = not self._inv_mode
        return False

    # Convert and dispatch
    abstract_key = _CONSOLE_TO_KEYS.get(key)
    modifiers = Modifiers.SHIFT if self._inv_mode else 0
    self.handle_key(abstract_key, modifiers)  # ← inherited from AppWindowBase

# handle_key() inherited from AppWindowBase
```

#### Headless Backend (inherits from AppWindowBase)
```python
# Tests call inject_key() directly - inherited from AppWindowBase

# inject_key() inherited from AppWindowBase
# handle_key() inherited from AppWindowBase
# inject_key_sequence() inherited from AppWindowBase
```

### 1.9 Key Files

| File | Purpose |
|------|---------|
| `main_window/app_window_base.py` | `handle_key_with_error_handling()` - single entry point |
| `main_window/main_g_keyboard_input.py` | All command logic (~600 lines) |
| `gui/types.py` | Abstract `Keys` class with ASCII-like values |
| `gui/backends/pyglet/window.py` | `_PYGLET_TO_KEYS` mapping |
| `gui/backends/tkinter/window.py` | `_TK_KEY_MAP` mapping |
| `gui/backends/console/app_window.py` | `_CONSOLE_TO_KEYS` mapping |

---

## 2. Key Injection

### 2.1 inject_key_sequence()

Each backend still has its own `inject_key_sequence()` for test convenience:

```python
window.inject_key_sequence("1/Q")  # Scramble seed 1, solve, quit
```

This is a high-level API that maps characters to Keys and calls `inject_key()`.

### 2.2 inject_key()

Low-level API that injects a single abstract key:

```python
window.inject_key(Keys.R, Modifiers.SHIFT)  # R' (R inverse)
```

All backends implement this by calling `handle_key_with_error_handling()`.

---

## 3. Future: Command Pattern (A2)

### 3.1 Motivation

While keyboard handling is now unified, tests still inject **keys** which requires:
- Character → Key mapping in each backend's `inject_key_sequence()`
- Understanding key semantics (SHIFT = inverse)

### 3.2 Proposed Solution

Replace key injection with **command injection**:

```python
# Current (key-based)
window.inject_key_sequence("1/Q")

# Future (command-based)
window.inject_commands([Command.SCRAMBLE_1, Command.SOLVE, Command.QUIT])
```

### 3.3 Command Enum (Planned)

```python
class Command(Enum):
    ROTATE_R = auto()
    ROTATE_R_PRIME = auto()
    SCRAMBLE_1 = auto()
    SOLVE = auto()
    QUIT = auto()
    # ... etc
```

### 3.4 Benefits

1. **Backend-agnostic tests** - No key mapping needed
2. **Type-safe** - `Command.ROTATE_R` vs magic string "R"
3. **Explicit semantics** - `ROTATE_R_PRIME` vs `Keys.R + SHIFT`
4. **Extensible** - Add commands without changing key handler

---

## 4. Migration History

### Completed (2025-11-30)

1. ✅ Created `handle_key_with_error_handling()` in `app_window_base.py`
2. ✅ Simplified `PygletAppWindow.on_key_press()` - removed duplicate error handling
3. ✅ Updated `TkinterAppWindow` to use `_on_tk_key_event()` native handler
4. ✅ Simplified `HeadlessAppWindow` - now inherits from `AppWindowBase`
5. ✅ **Fixed ConsoleAppWindow** - now inherits from `AppWindowBase`
6. ✅ **Unified inheritance** - Tkinter, Console, Headless all inherit from `AppWindowBase`
7. ✅ **Removed duplicate code** - `handle_key()`, `inject_key()`, `inject_key_sequence()` in base class

### Backend Inheritance Summary

| Backend | Inherits from | handle_key() |
|---------|---------------|--------------|
| **Tkinter** | `AppWindowBase` | Overrides (adds `_draw()`) |
| **Console** | `AppWindowBase` | Inherited from base |
| **Headless** | `AppWindowBase` | Inherited from base |
| **Pyglet** | `pyglet.window.Window` | Own implementation (metaclass conflict) |

### Before/After: Console Backend

**Before (60+ lines of duplicated logic):**
```python
def _handle_key(self, key):
    match key:
        case ConsoleKeys.R:
            op.play(Algs.R, self._inv_mode)  # Duplicate!
        case ConsoleKeys.L:
            op.play(Algs.L, self._inv_mode)  # Duplicate!
        # ... 50+ more lines
```

**After (clean delegation via inheritance):**
```python
class ConsoleAppWindow(AppWindowBase, AppWindow):
    # handle_key() inherited from AppWindowBase
    # inject_key() inherited from AppWindowBase

    def _on_console_key_event(self, key: str) -> bool:
        abstract_key = _CONSOLE_TO_KEYS.get(key)
        modifiers = Modifiers.SHIFT if self._inv_mode else 0
        self.handle_key(abstract_key, modifiers)  # ← inherited
```

### Pending (A2)

- [ ] Create `Command` enum
- [ ] Create `CommandDispatcher`
- [ ] Add `inject_command()` to AppWindow protocol
- [ ] Update GUI tests to use commands
