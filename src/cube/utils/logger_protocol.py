"""Logger protocol for dependency inversion.

Domain code programs against ``CubeLogger`` (which IS-A ``logging.Logger``).
This module re-exports the concrete type so that domain code does not
need to import from ``cube.utils.logger`` directly.

See Also:
    CubeLogger: The implementation in cube.utils.logger
"""
from __future__ import annotations

from typing import Any, Callable, TypeAlias

# Recursive type: a value OR a callable that returns another LazyArg.
# Allows lazy evaluation of debug arguments.
LazyArg: TypeAlias = "Callable[[], LazyArg] | Any"
