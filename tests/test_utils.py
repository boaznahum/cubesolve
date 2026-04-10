"""
Shared test utilities.

Provides StubServiceProvider for tests that create Cube directly without full app.

``_test_sp`` is a shared, **read-only** service provider for tests that only
need default config.  Any attempt to mutate its config raises RuntimeError.
Tests that need custom config must create their own ``StubServiceProvider()``.
"""

from cube.application.config_impl import AppConfig
from cube.utils.logging import CubeLogger, setup_root_logger
from cube.application.markers import IMarkerFactory, IMarkerManager, MarkerFactory, MarkerManager
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.service_provider import IServiceProvider


class StubServiceProvider(IServiceProvider):
    """Service provider for tests that create Cube directly without full app.

    Each test that needs custom config should create its own instance:
        sp = StubServiceProvider()
        sp.config.check_cube_sanity = True
        cube = Cube(3, sp=sp)

    For shared read-only access, use ``_test_sp`` (frozen=True).
    """

    def __init__(self, *, frozen: bool = False) -> None:
        self._config = AppConfig(
            frozen=frozen,
            _error_prefix="_test_sp.config"
        )
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


# Shared READ-ONLY instance — any config mutation raises RuntimeError.
# Tests that need custom config must create their own StubServiceProvider().
_test_sp = StubServiceProvider(frozen=True)
