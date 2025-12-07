# Application-level exceptions
#
# Domain exceptions are re-exported here for backward compatibility.
# New code should import directly from cube.domain.exceptions.

# Application-only exceptions (not used by domain)
from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.application.exceptions.ExceptionRunStop import RunStop

# Re-export domain exceptions for backward compatibility
from cube.domain.exceptions import (
    InternalSWError,
    OpAborted,
    EvenCubeEdgeParityException,
    EvenCubeCornerSwapException,
)

__all__ = [
    # Application-only
    "AppExit",
    "RunStop",
    # Re-exported from domain (for backward compatibility)
    "InternalSWError",
    "OpAborted",
    "EvenCubeEdgeParityException",
    "EvenCubeCornerSwapException",
]
