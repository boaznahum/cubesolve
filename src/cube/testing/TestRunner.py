"""
Backend-agnostic test runner for the Cube Solver.

This module provides a unified test runner that works with all backends
(pyglet, tkinter, console, headless).
"""

import threading
import time
import traceback
from dataclasses import dataclass
from typing import Any

from cube import config
from cube.app.AbstractApp import AbstractApp
from cube.main_any_backend import create_app_window


@dataclass
class TestResult:
    """Result from running a test.

    Attributes:
        success: Whether the test passed.
        error: Exception that occurred, if any.
        message: Human-readable result message.
        elapsed_time: Time taken in seconds.
        backend: Backend that was used.
    """
    success: bool
    message: str
    error: Exception | None = None
    elapsed_time: float = 0.0
    backend: str = ""

    def __str__(self) -> str:
        status = "PASS" if self.success else "FAIL"
        s = f"[{status}] {self.message}"
        if self.elapsed_time > 0:
            s += f" ({self.elapsed_time:.2f}s)"
        if self.error:
            s += f"\n  Error: {self.error}"
        return s


class TestTimeout(Exception):
    """Exception raised when a test times out."""
    pass


class TestRunner:
    """Backend-agnostic test runner.

    This class provides a unified interface for running GUI tests across
    all backends. It uses the create_app_window() factory to create
    windows with any registered backend.

    Examples
    --------
    Run a test with the default (pyglet) backend:

        >>> result = TestRunner.run_test("1?q", timeout_sec=60.0)
        >>> print(result)

    Run with a specific backend:

        >>> result = TestRunner.run_test(
        ...     key_sequence="1?q",
        ...     backend="headless",
        ...     timeout_sec=30.0
        ... )

    Run with animation:

        >>> result = TestRunner.run_test(
        ...     key_sequence="+++1?q",
        ...     backend="pyglet",
        ...     enable_animation=True,
        ...     timeout_sec=120.0
        ... )
    """

    @staticmethod
    def run_test(
        key_sequence: str,
        backend: str = "headless",
        timeout_sec: float = 30.0,
        cube_size: int = 3,
        enable_animation: bool = False,
        debug: bool = False,
    ) -> TestResult:
        """Run a test with a key sequence on any backend.

        Args:
            key_sequence: Key sequence to inject (e.g., "1?q").
            backend: Backend to use ("pyglet", "tkinter", "console", "headless").
            timeout_sec: Maximum time to wait for completion.
            cube_size: Size of the cube (default 3).
            enable_animation: Enable animations (slower but visible).
            debug: Enable debug output.

        Returns:
            TestResult with success status and details.

        Example:
            >>> result = TestRunner.run_test("1?q", backend="headless")
            >>> assert result.success
        """
        # Save original config
        original_test_mode = config.GUI_TEST_MODE
        original_animation = config.animation_enabled
        original_cube_size = config.CUBE_SIZE
        original_debug = getattr(config, 'KEYBOAD_INPUT_DEBUG', False)

        start_time = time.time()
        test_error: Exception | None = None
        test_success = False
        timeout_occurred = False
        window: Any = None

        def timeout_watchdog():
            """Watchdog thread to enforce timeout."""
            nonlocal timeout_occurred, window
            time.sleep(timeout_sec)
            if not test_success and test_error is None:
                timeout_occurred = True
                # Try to close the window
                if window:
                    try:
                        window.close()
                    except Exception:
                        pass

        try:
            # Configure for testing
            config.GUI_TEST_MODE = True
            config.animation_enabled = enable_animation
            config.CUBE_SIZE = cube_size
            if hasattr(config, 'KEYBOAD_INPUT_DEBUG'):
                config.KEYBOAD_INPUT_DEBUG = debug

            if debug:
                print(f"Starting test with sequence: '{key_sequence}'")
                print(f"  Backend: {backend}, Cube: {cube_size}x{cube_size}")
                print(f"  Animation: {enable_animation}, Timeout: {timeout_sec}s")

            # Create app
            app = AbstractApp.create_non_default(
                cube_size=cube_size,
                animation=enable_animation
            )

            # Create window with specified backend
            window = create_app_window(
                app,
                backend_name=backend,
                width=720,
                height=720,
                title="Cube Test"
            )

            # Start timeout watchdog
            watchdog = threading.Thread(target=timeout_watchdog, daemon=True)
            watchdog.start()

            # Inject key sequence
            if debug:
                print(f"Injecting key sequence: '{key_sequence}'")

            window.inject_key_sequence(key_sequence)

            # Run the window (for backends that need it)
            if backend in ("pyglet", "tkinter"):
                window.run()

            # Check for timeout
            if timeout_occurred:
                raise TestTimeout(f"Test exceeded timeout of {timeout_sec} seconds")

            test_success = True
            elapsed = time.time() - start_time

            if debug:
                print(f"Test completed in {elapsed:.2f}s")

            return TestResult(
                success=True,
                message=f"Test completed with sequence '{key_sequence}'",
                elapsed_time=elapsed,
                backend=backend
            )

        except TestTimeout as e:
            test_error = e
            elapsed = time.time() - start_time
            return TestResult(
                success=False,
                error=e,
                message=f"Test timed out after {timeout_sec}s",
                elapsed_time=elapsed,
                backend=backend
            )

        except Exception as e:
            test_error = e
            elapsed = time.time() - start_time

            if debug:
                print(f"Exception occurred: {e}")
                traceback.print_exc()

            return TestResult(
                success=False,
                error=e,
                message=f"Test failed: {type(e).__name__}",
                elapsed_time=elapsed,
                backend=backend
            )

        finally:
            # Cleanup
            if window:
                try:
                    if window.viewer:
                        window.viewer.cleanup()
                except Exception:
                    pass

            # Restore config
            config.GUI_TEST_MODE = original_test_mode
            config.animation_enabled = original_animation
            config.CUBE_SIZE = original_cube_size
            if hasattr(config, 'KEYBOAD_INPUT_DEBUG'):
                config.KEYBOAD_INPUT_DEBUG = original_debug

            if debug:
                print("Test cleanup complete, config restored")

    @classmethod
    def run_headless_test(
        cls,
        key_sequence: str,
        cube_size: int = 3,
        debug: bool = False,
    ) -> TestResult:
        """Run a quick headless test.

        This is a convenience method for running tests without GUI output.
        Ideal for CI/CD pipelines and automated testing.

        Args:
            key_sequence: Key sequence to inject.
            cube_size: Cube size (default 3).
            debug: Enable debug output.

        Returns:
            TestResult with success status.

        Example:
            >>> result = TestRunner.run_headless_test("1?q")
            >>> assert result.success
        """
        return cls.run_test(
            key_sequence=key_sequence,
            backend="headless",
            timeout_sec=30.0,
            cube_size=cube_size,
            enable_animation=False,
            debug=debug,
        )

    @classmethod
    def run_all_backends(
        cls,
        key_sequence: str,
        backends: list[str] | None = None,
        timeout_sec: float = 30.0,
        cube_size: int = 3,
        debug: bool = False,
    ) -> dict[str, TestResult]:
        """Run the same test on multiple backends.

        Args:
            key_sequence: Key sequence to inject.
            backends: List of backends to test (default: all).
            timeout_sec: Timeout per backend.
            cube_size: Cube size.
            debug: Enable debug output.

        Returns:
            Dictionary mapping backend name to TestResult.

        Example:
            >>> results = TestRunner.run_all_backends("1?q")
            >>> for backend, result in results.items():
            ...     print(f"{backend}: {result.success}")
        """
        if backends is None:
            backends = ["headless", "console"]  # Safe defaults

        results = {}
        for backend in backends:
            if debug:
                print(f"\n=== Testing backend: {backend} ===")

            try:
                results[backend] = cls.run_test(
                    key_sequence=key_sequence,
                    backend=backend,
                    timeout_sec=timeout_sec,
                    cube_size=cube_size,
                    enable_animation=False,
                    debug=debug,
                )
            except ImportError as e:
                results[backend] = TestResult(
                    success=False,
                    error=e,
                    message=f"Backend '{backend}' not available",
                    backend=backend
                )

        return results
