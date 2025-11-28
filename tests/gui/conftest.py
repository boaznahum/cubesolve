"""
Pytest configuration for GUI tests.

Provides the --animate command-line option to enable animations during testing.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for GUI tests."""
    parser.addoption(
        "--animate",
        action="store_true",
        default=False,
        help="Enable animations during GUI tests (slower but visible)"
    )


@pytest.fixture
def enable_animation(request):
    """Fixture that returns True if --animate flag is passed."""
    return request.config.getoption("--animate")
