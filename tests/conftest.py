"""
Root pytest configuration for all tests.

Provides command-line options for debug output control:
- --quiet-debug: Suppress all debug output (sets quiet_all=True)
- --debug-all: Enable all debug output (sets debug_all=True)

Provides TestServiceProvider for tests that create Cube directly without full app.
"""

import pytest

from cube.application.config_impl import AppConfig
from cube.utils.config_protocol import IServiceProvider, ConfigProtocol


class TestServiceProvider(IServiceProvider):
    """Service provider for tests that create Cube directly without full app.

    Implements IServiceProvider protocol - can be passed to Cube(size, sp=test_sp).
    """

    def __init__(self) -> None:
        self._config = AppConfig()

    @property
    def config(self) -> ConfigProtocol:
        return self._config


# Create a shared instance for tests to use
_test_sp = TestServiceProvider()


@pytest.fixture
def test_sp() -> IServiceProvider:
    """Fixture providing a TestServiceProvider for tests that create Cube directly."""
    return _test_sp


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
