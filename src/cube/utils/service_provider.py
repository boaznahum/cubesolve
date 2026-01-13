"""Service provider protocol for dependency inversion.

Domain classes receive IServiceProvider via dependency injection.
Application (_App) implements this protocol.
Tests use a lightweight TestServiceProvider.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from cube.utils.config_protocol import ConfigProtocol

if TYPE_CHECKING:
    from cube.application.markers.IMarkerFactory import IMarkerFactory
    from cube.application.markers.IMarkerManager import IMarkerManager
    from cube.utils.logger_protocol import ILogger


@runtime_checkable
class IServiceProvider(Protocol):
    """Service provider protocol - provides access to application services.

    Domain classes receive this via dependency injection.
    Application (_App) implements this protocol.
    Tests use a lightweight TestServiceProvider.

    Extensible: future services (debug, logging) can be added here.
    """

    @property
    def config(self) -> ConfigProtocol:
        """Get the application configuration."""
        ...

    @property
    def marker_factory(self) -> "IMarkerFactory":
        """Get the marker factory for creating marker configurations."""
        ...

    @property
    def marker_manager(self) -> "IMarkerManager":
        """Get the marker manager for adding/retrieving markers on cube stickers."""
        ...

    @property
    def logger(self) -> "ILogger":
        """Get the logger for debug output control."""
        ...