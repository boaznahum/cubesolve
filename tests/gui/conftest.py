"""
Pytest configuration for GUI tests.

Provides command-line options for GUI test configuration:
- --animate: Enable animations during testing
- --speed-up: Number of times to increase animation speed (default: 3)
"""

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for GUI tests."""
    parser.addoption(
        "--animate",
        action="store_true",
        default=True,
        help="Enable animations during GUI tests (default: on)"
    )
    parser.addoption(
        "--speed-up",
        action="store",
        type=int,
        default=3,
        help="Number of times to increase animation speed (default: 3)"
    )


@pytest.fixture
def enable_animation(request) -> bool:
    """Fixture that returns True if --animate flag is passed (default: True)."""
    return request.config.getoption("--animate")


@pytest.fixture
def speed_up_count(request) -> int:
    """Fixture that returns the number of speed-up key presses."""
    return request.config.getoption("--speed-up")
