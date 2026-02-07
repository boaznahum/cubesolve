"""Tests for LayerByLayerNxNSolver - Layer-by-Layer method for big cubes.

Currently only Layer 1 is implemented, so tests focus on:
- Layer 1 centers (SolveStep.LBL_L1_Ctr)
- Layer 1 cross (SolveStep.L1x) - centers + edges paired + edges positioned
- Layer 1 complete (SolveStep.LBL_L1) - centers + edges + corners
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep

from .conftest import CUBE_SIZES_ODD, get_scramble_params, skip_even_cubes


class TestLBLBigCubeSolver:
    """Test LayerByLayerNxNSolver with various cube sizes and scrambles."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_ODD, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_slices_ctr(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Test LBL_SLICES_CTR step solves middle slices."""
        skip_even_cubes(cube_size)

        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        app.scramble(actual_seed, None, animation=False, verbose=False)

        solver.solve(what=SolveStep.LBL_SLICES_CTR, debug=False, animation=False)

        assert solver._is_l2_slices_solved(), (
            f"L2 slices not solved (size={cube_size}, scramble={scramble_name})"
        )
    def test_single_e_slice_big_blocks(self) -> None:
        """Single E-slice rotation on 15x15 is solved efficiently.

        Instead of scrambling, rotate a single E slice near the center.
        This displaces one row of 13 center pieces on each equatorial face,
        creating a highly structured disruption.

        With pre-alignment optimization, the solver detects this is a simple
        rotation and reverses it directly (0 blocks needed). Without pre-alignment,
        it would use big blocks (7x1, 6x1, etc.).

        We avoid E[7] (the exact center slice) because it moves the face
        center piece, changing face.color and confusing the solver.
        E[6] is one slice below center — same effect without that issue.
        """
        app = AbstractApp.create_non_default(cube_size=15, animation=False)
        cube = app.cube

        # Rotate a single E slice near the center (not E[7] which moves face centers)
        Algs.E[6:6].play(cube)
        assert not cube.solved

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)
        solver.solve(what=SolveStep.LBL_SLICES_CTR, debug=False, animation=False)

        assert solver._is_l2_slices_solved(), "15x15 single E-slice not solved"

        stats = solver._lbl_slices._centers.get_statistics()

        if stats:
            # If blocks were used, verify big blocks were found
            max_block_size = max(stats.keys())
            assert max_block_size > 1, (
                f"Expected big blocks for structured single-slice disruption, "
                f"got only 1x1: {stats}"
            )
            parts = [f"{size}x1:{count}" for size, count in sorted(stats.items())]
            print(f"\n[15x15 E-slice test] Block statistics: {', '.join(parts)}")
        else:
            # Pre-alignment solved it directly — optimal outcome
            print("\n[15x15 E-slice test] Pre-alignment solved it (0 blocks needed)")

    @pytest.mark.parametrize("cube_size", [5], ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        [ ("f{s}", s) for s in range(0, 300) ],
        ids=lambda x: x if isinstance(x, str) else None,
    )
    # to diacover failing: we found: 9, 18, 42, 48, 138, 260
    # with sorting, 7, 89
    def test_lbl_slices_ctr_5x5(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Test LBL_SLICES_CTR step solves middle slices."""
        skip_even_cubes(cube_size)

        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        app.scramble(actual_seed, None, animation=False, verbose=False)

        solver.solve(what=SolveStep.LBL_SLICES_CTR, debug=False, animation=False)

        assert solver._is_l2_slices_solved(), (
            f"L2 slices not solved (size={cube_size}, scramble={scramble_name})"
        )
