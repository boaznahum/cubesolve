"""
Tkinter-based GUI entry point for the Cube Solver.

This module uses the tkinter backend for 2D isometric rendering.
All CLI options are inherited from main_any_backend.

Usage:
    python -m cube.main_tkinter
    python -m cube.main_tkinter --debug-all
    python -m cube.main_tkinter --quiet
    python -m cube.main_tkinter --cube-size 5
"""
import sys
from cube.main_any_backend import main as main_any


def main():
    """Main entry point for the tkinter-based GUI."""
    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=tkinter")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
