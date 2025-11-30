"""
GUITestRunner - Utility class for running automated GUI tests.

This module provides a clean, reusable interface for running automated GUI tests
with command injection, timeout handling, and error detection.

Usage
-----
Run a simple test with commands:
    from tests.gui.tester.GUITestRunner import GUITestRunner
    from cube.gui.command import Command

    result = GUITestRunner.run_test(
        commands=Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        timeout_sec=60.0
    )

With custom configuration:
    result = GUITestRunner.run_test(
        commands=Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        cube_size=3,
        enable_animation=True,
        timeout_sec=120.0,
        debug=True
    )

With specific backend:
    result = GUITestRunner.run_test(
        commands=Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        backend="headless",  # or "pyglet", "console"
        timeout_sec=30.0
    )
"""

import threading
import time
import traceback

from cube import config
from cube.app.abstract_ap import AbstractApp
from cube.app.app_exceptions import AppExit
from cube.gui.factory import BackendRegistry
from cube.gui.command import Command, CommandSequence
from tests.gui.tester.GUITestResult import GUITestResult
from tests.gui.tester.GUITestTimeout import GUITestTimeout


class GUITestRunner:
    """
    Utility class for running automated GUI tests.

    This class provides a clean static interface for running GUI tests with
    command injection, timeout handling, and error detection. Designed
    for reusability across different test suites and backends.

    Examples
    --------
    Basic test with scramble and solve:

    >>> result = GUITestRunner.run_test(
    ...     Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
    ...     timeout_sec=60.0
    ... )
    >>> if result.success:
    ...     print("Test passed!")

    Test with specific backend:

    >>> result = GUITestRunner.run_test(
    ...     Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
    ...     backend="headless",
    ...     timeout_sec=30.0
    ... )
    """

    @staticmethod
    def run_test(
        commands: Command | CommandSequence,
        timeout_sec: float = 30.0,
        cube_size: int = 3,
        enable_animation: bool = False,
        backend: str = "pyglet",
        debug: bool = False
    ) -> GUITestResult:
        """
        Run a GUI test with a command sequence.

        Parameters
        ----------
        commands : Command | CommandSequence
            Commands to execute. Use + to combine commands:
            Examples:
                Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT
                Command.SPEED_UP * 5 + Command.SCRAMBLE_1 + Command.QUIT
        timeout_sec : float, optional
            Maximum time to wait for test completion. Default is 30 seconds.
        cube_size : int, optional
            Size of cube to test (3, 4, 5, etc.). Default is 3.
        enable_animation : bool, optional
            Enable animations during test. Default is False (faster).
            Note: Only pyglet backend supports animation.
        backend : str, optional
            Backend to use: "pyglet", "headless", or "console". Default is "pyglet".
        debug : bool, optional
            Enable debug output. Default is False.

        Returns
        -------
        GUITestResult
            Result object with success status, error (if any), and message.

        Examples
        --------
        Test scramble and solve:

        >>> result = GUITestRunner.run_test(
        ...     Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        ...     timeout_sec=60.0
        ... )
        >>> if result.success:
        ...     print("Test passed!")

        Test with headless backend (faster, no display):

        >>> result = GUITestRunner.run_test(
        ...     Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        ...     backend="headless",
        ...     timeout_sec=30.0
        ... )
        """
        # Normalize to CommandSequence for uniform handling
        if isinstance(commands, Command):
            cmd_seq = CommandSequence([commands])
        else:
            cmd_seq = commands

        # Save original config values
        original_test_mode = config.GUI_TEST_MODE
        original_animation = config.animation_enabled
        original_cube_size = config.CUBE_SIZE
        original_debug = config.KEYBOAD_INPUT_DEBUG

        test_error: Exception | None = None
        test_success = False
        timeout_occurred = False
        event_loop = None

        def timeout_watchdog():
            """Watchdog thread that enforces timeout."""
            nonlocal timeout_occurred
            time.sleep(timeout_sec)
            if not test_success and test_error is None:
                timeout_occurred = True
                # Force quit the event loop
                if event_loop is not None:
                    event_loop.stop()

        try:
            # Ensure backend is registered
            BackendRegistry.ensure_registered(backend)

            # Configure for testing
            config.GUI_TEST_MODE = True
            config.animation_enabled = enable_animation
            config.CUBE_SIZE = cube_size
            config.KEYBOAD_INPUT_DEBUG = debug

            if debug:
                print(f"Starting GUI test with commands: {cmd_seq}")
                print(f"  Backend: {backend}, Cube size: {cube_size}, Animation: {enable_animation}, Timeout: {timeout_sec}s")

            # Create app and backend
            app = AbstractApp.create()
            gui_backend = BackendRegistry.get_backend(backend)
            event_loop = gui_backend.event_loop

            # Create app window using backend factory
            win = gui_backend.create_app_window(app, 720, 720, "Cube Test")

            # Start timeout watchdog
            watchdog = threading.Thread(target=timeout_watchdog, daemon=True)
            watchdog.start()

            # Schedule command injection after window is ready
            def inject_commands(dt):
                try:
                    if debug:
                        print(f"Injecting commands: {cmd_seq}")
                    for cmd in cmd_seq:
                        win.inject_command(cmd)
                except Exception as e:
                    # This exception will propagate to inject_command which will handle it
                    raise

            event_loop.schedule_once(inject_commands, 0.1)  # Small delay to let window initialize

            # Run the event loop
            if debug:
                print(f"Starting {backend} event loop...")

            event_loop.run()

            # If we get here, the test completed (likely quit via 'q' key)
            if timeout_occurred:
                raise GUITestTimeout(f"Test exceeded timeout of {timeout_sec} seconds")

            test_success = True

            if debug:
                print("Event loop exited normally")

            return GUITestResult(
                success=True,
                message=f"Test completed successfully with {len(cmd_seq)} commands on {backend}"
            )

        except GUITestTimeout as e:
            test_error = e
            return GUITestResult(
                success=False,
                error=e,
                message=f"Test timed out after {timeout_sec} seconds"
            )

        except AppExit:
            # AppExit is expected when quit is pressed - this is success
            if debug:
                print("AppExit received (quit command) - test completed successfully")
            return GUITestResult(
                success=True,
                message=f"Test completed successfully with {len(cmd_seq)} commands on {backend}"
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
            # Clean up window and event loop state
            try:
                # Close window if it exists and isn't already closed
                if 'win' in locals() and win and hasattr(win, 'has_exit') and not win.has_exit:
                    win.close()
            except:
                pass  # Window might already be closed

            # Clear all scheduled clock events
            try:
                if event_loop is not None:
                    event_loop.unschedule(inject_commands)
            except:
                pass

            # Restore original config
            config.GUI_TEST_MODE = original_test_mode
            config.animation_enabled = original_animation
            config.CUBE_SIZE = original_cube_size
            config.KEYBOAD_INPUT_DEBUG = original_debug

            if debug:
                print("Test completed, config restored")
