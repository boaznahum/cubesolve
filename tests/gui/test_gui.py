"""
GUI Testing Harness for Rubik's Cube Solver (pytest version)

This module provides pytest test functions for automated GUI testing by injecting keyboard
sequences and detecting exceptions or errors during execution.

Usage
-----
Run all GUI tests with pytest:
    pytest tests/gui/test_gui.py -v

Run a specific test:
    pytest tests/gui/test_gui.py::test_scramble_and_solve -v

Note: Due to pyglet event loop limitations, tests are marked with 'gui' marker
and should be run one at a time or with pytest-forked for isolation.
"""

import pytest

from tests.gui.tester.GUITestRunner import GUITestRunner


# Mark all tests in this module as GUI tests
pytestmark = pytest.mark.gui


@pytest.mark.parametrize("cube_size", [3])
def test_scramble_and_solve(cube_size: int):
    """
    Test scrambling and solving a cube.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    """
    result = GUITestRunner.run_test(
        key_sequence="1/q",
        cube_size=cube_size,
        timeout_sec=60.0,
        enable_animation=False,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


@pytest.mark.parametrize("cube_size", [3])
def test_multiple_scrambles(cube_size: int):
    """
    Test multiple scrambles followed by solve.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    """
    result = GUITestRunner.run_test(
        key_sequence="123/q",
        cube_size=cube_size,
        timeout_sec=90.0,
        enable_animation=False,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


def test_face_rotations():
    """Test basic face rotations."""
    result = GUITestRunner.run_test(
        key_sequence="rrrludfbq",
        cube_size=3,
        timeout_sec=30.0,
        enable_animation=False,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


# Legacy main() for direct script execution
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Running GUI Tests for Rubik's Cube Solver")
    print("=" * 70)
    print()
    print("NOTE: For pytest, run: pytest tests/gui/test_gui.py -v")
    print()

    # Run one test (due to pyglet event loop limitations)
    test_name = "Scramble and Solve (3x3)"
    print(f"Running: {test_name}")
    print("-" * 70)

    result = GUITestRunner.run_test(
        key_sequence="1/q",
        cube_size=3,
        timeout_sec=60.0,
        enable_animation=False,
        debug=True
    )

    print(result)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    status = "[PASS]" if result.success else "[FAIL]"
    print(f"{status}: {test_name}")

    sys.exit(0 if result.success else 1)
