"""Logger re-export for backwards compatibility.

See Also:
    cube.utils.logger: The CubeLogger implementation
"""
from __future__ import annotations

from cube.utils.logger import CubeLogger, setup_root_logger

__all__ = ["CubeLogger", "setup_root_logger"]
