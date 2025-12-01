"""
GUI Testing Harness for Rubik's Cube Solver (pytest version)

This module provides pytest test functions for automated GUI testing by injecting
command sequences and detecting exceptions or errors during execution.

Usage
-----
Run all GUI tests with pytest:
    pytest tests/gui/test_gui.py -v

Run with all backends (default):
    pytest tests/gui/test_gui.py -v --backend=all

Run with specific backend:
    pytest tests/gui/test_gui.py -v --backend=pyglet
    pytest tests/gui/test_gui.py -v --backend=headless

Run with animations enabled (slower but visible):
    pytest tests/gui/test_gui.py -v --animate

Control animation speed (default: 3 speed-ups):
    pytest tests/gui/test_gui.py -v --animate --speed-up 5

Run a specific test:
    pytest tests/gui/test_gui.py::test_scramble_and_solve -v

Note: Due to pyglet event loop limitations, tests are marked with 'gui' marker
and should be run one at a time or with pytest-forked for isolation.
"""

import pytest

from cube.presentation.gui.Command import Command
from tests.gui.tester.GUITestRunner import GUITestRunner


# Mark all tests in this module as GUI tests
pytestmark = pytest.mark.gui


@pytest.mark.parametrize("cube_size", [3])
def test_scramble_and_solve(cube_size: int, enable_animation: bool, speed_up_count: int, backend: str):
    """
    Test scrambling and solving a cube.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    enable_animation : bool
        Fixture from conftest.py, controlled by --animate flag.
    speed_up_count : int
        Fixture from conftest.py, controlled by --speed-up flag.
    backend : str
        Backend to use, parametrized from conftest.py.
    """
    result = GUITestRunner.run_test(
        commands=Command.SPEED_UP * speed_up_count + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        cube_size=cube_size,
        timeout_sec=60.0,
        enable_animation=enable_animation,
        backend=backend,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


@pytest.mark.skip(reason="B1: Lazy cache initialization bug - fails intermittently with animation")
@pytest.mark.parametrize("cube_size", [3])
def test_multiple_scrambles(cube_size: int, enable_animation: bool, speed_up_count: int, backend: str):
    """
    Test multiple scrambles followed by solve.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    enable_animation : bool
        Fixture from conftest.py, controlled by --animate flag.
    speed_up_count : int
        Fixture from conftest.py, controlled by --speed-up flag.
    backend : str
        Backend to use, parametrized from conftest.py.
    """
    result = GUITestRunner.run_test(
        commands=(Command.SPEED_UP * speed_up_count +
                  Command.SCRAMBLE_1 + Command.SCRAMBLE_2 + Command.SCRAMBLE_3 +
                  Command.SOLVE_ALL + Command.QUIT),
        cube_size=cube_size,
        timeout_sec=90.0,
        enable_animation=enable_animation,
        backend=backend,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


@pytest.mark.parametrize("cube_size", [3])
def test_face_rotations(cube_size: int, enable_animation: bool, speed_up_count: int, backend: str):
    """Test basic face rotations.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    enable_animation : bool
        Fixture from conftest.py, controlled by --animate flag.
    speed_up_count : int
        Fixture from conftest.py, controlled by --speed-up flag.
    backend : str
        Backend to use, parametrized from conftest.py.
    """
    result = GUITestRunner.run_test(
        commands=(Command.SPEED_UP * speed_up_count +
                  Command.ROTATE_R * 3 + Command.ROTATE_L + Command.ROTATE_U +
                  Command.ROTATE_D + Command.ROTATE_F + Command.ROTATE_B +
                  Command.QUIT),
        cube_size=cube_size,
        timeout_sec=30.0,
        enable_animation=enable_animation,
        backend=backend,
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
        commands=Command.SPEED_UP * 3 + Command.SCRAMBLE_1 + Command.SOLVE_ALL + Command.QUIT,
        cube_size=3,
        timeout_sec=60.0,
        enable_animation=False,
        backend="pyglet",
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
