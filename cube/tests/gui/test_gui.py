"""
GUI Testing Harness for Rubik's Cube Solver

This module provides test functions for automated GUI testing by injecting keyboard sequences
and detecting exceptions or errors during execution.

Usage
-----
Run a simple test:
    python -m cube.tests.gui.test_gui

Run with custom sequence:
    from cube.tests.gui.gui_test_runner import GUITestRunner
    result = GUITestRunner.run_test("123/q", timeout_sec=60.0)

Note: Due to pyglet event loop limitations, each test should run in a fresh process.
The test runner handles this automatically.
"""

import sys

from cube.tests.gui.GUITestRunner import GUITestRunner
from cube.tests.gui.GUITestResult import GUITestResult


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
    return GUITestRunner.run_test(
        key_sequence="1/q",
        cube_size=cube_size,
        timeout_sec=timeout,
        enable_animation=enable_animation,
        debug=True
    )


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
    return GUITestRunner.run_test(
        key_sequence="123/q",
        cube_size=cube_size,
        timeout_sec=timeout,
        enable_animation=enable_animation,
        debug=True
    )


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
    return GUITestRunner.run_test(
        key_sequence="rrrludfbq",
        cube_size=3,
        timeout_sec=timeout,
        enable_animation=enable_animation,
        debug=True
    )


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
