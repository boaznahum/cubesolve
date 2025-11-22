# Generator + Command Pattern - The Real Problem and Solution

## The Actual Problem Being Solved

### What You Wanted

**Test the GUI application with scripted keyboard input while keeping real GUI and animation running.**

**NOT** about running headless tests without GUI!

### The Challenge

You have two different execution modes with different behaviors:

| Mode | Input Source | GUI + Animation | Error Handling |
|------|--------------|-----------------|----------------|
| **Interactive** | Real keyboard | ✅ Active | Log error, **continue main loop** |
| **Test** | Scripted sequence | ✅ Active | **Abort test immediately** (fail fast) |

**The problem**: The original keyboard handler was tightly coupled to pyglet's event loop, making it impossible to:
1. Feed **scripted key sequences** into the running GUI
2. Have **different error handling** for tests vs. interactive use
3. **Inspect state** between individual keypresses
4. Test GUI workflows with real animation

---

## The Solution: Generator + Command Pattern

The generator pattern allows **separation of input source from processing**:

```python
# Same generator works for BOTH modes:
for cmd in keyboard_event_generator(events):
    result = cmd.execute(app)  # With GUI, with animation
    # ← Caller controls what happens here (error handling, assertions)
```

### Key Insight

The **yield point** in the generator is where **control returns to the caller**, who then decides:
- How to handle errors (log vs. abort)
- Whether to check state
- When to refresh GUI

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│         Input Source (Real OR Scripted)             │
│    Real Keyboard Events  OR  Test Event List        │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│        keyboard_event_generator(events)             │
│                                                      │
│  for event in events:                               │
│      cmd = map_to_command(event)                    │
│      yield cmd  ← ← ← CONTROL POINT                │
└────────────────┬────────────────────────────────────┘
                 │ yields Command
                 ▼
┌─────────────────────────────────────────────────────┐
│                Caller's Choice:                      │
│                                                      │
│  Interactive:              Test:                    │
│  try:                      result = cmd.execute()   │
│    cmd.execute()           assert result.error      │
│  except:                   # Abort on error         │
│    log_error()                                      │
│    continue                                         │
└─────────────────────────────────────────────────────┘
```

---

## Complete Examples

### Example 1: Interactive GUI (Real Keyboard)

Keys come from user's keyboard, errors are logged but don't crash the app:

```python
# In gui_adapter.py
class KeyboardInputAdapter:
    """Handles real keyboard input in the GUI"""

    def handle_key_press(self, symbol: int, modifiers: int) -> bool:
        """Called by pyglet when user presses a key"""

        # Wrap pyglet event
        event = KeyEvent(symbol, modifiers)
        animation_running = self.window.animation_running

        # Generator yields command(s) for this key
        for cmd in keyboard_event_generator([event], animation_running):
            try:
                # Execute with full GUI and animation
                result = cmd.execute(self.window.app)

                # Handle result
                if result.needs_viewer_reset:
                    self.window.viewer.reset()

                if result.needs_redraw:
                    self.window.update_gui_elements()

                return True

            except Exception as e:
                # Interactive mode: LOG and CONTINUE
                print(f"Error executing {cmd}: {e}")
                import traceback
                traceback.print_exc()

                # GUI keeps running!
                return True

        return False  # No command for this key
```

**Behavior**: User presses 'R' → Executes RotateFaceCommand → If error, logs it → GUI continues

---

### Example 2: Automated Test WITH GUI and Animation

**This is the key use case!**

Keys come from test script, GUI and animation are active, errors abort the test:

```python
def test_scramble_solve_with_full_gui():
    """
    Test the REAL GUI with REAL ANIMATION using scripted input.

    This is NOT a headless test - GUI and animation are active!
    The difference: keys come from our script, not user's keyboard.
    """

    # Create app WITH animation enabled
    app = AbstractApp.create_non_default(cube_size=3, animation=True)

    # Create actual GUI window (can be invisible for automated tests)
    window = Window(app, width=800, height=600, visible=False)

    # Define scripted key sequence - like a user pressing keys
    test_events = [
        KeyEvent(key._1, 0),      # Press '1' - scramble (with animation!)
        KeyEvent(key.SLASH, 0),   # Press '/' - solve (with animation!)
    ]

    # Process events through generator
    for cmd in keyboard_event_generator(test_events):
        print(f"\n→ Executing: {cmd}")

        # Execute command - GUI and animation are ACTIVE
        result = cmd.execute(app)

        # Test mode: NO try/except - errors ABORT test
        assert result.error is None, f"Command failed: {result.error}"

        # If command triggered animation, wait for it
        if hasattr(window, 'animation_running') and window.animation_running:
            # Wait for animation to complete
            while window.animation_running:
                pyglet.clock.tick()
                window.dispatch_events()
                window.on_draw()

        # Check state after this command
        print(f"  Cube solved: {app.cube.solved}")
        print(f"  Move count: {app.op.count}")

    # Final assertion
    assert app.cube.solved, "Cube should be solved after scramble + solve!"

    window.close()
