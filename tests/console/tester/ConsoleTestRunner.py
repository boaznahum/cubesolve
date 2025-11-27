"""
ConsoleTestRunner - Utility class for running automated console tests.

This module provides a clean, reusable interface for running automated console
tests with keyboard input injection via command-line arguments.

Usage
-----
Run a simple test:
    from tests.console.tester import ConsoleTestRunner
    result = ConsoleTestRunner.run_test("frq", timeout_sec=30.0)

With debug output:
    result = ConsoleTestRunner.run_test(
        key_sequence="frq",
        timeout_sec=30.0,
        debug=True
    )
"""

import subprocess
import sys
from .ConsoleTestResult import ConsoleTestResult


class ConsoleTestRunner:
    """
    Utility class for running automated console tests.

    This class provides a clean static interface for running console tests with
    keyboard input injection via command-line arguments to main_c.py.
    """

    @staticmethod
    def run_test(
        key_sequence: str,
        timeout_sec: float = 30.0,
        debug: bool = False
    ) -> ConsoleTestResult:
        """
        Run a console test with a keyboard sequence.

        Parameters
        ----------
        key_sequence : str
            String of characters representing key presses.
            Must end with 'q' to quit the application.
            Examples:
                "frq"   - F rotation, R rotation, quit
                "1?q"   - Scramble with seed 1, solve, quit
                "rrrq"  - Three R rotations, quit
        timeout_sec : float, optional
            Maximum time to wait for test completion. Default is 30 seconds.
        debug : bool, optional
            Enable debug output. Default is False.

        Returns
        -------
        ConsoleTestResult
            Result object with success status, error (if any), stdout, stderr.
        """
        if debug:
            print(f"Starting console test with sequence: '{key_sequence}'")
            print(f"  Timeout: {timeout_sec}s")

        try:
            # Run main_c.py as a subprocess with the key sequence as argument
            result = subprocess.run(
                [sys.executable, "-m", "cube.main_console.main_c", key_sequence],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )

            if debug:
                print(f"Return code: {result.returncode}")
                print(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"STDERR:\n{result.stderr}")

            # Check for success - return code 0 means success
            if result.returncode == 0:
                return ConsoleTestResult(
                    success=True,
                    message=f"Test completed successfully with sequence '{key_sequence}'",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode
                )
            else:
                return ConsoleTestResult(
                    success=False,
                    message=f"Test failed with return code {result.returncode}",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode
                )

        except subprocess.TimeoutExpired as e:
            return ConsoleTestResult(
                success=False,
                error=e,
                message=f"Test timed out after {timeout_sec} seconds",
                stdout=e.stdout or "" if hasattr(e, 'stdout') else "",
                stderr=e.stderr or "" if hasattr(e, 'stderr') else "",
                return_code=-1
            )

        except Exception as e:
            if debug:
                print(f"Exception occurred: {e}")

            return ConsoleTestResult(
                success=False,
                error=e,
                message=f"Test failed with exception: {type(e).__name__}: {e}"
            )
