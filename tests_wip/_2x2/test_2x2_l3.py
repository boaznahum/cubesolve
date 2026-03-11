"""Tests for 2x2 beginner solver — Layer 3 (permute + orient).

Verifies that L3Permute and L3Orient correctly solve the last layer
after L1 is solved, across multiple scrambles.
Order: permute first (position corners), then orient (twist yellow up).
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver._2x2_beginner.Solver2x2Beginner import Solver2x2Beginner


# GUI keyboard scramble seeds (same as keys 0-9)
SCRAMBLE_SEEDS: list[int] = list(range(10))

# Additional seeds for extra coverage
ADDITIONAL_SEEDS: list[int] = [101, 202, 303, 42, 999, 12345]

ALL_SEEDS: list[int] = SCRAMBLE_SEEDS + ADDITIONAL_SEEDS


@pytest.mark.parametrize(
    "scramble_seed",
    ALL_SEEDS,
    ids=lambda s: f"seed_{s}",
)
class TestL3:

    def test_l3_permute_solves_after_l1(self, scramble_seed: int) -> None:
        """After L1 + L3Permute, all top corners should be in correct positions."""
        app = AbstractApp.create_app(cube_size=2)
        solver = Solver2x2Beginner(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)
        solver._l1.solve()
        assert solver._l1.is_solved, f"L1 not solved (seed={scramble_seed})"

        solver._l3_permute.solve()
        assert solver._l3_permute.is_solved, (
            f"L3 Permute not solved (seed={scramble_seed})"
        )

    def test_l3_orient_solves_after_permute(self, scramble_seed: int) -> None:
        """After L1 + L3Permute + L3Orient, all corners should have yellow up."""
        app = AbstractApp.create_app(cube_size=2)
        solver = Solver2x2Beginner(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)
        solver._l1.solve()
        assert solver._l1.is_solved

        solver._l3_permute.solve()
        assert solver._l3_permute.is_solved

        solver._l3_orient.solve()
        assert solver._l3_orient.is_solved, (
            f"L3 Orient not solved (seed={scramble_seed})"
        )

    def test_full_solve(self, scramble_seed: int) -> None:
        """After full solve, cube should be solved."""
        app = AbstractApp.create_app(cube_size=2)
        solver = Solver2x2Beginner(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)
        assert not app.cube.solved

        solver._l1.solve()
        solver._l3_permute.solve()
        solver._l3_orient.solve()

        assert app.cube.solved, f"Cube not solved after full solve (seed={scramble_seed})"
