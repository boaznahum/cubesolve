"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for rendering.
Delegates to main_any_backend with --backend=pyglet.

Usage:
    python -m cube.main_pyglet
"""
import sys
from cube.main_any_backend import main as any_main


def main():
    """Main entry point for the pyglet-based GUI."""
    sys.argv.extend(["--backend", "pyglet"])
    return any_main()


if __name__ == '__main__':
    sys.exit(main() or 0)
