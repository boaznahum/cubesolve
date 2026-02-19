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

from cube.presentation.gui.commands import Commands
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
        commands=Commands.SPEED_UP * speed_up_count + Commands.SCRAMBLE_1 + Commands.SOLVE_ALL + Commands.QUIT,
        cube_size=cube_size,
        timeout_sec=60.0,
        enable_animation=enable_animation,
        backend=backend,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


#@pytest.mark.skip(reason="B1: Lazy cache initialization bug - fails intermittently with animation")
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
        commands=(Commands.SPEED_UP * speed_up_count +
                  Commands.SCRAMBLE_1 + Commands.SCRAMBLE_2 + Commands.SCRAMBLE_3 +
                  Commands.SOLVE_ALL + Commands.QUIT),
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
    # pyglet2 works without animation but animation system needs legacy GL
    if backend == "pyglet2":
        enable_animation = False
        speed_up_count = 0
    result = GUITestRunner.run_test(
        commands=(Commands.SPEED_UP * speed_up_count +
                  Commands.ROTATE_R * 3 + Commands.ROTATE_L + Commands.ROTATE_U +
                  Commands.ROTATE_D + Commands.ROTATE_F + Commands.ROTATE_B +
                  Commands.QUIT),
        cube_size=cube_size,
        timeout_sec=30.0,
        enable_animation=enable_animation,
        backend=backend,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"


@pytest.mark.parametrize("cube_size", [3])
def test_simple_quit(cube_size: int, backend: str):
    """Test that the window opens and quits cleanly.

    This is a basic smoke test to verify the backend initializes correctly
    and can exit without errors.

    Parameters
    ----------
    cube_size : int
        Size of cube to test.
    backend : str
        Backend to use, parametrized from conftest.py.
    """
    result = GUITestRunner.run_test(
        commands=Commands.QUIT,
        cube_size=cube_size,
        timeout_sec=10.0,
        enable_animation=False,
        backend=backend,
        debug=True
    )
    assert result.success, f"Simple quit test failed: {result.message}. Error: {result.error}"


# =============================================================================
# BUG REPRODUCTION TESTS
# =============================================================================
# These tests reproduce specific bugs. Workflow:
#
# 1. When a bug is found, add a test here that reproduces it (test should FAIL)
# 2. Run the test to confirm it fails with the expected error
# 3. Fix the bug in the code
# 4. Run the test again to confirm it now PASSES
# 5. Update __todo.md to mark the bug as fixed (move to Done section)


def test_bug_B7_size_dec_viewer_error(backend: str):
    """
    Bug B7: Commands accessing ctx.viewer fail in pyglet2 backend.

    SYMPTOM:
        Pressing `-` key crashes with:
        RuntimeError: GCubeViewer not available in pyglet2 backend - use modern_viewer

    REPRODUCE:
        1. Run: python -m cube.main_pyglet2
        2. Press `-` key (decrease cube size)
        3. Observe crash

    ROOT CAUSE:
        pyglet2 backend uses `modern_viewer` (ModernGLCubeViewer) instead of
        `viewer` (GCubeViewer). Commands call ctx.viewer.reset() but pyglet2's
        viewer property raises RuntimeError.

    FIX:
        Changed AppWindow.viewer to return AnimatableViewer protocol.
        Both GCubeViewer and ModernGLCubeViewer implement this protocol.
        PygletAppWindow.viewer now returns self._modern_viewer.

    AFFECTED COMMANDS:
        - SizeDecCommand (ctx.viewer.reset)
        - SizeIncCommand (ctx.viewer.reset)
        - ResetCommand (ctx.viewer.reset)
    """
    result = GUITestRunner.run_test(
        commands=Commands.SIZE_DEC + Commands.QUIT,
        timeout_sec=10.0,
        enable_animation=False,
        backend=backend,
        debug=True
    )
    assert result.success, f"B7 test failed: {result.message}. Error: {result.error}"


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
        commands=Commands.SPEED_UP * 3 + Commands.SCRAMBLE_1 + Commands.SOLVE_ALL + Commands.QUIT,
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
