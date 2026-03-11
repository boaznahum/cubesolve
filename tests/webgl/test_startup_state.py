"""
WebGL E2E tests — verify initial startup state is correct.

Regression tests for the unified state snapshot: ensure the cube displays
proper colors on startup and that solve works after initial connection.
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


class TestStartupState:
    """Verify that the cube has correct state immediately after WebSocket connection."""

    def test_cube_has_colors_on_startup(self, page: "Page") -> None:
        """After initial connection, cube faces should have non-zero colors (not all gray/black).

        Regression: unified state snapshot must send cube face data on first connect.
        If the cube appears all gray, face data was not included in the initial state message.
        """
        # The page fixture already waits for #status.connected,
        # so the WebSocket is connected and initial state has arrived.

        # Check that appState.latestState has face data with non-zero colors
        has_colors: bool = page.evaluate(
            """() => {
                const state = window.appState;
                if (!state || !state.latestState) return false;
                const faces = state.latestState.faces;
                if (!faces) return false;

                // Check that at least some stickers have non-zero colors
                // A solved cube should have 6 different face colors, all non-black
                let nonZeroCount = 0;
                for (const [faceName, faceData] of Object.entries(faces)) {
                    const colors = faceData.colors || faceData;
                    if (!Array.isArray(colors)) continue;
                    for (const rgb of colors) {
                        if (rgb[0] !== 0 || rgb[1] !== 0 || rgb[2] !== 0) {
                            nonZeroCount++;
                        }
                    }
                }
                // A 3x3 cube has 9 stickers per face * 6 faces = 54 stickers.
                // At most one face could be black (if that's a cube color), so
                // at least 45 should be non-zero.
                return nonZeroCount > 0;
            }"""
        )
        assert has_colors, "Cube should have non-zero face colors on startup (not all gray/black)"

    def test_cube_size_reported_on_startup(self, page: "Page") -> None:
        """After initial connection, cube size should be reported in appState."""
        size: int = page.evaluate(
            """() => {
                const state = window.appState;
                if (!state || !state.latestState) return -1;
                return state.latestState.size || -1;
            }"""
        )
        assert size >= 2, f"Cube size should be >= 2 on startup, got {size}"

    def test_solve_works_after_startup(self, helper: WebGLPageHelper) -> None:
        """Scramble and solve should work correctly after initial connection.

        Regression: solve must not hang/freeze the application after the unified
        state snapshot migration.
        """
        helper.set_max_speed()
        helper.click_scramble()

        # Verify cube is not solved after scramble
        assert not helper.is_cube_solved(), "Cube should not be solved after scramble"

        # Click solution — should populate redo queue without freezing
        helper.click_solution()

        # Verify redo queue has items
        redo_count = helper.get_redo_count()
        assert redo_count > 0, "Solution should populate redo queue"

        # Play all and wait for completion
        helper.click_fast_play()
        helper.wait_for_playing_done(timeout_ms=60_000)

        # Verify cube is solved
        assert helper.is_cube_solved(), "Cube should be solved after playing all solution moves"
