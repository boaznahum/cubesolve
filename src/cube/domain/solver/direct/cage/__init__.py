"""Cage Method NxN solver package.

Solves big cubes by building a "cage" (edges + corners first),
then filling centers last using commutators. Parity-free approach.
"""

from .CageNxNSolver import CageNxNSolver

__all__ = ["CageNxNSolver"]
