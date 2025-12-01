# Running the Cube Solver

This document describes all command-line options for running the Cube Solver application.

## Quick Start

```bash
# Default (pyglet backend, 3x3 cube)
python -m cube.main_any_backend

# Or using the module directly
python -m cube.main_pyglet
```

## Entry Points

| Module | Description |
|--------|-------------|
| `cube.main_any_backend` | **Recommended** - Unified entry point supporting all backends |
| `cube.main_pyglet` | Direct pyglet backend (OpenGL 3D) |
| `cube.main_headless` | Headless mode for testing |
| `cube.main_console_new` | Console text-based interface |
| `cube.main_tkinter` | Tkinter backend (2D canvas) |

## Command-Line Options

### Backend Selection

```bash
python -m cube.main_any_backend --backend=<name>
python -m cube.main_any_backend -b <name>
```

| Backend | Description |
|---------|-------------|
| `pyglet` | OpenGL-based 3D rendering (default, requires pyglet) |
| `tkinter` | 2D canvas-based rendering (built-in Python) |
| `console` | Text-based console output |
| `headless` | No visual output, for testing |

### Cube Size

```bash
python -m cube.main_any_backend --cube-size=5
python -m cube.main_any_backend -s 5
```

| Option | Description |
|--------|-------------|
| `--cube-size N`, `-s N` | Set cube size (default: 3) |

Valid sizes: 2, 3, 4, 5, ... (any integer >= 2)

### Window Options

```bash
python -m cube.main_any_backend --width=1024 --height=768 --title="My Cube"
python -m cube.main_any_backend -W 1024 -H 768 -t "My Cube"
```

| Option | Description |
|--------|-------------|
| `--width N`, `-W N` | Window width in pixels (default: 720) |
| `--height N`, `-H N` | Window height in pixels (default: 720) |
| `--title TEXT`, `-t TEXT` | Window title (default: "Cube Solver") |

*Note: Width/height are ignored for console and headless backends.*

### Animation

```bash
python -m cube.main_any_backend --no-animation
```

| Option | Description |
|--------|-------------|
| `--no-animation` | Disable cube rotation animations |

### Debug Output

```bash
python -m cube.main_any_backend --debug-all   # Enable all debug output
python -m cube.main_any_backend --quiet       # Suppress all debug output
python -m cube.main_any_backend -q            # Short form
```

| Option | Description |
|--------|-------------|
| `--debug-all` | Enable verbose debug logging (shows solver steps, etc.) |
| `--quiet`, `-q` | Suppress all debug output |

**Debug output behavior:**
- Without flags: Shows output controlled by individual debug flags (e.g., `config.SOLVER_DEBUG`)
- `--debug-all`: Shows ALL debug output regardless of individual flags
- `--quiet`: Suppresses ALL debug output regardless of individual flags

### Testing / Automation

```bash
python -m cube.main_any_backend --key-sequence="1?Q"
python -m cube.main_any_backend -k "1?Q"
```

| Option | Description |
|--------|-------------|
| `--key-sequence TEXT`, `-k TEXT` | Inject key sequence for automated testing |

**Key sequence examples:**
- `1?Q` - Scramble with seed 1, solve, quit
- `++++` - Press speed-up 4 times
- `5?Q` - Scramble with seed 5, solve, quit

## Examples

```bash
# Run with tkinter backend and 5x5 cube
python -m cube.main_any_backend -b tkinter -s 5

# Run with debug output enabled
python -m cube.main_any_backend --debug-all

# Run in quiet mode (no debug output)
python -m cube.main_any_backend -q

# Run automated test sequence
python -m cube.main_any_backend -b headless -k "1?Q"

# Large window with 4x4 cube
python -m cube.main_any_backend -W 1024 -H 1024 -s 4

# Console mode
python -m cube.main_any_backend -b console
```

## Programmatic Usage

```python
from cube.main_any_backend import run_with_backend

# Run with tkinter
run_with_backend("tkinter", cube_size=5)

# Run with debug output
run_with_backend("pyglet", debug_all=True)

# Run automated test
run_with_backend("headless", key_sequence="1?Q", quiet_all=True)
```

## Environment Requirements

| Backend | Requirements |
|---------|--------------|
| `pyglet` | `pip install pyglet` (OpenGL capable display) |
| `tkinter` | Built-in (Python with Tk) |
| `console` | Built-in (terminal) |
| `headless` | Built-in (no display needed) |

## See Also

- `tests/TESTING.md` - Running tests with pytest
- `docs/design/keyboard_and_commands.md` - Keyboard controls and commands
- `.claude/CLAUDE.md` - Project overview and architecture
