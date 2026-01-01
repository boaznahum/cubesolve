"""Commutator-based NxN solver package.

Solves big cubes piece-by-piece using commutators [A, B] = A B A' B'.
"""

from .CommutatorNxNSolver import CommutatorNxNSolver

__all__ = ["CommutatorNxNSolver"]
