"""
Root pytest configuration for all tests.

Provides command-line options for debug output control:
- --quiet-debug: Suppress all debug output (sets quiet_all=True)
- --debug-all: Enable all debug output (sets debug_all=True)
"""

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for debug output control."""
    parser.addoption(
        "--quiet-debug",
        action="store_true",
        default=False,
        help="Suppress all debug output during tests (sets quiet_all=True)"
    )
    parser.addoption(
        "--debug-all",
        action="store_true",
        default=False,
        help="Enable all debug output during tests (sets debug_all=True)"
    )


@pytest.fixture
def quiet_all(request) -> bool:
    """Fixture that returns True if --quiet-debug flag is passed."""
    return request.config.getoption("--quiet-debug")


@pytest.fixture
def debug_all(request) -> bool:
    """Fixture that returns True if --debug-all flag is passed."""
    return request.config.getoption("--debug-all")
