# GUI Testing for Rubik's Cube Solver

This document describes the automated GUI testing framework that allows testing the application by injecting keyboard sequences.

## Problem Solved

Previously, exceptions in the GUI event loop were caught and displayed as error messages, preventing automated testing. The application would not quit on errors, making it impossible to detect test failures.

## Solution

A comprehensive GUI testing framework that:
1. Enables test mode where exceptions propagate instead of being suppressed
2. Provides programmatic keyboard sequence injection
3. Includes timeout handling and result reporting
4. Allows automated testing of scramble/solve operations

## Components

### 1. Configuration (`cube/config/config.py`)

Two new configuration flags:

```python
GUI_TEST_MODE = False  # Enable for automated testing
QUIT_ON_ERROR_IN_TEST_MODE = True  # Quit app on error during tests
```

### 2. Modified Exception Handling (`cube/main_window/Window.py`)

The `Window.on_key_press()` method now checks `GUI_TEST_MODE`:

- **Normal mode**: Exceptions are caught and displayed in GUI (original behavior)
- **Test mode**: Exceptions propagate, window closes, app quits

```python
except Exception as e:
    if config.GUI_TEST_MODE and config.QUIT_ON_ERROR_IN_TEST_MODE:
        self.close()
        raise  # Re-raise for test harness
    else:
        # Show error in GUI
        self.app.set_error(str(e))
```

### 3. Command Injection

Type-safe command injection with IDE autocomplete:

```python
from cube.gui.Command import Command

window.inject_command(Command.SCRAMBLE_1)
window.inject_command(Command.SOLVE_ALL)
window.inject_command(Command.QUIT)
```

Available commands include:
- **Scrambles**: `SCRAMBLE_0` through `SCRAMBLE_9`
- **Face rotations**: `ROTATE_R`, `ROTATE_L`, `ROTATE_U`, etc.
- **Solve**: `SOLVE_ALL`, `SOLVE_L1`, `SOLVE_L2`, etc.
- **Application**: `QUIT`, `UNDO`, `RESET_CUBE`

### 4. Test Harness (`tests/gui/tester/GUITestRunner.py`)

Complete testing framework with:

```python
from tests.gui.tester.GUITestRunner import GUITestRunner
from cube.gui.Command import Command

result = GUITestRunner.run_test(
    commands=Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
    cube_size=3,
    backend="pyglet"
)

if result.success:
    print("Test passed!")
else:
    print(f"Test failed: {result.error}")
```

**Built-in test functions:**
- `test_scramble_and_solve(cube_size)` - Basic test
- `test_multiple_scrambles(cube_size)` - Multiple scrambles then solve
- `test_face_rotations()` - Test all face moves

### 5. Example Usage (`example_gui_test.py`)

Demonstrates various testing scenarios:

```python
# Example 1: Basic test
result = run_gui_test("1/q", cube_size=3, timeout_sec=60.0)

# Example 2: Multiple operations
result = run_gui_test("123/q", cube_size=3, timeout_sec=90.0)

# Example 3: 4x4 cube
result = run_gui_test("1/q", cube_size=4, timeout_sec=120.0)

# Example 4: With animation
result = run_gui_test("1/q", enable_animation=True, timeout_sec=120.0)

# Example 5: Custom moves
result = run_gui_test("rrrluuufq", cube_size=3, timeout_sec=30.0)
```

## Running Tests

### Run all built-in tests:

```bash
python -m cube.tests.test_gui
```

### Run examples:

```bash
python example_gui_test.py
```

### Run programmatically:

```python
from cube.tests.gui.test_gui import run_gui_test

# Simple test
result = run_gui_test("1/q")
assert result.success, f"Test failed: {result.error}"

# Advanced test
result = run_gui_test(
    key_sequence="123/q",
    timeout_sec=120.0,
    cube_size=4,
    enable_animation=False,
    debug=True
)
```

## Key Sequences

Examples of useful key sequences:

| Sequence | Description |
|----------|-------------|
| `1/q` | Scramble with key 1, solve, quit |
| `123/q` | Three different scrambles, solve, quit |
| `1aq` | Scramble, toggle animation, quit |
| `rrrq` | Three R rotations, quit |
| `1,,,q` | Scramble, undo 3 times, quit |
| `rr[q` | Two R moves, redo, quit |
| `123456/q` | Six scrambles, solve, quit |

## Timeout Handling

Tests automatically timeout if they exceed the specified duration:

```python
result = run_gui_test("1/q", timeout_sec=30.0)
if isinstance(result.error, GUITestTimeout):
    print("Test took too long!")
```

## Animation Control

Tests run faster with animation disabled:

```python
# Fast (no animation)
result = run_gui_test("1/q", enable_animation=False, timeout_sec=30.0)

# Slower but visual
result = run_gui_test("1/q", enable_animation=True, timeout_sec=120.0)
```

## Debugging

Enable debug output to see what's happening:

```python
result = run_gui_test("1/q", debug=True)
```

Output:
```
Starting GUI test with sequence: '1/q'
  Cube size: 3, Animation: False, Timeout: 60.0s
Starting pyglet event loop...
Injecting key sequence: '1/q'
Event loop exited normally
Test completed, config restored
```

## Test Result Object

`GUITestResult` contains:

```python
result.success  # bool: True if test passed
result.error    # Exception | None: Error if failed
result.message  # str: Human-readable message

# String representation
print(result)  # "✓ Test passed: ..." or "✗ Test failed: ..."
```

## Implementation Details

### How It Works

1. **Setup**: Test harness sets `config.GUI_TEST_MODE = True`
2. **Initialization**: Creates `AbstractApp` and `AppWindow` via backend
3. **Command Injection**: Injects commands via `inject_command()`
4. **Event Loop**: Runs backend event loop
5. **Exception Handling**:
   - If exception occurs: Window closes, exception propagates, test fails
   - If QUIT command: `AppExit` raised, window closes, test succeeds
   - If timeout: Watchdog thread exits event loop, test fails
6. **Cleanup**: Restores original config values

### Thread Safety

- Main thread runs pyglet event loop
- Watchdog thread monitors timeout (daemon thread)
- Both threads coordinate via `pyglet.app.exit()`

### Platform Compatibility

- **Windows**: Fully tested and working
- **Linux**: Should work (pyglet is cross-platform)
- **macOS**: Should work (pyglet is cross-platform)

## Troubleshooting

### Test hangs forever

**Cause**: Key sequence doesn't include 'q' to quit

**Solution**: Always end sequences with 'q':
```python
run_gui_test("1/q")  # Good
run_gui_test("1")    # Bad - will hang until timeout
```

### Test times out

**Causes**:
- Timeout too short for operation
- Solver taking longer than expected
- Animation enabled (slower)

**Solutions**:
```python
# Increase timeout
run_gui_test("1/q", timeout_sec=120.0)

# Disable animation
run_gui_test("1/q", enable_animation=False)

# Use smaller cube size for faster tests
run_gui_test("1/q", cube_size=3)
```

### Exception not detected

**Cause**: `GUI_TEST_MODE` not enabled

**Solution**: Use `run_gui_test()` which handles this automatically

### Window doesn't close

**Cause**: 'q' key not in sequence or exception occurred before 'q'

**Solution**: Check test result for errors

## Future Enhancements

Possible improvements:

1. **Screenshot capture**: Save screenshots at each step
2. **State verification**: Check cube state after operations
3. **Performance metrics**: Track solve time, move count
4. **Parallel testing**: Run multiple tests concurrently
5. **CI/CD integration**: GitHub Actions, Jenkins, etc.
6. **Visual regression testing**: Compare rendered output
7. **Headless mode**: Run without displaying window

## Files Modified/Created

### Modified Files:
- `cube/config/config.py` - Added `GUI_TEST_MODE` and `QUIT_ON_ERROR_IN_TEST_MODE`
- `cube/main_window/Window.py` - Modified exception handling, added key injection methods

### New Files:
- `cube/tests/test_gui.py` - Complete test harness
- `example_gui_test.py` - Usage examples
- `GUI_TESTING.md` - This documentation

## Summary

The GUI testing framework solves the original problem of exceptions being suppressed in the GUI loop. Now you can:

✓ Inject keyboard sequences programmatically
✓ Detect exceptions during test execution
✓ Ensure application quits properly on completion or error
✓ Run automated tests for scramble/solve operations
✓ Set timeouts to prevent hanging tests
✓ Control animation and cube size for different test scenarios

Example:

```python
from cube.tests.gui.test_gui import run_gui_test

# Test: Scramble with key 1, solve, quit - should complete without errors
result = run_gui_test("1/q", timeout_sec=60.0, cube_size=3)
assert result.success, f"Test failed: {result.error}"
```
