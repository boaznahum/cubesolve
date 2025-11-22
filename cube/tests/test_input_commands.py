"""
Tests for the command-based input system.

This demonstrates how the generator + command pattern enables GUI testing
without requiring an actual GUI window.
"""

# Import key constants - using try/except for headless environments
try:
    from pyglet.window import key  # type: ignore
except (ImportError, OSError):
    # Headless environment - define key constants manually
    class key:
        """Mock key constants for headless testing"""
        # Letters
        R = 114
        L = 108
        U = 117
        D = 100
        F = 102
        B = 98
        M = 109
        E = 101
        S = 115
        X = 120
        Y = 121
        Z = 122
        C = 99
        P = 112
        Q = 113

        # Numbers
        _0 = 48
        _1 = 49
        _2 = 50
        _3 = 51
        _4 = 52
        _5 = 53
        _6 = 54
        _7 = 55
        _8 = 56
        _9 = 57

        # Special keys
        SLASH = 47
        QUESTION = 63
        COMMA = 44
        EQUAL = 61
        PLUS = 43
        MINUS = 45
        SPACE = 32

        # Function keys
        F1 = 65470
        F2 = 65471
        F3 = 65472
        F4 = 65473
        F5 = 65474

        # Arrow keys
        UP = 65362
        DOWN = 65364
        LEFT = 65361
        RIGHT = 65363

        # Numpad
        NUM_ADD = 65451
        NUM_SUBTRACT = 65453

        # Modifiers
        MOD_SHIFT = 1
        MOD_CTRL = 2
        MOD_ALT = 4

        # Modifier keys
        LSHIFT = 65505
        RSHIFT = 65506
        LCTRL = 65507
        RCTRL = 65508
        LALT = 65513
        RALT = 65514
        LOPTION = 65488
        ROPTION = 65489

    # Inject key constants into keyboard_generator module for headless testing
    import cube.input.keyboard_generator
    cube.input.keyboard_generator.key = key

from cube.app.abstract_ap import AbstractApp
from cube.input.keyboard_generator import keyboard_event_generator, KeyEvent
from cube.input.command_impl import (
    RotateFaceCommand, ScrambleCommand, SolveCommand,
    ChangeCubeSizeCommand, QuitCommand
)
from cube.algs import Algs
from cube.app.app_exceptions import AppExit


def test_single_command_execution():
    """Test executing a single command"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Create and execute a command directly
    cmd = RotateFaceCommand(Algs.R, inverted=False)
    result = cmd.execute(app)

    assert result.error is None
    assert result.needs_redraw
    assert not app.cube.solved  # Cube changed from solved state


def test_keyboard_generator_basic():
    """Test generator yields commands from keyboard events"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Simulate key presses: R, U, R', U'
    events = [
        KeyEvent(key.R, 0),                    # R
        KeyEvent(key.U, 0),                    # U
        KeyEvent(key.R, key.MOD_SHIFT),        # R'
        KeyEvent(key.U, key.MOD_SHIFT),        # U'
    ]

    # Process events through generator
    for cmd in keyboard_event_generator(events):
        result = cmd.execute(app)
        assert result.error is None

    # After R U R' U' from solved state, cube should be solved
    assert app.cube.solved


def test_scramble_and_check_state():
    """Test that scramble changes cube state"""
    app = AbstractApp.create_non_default(3, animation=False)
    original_state = app.cube.get_state()

    # Generate scramble command from keyboard
    events = [KeyEvent(key._1, 0)]  # Press '1' to scramble

    for cmd in keyboard_event_generator(events):
        assert isinstance(cmd, ScrambleCommand)
        result = cmd.execute(app)
        assert result.error is None

    # Cube should be changed
    assert app.cube.get_state() != original_state
    assert not app.cube.solved


def test_scramble_and_solve_workflow():
    """Test full workflow: scramble then solve"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Simulate: press '1' (scramble), then '/' (solve)
    events = [
        KeyEvent(key._1, 0),           # Scramble
        KeyEvent(key.SLASH, 0),        # Solve
    ]

    commands_executed = []
    for cmd in keyboard_event_generator(events):
        commands_executed.append(cmd)
        result = cmd.execute(app)
        assert result.error is None

    # Should have executed 2 commands
    assert len(commands_executed) == 2
    assert isinstance(commands_executed[0], ScrambleCommand)
    assert isinstance(commands_executed[1], SolveCommand)

    # Cube should be solved
    assert app.cube.solved


def test_size_change():
    """Test changing cube size"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Press '+' to increase size
    events = [KeyEvent(key.EQUAL, 0)]

    for cmd in keyboard_event_generator(events):
        assert isinstance(cmd, ChangeCubeSizeCommand)
        result = cmd.execute(app)
        assert result.error is None
        assert result.needs_viewer_reset

    assert app.vs.cube_size == 4
    assert app.cube.size == 4


