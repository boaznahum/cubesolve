"""Scrambler protocol for generating scramble algorithms."""

from __future__ import annotations

from enum import Flag, auto
from random import Random
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.domain.algs.Alg import Alg


class ScrambleWhat(Flag):
    """What types of moves to include in scramble. Can be combined with |."""
    WHOLE_CUBE = auto()   # Whole cube rotations (x, y, z)
    FACE = auto()         # Face moves (R, L, U, D, F, B)
    SLICE = auto()        # Slice moves (M, E, S)

    # Convenient combinations
    ALL = WHOLE_CUBE | FACE | SLICE


class ScramblerProtocol(Protocol):
    """Protocol for scramble generation."""

    def scramble(
        self,
        what: ScrambleWhat,
        seed: int | None = None,
        length: int | None = None,
        animation: bool = False,
    ) -> Alg:
        """Generate and apply a scramble algorithm.

        Args:
            what: Set of move types to include (can combine with |)
            seed: Random seed for reproducibility
            length: Number of moves (None for default)
            animation: Whether to animate the scramble

        Returns:
            The generated scramble algorithm
        """
        ...


class Scrambler(ScramblerProtocol):
    """Implementation of ScramblerProtocol."""

    def __init__(self, app: "AbstractApp") -> None:
        self._app = app

    def scramble(
        self,
        what: ScrambleWhat,
        seed: int | None = None,
        length: int | None = None,
        animation: bool = False,
    ) -> Alg:
        """Generate and apply a scramble algorithm."""
        from cube.domain.algs.Algs import Algs
        from cube.domain.algs.SeqAlg import SeqAlg

        rng = Random(seed)
        if length is None:
            length = rng.randint(3, 7) if what == ScrambleWhat.WHOLE_CUBE else rng.randint(20, 40)

        # Build move pool based on flags - use actual Alg instances
        moves: list[Alg] = []
        if ScrambleWhat.WHOLE_CUBE in what:
            for whole_alg in [Algs.X, Algs.Y, Algs.Z]:
                moves.extend([whole_alg, whole_alg.inv(), whole_alg * 2])
        if ScrambleWhat.FACE in what:
            for face_alg in [Algs.R, Algs.L, Algs.U, Algs.D, Algs.F, Algs.B]:
                moves.extend([face_alg, face_alg.inv(), face_alg * 2])
        if ScrambleWhat.SLICE in what:
            for slice_alg in [Algs.M, Algs.E, Algs.S]:
                moves.extend([slice_alg, slice_alg.inv(), slice_alg * 2])

        if not moves:
            raise ValueError(f"No moves available for scramble type: {what}")

        # Generate scramble
        algs = [rng.choice(moves) for _ in range(length)]

        alg = SeqAlg(f"scramble_{what.name}_{seed}", *algs)
        self._app.op.play(alg, animation=animation)
        return alg
