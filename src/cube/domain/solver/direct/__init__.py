"""Direct NxN solvers - solve big cubes without reduction to 3x3.

Available solvers:
- CommutatorNxNSolver: Piece-by-piece using commutators (centers first)
- CageNxNSolver: Edges+corners first, centers last (parity-free)
"""

from .commutator import CommutatorNxNSolver
from .cage import CageNxNSolver

__all__ = ["CommutatorNxNSolver", "CageNxNSolver"]