def test_minimum_size_constraint():
    """Test that cube size cannot go below 3"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Try to decrease size below 3
    cmd = ChangeCubeSizeCommand(delta=-1)
    result = cmd.execute(app)

    # Should get error
    assert result.error is not None
    assert "Minimum" in result.error
    assert app.vs.cube_size == 3


def test_quit_command_raises_exception():
    """Test that quit command raises AppExit"""
    app = AbstractApp.create_non_default(3, animation=False)

    events = [KeyEvent(key.Q, 0)]

    try:
        for cmd in keyboard_event_generator(events):
            assert isinstance(cmd, QuitCommand)
            cmd.execute(app)
            assert False, "Should have raised AppExit"
    except AppExit:
        pass  # Expected


def test_command_during_animation_blocked():
    """Test that most commands are blocked during animation"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Try to execute R during animation
    events = [KeyEvent(key.R, 0)]

    # Set animation_running = True
    commands = list(keyboard_event_generator(events, animation_running=True))

    # Should get no commands (R is blocked during animation)
    assert len(commands) == 0


def test_view_command_during_animation_allowed():
    """Test that view commands work during animation"""
    app = AbstractApp.create_non_default(3, animation=False)

    # View rotation (Ctrl+X) should work during animation
    events = [KeyEvent(key.X, key.MOD_CTRL)]

    commands = list(keyboard_event_generator(events, animation_running=True))

    # Should get the view command
    assert len(commands) == 1


def test_state_inspection_between_commands():
    """
    Test that we can inspect state between each command.
    This is the KEY BENEFIT of the generator approach!
    """
    app = AbstractApp.create_non_default(3, animation=False)

    # Sequence: R, U, R', U'
    events = [
        KeyEvent(key.R, 0),
        KeyEvent(key.U, 0),
        KeyEvent(key.R, key.MOD_SHIFT),
        KeyEvent(key.U, key.MOD_SHIFT),
    ]

    states_after_each_move = []

    for cmd in keyboard_event_generator(events):
        result = cmd.execute(app)
        assert result.error is None

        # Capture state after each move
        states_after_each_move.append(app.cube.get_state())

    # Should have 4 different states
    assert len(states_after_each_move) == 4

    # First 3 states should be different from solved
    assert states_after_each_move[0] != states_after_each_move[-1]
    assert states_after_each_move[1] != states_after_each_move[-1]
    assert states_after_each_move[2] != states_after_each_move[-1]

    # Last state should be solved (R U R' U' returns to start)
    assert app.cube.solved


def test_partial_solve():
    """Test solving only first layer"""
    app = AbstractApp.create_non_default(3, animation=False)

    # Scramble then solve L1 only (F1)
    events = [
        KeyEvent(key._1, 0),           # Scramble
        KeyEvent(key.F1, 0),           # Solve L1
    ]

    for cmd in keyboard_event_generator(events):
        result = cmd.execute(app)
        assert result.error is None

    # First layer should be solved, but not whole cube
    # (We don't have a helper to check L1 only, but cube shouldn't be fully solved)
    # This would need more sophisticated state checking


def test_force_instant_solve():
    """Test that Shift+/ forces instant solve (no animation)"""
    app = AbstractApp.create_non_default(3, animation=True)  # Animation ON

    # Scramble
    ScrambleCommand(seed=1, animation=False).execute(app)

    # Shift+/ should solve instantly even with animation on
    events = [KeyEvent(key.SLASH, key.MOD_SHIFT)]

    for cmd in keyboard_event_generator(events):
        assert isinstance(cmd, SolveCommand)
        assert cmd.animation is False  # Should be instant

        result = cmd.execute(app)
        assert result.error is None

    assert app.cube.solved


def test_modifier_keys_ignored():
    """Test that modifier keys alone don't generate commands"""
    events = [
        KeyEvent(key.LSHIFT, 0),
        KeyEvent(key.LCTRL, 0),
        KeyEvent(key.LALT, 0),
    ]

    commands = list(keyboard_event_generator(events))
    assert len(commands) == 0


# Run tests if executed directly
if __name__ == '__main__':
    print("Running input command tests...")

    tests = [
        test_single_command_execution,
        test_keyboard_generator_basic,
        test_scramble_and_check_state,
        test_scramble_and_solve_workflow,
        test_size_change,
        test_minimum_size_constraint,
        test_quit_command_raises_exception,
        test_command_during_animation_blocked,
        test_view_command_during_animation_allowed,
        test_state_inspection_between_commands,
        test_partial_solve,
        test_force_instant_solve,
        test_modifier_keys_ignored,
    ]

    for test_func in tests:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: {type(e).__name__}: {e}")

    print("\nDone!")
