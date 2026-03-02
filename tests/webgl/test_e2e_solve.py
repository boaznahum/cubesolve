"""
WebGL E2E tests — verify scramble, solve, and playback through the browser.

These tests launch a real WebGL server, connect via Playwright, and interact
with the UI to verify end-to-end functionality.

Run with (Bash):
    CUBE_QUIET_ALL=1 python -m pytest tests/webgl/ -v -n0 --headed  # see browser
    CUBE_QUIET_ALL=1 python -m pytest tests/webgl/ -v -n0           # headless (CI)

Run with (PowerShell):
    $env:CUBE_QUIET_ALL="1"; python -m pytest tests/webgl/ -v -n0 --headed
    $env:CUBE_QUIET_ALL="1"; python -m pytest tests/webgl/ -v -n0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.webgl.helpers import WebGLPageHelper

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.webgl


@pytest.fixture()
def helper(page: "Page") -> WebGLPageHelper:
    """Create a WebGLPageHelper wrapping the page fixture."""
    return WebGLPageHelper(page)


class TestScrambleSolutionPlayback:
    """Test the core scramble -> solution -> play workflow."""

    def test_scramble_solution_play_stop_play(self, helper: WebGLPageHelper) -> None:
        """Scramble smallest cube, get solution, play, stop mid-way, play again, verify solved.

        This is the primary E2E scenario:
        1. Select smallest available cube
        2. Use default solver (whatever server provides)
        3. Set max speed
        4. Scramble
        5. Click Solution -> redo queue populated
        6. Play All -> let a few moves play
        7. Stop
        8. Play All again
        9. Wait for completion
        10. Assert cube is solved
        """
        size = helper.get_smallest_size()
        helper.select_cube_size(size)
        helper.set_max_speed()

        helper.click_scramble()

        # Generate solution (fills redo queue)
        helper.click_solution()
        redo_count = helper.get_redo_count()
        assert redo_count > 0, "Solution should produce redo moves"

        # Play all moves
        helper.click_fast_play()

        # Let a few moves play, then try to stop
        # (at max speed, playback may finish before we get to stop)
        helper._page.wait_for_timeout(500)

        if helper.is_playing():
            helper.click_stop()
            # Wait for current animation to finish
            helper.wait_for_animation_idle()
            helper._page.wait_for_timeout(300)

            # Check if there are remaining redo moves
            remaining = helper.get_redo_count()
            if remaining > 0:
                # Resume playback
                helper.click_fast_play()
                helper.wait_for_playing_done()
        else:
            # Playback already finished — wait for any pending state
            helper.wait_for_no_redo()

        # Verify cube is solved
        assert helper.is_cube_solved(), "Cube should be solved after playing all solution moves"


class TestScrambleAndSolve:
    """Test scramble -> solve_and_play (combined button)."""

    def test_scramble_solve_and_play_small(self, helper: WebGLPageHelper) -> None:
        """Scramble smallest cube, Solve & Play, wait, assert solved."""
        size = helper.get_smallest_size()
        helper.select_cube_size(size)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solve_and_play()
        helper.wait_for_playing_done(timeout_ms=120_000)

        assert helper.is_cube_solved(), f"{size}x{size} cube should be solved"

    def test_scramble_solve_and_play_3x3(self, helper: WebGLPageHelper) -> None:
        """Scramble 3x3, Solve & Play, wait, assert solved."""
        sizes = helper.get_available_sizes()
        if 3 not in sizes:
            pytest.skip("3x3 not available in dropdown")

        helper.select_cube_size(3)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solve_and_play()
        helper.wait_for_playing_done(timeout_ms=120_000)

        assert helper.is_cube_solved(), "3x3 cube should be solved"


class TestStepThrough:
    """Test stepping through solution one move at a time."""

    def test_scramble_solution_step_through(self, helper: WebGLPageHelper) -> None:
        """Scramble smallest cube, get solution, step through all redo moves one by one."""
        size = helper.get_smallest_size()
        helper.select_cube_size(size)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solution()

        total_moves = helper.get_redo_count()
        assert total_moves > 0, "Solution should produce redo moves"

        # Step through each move
        for _ in range(total_moves):
            helper.click_redo()
            # Wait for the animation of this single move to finish
            helper._page.wait_for_timeout(200)

        # All redo moves consumed
        helper.wait_for_no_redo(timeout_ms=30_000)

        assert helper.is_cube_solved(), "Cube should be solved after stepping through all moves"
