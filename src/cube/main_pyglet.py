"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for OpenGL 3D rendering.

Usage:
    python -m cube.main_pyglet
"""
import sys
from cube.main_any_backend import run_with_backend


def main():
    """Main entry point for the pyglet-based GUI."""
    return run_with_backend("pyglet")


if __name__ == '__main__':
    sys.exit(main())
