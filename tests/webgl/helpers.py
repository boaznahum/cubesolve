"""
WebGL E2E test helpers — encapsulates all UI interactions with the WebGL app.

Provides a WebGLPageHelper class that wraps Playwright page operations
with domain-specific methods for cube manipulation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


class WebGLPageHelper:
    """High-level wrapper for interacting with the WebGL cube app via Playwright."""

    def __init__(self, page: Page) -> None:
        self._page = page

    # ── Toolbar controls ──

    def _js_select(self, selector: str, value: str) -> None:
        """Set a <select> value via JS and dispatch change event.

        More reliable than Playwright's select_option for dynamically-populated
        selects whose options are built by JS modules.
        """
        success: bool = self._page.evaluate(
            """([sel, val]) => {
                const el = document.querySelector(sel);
                if (!el) return false;
                // Verify option exists
                const options = Array.from(el.options);
                const match = options.find(o => o.value === val);
                if (!match) return false;
                el.value = val;
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }""",
            [selector, value],
        )
        if not success:
            # Debug: dump available options
            opts = self._page.evaluate(
                """(sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return 'element not found';
                    return Array.from(el.options).map(o => o.value);
                }""",
                selector,
            )
            raise RuntimeError(
                f"Failed to select value '{value}' in '{selector}'. "
                f"Available options: {opts}"
            )

    def select_cube_size(self, n: int) -> None:
        """Select cube size from the size dropdown and wait for cube rebuild.

        After selection, verifies that the server actually rebuilt the cube
        at the requested size (checks appState.latestState.size).
        """
        # Wait for size dropdown to be populated (options added by Toolbar._bindToolbar)
        self._page.wait_for_function(
            "document.querySelectorAll('#size-select option').length > 0",
        )
        self._js_select("#size-select", str(n))
        # Wait for the cube state to arrive (cursor resets after server processes)
        self._page.wait_for_function(
            "document.body.style.cursor === '' || document.body.style.cursor === 'auto'"
        )
        # Brief settle time for the cube model to rebuild
        self._page.wait_for_timeout(500)
        # Verify the server actually applied the requested size
        actual = self.get_current_size()
        if actual != n:
            raise RuntimeError(
                f"Requested cube size {n} but server reports size {actual}"
            )

    def get_available_sizes(self) -> list[int]:
        """Return the list of available cube sizes from the dropdown."""
        self._page.wait_for_function(
            "document.querySelectorAll('#size-select option').length > 0",
        )
        result: list[str] = self._page.evaluate(
            """() => Array.from(document.getElementById('size-select').options)
                       .map(o => o.value)"""
        )
        return [int(v) for v in result]

    def get_smallest_size(self) -> int:
        """Return the smallest available cube size."""
        sizes = self.get_available_sizes()
        return min(sizes)

    def get_current_size(self) -> int:
        """Return the current cube size from the model (via appState.latestState.size)."""
        result: int = self._page.evaluate(
            """() => {
                const state = window.appState && window.appState.latestState;
                return state ? state.size : -1;
            }"""
        )
        return result

    def select_solver(self, name: str) -> None:
        """Select a solver by its visible label text (or partial prefix match).

        Waits for the server to confirm the solver change via WebSocket
        round-trip (appState.solverName updated).
        """
        # Wait for solver dropdown to be populated (options added by toolbar_state message)
        self._page.wait_for_function(
            "document.querySelectorAll('#solver-select option').length > 0",
        )
        # Find the option with matching text (exact or prefix) and select by value.
        # Returns the matched solver name so we can wait for it.
        matched_name: str = self._page.evaluate(
            """(name) => {
                const sel = document.getElementById('solver-select');
                const lower = name.toLowerCase();
                // Exact match first
                for (const opt of sel.options) {
                    if (opt.textContent.toLowerCase() === lower) {
                        sel.value = opt.value;
                        sel.dispatchEvent(new Event('change', { bubbles: true }));
                        return opt.textContent;
                    }
                }
                // Prefix match
                for (const opt of sel.options) {
                    if (opt.textContent.toLowerCase().startsWith(lower)) {
                        sel.value = opt.value;
                        sel.dispatchEvent(new Event('change', { bubbles: true }));
                        return opt.textContent;
                    }
                }
                const avail = Array.from(sel.options).map(o => o.textContent);
                throw new Error('Solver not found: ' + name + '. Available: ' + avail.join(', '));
            }""",
            name,
        )
        # Wait for the server round-trip to confirm the solver change
        self._page.wait_for_function(
            f"() => window.appState && window.appState.solverName === {matched_name!r}",
            timeout=10_000,
        )

    def get_available_solvers(self) -> list[str]:
        """Return the list of available solver names from the dropdown."""
        self._page.wait_for_function(
            "document.querySelectorAll('#solver-select option').length > 0",
        )
        result: list[str] = self._page.evaluate(
            """() => Array.from(document.getElementById('solver-select').options)
                       .map(o => o.textContent)"""
        )
        return result

    def get_current_solver(self) -> str:
        """Return the current solver name from appState."""
        result: str = self._page.evaluate(
            "() => window.appState.solverName"
        )
        return result

    def set_speed(self, index: int) -> None:
        """Select animation speed by index value (0=slowest, 7=fastest)."""
        # Wait for speed dropdown to be populated
        self._page.wait_for_function(
            "document.querySelectorAll('#speed-select option').length > 0",
        )
        self._js_select("#speed-select", str(index))

    def set_max_speed(self) -> None:
        """Select the fastest available animation speed (last option in dropdown)."""
        self._page.wait_for_function(
            "document.querySelectorAll('#speed-select option').length > 0",
        )
        self._page.evaluate(
            """() => {
                const sel = document.getElementById('speed-select');
                const last = sel.options[sel.options.length - 1];
                sel.value = last.value;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
            }"""
        )

    # ── Action buttons ──

    def click_scramble(self) -> None:
        """Click Scramble and wait for the operation to complete.

        Scramble sets cursor to 'progress'; it resets when cube_state arrives.
        """
        self._page.click('[data-cmd="scramble"]')
        # Wait for progress cursor to appear then reset
        self._page.wait_for_function(
            "document.body.style.cursor !== 'progress'",
            timeout=30_000,
        )
        # Allow history panel to update
        self._page.wait_for_timeout(300)

    def click_solution(self) -> None:
        """Click Solution and wait for redo items to appear in history panel.

        Solution generates the solver moves and puts them in the redo queue
        without playing them.
        """
        self._page.click('[data-cmd="solve"]')
        # Wait for cursor to reset (server processing done)
        self._page.wait_for_function(
            "document.body.style.cursor !== 'progress'",
            timeout=60_000,
        )
        # Wait for redo items to appear in history
        self._page.wait_for_selector(".hp-redo", timeout=30_000)

    def click_solve_and_play(self) -> None:
        """Click Solve & Play (one-phase solve).

        One-phase solve animates moves as the solver runs — moves go
        directly to history (hp-done), not to the redo queue. We wait
        for either done items to appear (solve in progress) or the cube
        to already be solved (solve finished before we could observe).
        """
        self._page.click('[data-cmd="solve_and_play"]')
        # One-phase: moves stream into history as hp-done, no redo queue.
        self._page.wait_for_function(
            """() => {
                // Moves being animated — done items appearing
                if (document.querySelectorAll('.hp-done').length > 0) return true;
                // Solve already finished
                const state = window.appState && window.appState.latestState;
                return !!(state && state.solved);
            }""",
            timeout=60_000,
        )

    def click_fast_play(self) -> None:
        """Click Play All (fast-forward) button."""
        btn = self._page.locator("#btn-fastplay")
        btn.wait_for(state="attached")
        # Wait until button is enabled
        self._page.wait_for_function(
            "!document.getElementById('btn-fastplay').disabled",
            timeout=10_000,
        )
        btn.click()

    def click_stop(self) -> None:
        """Click the Stop button (only if enabled, i.e. playing is active)."""
        is_enabled: bool = self._page.evaluate(
            "!document.getElementById('btn-stop').disabled"
        )
        if is_enabled:
            self._page.click('[data-cmd="stop"]')

    def is_playing(self) -> bool:
        """Check if autoplay is currently active (stop button is enabled)."""
        return self._page.evaluate(
            "!document.getElementById('btn-stop').disabled"
        )

    def click_redo(self) -> None:
        """Click Redo (single step forward)."""
        btn = self._page.locator("#btn-redo")
        self._page.wait_for_function(
            "!document.getElementById('btn-redo').disabled",
            timeout=10_000,
        )
        btn.click()

    def click_undo(self) -> None:
        """Click Undo (single step backward)."""
        self._page.locator("#btn-undo").click()

    # ── Waiting helpers ──

    def wait_for_playing_done(self, timeout_ms: int = 120_000) -> None:
        """Wait until solve/playback is complete.

        Works for both flows:
        - Two-phase (solution + play): redo queue drains to zero, fastplay disabled
        - One-phase (solve_and_play): FSM leaves 'solving', cube is solved
        """
        self._page.wait_for_function(
            """() => {
                const as = window.appState;
                if (!as) return false;
                const ms = as.machineState;
                // Still solving — not done yet
                if (ms === 'solving') return false;
                const redos = document.querySelectorAll('.hp-redo');
                if (redos.length > 0) return false;
                // Two-phase: fastplay disabled and no redo items
                const btn = document.getElementById('btn-fastplay');
                if (btn && btn.disabled) return true;
                // One-phase: cube solved, no longer solving
                const state = as.latestState;
                return !!(state && state.solved);
            }""",
            timeout=timeout_ms,
        )
        # Allow final animations to settle
        self._page.wait_for_timeout(500)

    def wait_for_no_redo(self, timeout_ms: int = 120_000) -> None:
        """Wait until there are no redo items remaining in the history panel."""
        self._page.wait_for_function(
            "document.querySelectorAll('.hp-redo').length === 0",
            timeout=timeout_ms,
        )

    def wait_for_animation_idle(self, timeout_ms: int = 10_000) -> None:
        """Wait until no animation is running (stop button is disabled)."""
        self._page.wait_for_function(
            """() => {
                const btn = document.getElementById('btn-stop');
                return btn && btn.disabled;
            }""",
            timeout=timeout_ms,
        )

    def wait_for_queue_idle(self, timeout_ms: int = 10_000) -> None:
        """Wait until the AnimationQueue is truly idle (no animation, no queue, no preview)."""
        self._page.wait_for_function(
            """() => {
                const aq = window._testAnimQueue;
                return aq && !aq.currentAnim && aq.queue.length === 0 && !aq._previewState;
            }""",
            timeout=timeout_ms,
        )

    # ── Query helpers ──

    def get_redo_count(self) -> int:
        """Count the number of .hp-redo elements in the history panel."""
        return self._page.locator(".hp-redo").count()

    def get_done_count(self) -> int:
        """Count the number of .hp-done elements in the history panel."""
        return self._page.locator(".hp-done").count()

    def is_cube_solved(self) -> bool:
        """Check if the cube is solved using the model's authoritative answer.

        The server includes ``solved: bool`` in every ``cube_state`` message,
        computed by ``Cube.solved`` which checks all faces/parts — not just
        sticker colors. This is the definitive check for any cube size.
        """
        result: bool = self._page.evaluate(
            """() => {
                const state = window.appState && window.appState.latestState;
                if (!state) return false;
                return !!state.solved;
            }"""
        )
        return result
