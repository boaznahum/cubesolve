"""
Test checkmark markers on cube center pieces.

This test displays green checkmark markers on all center pieces of the cube,
keeps the GUI running for a few seconds so you can see them, then quits.

Usage
-----
Run with visible GUI (slower, can see markers):
    pytest tests/gui/test_checkmark_markers.py -v --backend=pyglet2

Run for 5 seconds viewing time:
    pytest tests/gui/test_checkmark_markers.py -v --backend=pyglet2 -s
"""

import pytest

from cube.application import _config as config
from cube.application.AbstractApp import AbstractApp
from cube.application.exceptions.app_exceptions import AppExit
from cube.presentation.gui.factory import BackendRegistry
from cube.presentation.gui.commands import Commands
from tests.gui.tester.GUITestResult import GUITestResult


pytestmark = pytest.mark.gui


def test_checkmark_markers_on_centers(backend: str):
    """
    Test that displays checkmark markers on all center pieces.

    Opens the GUI, adds green checkmarks to all 6 face centers,
    displays them for 3 seconds (without freezing), then quits.

    Parameters
    ----------
    backend : str
        Backend to use, parametrized from conftest.py.
    """
    # Save original config
    original_test_mode = config.GUI_TEST_MODE

    event_loop = None
    view_duration = 0.1  # seconds to view markers before quit

    try:
        config.GUI_TEST_MODE = True

        # Create app with 3x3 cube
        app = AbstractApp.create_app(cube_size=5)
        cube = app.cube

        # Get marker factory and manager from service provider
        mf = cube.sp.marker_factory
        mm = cube.sp.marker_manager

        # Add checkmark markers to all center pieces
        checkmark = mf.checkmark()  # Green checkmark
        for center in cube.centers:
            # For 3x3 cube, get the single center sticker's PartEdge
            center_edge = center.edg()
            mm.add_marker(center_edge, "checkmark", checkmark, moveable=False)

        print(f"\nAdded checkmark markers to {len(list(cube.centers))} center pieces")

        # Create backend and window
        gui_backend = BackendRegistry.get_backend(backend)
        event_loop = gui_backend.event_loop
        win = gui_backend.create_app_window(app, 720, 720, "Checkmark Markers Test")

        # Schedule quit after viewing time using command sequence
        print(f"Will view markers for {view_duration} seconds then quit...")
        win.inject_command_sequence(
            Commands.Sleep(view_duration) + Commands.QUIT
        )

        # Run event loop (GUI stays responsive during wait)
        event_loop.run()

        result = GUITestResult(
            success=True,
            message="Checkmark markers displayed successfully"
        )

    except AppExit:
        # Expected when quit is pressed
        result = GUITestResult(
            success=True,
            message="Checkmark markers displayed successfully"
        )

    except Exception as e:
        result = GUITestResult(
            success=False,
            error=e,
            message=f"Test failed: {type(e).__name__}: {e}"
        )

    finally:
        # Clean up
        try:
            if 'win' in locals() and win and hasattr(win, 'has_exit') and not win.has_exit:
                win.close()
        except:
            pass

        config.GUI_TEST_MODE = original_test_mode

    assert result.success, f"Test failed: {result.message}. Error: {result.error}"


@pytest.mark.parametrize("cube_size", [4, 5])
def test_checkmark_markers_on_nxn_centers(cube_size: int, backend: str):
    """
    Test checkmark markers on NxN cube centers (multiple center stickers per face).

    For 4x4: 4 center stickers per face (2x2 grid)
    For 5x5: 9 center stickers per face (3x3 grid)

    Parameters
    ----------
    cube_size : int
        Size of cube (4 or 5).
    backend : str
        Backend to use.
    """
    original_test_mode = config.GUI_TEST_MODE
    event_loop = None
    view_duration = 3.0

    try:
        config.GUI_TEST_MODE = True

        app = AbstractApp.create_app(cube_size=cube_size)
        cube = app.cube

        mf = cube.sp.marker_factory
        mm = cube.sp.marker_manager

        # Add checkmark to ALL center slices (multiple per face for NxN)
        checkmark = mf.checkmark()
        marker_count = 0
        for center in cube.centers:
            for center_slice in center.all_slices:
                center_edge = center_slice.edge
                mm.add_marker(center_edge, f"checkmark_{marker_count}", checkmark, moveable=False)
                marker_count += 1

        print(f"\nAdded {marker_count} checkmark markers to {cube_size}x{cube_size} cube centers")

        gui_backend = BackendRegistry.get_backend(backend)
        event_loop = gui_backend.event_loop
        win = gui_backend.create_app_window(app, 720, 720, f"Checkmark Markers - {cube_size}x{cube_size}")

        # Schedule quit after viewing time using command sequence
        print(f"Will view markers for {view_duration} seconds then quit...")
        win.inject_command_sequence(
            Commands.Sleep(view_duration) + Commands.QUIT
        )
        event_loop.run()

        result = GUITestResult(success=True, message="Checkmark markers displayed successfully")

    except AppExit:
        result = GUITestResult(success=True, message="Checkmark markers displayed successfully")

    except Exception as e:
        result = GUITestResult(success=False, error=e, message=f"Test failed: {type(e).__name__}: {e}")

    finally:
        try:
            if 'win' in locals() and win and hasattr(win, 'has_exit') and not win.has_exit:
                win.close()
        except:
            pass
        config.GUI_TEST_MODE = original_test_mode

    assert result.success, f"Test failed: {result.message}. Error: {result.error}"
