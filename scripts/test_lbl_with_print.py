#!/usr/bin/env python3
"""Test script for LBL solver with console cube printing.

Solves Layer 1 and first slice, printing the cube at each stage.
"""

import sys
sys.path.insert(0, "src")

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep
from cube.utils.text_cube_viewer import print_cube


def main():
    # Create 5x5 cube
    size = 5
    seed = 42

    print(f"\n{'='*60}")
    print(f"LBL Solver Test - {size}x{size} cube, seed={seed}")
    print(f"{'='*60}\n")

    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    cube = app.cube

    # Print solved cube
    print_cube(cube, "Initial (solved)")

    # Scramble
    app.scramble(seed, None, animation=False, verbose=False)
    print_cube(cube, f"After scramble (seed={seed})")

    # Create solver
    solver = LayerByLayerNxNSolver(app.op)

    # Solve Layer 1 centers
    print("\n>>> Solving Layer 1 centers...")
    solver.solve(what=SolveStep.LBL_L1_Ctr, animation=False)
    print_cube(cube, "After Layer 1 centers")

    # Solve Layer 1 edges (pairing)
    print("\n>>> Solving Layer 1 edges (pairing)...")
    solver2 = LayerByLayerNxNSolver(app.op)
    solver2.solve(what=SolveStep.L1x, animation=False)
    print_cube(cube, "After Layer 1 cross (centers + edges paired + positioned)")

    # Solve Layer 1 complete
    print("\n>>> Solving Layer 1 complete (corners)...")
    solver3 = LayerByLayerNxNSolver(app.op)
    solver3.solve(what=SolveStep.LBL_L1, animation=False)
    print_cube(cube, "After Layer 1 complete")

    # Solve slice centers (first slice only)
    print("\n>>> Solving slice centers (first slice)...")
    solver4 = LayerByLayerNxNSolver(app.op)
    solver4.solve(what=SolveStep.LBL_SLICES_CTR, animation=False)
    print_cube(cube, "After slice centers (first slice)")

    # Print solver status
    print(f"\nSolver status: {solver4.status}")
    print(f"\n{'='*60}")
    print("Done!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
