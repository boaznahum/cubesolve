"""Logger re-export from unified implementation.

The Logger class is now in cube.utils.prefixed_logger.
This module provides backwards compatibility for existing imports.

See Also:
    cube.utils.prefixed_logger: The unified Logger implementation
    ILogger: The protocol definition in cube.utils.logger_protocol
"""
from __future__ import annotations

# Re-export from unified implementation
from cube.utils.logger import Logger

__all__ = ["Logger"]
