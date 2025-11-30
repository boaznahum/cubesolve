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
- `tkinter/app_window.py:171` - `handle_key()` protocol method
- `console/app_window.py:153` - `_on_console_key_event()` native handler
- `console/app_window.py:193` - `handle_key()` protocol method
- `headless/app_window.py:145` - `inject_key()` native handler
- `headless/app_window.py:156` - `handle_key()` protocol method
- `app_window_base.py:214` - `handle_key()` base implementation

### 1.4 Detailed Flow by Backend (with line numbers)

#### Pyglet Backend Flow
```
User presses 'R' key
    │
    ▼
pyglet.window.Window.on_key_press(symbol=114, modifiers=0)     [pyglet internal]
    │
    ▼
PygletAppWindow.on_key_press(symbol=114, modifiers=0)          [pyglet/app_window.py:144]
    │
    ├── abstract_symbol = _PYGLET_TO_KEYS.get(114) → Keys.R (82)
    ├── abstract_mods = _convert_modifiers(0) → 0
    │
    ▼
PygletAppWindow.handle_key(82, 0)                              [pyglet/app_window.py:154]
    │
    ▼
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
```

#### Tkinter Backend Flow
```
User presses 'R' key
    │
    ▼
TkinterWindow._on_key_press(tk_event)                          [tkinter/window.py]
    │
    ├── symbol = _TK_KEY_MAP.get("r") → Keys.R (82)
    ├── modifiers = _convert_modifiers(tk_event.state) → 0
    ├── event = KeyEvent(symbol=82, modifiers=0)
    │
    ▼
key_press_handler(event) → TkinterAppWindow._on_tk_key_event(event)  [tkinter/app_window.py:163]
    │
    ▼
TkinterAppWindow.handle_key(82, 0)                             [tkinter/app_window.py:171]
    │
    ▼
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
```

#### Console Backend Flow
```
User types 'R' character
    │
    ▼
ConsoleEventLoop reads stdin → calls key_handler('R')          [console/event_loop.py]
    │
    ▼
ConsoleAppWindow._on_console_key_event('R')                    [console/app_window.py:153]
    │
    ├── abstract_key = _CONSOLE_TO_KEYS.get('R') → Keys.R (82)
    ├── modifiers = Modifiers.SHIFT if self._inv_mode else 0
    │
    ▼
ConsoleAppWindow.handle_key(82, 0)                             [console/app_window.py:193]
    │
    ▼
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
```

#### Headless Backend Flow (Testing)
```
Test calls window.inject_key(Keys.R, 0)
    │
    ▼
HeadlessAppWindow.inject_key(82, 0)                            [headless/app_window.py:145]
    │
    ▼
HeadlessAppWindow.handle_key(82, 0)                            [headless/app_window.py:156]
    │
    ▼
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
```

### 1.5 Summary Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           NATIVE KEY EVENT                                  │
├────────────────────────────────────────────────────────────────────────────┤
│ Pyglet:   pyglet.window.Window dispatches to on_key_press(symbol, mods)    │
│ Tkinter:  TkinterWindow dispatches to key_press_handler(KeyEvent)          │
│ Console:  ConsoleEventLoop dispatches to key_handler(char: str)            │
│ Headless: test calls inject_key(key, modifiers)                            │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│     NATIVE HANDLER (converts) ──────────────────────► PROTOCOL METHOD      │
├────────────────────────────────────────────────────────────────────────────┤
│ Pyglet:   on_key_press()           ─────────────────► handle_key()         │
│ Tkinter:  _on_tk_key_event()       ─────────────────► handle_key()         │
│ Console:  _on_console_key_event()  ─────────────────► handle_key()         │
│ Headless: inject_key()             ─────────────────► handle_key()         │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  handle_key_with_error_handling(window, symbol: int, modifiers: int)       │
│  Location: src/cube/main_window/app_window_base.py:41                      │
│                                                                             │
│  - Unified error handling for all backends                                 │
│  - Wraps call with try/except for AppExit, RunStop, OpAborted              │
│  - Handles GUI_TEST_MODE vs normal mode error display                      │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  main_g_keyboard_input.handle_keyboard_input(window, value, modifiers)     │
│  Location: src/cube/main_window/main_g_keyboard_input.py:19                │
│                                                                             │
│  - All command logic: match value: case Keys.R: op.play(Algs.R, inv) ...   │
│  - Animation mode vs main mode branching                                    │
│  - ~600 lines of command handling                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.6 Backend Inheritance Structure

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

### 1.7 Backend Implementation Details

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

### 1.8 Key Files

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
