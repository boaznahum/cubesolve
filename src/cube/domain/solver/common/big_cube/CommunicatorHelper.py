"""
Communicator Helper for NxN Big Cubes.
"""

from cube.domain.model.Cube import Cube


class CommunicatorHelper:
    """Helper for the block commutator algorithm on NxN cubes."""

    def __init__(self, cube: Cube) -> None:
        self._cube = cube

    @property
    def n_slices(self) -> int:
        return self._cube.n_slices
