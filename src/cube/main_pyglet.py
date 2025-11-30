"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for OpenGL 3D rendering.

Usage:
    python -m cube.main_pyglet
    python -m cube.main_pyglet --debug-all
"""
import argparse
import sys
from cube.main_any_backend import run_with_backend


def main():
    """Main entry point for the pyglet-based GUI."""
    parser = argparse.ArgumentParser(description="Rubik's Cube Solver (pyglet)")
    parser.add_argument(
        "--debug-all",
        action="store_true",
        help="Enable debug_all mode for verbose logging"
    )
    parser.add_argument(
        "--cube-size", "-s",
        type=int,
        default=None,
        help="Cube size (default: 3)"
    )
    args = parser.parse_args()

    return run_with_backend("pyglet", debug_all=args.debug_all, cube_size=args.cube_size)


if __name__ == '__main__':
    sys.exit(main())
