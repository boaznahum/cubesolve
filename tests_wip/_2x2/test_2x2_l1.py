"""Tests for 2x2 beginner solver — Layer 1 (corners).

Verifies that L1 correctly solves all 4 first-layer corners
across multiple scrambles.
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
class TestL1:

    def test_l1_solves_first_layer(self, scramble_seed: int) -> None:
        """After L1.solve(), all 4 corners on the L1 face should match."""
        app = AbstractApp.create_app(cube_size=2)
        solver = Solver2x2Beginner(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)

        # Cube should not be solved after scramble
        assert not app.cube.solved, f"Cube still solved after scramble (seed={scramble_seed})"

        solver._l1.solve()

        assert solver._l1.is_solved, (
            f"L1 not solved (seed={scramble_seed})"
        )

    def test_l1_is_solved_after_scramble_and_re_solve(self, scramble_seed: int) -> None:
        """Solver is stateless: scramble again, solve again, still works."""
        app = AbstractApp.create_app(cube_size=2)
        solver = Solver2x2Beginner(app.op, app.op.sp.logger)

        # First solve
        app.scramble(scramble_seed, None, animation=False, verbose=False)
        solver._l1.solve()
        assert solver._l1.is_solved

        # Scramble again with a different seed
        app.scramble(scramble_seed + 1000, None, animation=False, verbose=False)

        # is_solved should reflect the NEW cube state (likely False)
        # (could be True by luck, so we just re-solve and verify)
        solver._l1.solve()
        assert solver._l1.is_solved, (
            f"L1 not solved after re-scramble (seed={scramble_seed + 1000})"
        )
