# Domain-level exceptions
#
# These exceptions are used by domain layer (model, solver, algs)
# and should NOT depend on any other layer.

from cube.domain.exceptions.EvenCubeCornerSwapException import (
    EvenCubeCornerSwapException,
)
from cube.domain.exceptions.EvenCubeEdgeParityException import (
    EvenCubeEdgeParityException,
)
from cube.domain.exceptions.EvenCubeEdgeSwapParityException import (
    EvenCubeEdgeSwapParityException,
)
from cube.domain.exceptions.GeometryError import GeometryError, GeometryErrorCode
from cube.domain.exceptions.InternalSWError import InternalSWError
from cube.domain.exceptions.OpAborted import OpAborted

__all__ = [
    "InternalSWError",
    "OpAborted",
    "EvenCubeEdgeParityException",
    "EvenCubeCornerSwapException",
    "EvenCubeEdgeSwapParityException",
    "GeometryError",
    "GeometryErrorCode",
]
