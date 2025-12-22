"""CFOP 3x3 solver - Fridrich method.

This package implements the CFOP (Fridrich) 3x3 solving method:
1. Cross - Build white cross on bottom
2. F2L - First two layers (pairs corners with edges)
3. OLL - Orient last layer (yellow face all same color)
4. PLL - Permute last layer (final permutation)

Layer: 3a (part of 3x3/)
Can import: protocols/ (Layer 1), common/ (Layer 2), 3x3/shared/
Cannot import: Other 3x3 solvers (beginner, kociemba), reducers/, direct/
"""

from cube.domain.solver._3x3.cfop.CFOP3x3 import CFOP3x3

__all__ = ["CFOP3x3"]