```

**Behavior**:
- Test presses '1' → Scramble runs **with animation** → Window shows animated scramble
- Test presses '/' → Solve runs **with animation** → Window shows animated solution
- If ANY error → Test aborts immediately (fail fast)

---

### Example 3: Test With GUI, Without Animation (Faster)

Same test, but skip animation for speed:

```python
def test_scramble_solve_no_animation():
    """
    Test with GUI visible but animation disabled.
    Faster than full animation but still uses real GUI code path.
    """

    # animation=False - GUI exists but moves are instant
    app = AbstractApp.create_non_default(cube_size=3, animation=False)
    window = Window(app, width=800, height=600, visible=True)

    test_events = [
        KeyEvent(key._2, 0),      # Scramble key 2 (no animation for keys 1-9)
        KeyEvent(key.SLASH, 0),   # Solve
    ]

    for cmd in keyboard_event_generator(test_events):
        result = cmd.execute(app)

        # Errors abort test
        assert result.error is None

        # Immediate state check (no animation delay)
        if result.needs_redraw:
            window.update_gui_elements()

    assert app.cube.solved
    window.close()
```

---

### Example 4: Headless Test (No GUI at All)

For unit tests that only care about logic:

```python
def test_algorithm_correctness_headless():
    """
    Pure logic test - no GUI, no window, no animation.
    Fastest option for algorithm correctness tests.
    """

    # No GUI created
    app = AbstractApp.create_non_default(cube_size=3, animation=False)

    # Sexy move 6 times = back to solved
    test_events = [
        KeyEvent(key.R, 0),              # R
        KeyEvent(key.U, 0),              # U
        KeyEvent(key.R, key.MOD_SHIFT),  # R' (prime)
        KeyEvent(key.U, key.MOD_SHIFT),  # U' (prime)
    ] * 6

    for cmd in keyboard_event_generator(test_events):
        result = cmd.execute(app)
        assert result.error is None

    assert app.cube.solved
```

---

## The Power of the Yield Point

### Why Generators?

**The yield is where control returns to the caller:**

```python
def keyboard_event_generator(events):
    for event in events:
        cmd = create_command(event)

        yield cmd  # ← ← ← MAGIC HAPPENS HERE

        # Control has left this function
        # Caller can do WHATEVER they want:
        #   - Execute with try/except (interactive)
        #   - Execute without try/except (test - abort on error)
        #   - Check state
        #   - Wait for animation
        #   - Update GUI
        # Then caller continues iteration to get next command
```

### Without Generators (Traditional Callback)

```python
# ❌ OLD WAY - can't control error handling
def process_keys(keys, on_command):
    for key in keys:
        cmd = create_command(key)
        on_command(cmd)  # ← Caller provides callback
        # But caller can't choose error handling here!
```

### With Generators (New Way)

```python
# ✅ NEW WAY - caller controls everything
for cmd in keyboard_event_generator(keys):
    # ← Caller decides error handling
    # ← Caller decides when to check state
    # ← Caller controls the flow
    result = cmd.execute(app)
```

---

## Comparison: Interactive vs. Test

### Interactive Mode (Real GUI)

```python
# gui_adapter.py
for cmd in keyboard_event_generator([event], animation_running):
    try:
        result = cmd.execute(app)  # GUI + animation active
        if result.needs_redraw:
            window.update_gui_elements()
    except Exception as e:
        log_error(e)  # ← Log and continue
        # GUI keeps running
