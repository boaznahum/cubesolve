"""Direct NxN solvers - solve big cubes without reduction to 3x3.

Available solvers:
- CageNxNSolver: Edges+corners first, centers last (parity-free)
"""

from .cage import CageNxNSolver

__all__ = ["CageNxNSolver"]
