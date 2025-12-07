Capture and document a new GUI bug. The argument $ARGUMENTS is optional and contains a description of the expected behavior.

## Automated Workflow

1. **Launch GUI with Debug Output (filtered)**:
   ```bash
   cd E:/dev/code/cubesolve && .venv/Scripts/python.exe -m cube.main_pyglet2 --debug-all 2>&1 | grep -E "(on_key_press|on_mouse|Traceback|Error|RuntimeError|Exception|File \")" | head -100
   ```
   This filters the verbose debug dump to show only key presses, mouse events, and errors.

2. **Wait for User to Reproduce Bug**:
   - Tell user: "GUI is running. Press keys to reproduce the bug, then press `q` to quit."
   - The filtered output shows key presses and any errors in real-time

3. **Analyze Output**:
   - Extract key presses from `DEBUG: on_key_press: symbol=X, modifiers=Y` lines
   - Extract error tracebacks
   - Map symbol numbers to key names and commands

4. **Document the Bug**:
   - Add to `__todo.md` with next available B# ID
   - Include: key pressed, command triggered, error/unexpected behavior
   - Status: `❌` (not started)

5. **Create GUI Test**:
   - Add test to `tests/gui/test_gui.py` in the "BUG REPRODUCTION TESTS" section
   - Test name: `test_bug_B{number}_{short_description}`
   - Mark with `@pytest.mark.skip(reason="B#: <description>")` until fixed

6. **Report Back**: Show:
   - Bug ID assigned
   - Key presses captured
   - Error found
   - Test location
   - Root cause analysis

## Key Symbol Reference (common keys)
| Symbol | Key | Common Command |
|--------|-----|----------------|
| 45 | `-` | SIZE_DEC |
| 61 | `=` | SIZE_INC |
| 91 | `[` | BRIGHTNESS_DOWN |
| 93 | `]` | BRIGHTNESS_UP |
| 113 | `q` | QUIT |
| 114 | `r` | ROTATE_R |
| 65307 | Escape | RESET |
| 65361-65364 | Arrow keys | View rotation |
