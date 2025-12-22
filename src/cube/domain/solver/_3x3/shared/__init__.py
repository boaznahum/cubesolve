"""Shared 3x3 solver components.

These components are used by multiple 3x3 solvers:
- L1Cross - Layer 1 cross (used by beginner, CFOP)

Layer: 3a (part of 3x3/)
Can import: protocols/ (Layer 1), common/ (Layer 2)
Cannot import: Other 3x3 solvers, reducers/, direct/
"""

from cube.domain.solver._3x3.shared.L1Cross import L1Cross

__all__ = ["L1Cross"]
