"""
Test LBL edge solver without GUI/animation.

This test isolates the edge solver to determine if bugs are in the solver logic
itself or in the animation/GUI handling.
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.model import Color
from cube.domain.solver import Solvers

from .conftest import CUBE_SIZES_ALL, get_scramble_params, skip_even_cubes


def check_edge_wings_on_row_solved(cube, target_face, l1_face, row_distance_from_l1: int) -> list[str]:
    """
    Check if edge wings on a specific row are solved.

    Returns list of error messages for unsolved wings (empty if all solved).
    """
    errors = []

    edge_info = cube.sized_layout.get_orthogonal_index_by_distance_from_face(
        target_face, l1_face, row_distance_from_l1
    )

    # Check both edges on this row
    for edge, index in [(edge_info.edge_one, edge_info.index_on_edge_one),
                        (edge_info.edge_two, edge_info.index_on_edge_two)]:
        wing = edge.get_slice(index)
        if not wing.match_faces:
            errors.append(
                f"Wing {wing.parent_name_and_index} on row {row_distance_from_l1} "
                f"not solved: colors={wing.colors_id}, match_faces={wing.match_faces}"
            )

    return errors


def get_orthogonal_edges(cube, l1_face):
    """
    Get edges orthogonal to L1 face (edges that don't touch L1 or its opposite).

    These are the 4 edges connecting the side faces.
    """
    l1_opposite = l1_face.opposite
    return [e for e in cube.edges
            if not e.on_face(l1_face) and not e.on_face(l1_opposite)]


def check_all_side_edges_solved(cube, l1_face) -> list[str]:
    """
    Check if all orthogonal edge wings are solved.

    Only checks edges ORTHOGONAL to L1 face (the 4 edges connecting side faces),
    not the edges on L1 or its opposite face.

    Returns list of error messages for unsolved wings.
    """
    errors = []

    for edge in get_orthogonal_edges(cube, l1_face):
        for wing in edge.all_slices:
            if not wing.match_faces:
                errors.append(
                    f"Wing {wing.parent_name_and_index} not solved: "
                    f"colors={wing.colors_id}, match_faces={wing.match_faces}"
                )

    return errors


class TestLBLEdges:
    """Test LBL solver edge handling without animation."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_ALL, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_solver_edges(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Test that LBL solver correctly solves edges without animation."""
        skip_even_cubes(cube_size)

        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        cube = app.cube

        solver = Solvers.lbl_big(app.op)

        app.scramble(actual_seed, None, animation=False, verbose=False)

        assert not solver.is_solved, f"Cube should be scrambled (size={cube_size}, scramble={scramble_name})"

        solver.solve(debug=False, animation=False)

        l1_face = cube.color_2_face(Color.WHITE)
        for edge in get_orthogonal_edges(cube, l1_face):
            assert edge.is3x3, (
                f"Edge {edge.name} not solved after LBL solver "
                f"(size={cube_size}, scramble={scramble_name})"
            )

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_ALL, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_edges_detailed(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Detailed test with edge state logging."""
        skip_even_cubes(cube_size)

        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        cube = app.cube

        solver = Solvers.lbl_big(app.op)

        app.scramble(actual_seed, None, animation=False, verbose=False)

        solver.solve(debug=False, animation=False)

        l1_face = cube.down
        unsolved_edges = []
        for edge in get_orthogonal_edges(cube, l1_face):
            if not edge.is3x3:
                unsolved_edges.append(edge.name)

        assert not unsolved_edges, (
            f"Unsolved edges after LBL: {unsolved_edges} (size={cube_size}, scramble={scramble_name})"
        )

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_ALL, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_solver_full_edges_check(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """
        Test full LBL solve with detailed edge checks after completion.

        This verifies all edges are properly paired on all 4 side faces.
        """
        skip_even_cubes(cube_size)

        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        cube = app.cube

        app.scramble(actual_seed, None, animation=False, verbose=False)

        solver = Solvers.lbl_big(app.op)

        solver.solve(debug=False, animation=False)

        l1_face = cube.down
        errors = check_all_side_edges_solved(cube, l1_face)

        assert not errors, (
            f"Edges not solved after full LBL solve: {errors} "
            f"(size={cube_size}, scramble={scramble_name})"
        )
