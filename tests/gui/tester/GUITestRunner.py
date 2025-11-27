"""
GUITestRunner - Utility class for running automated GUI tests.

This module provides a clean, reusable interface for running automated GUI tests
with keyboard input injection, timeout handling, and error detection.

Usage
-----
Run a simple test:
    from tests.gui.GUITestRunner import GUITestRunner
    result = GUITestRunner.run_test("1/q", timeout_sec=60.0)

With custom configuration:
    result = GUITestRunner.run_test(
        key_sequence="1/q",
        cube_size=3,
        enable_animation=True,
        timeout_sec=120.0,
        debug=True
    )
"""

import threading
import time
import traceback

import pyglet  # type: ignore[import-untyped]

from cube import config
from cube.app.abstract_ap import AbstractApp
from cube.main_window.Window import Window
from cube.gui.backends import BackendRegistry
# Import pyglet backend to register it
import cube.gui.backends.pyglet  # noqa: F401
from tests.gui.tester.GUITestResult import GUITestResult
from tests.gui.tester.GUITestTimeout import GUITestTimeout


class GUITestRunner:
    """
    Utility class for running automated GUI tests.

    This class provides a clean static interface for running GUI tests with
    keyboard input injection, timeout handling, and error detection. Designed
    for reusability across different test suites.

    Examples
    --------
    Basic test with scramble and solve:

    >>> result = GUITestRunner.run_test("1/q", timeout_sec=60.0)
    >>> if result.success:
    ...     print("Test passed!")

    Test with animation enabled:

    >>> result = GUITestRunner.run_test(
    ...     key_sequence="1/q",
    ...     cube_size=3,
    ...     enable_animation=True,
    ...     timeout_sec=120.0,
    ...     debug=True
    ... )

    Test multiple operations:

    >>> result = GUITestRunner.run_test("123/q", cube_size=4, timeout_sec=90.0)
    """

    @staticmethod
    def run_test(
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

        >>> result = GUITestRunner.run_test("1/q", timeout_sec=60.0)
        >>> if result.success:
        ...     print("Test passed!")
        >>> else:
        ...     print(f"Test failed: {result.error}")

        Test multiple scrambles:

        >>> result = GUITestRunner.run_test("123/q", cube_size=4)

        Test with animation enabled:

        >>> result = GUITestRunner.run_test("1/q", enable_animation=True, timeout_sec=120.0)
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

            # Create app, renderer, and window
            app = AbstractApp.create()
            renderer = BackendRegistry.create_renderer(backend="pyglet")
            win = Window(app, 720, 720, "Cube Test", renderer=renderer)

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
