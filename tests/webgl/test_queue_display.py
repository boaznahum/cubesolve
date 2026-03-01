"""
WebGL E2E tests — verify queue display behavior.

Tests that the history panel shows clean queue state:
- No scramble clutter in the done items
- Only solve moves shown in the done queue
- Redo queue properly populated after Solution click

Run with:
    CUBE_QUIET_ALL=1 python -m pytest tests/webgl/test_queue_display.py -v -n0
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
    return WebGLPageHelper(page)


class TestQueueDisplayClean:
    """After scramble, done queue should NOT show scramble moves."""

    def test_scramble_queue_has_no_scramble_clutter(self, helper: WebGLPageHelper) -> None:
        """Scramble 2x2, then check that done items don't contain scramble entries."""
        helper.select_cube_size(2)
        helper.set_max_speed()

        helper.click_scramble()

        # After scramble, the done queue should NOT show scramble-related
        # clutter (scramble summary or individual scramble face moves).
        # The user wants a clean queue showing only solve moves.
        done_count = helper.get_done_count()
        assert done_count == 0, (
            f"After scramble, done queue should be empty (no scramble clutter), "
            f"but found {done_count} done items"
        )

    def test_solution_fills_redo_cleanly(self, helper: WebGLPageHelper) -> None:
        """Scramble 2x2, click Solution, verify redo queue has solve moves."""
        helper.select_cube_size(2)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solution()

        # Redo queue should have solve moves
        redo_count = helper.get_redo_count()
        assert redo_count > 0, "Solution should produce redo moves"

        # Done queue should still be empty (only scramble items, which are hidden)
        done_count = helper.get_done_count()
        assert done_count == 0, (
            f"After solution (before playing), done queue should be empty, "
            f"but found {done_count} done items"
        )

    def test_play_all_shows_solve_moves_in_done(self, helper: WebGLPageHelper) -> None:
        """Scramble 2x2, Solution, Play All — done shows only solve moves."""
        helper.select_cube_size(2)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solution()

        redo_before = helper.get_redo_count()
        assert redo_before > 0

        helper.click_fast_play()
        helper.wait_for_playing_done()

        # After playing, done queue should contain the solve moves
        done_count = helper.get_done_count()
        assert done_count > 0, "After playing solution, done queue should show solve moves"

        # Cube should be solved
        assert helper.is_cube_solved(), "Cube should be solved after playing all solution moves"
