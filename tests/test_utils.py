"""
Shared test utilities.

Provides TestServiceProvider for tests that create Cube directly without full app.
"""

from cube.application.config_impl import AppConfig
from cube.application.markers import IMarkerFactory, IMarkerManager, MarkerFactory, MarkerManager
from cube.utils.config_protocol import IServiceProvider, ConfigProtocol


class TestServiceProvider(IServiceProvider):
    """Service provider for tests that create Cube directly without full app.

    Implements IServiceProvider protocol - can be passed to Cube(size, sp=test_sp).
    """

    def __init__(self) -> None:
        self._config = AppConfig()
        self._marker_factory = MarkerFactory()
        self._marker_manager = MarkerManager()

    @property
    def config(self) -> ConfigProtocol:
        return self._config

    @property
    def marker_factory(self) -> IMarkerFactory:
        return self._marker_factory

    @property
    def marker_manager(self) -> IMarkerManager:
        return self._marker_manager


# Create a shared instance for tests to use
_test_sp = TestServiceProvider()
