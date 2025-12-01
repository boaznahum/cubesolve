"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for OpenGL 3D rendering.
All CLI options are inherited from main_any_backend.

Usage:
    python -m cube.main_pyglet
    python -m cube.main_pyglet --debug-all
    python -m cube.main_pyglet --quiet
    python -m cube.main_pyglet --cube-size 5
"""
import sys
from cube.main_any_backend import main as main_any


def main():
    """Main entry point for the pyglet-based GUI."""
    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=pyglet")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
