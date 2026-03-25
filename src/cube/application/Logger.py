"""Logger re-export for backwards compatibility.

See Also:
    cube.utils.logging: The CubeLogger implementation
"""
from __future__ import annotations

from cube.utils.logging import CubeLogger, setup_root_logger

__all__ = ["CubeLogger", "setup_root_logger"]
