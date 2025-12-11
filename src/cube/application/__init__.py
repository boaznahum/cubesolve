# Application Layer - Orchestration and business logic coordination
#
# NOTE: Imports are NOT re-exported here to avoid circular import issues.
# Import components explicitly from their modules:
#   from cube.application.app import _App as App
#   from cube.application.AbstractApp import AbstractApp
#   from cube.application.state import ApplicationAndViewState
#
# PRIVATE CONFIG MODULE:
# The _config module is private to this package. To access configuration values:
#   - In domain/presentation layers: Use ConfigProtocol via cube.config property
#   - In tests only: Import as `from cube.application import _config as config`
# DO NOT import _config directly in production code.
