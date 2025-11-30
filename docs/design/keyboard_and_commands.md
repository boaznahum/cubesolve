# Keyboard Handling and Command System

## 1. Architecture (After Refactoring)

> **Last Updated:** 2025-11-30

### 1.1 Overview

All backends now use a **single entry point** for keyboard handling:

```
User Input → Backend Native Event → Abstract Keys → handle_key_with_error_handling() → Action
```

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

### 1.3 Detailed Flow by Backend

#### Pyglet Backend Flow
```
User presses 'R' key
    │
    ▼
pyglet.window.Window.on_key_press(symbol=114, modifiers=0)     [pyglet internal]
    │
    ▼
PygletAppWindow.on_key_press(symbol=114, modifiers=0)          [pyglet/app_window.py:146]
    │
    ├── abstract_symbol = _PYGLET_TO_KEYS.get(114) → Keys.R (82)
    ├── abstract_mods = _convert_modifiers(0) → 0
    │
    ▼
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
    │
    ▼
match value:
    case Keys.R:  # 82
        op.play(Algs.R, inverse=False)
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
key_press_handler(event)  →  TkinterAppWindow._on_key_press(event)  [tkinter/app_window.py:163]
    │
    ▼
self._on_native_key_press(82, 0)                               [inherited from AppWindowBase]
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
ConsoleAppWindow._handle_key('R')                              [console/app_window.py:153]
    │
    ├── abstract_key = _CONSOLE_TO_KEYS.get('R') → Keys.R (82)
    ├── modifiers = Modifiers.SHIFT if self._inv_mode else 0
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
handle_key_with_error_handling(self, 82, 0)                    [app_window_base.py:41]
    │
    ▼
main_g_keyboard_input.handle_keyboard_input(window, 82, 0)     [main_g_keyboard_input.py:19]
```

### 1.4 Summary Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           NATIVE KEY EVENT                                  │
├────────────────────────────────────────────────────────────────────────────┤
│ Pyglet:   pyglet.window.Window.on_key_press(symbol: int)                   │
│ Tkinter:  TkinterWindow._on_key_press(tk_event) → KeyEvent                 │
│ Console:  ConsoleEventLoop → key_handler(char: str)                        │
│ Headless: test calls inject_key(key: int)                                  │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND APP WINDOW METHOD                            │
├────────────────────────────────────────────────────────────────────────────┤
│ PygletAppWindow.on_key_press()        → converts via _PYGLET_TO_KEYS       │
│ TkinterAppWindow._on_key_press()      → already converted by TkinterWindow │
│ ConsoleAppWindow._handle_key()        → converts via _CONSOLE_TO_KEYS      │
│ HeadlessAppWindow.inject_key()        → already abstract Keys              │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  handle_key_with_error_handling(window, symbol: int, modifiers: int)       │
│  Location: src/cube/main_window/app_window_base.py:41                      │
│                                                                             │
│  - SINGLE ENTRY POINT for all backends                                     │
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

### 1.4 Backend Implementation Details

#### Pyglet Backend
```python
# src/cube/gui/backends/pyglet/app_window.py
def on_key_press(self, symbol, modifiers):
    abstract_symbol = _PYGLET_TO_KEYS.get(symbol, symbol)
    abstract_mods = _convert_modifiers(modifiers)
    handle_key_with_error_handling(self, abstract_symbol, abstract_mods)
```

#### Tkinter Backend
```python
# src/cube/gui/backends/tkinter/app_window.py
def _on_key_press(self, event):
    self._on_native_key_press(event.symbol, event.modifiers)  # Inherited from AppWindowBase
    self._draw()
```

#### Headless Backend
```python
# src/cube/gui/backends/headless/app_window.py
def inject_key(self, key, modifiers=0):
    handle_key_with_error_handling(self, key, modifiers)
```

#### Console Backend
```python
# src/cube/gui/backends/console/app_window.py

# Mapping from console characters to abstract Keys
_CONSOLE_TO_KEYS = {
    'R': Keys.R, 'L': Keys.L, 'U': Keys.U, ...
    '0': Keys._0, '1': Keys._1, ...
    '?': Keys.SLASH, '<': Keys.COMMA, 'Q': Keys.Q,
}

def _handle_key(self, key: str):
    if key == ConsoleKeys.INV:  # Handle console-specific inverse mode
        self._inv_mode = not self._inv_mode
        return False

    abstract_key = _CONSOLE_TO_KEYS.get(key)
    modifiers = Modifiers.SHIFT if self._inv_mode else 0
    handle_key_with_error_handling(self, abstract_key, modifiers)
```

### 1.5 Key Files

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
3. ✅ Updated `TkinterAppWindow` to use `_on_native_key_press()`
4. ✅ Simplified `HeadlessAppWindow` - now calls `handle_key_with_error_handling()`
5. ✅ **Fixed ConsoleAppWindow** - removed 60+ lines of duplicated command logic

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

**After (clean delegation):**
```python
def _handle_key(self, key):
    abstract_key = _CONSOLE_TO_KEYS.get(key)
    modifiers = Modifiers.SHIFT if self._inv_mode else 0
    handle_key_with_error_handling(self, abstract_key, modifiers)
```

### Pending (A2)

- [ ] Create `Command` enum
- [ ] Create `CommandDispatcher`
- [ ] Add `inject_command()` to AppWindow protocol
- [ ] Update GUI tests to use commands
