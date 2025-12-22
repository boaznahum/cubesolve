"""Kociemba 3x3 solver - Two-phase near-optimal algorithm.

This package implements Herbert Kociemba's two-phase algorithm for
near-optimal 3x3 solving (typically 18-22 moves).

Note: Only works on actual 3x3 cubes. For NxN support, use the
NxNSolverOrchestrator which handles reduction.

Layer: 3a (part of 3x3/)
Can import: protocols/ (Layer 1), common/ (Layer 2)
Cannot import: Other 3x3 solvers, reducers/, direct/
"""

from cube.domain.solver._3x3.kociemba.Kociemba3x3 import Kociemba3x3

__all__ = ["Kociemba3x3"]
