"""
Shared test utilities.

Provides StubServiceProvider for tests that create Cube directly without full app.
"""

from cube.application.config_impl import AppConfig
from cube.utils.logger import setup_root_logger
from cube.application.markers import IMarkerFactory, IMarkerManager, MarkerFactory, MarkerManager
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.service_provider import IServiceProvider
from cube.utils.logger import CubeLogger


class StubServiceProvider(IServiceProvider):
    """Service provider for tests that create Cube directly without full app.

    Implements IServiceProvider protocol - can be passed to Cube(size, sp=test_sp).
    """

    def __init__(self) -> None:
        self._config = AppConfig()
        self._marker_factory = MarkerFactory()
        self._marker_manager = MarkerManager()
        self._logger = setup_root_logger()  # Uses env var override if set

    @property
    def config(self) -> ConfigProtocol:
        return self._config

    @property
    def marker_factory(self) -> IMarkerFactory:
        return self._marker_factory

    @property
    def marker_manager(self) -> IMarkerManager:
        return self._marker_manager

    @property
    def logger(self) -> CubeLogger:
        return self._logger


# Create a shared instance for tests to use
_test_sp = StubServiceProvider()
