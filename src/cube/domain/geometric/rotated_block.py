"""
RotatedBlock - Backward compatibility wrapper.

The core static methods (iterate_points, detect_n_rotations) have been
moved to Block. This module re-exports them for backward compatibility.

For documentation, see: RotatedBlock.md and block.py
"""
from __future__ import annotations

from cube.domain.geometric.block import Block


class RotatedBlock:
    """Backward compatibility wrapper — delegates to Block."""

    iterate_points = staticmethod(Block.iterate_points)
    detect_n_rotations = staticmethod(Block.detect_n_rotations)
