"""
Test for issue #24: Stop button must stay enabled while client animations play.

The bug: server sends playing(false) when its redo queue empties, but the
client AnimationQueue still has pending/running animations. This causes the
Stop button to disable before the cube finishes animating visually.

The fix: client-side Toolbar._deferStopDisable() polls the AnimationQueue
and only disables Stop when the queue is truly empty.

Run with:
    CUBE_QUIET_ALL=1 python -m pytest tests/webgl/test_issue_24_stop_button.py -v -n0
    CUBE_QUIET_ALL=1 python -m pytest tests/webgl/test_issue_24_stop_button.py -v -n0 --headed
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


class TestStopButtonTiming:
    """Issue #24: Stop button must stay enabled while animations are playing."""

    def test_stop_enabled_during_solve_playback(self, helper: WebGLPageHelper) -> None:
        """Stop button stays enabled while client animations are running.

        Regression test for issue #24: the server sends playing(false) when
        its redo queue empties, but client animations may still be running.
        The Stop button must remain enabled until the client AnimationQueue
        is truly idle.

        Strategy: use a SLOW speed so animations take long enough that we
        can reliably sample the stop button state mid-playback.
        """
        size = helper.get_smallest_size()
        helper.select_cube_size(size)

        # Use a medium-slow speed so animations are visible and we can
        # sample state mid-playback. Speed 2 gives ~300ms per move.
        helper.set_speed(2)

        helper.click_scramble()
        helper.click_solve_and_play()

        # The stop button should be enabled during playback.
        # Poll repeatedly — we want to catch the moment where the server
        # has emptied its queue but the client is still animating.
        page = helper._page

        # Wait a bit for playback to start
        page.wait_for_timeout(300)

        # Sample multiple times during playback to detect premature disable
        premature_disable_detected = False
        for _ in range(20):
            client_animating: bool = page.evaluate(
                """() => {
                    const aq = window._testAnimQueue;
                    if (!aq) return false;
                    return !!(aq.currentAnim || aq.queue.length > 0 || aq._previewState);
                }"""
            )
            stop_enabled: bool = page.evaluate(
                "!document.getElementById('btn-stop').disabled"
            )

            if client_animating and not stop_enabled:
                premature_disable_detected = True
                break

            page.wait_for_timeout(100)

        # Wait for everything to finish
        helper.wait_for_playing_done()

        assert not premature_disable_detected, (
            "Stop button was disabled while client animations were still running "
            "(issue #24)"
        )

        # After completion, stop should be disabled and cube should be solved
        assert not helper.is_playing(), "Stop should be disabled after playback"
        assert helper.is_cube_solved(), "Cube should be solved"

    def test_stop_enabled_during_solve_playback_max_speed(
        self, helper: WebGLPageHelper
    ) -> None:
        """Same test at max speed — the most common failure mode for issue #24.

        At max speed, server timers fire very fast and the race between
        server queue empty and client animation is most pronounced.
        """
        size = helper.get_smallest_size()
        helper.select_cube_size(size)
        helper.set_max_speed()

        helper.click_scramble()
        helper.click_solve_and_play()

        page = helper._page
        page.wait_for_timeout(200)

        premature_disable_detected = False
        for _ in range(30):
            client_animating: bool = page.evaluate(
                """() => {
                    const aq = window._testAnimQueue;
                    if (!aq) return false;
                    return !!(aq.currentAnim || aq.queue.length > 0 || aq._previewState);
                }"""
            )
            stop_enabled: bool = page.evaluate(
                "!document.getElementById('btn-stop').disabled"
            )

            if client_animating and not stop_enabled:
                premature_disable_detected = True
                break

            page.wait_for_timeout(50)

        helper.wait_for_playing_done()

        assert not premature_disable_detected, (
            "Stop button was disabled while client animations were still running "
            "at max speed (issue #24)"
        )
        assert helper.is_cube_solved(), "Cube should be solved"
