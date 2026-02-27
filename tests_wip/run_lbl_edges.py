"""
Script to run LBL edge solver and display cube state.

Run with: python -m tests.solvers.run_lbl_edges
"""
from __future__ import annotations

from cube.application.AbstractApp import AbstractApp
from cube.domain.model import Color
from cube.domain.solver import Solvers
from cube.utils.text_cube_viewer import print_cube


def main():
    cube_size = 5
    seed = 0  # This seed fails in tests

    print(f"Creating {cube_size}x{cube_size} cube...")
    app = AbstractApp.create_app(cube_size=cube_size)
    cube = app.cube

    # Create Reducer solver (LayerByLayerNxNSolver)
    solver = Solvers.reducer(app.op)

    print(f"Scrambling with seed {seed}...")
    app.scramble(seed, None, animation=False, verbose=False)

    print("\n=== BEFORE SOLVE ===")
    print_cube(cube)

    print(f"\nis_solved before: {solver.is_solved}")

    print("\nSolving...")
    solver.solve(debug=None, animation=False)

    print("\n=== AFTER SOLVE ===")
    print_cube(cube)

    print(f"\nis_solved after: {solver.is_solved}")

    # Get orthogonal edges (edges between side faces, not on L1 or L6)
    l1_face = cube.color_2_face(Color.WHITE)
    l1_opposite = l1_face.opposite
    orthogonal_edges = [e for e in cube.edges
                        if not e.on_face(l1_face) and not e.on_face(l1_opposite)]

    print(f"\nOrthogonal edges: {[e.name for e in orthogonal_edges]}")

    # Check orthogonal edges
    print("\n=== ORTHOGONAL EDGE STATUS ===")
    unsolved_edges = []
    for edge in orthogonal_edges:
        if not edge.is3x3:
            unsolved_edges.append(edge.name)
            print(f"  UNSOLVED: {edge.name}")

    if unsolved_edges:
        print(f"\nUnsolved orthogonal edges: {unsolved_edges}")
    else:
        print("\nAll orthogonal edges are is3x3 (paired)!")

    # Check all wings match_faces on orthogonal edges
    print("\n=== WING MATCH_FACES STATUS (orthogonal edges only) ===")
    for edge in orthogonal_edges:
        for i, wing in enumerate(edge.all_slices):
            if not wing.match_faces:
                print(f"  Wing {edge.name}[{i}] NOT match_faces: colors={wing.colors_id}")


if __name__ == "__main__":
    main()
