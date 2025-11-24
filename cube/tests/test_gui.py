"""
GUI Testing Harness for Rubik's Cube Solver

This module provides utilities for automated GUI testing by injecting keyboard sequences
and detecting exceptions or errors during execution.

Usage
-----
Run a simple test:
    python -m cube.tests.test_gui

Run with custom sequence:
    from cube.tests.test_gui import run_gui_test
    success, error = run_gui_test("123/q", timeout_sec=60.0)

Note: Due to pyglet event loop limitations, each test should run in a fresh process.
The test runner handles this automatically.
"""

import subprocess
import sys
import threading
import time
import traceback
from typing import Tuple

import pyglet

from cube import config
from cube.app.abstract_ap import AbstractApp
from cube.main_window.Window import Window


class GUITestResult:
    """Result of a GUI test run."""

    def __init__(self, success: bool, error: Exception | None = None, message: str = ""):
        self.success = success
        self.error = error
        self.message = message

    def __str__(self):
        # Use ASCII characters for Windows console compatibility
        if self.success:
            return f"[PASS] Test passed: {self.message}"
        else:
            return f"[FAIL] Test failed: {self.message}\n  Error: {self.error}"


class GUITestTimeout(Exception):
    """Raised when a GUI test exceeds its timeout."""
    pass


def run_gui_test(
    key_sequence: str,
    timeout_sec: float = 30.0,
    cube_size: int = 3,
    enable_animation: bool = False,
    debug: bool = False
) -> GUITestResult:
    """
    Run a GUI test with a keyboard sequence.

    Parameters
    ----------
    key_sequence : str
        String of characters representing key presses.
        Examples:
            "1/q"   - Scramble with key 1, solve, quit
            "123/q" - Three different scrambles, solve, quit
            "rrrq"  - Three R rotations, quit
            "1aq"   - Scramble, toggle animation, quit
    timeout_sec : float, optional
        Maximum time to wait for test completion. Default is 30 seconds.
    cube_size : int, optional
        Size of cube to test (3, 4, 5, etc.). Default is 3.
    enable_animation : bool, optional
        Enable animations during test. Default is False (faster).
    debug : bool, optional
        Enable debug output. Default is False.

    Returns
    -------
    GUITestResult
        Result object with success status, error (if any), and message.

    Examples
    --------
    Test scramble and solve:

    >>> result = run_gui_test("1/q", timeout_sec=60.0)
    >>> if result.success:
    ...     print("Test passed!")
    >>> else:
    ...     print(f"Test failed: {result.error}")

    Test multiple scrambles:

    >>> result = run_gui_test("123/q", cube_size=4)

    Test with animation enabled:

    >>> result = run_gui_test("1/q", enable_animation=True, timeout_sec=120.0)
    """
    # Save original config values
    original_test_mode = config.GUI_TEST_MODE
    original_animation = config.animation_enabled
    original_cube_size = config.CUBE_SIZE
    original_debug = config.KEYBOAD_INPUT_DEBUG

    test_error: Exception | None = None
    test_success = False
    timeout_occurred = False

    def timeout_watchdog():
        """Watchdog thread that enforces timeout."""
        nonlocal timeout_occurred
        time.sleep(timeout_sec)
        if not test_success and test_error is None:
            timeout_occurred = True
            # Force quit the event loop
            pyglet.app.exit()

    try:
        # Configure for testing
        config.GUI_TEST_MODE = True
        config.animation_enabled = enable_animation
        config.CUBE_SIZE = cube_size
        config.KEYBOAD_INPUT_DEBUG = debug

        if debug:
            print(f"Starting GUI test with sequence: '{key_sequence}'")
            print(f"  Cube size: {cube_size}, Animation: {enable_animation}, Timeout: {timeout_sec}s")

        # Create app and window
        app = AbstractApp.create()
        win = Window(app, 720, 720, "Cube Test")

        # Start timeout watchdog
        watchdog = threading.Thread(target=timeout_watchdog, daemon=True)
        watchdog.start()

        # Schedule key injection after window is ready
        def inject_keys(dt):
            try:
                if debug:
                    print(f"Injecting key sequence: '{key_sequence}'")
                win.inject_key_sequence(key_sequence, process_events=True)
            except Exception as e:
                # This exception will propagate to on_key_press which will handle it
                raise

        pyglet.clock.schedule_once(inject_keys, 0.1)  # Small delay to let window initialize

        # Run the event loop
        if debug:
            print("Starting pyglet event loop...")

        pyglet.app.run()

        # If we get here, the test completed (likely quit via 'q' key)
        if timeout_occurred:
            raise GUITestTimeout(f"Test exceeded timeout of {timeout_sec} seconds")

        test_success = True

        if debug:
            print("Event loop exited normally")

        return GUITestResult(
            success=True,
            message=f"Test completed successfully with sequence '{key_sequence}'"
        )

    except GUITestTimeout as e:
        test_error = e
        return GUITestResult(
            success=False,
            error=e,
            message=f"Test timed out after {timeout_sec} seconds"
        )

    except Exception as e:
        test_error = e
        if debug:
            print(f"Exception occurred: {e}")
            traceback.print_exc()

        return GUITestResult(
            success=False,
            error=e,
            message=f"Test failed with exception: {type(e).__name__}"
        )

    finally:
        # Clean up window and pyglet state
        try:
            # Close window if it exists and isn't already closed
            if 'win' in locals() and win and not win.has_exit:
                win.close()
        except:
            pass  # Window might already be closed

        # Clear all scheduled clock events
        try:
            pyglet.clock.unschedule(inject_keys)
        except:
            pass

        # Restore original config
        config.GUI_TEST_MODE = original_test_mode
        config.animation_enabled = original_animation
        config.CUBE_SIZE = original_cube_size
        config.KEYBOAD_INPUT_DEBUG = original_debug

        if debug:
            print("Test completed, config restored")


