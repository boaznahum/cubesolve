"""
WebGL E2E test — verify that changing cube size preserves the selected solver.

Regression test for bug where _handle_size() called app.reset() which
unconditionally reset the solver to the default (Kociemba).
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


class TestSizeChangePreservesSolver:
    """Changing cube size should NOT reset the solver selection."""

    def test_size_change_preserves_solver(self, helper: WebGLPageHelper) -> None:
        """Select a non-default solver, change size, verify solver is preserved."""
        # Start with default (Kociemba on 3×3)
        assert helper.get_current_solver() == "Kociemba"

        # Switch to Beginner Reducer
        helper.select_solver("Beginner Reducer")
        helper.get_current_solver()  # wait for state round-trip
        assert helper.get_current_solver() == "Beginner Reducer"

        # Change size from 3→5
        helper.select_cube_size(5)

        # Solver should still be Beginner Reducer
        assert helper.get_current_solver() == "Beginner Reducer"

    def test_size_change_preserves_solver_multiple_sizes(
        self, helper: WebGLPageHelper
    ) -> None:
        """Solver should be preserved across multiple size changes."""
        helper.select_solver("CFOP")
        assert helper.get_current_solver() == "CFOP"

        for size in [4, 7, 3]:
            helper.select_cube_size(size)
            assert helper.get_current_solver() == "CFOP", (
                f"Solver changed to {helper.get_current_solver()} after size→{size}"
            )
