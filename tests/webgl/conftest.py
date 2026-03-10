"""
Pytest configuration for WebGL E2E browser tests.

Provides:
- Server fixture: starts WebGL backend in a daemon thread per test
- Playwright fixtures: browser and page management
- CLI options: --headed, --browser-type, --webgl-timeout
"""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page, Playwright


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add WebGL E2E test CLI options."""
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode (visible window)",
    )
    parser.addoption(
        "--browser-type",
        action="store",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser engine to use (default: chromium)",
    )
    parser.addoption(
        "--webgl-timeout",
        action="store",
        type=int,
        default=60,
        help="Default timeout in seconds for WebGL test assertions (default: 60)",
    )


# ── Server fixture (function-scoped: fresh server per test) ──


@pytest.fixture()
def webgl_server(request: pytest.FixtureRequest) -> Generator[str, None, None]:
    """Start a WebGL server in a daemon thread, yield the base URL.

    Sets GUI_TEST_MODE so the server binds to localhost on a random port
    and does not open a browser.
    """
    from cube.application import _config as cfg

    # Enable test mode: localhost binding, random port, no browser
    original_test_mode = cfg.DEFAULTS.gui_test_mode
    cfg.DEFAULTS.gui_test_mode = True

    # Temporarily hide dist/ so server serves from source static/
    # (dist/ may be stale and missing test-time JS changes like window.appState)
    webgl_dir = Path(__file__).resolve().parents[2] / "src" / "cube" / "presentation" / "gui" / "backends" / "webgl" / "static"
    dist_dir = webgl_dir / "dist"
    dist_hidden = webgl_dir / "_dist_hidden_by_test"
    did_hide_dist = False
    if dist_dir.exists():
        # Remove stale leftover from a previous crashed run (Windows
        # doesn't allow rename-over-existing-directory)
        if dist_hidden.exists():
            shutil.rmtree(dist_hidden)
        dist_dir.rename(dist_hidden)
        did_hide_dist = True

    try:
        from cube.main_any_backend import create_app_window

        window = create_app_window("webgl", quiet_all=True)
        event_loop = window._event_loop  # type: ignore[attr-defined]
        port = event_loop._resolve_port()
        server_url = f"http://localhost:{port}"

        # Run event loop in a daemon thread
        def _run_server() -> None:
            event_loop.run()

        server_thread = threading.Thread(target=_run_server, daemon=True)
        server_thread.start()

        # Poll until the server is ready (max 10s)
        import urllib.request
        import urllib.error

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(server_url, timeout=1)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.2)
        else:
            raise RuntimeError(f"WebGL server failed to start at {server_url}")

        yield server_url

        # Teardown
        event_loop.stop()
        server_thread.join(timeout=5)
        window.cleanup()

    finally:
        cfg.DEFAULTS.gui_test_mode = original_test_mode
        # Restore dist/ if we hid it
        if did_hide_dist and dist_hidden.exists():
            # Retry rename — on Windows, file locks may linger briefly
            for attempt in range(5):
                try:
                    dist_hidden.rename(dist_dir)
                    break
                except PermissionError:
                    time.sleep(0.5)


# ── Playwright fixtures (session-scoped: one browser per test session) ──


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """Provide a Playwright instance for the test session."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(
    request: pytest.FixtureRequest, playwright_instance: "Playwright"
) -> Generator[Browser, None, None]:
    """Launch a browser for the test session.

    Respects --headed and --browser-type CLI options.
    """
    headed: bool = request.config.getoption("--headed")
    browser_type_name: str = request.config.getoption("--browser-type")

    browser_type = getattr(playwright_instance, browser_type_name)
    b = browser_type.launch(headless=not headed)
    yield b
    b.close()


# ── Page fixture (function-scoped: fresh page per test) ──


@pytest.fixture()
def page(
    request: pytest.FixtureRequest,
    browser: "Browser",
    webgl_server: str,
) -> Generator[Page, None, None]:
    """Create a fresh browser page connected to the WebGL server.

    Navigates to the server URL and waits for WebSocket connection.
    """
    timeout_s: int = request.config.getoption("--webgl-timeout")
    timeout_ms = timeout_s * 1000

    context = browser.new_context()
    p = context.new_page()
    p.set_default_timeout(timeout_ms)

    # Navigate and wait for WebSocket connection
    p.goto(webgl_server)
    p.wait_for_selector("#status.connected", timeout=timeout_ms)

    yield p

    context.close()