def test_scramble_and_solve(cube_size: int = 3, enable_animation: bool = True) -> GUITestResult:
    """
    Test scrambling and solving a cube.

    Parameters
    ----------
    cube_size : int, optional
        Size of cube to test. Default is 3.
    enable_animation : bool, optional
        Enable animations during test. Default is True.

    Returns
    -------
    GUITestResult
        Test result
    """
    timeout = 120.0 if enable_animation else 60.0
    return run_gui_test("1/q", cube_size=cube_size, timeout_sec=timeout, enable_animation=enable_animation, debug=True)


def test_multiple_scrambles(cube_size: int = 3, enable_animation: bool = True) -> GUITestResult:
    """
    Test multiple scrambles followed by solve.

    Parameters
    ----------
    cube_size : int, optional
        Size of cube to test. Default is 3.
    enable_animation : bool, optional
        Enable animations during test. Default is True.

    Returns
    -------
    GUITestResult
        Test result
    """
    timeout = 180.0 if enable_animation else 90.0
    return run_gui_test("123/q", cube_size=cube_size, timeout_sec=timeout, enable_animation=enable_animation, debug=True)


def test_face_rotations(enable_animation: bool = True) -> GUITestResult:
    """
    Test basic face rotations.

    Parameters
    ----------
    enable_animation : bool, optional
        Enable animations during test. Default is True.

    Returns
    -------
    GUITestResult
        Test result
    """
    timeout = 60.0 if enable_animation else 30.0
    return run_gui_test("rrrludfbq", cube_size=3, timeout_sec=timeout, enable_animation=enable_animation, debug=True)


def main():
    """Run basic GUI test."""
    print("=" * 70)
    print("Running GUI Tests for Rubik's Cube Solver")
    print("=" * 70)
    print()
    print("NOTE: Due to pyglet event loop limitations, only one test can run per process.")
    print("To run all tests, execute this module multiple times or run tests individually.")
    print()

    # Run one test (due to pyglet event loop limitations)
    test_name = "Scramble and Solve (3x3)"
    print(f"Running: {test_name}")
    print("-" * 70)

    result = test_scramble_and_solve(3)

    print(result)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    status = "[PASS]" if result.success else "[FAIL]"
    print(f"{status}: {test_name}")

    if result.success:
        print("\n[PASS] Test completed successfully!")
        print("\nTo run other tests, call them individually:")
        print("  - test_scramble_and_solve(cube_size)")
        print("  - test_multiple_scrambles(cube_size)")
        print("  - test_face_rotations()")
        return 0
    else:
        print("\n[FAIL] Test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