```

**Features**:
- ✅ Keys from user's keyboard
- ✅ GUI visible and interactive
- ✅ Animation plays
- ✅ Errors logged, app continues
- ✅ Main loop never stops

---

### Test Mode (Scripted GUI)

```python
# test_input_commands.py
for cmd in keyboard_event_generator(test_events):
    result = cmd.execute(app)  # GUI + animation active

    # NO try/except - errors abort
    assert result.error is None

    # Check state between commands
    assert app.cube.valid
```

**Features**:
- ✅ Keys from test script
- ✅ GUI visible (optional - can be invisible)
- ✅ Animation plays (optional - can disable for speed)
- ✅ Errors abort test immediately (fail fast)
- ✅ Can assert state after every command

---

## Key Benefits

### 1. Same GUI Code Path

Tests use the **exact same GUI code** as interactive mode:
- Same Window class
- Same animation manager
- Same operators
- Same solvers

**No mocking, no fakes** - tests run the real thing!

### 2. Different Error Handling

Generator allows caller to decide:

| Mode | Error Handling |
|------|----------------|
| Interactive | `try: execute() except: log()` - continue |
| Test | `execute()` - abort on exception |

### 3. State Inspection

Can check app state after **every single command**:

```python
for cmd in generator(events):
    result = cmd.execute(app)

    # ← Check state HERE, between every command
    print(f"Solved: {app.cube.solved}")
    print(f"Moves: {app.op.count}")
    assert app.cube.valid
```

### 4. Flexible Testing

Choose your test speed/fidelity:

| Test Type | GUI | Animation | Speed | Use Case |
|-----------|-----|-----------|-------|----------|
| Full GUI | ✅ | ✅ | Slow | Visual regression |
| GUI no anim | ✅ | ❌ | Medium | Integration tests |
| Headless | ❌ | ❌ | Fast | Unit tests |

---

## Real-World Test Example

```python
def test_full_workflow_with_gui():
    """
    Complete workflow test with GUI and animation.

    Tests the entire user experience:
    1. Start with solved cube
    2. Scramble with animation
    3. Solve layer by layer with animation
    4. Verify cube is solved
    """

    # Create GUI with animation
    app = AbstractApp.create_non_default(3, animation=True)
    window = Window(app, visible=False)  # Invisible for automated test

    # User workflow simulation
    workflow = [
        (KeyEvent(key._1, 0), "Scramble"),
        (KeyEvent(key.F1, 0), "Solve L1"),
        (KeyEvent(key.F2, 0), "Solve L2"),
        (KeyEvent(key.F3, 0), "Solve L3"),
    ]

    print("\n=== Running Workflow Test ===")

    for event, description in workflow:
        print(f"\n{description}...")

        for cmd in keyboard_event_generator([event]):
            # Execute with full animation
            result = cmd.execute(app)

            # Test: abort on error
            assert result.error is None, f"{description} failed: {result.error}"

            # Wait for animation
            if window.animation_running:
                timeout = 10.0  # seconds
                start = time.time()
                while window.animation_running:
                    if time.time() - start > timeout:
                        raise TimeoutError(f"{description} animation timeout")
                    pyglet.clock.tick()
                    window.dispatch_events()
                    window.on_draw()

            # Log state
            print(f"  ✓ {description} complete")
            print(f"    Solved: {app.cube.solved}")
            print(f"    Moves: {app.op.count}")

    # Final verification
    assert app.cube.solved, "Cube should be solved!"
    print("\n=== Test Passed! ===")

    window.close()
```

**Output**:
```
=== Running Workflow Test ===

Scramble...
  ✓ Scramble complete
    Solved: False
    Moves: 15

Solve L1...
  ✓ Solve L1 complete
    Solved: False
    Moves: 28

Solve L2...
  ✓ Solve L2 complete
    Solved: False
    Moves: 43

Solve L3...
  ✓ Solve L3 complete
    Solved: True
    Moves: 67

=== Test Passed! ===
```

---

## Summary

### The Problem

**Cannot test GUI with scripted input while maintaining different error handling**

### The Solution

**Generator yields commands, caller controls execution and error handling**

### The Result

```python
# Interactive: Real keyboard, log errors, continue
for cmd in keyboard_event_generator([real_event]):
    try:
        cmd.execute(app)
    except:
        log()

# Test: Scripted keys, abort on errors, assert state
for cmd in keyboard_event_generator(test_events):
    cmd.execute(app)  # With GUI! With animation!
    assert state
```

**Both modes use the same generator, same commands, same GUI - just different error handling!** 🎉
