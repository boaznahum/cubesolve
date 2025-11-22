## Command-Based Input System

This package implements a **generator + command pattern** for handling keyboard input, enabling both interactive GUI and automated testing.

### Architecture

```
Keyboard Event
      ↓
keyboard_event_generator()  ← Generator yields commands
      ↓
Command.execute(ctx)        ← Testable, pure logic
      ↓
CommandResult              ← What happened, what needs updating
      ↓
GUI updates (or test assertions)
```

### Key Components

1. **Command** (`commands.py`)
   - Base class for all actions
   - Pure logic, no GUI dependencies
   - Returns `CommandResult` indicating what happened

2. **keyboard_event_generator** (`keyboard_generator.py`)
   - Generator that converts key events → commands
   - Yields one command per event
   - **Yield point = where GUI refreshes or tests assert**

3. **KeyEvent** (`keyboard_generator.py`)
   - Represents a keyboard event (symbol + modifiers)
   - Can be real (from pyglet) or simulated (tests)

4. **KeyboardInputAdapter** (`gui_adapter.py`)
   - Bridges pyglet events → command generator
   - Handles command execution and GUI updates

### Usage: Real GUI

```python
# In Window.on_key_press:
from cube.input.gui_adapter import KeyboardInputAdapter

class Window:
    def __init__(self, app):
        self.input_adapter = KeyboardInputAdapter(self)

    def on_key_press(self, symbol, modifiers):
        return self.input_adapter.handle_key_press(symbol, modifiers)
```

### Usage: Tests

```python
from cube.input.keyboard_generator import keyboard_event_generator, KeyEvent
from pyglet.window import key

# Create test app (no GUI)
app = AbstractApp.create_non_default(3, animation=False)

# Simulate key presses
events = [
    KeyEvent(key.R, 0),           # Press R
    KeyEvent(key.U, 0),           # Press U
    KeyEvent(key.SLASH, 0),       # Press / (solve)
]

# Process events
for cmd in keyboard_event_generator(events):
    result = cmd.execute(app)

    # ✅ Assert on result
    assert result.error is None

    # ✅ Check state after each command
    print(f"Executed: {cmd}")
    print(f"Cube solved: {app.cube.solved}")
```

### The Power of Generators

The **yield point** in `keyboard_event_generator` is where:
- **GUI**: Refreshes display, processes events
- **Tests**: Assert on state, validate results

```python
def keyboard_event_generator(events, animation_running=False):
    for event in events:
        cmd = _map_event_to_command(event, animation_running)
        if cmd:
            yield cmd  # ← Caller can execute and check state here
```

### Benefits

#### ✅ Testability
- Test any keyboard sequence without GUI
- Assert on state between each command
- No mocking needed

#### ✅ Clear Refresh Points
- Generator yields = where refresh happens
- No confusion about "when to redraw"

#### ✅ Separation of Concerns
- Commands: Pure business logic
- Generator: Input parsing
- Adapter: GUI integration

#### ✅ Replayability
- Commands can be recorded
- Replayed in tests or for debugging
- Sequences can be saved/loaded

#### ✅ Incremental Migration
- Can coexist with old keyboard handler
- Migrate keys one-by-one
- No "big bang" rewrite

### Example Test: Scramble and Solve

```python
def test_scramble_and_solve():
    app = AbstractApp.create_non_default(3, animation=False)

    # Simulate: scramble (key '1'), then solve (key '/')
    events = [
        KeyEvent(key._1, 0),
        KeyEvent(key.SLASH, 0),
    ]

    # Track what happens
    states = []
    for cmd in keyboard_event_generator(events):
        result = cmd.execute(app)
        assert result.error is None
        states.append(app.cube.get_state())

    # Validate
    assert len(states) == 2
    assert states[0] != states[1]  # Scramble changed state
    assert app.cube.solved         # Solve fixed it
```

### Example: Inspecting State Between Moves

```python
def test_r_u_r_prime_u_prime():
    """Test the sexy move: R U R' U'"""
    app = AbstractApp.create_non_default(3, animation=False)

    events = [
        KeyEvent(key.R, 0),              # R
        KeyEvent(key.U, 0),              # U
        KeyEvent(key.R, key.MOD_SHIFT),  # R'
        KeyEvent(key.U, key.MOD_SHIFT),  # U'
    ]

    move_count = 0
    for cmd in keyboard_event_generator(events):
        result = cmd.execute(app)
        move_count += 1

        # Check state after each move
        if move_count < 4:
            assert not app.cube.solved  # Not solved yet
        else:
            assert app.cube.solved      # Back to solved
```

### Migration Guide

#### Step 1: Install alongside existing code
- Keep old `handle_keyboard_input` working
- New system in `cube/input/` package

#### Step 2: Add adapter to Window
```python
from cube.input.gui_adapter import KeyboardInputAdapter

class Window:
    def __init__(self, app):
        self.input_adapter = KeyboardInputAdapter(self)
```

#### Step 3: Route through adapter (optional)
```python
def on_key_press(self, symbol, modifiers):
    # Try new system first
    if self.input_adapter.handle_key_press(symbol, modifiers):
        return True

    # Fall back to old system for unmapped keys
    from cube.main_window.main_g_keyboard_input import handle_keyboard_input
    handle_keyboard_input(self, symbol, modifiers)
```

#### Step 4: Write tests
```python
# Now you can test keyboard workflows!
def test_my_workflow():
    app = AbstractApp.create_non_default(3, animation=False)
    events = [...]
    for cmd in keyboard_event_generator(events):
        cmd.execute(app)
    assert ...
```

### Command Types

#### Cube Operations
- `RotateFaceCommand` - R, L, U, D, F, B, M, E, S, X, Y, Z
- `ScrambleCommand` - Generate random scramble
- `SolveCommand` - Solve cube (full or partial)
- `UndoCommand` - Undo last move

#### Application State
- `QuitCommand` - Exit application
- `ToggleAnimationCommand` - Toggle animation on/off
- `ChangeCubeSizeCommand` - Increase/decrease size
- `AdjustAnimationSpeedCommand` - Speed up/slow down

#### View Control
- `AdjustViewAngleCommand` - Rotate view
- `ZoomCommand` - Zoom in/out
- `PanCommand` - Pan left/right/up/down
- `ResetViewCommand` - Reset camera

#### Recording
- `ToggleRecordingCommand` - Start/stop recording
- `PlayRecordingCommand` - Replay sequence
- `ClearRecordingCommand` - Clear recording

### Answering Your Questions

#### Q: "Where should refresh happen?"
**A:** At the yield point in the generator. When the generator yields a command:
- Real GUI: Execute command → check result → refresh if needed
- Tests: Execute command → assert on state

#### Q: "What about non-algorithm keys (quit, resize)?"
**A:** All handled by specific commands:
- `QuitCommand` - Raises AppExit (same as today)
- `ChangeCubeSizeCommand` - Resets cube/operator/viewer
- `ToggleAnimationCommand` - Toggles flag

#### Q: "How do tests validate state?"
**A:** After each command execution:
```python
for cmd in keyboard_event_generator(events):
    result = cmd.execute(app)
    # ← Assert here on app.cube.get_state()
```

#### Q: "What about exceptions?"
**A:** Commands return `CommandResult` with error field:
- Success: `result.error is None`
- Failure: `result.error = "message"`
- Quit: Raises `AppExit` (flow control exception)

### Running Tests

```bash
# Run input command tests
python cube/tests/test_input_commands.py

# Or via pytest
pytest cube/tests/test_input_commands.py -v
```
