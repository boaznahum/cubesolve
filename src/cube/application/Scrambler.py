"""Scrambler protocol for generating scramble algorithms."""

from __future__ import annotations

from enum import Flag, auto
from random import Random
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.domain.algs import Alg


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


class Scrambler:
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

        # Build move pool based on flags
        moves: list[str] = []
        if ScrambleWhat.WHOLE_CUBE in what:
            moves.extend(["x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"])
        if ScrambleWhat.FACE in what:
            moves.extend(["R", "R'", "R2", "L", "L'", "L2",
                          "U", "U'", "U2", "D", "D'", "D2",
                          "F", "F'", "F2", "B", "B'", "B2"])
        if ScrambleWhat.SLICE in what:
            moves.extend(["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"])

        if not moves:
            raise ValueError(f"No moves available for scramble type: {what}")

        # Generate scramble
        algs = []
        for _ in range(length):
            move = rng.choice(moves)
            algs.append(Algs.parse(move))

        alg = SeqAlg(f"scramble_{what.name}_{seed}", *algs)
        self._app.op.play(alg, animation=animation)
        return alg
