"""Beginner 3x3 solver - Layer-by-layer method.

This package implements the beginner layer-by-layer 3x3 solving method:
1. L1 Cross - White cross on bottom
2. L1 Corners - White corners
3. L2 - Middle layer edges
4. L3 Cross - Yellow cross orientation
5. L3 Corners - Yellow corners permutation

Layer: 3a (part of 3x3/)
Can import: protocols/ (Layer 1), common/ (Layer 2), 3x3/shared/
Cannot import: Other 3x3 solvers (cfop, kociemba), reducers/, direct/
"""

from cube.domain.solver._3x3.beginner.BeginnerSolver3x3 import BeginnerSolver3x3

__all__ = ["BeginnerSolver3x3"]
