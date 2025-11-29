"""
Tkinter-based GUI entry point for the Cube Solver.

This module uses the tkinter backend for 2D isometric rendering.

Usage:
    python -m cube.main_tkinter
"""
import sys
from cube.main_any_backend import run_with_backend


def main():
    """Main entry point for the tkinter-based GUI."""
    return run_with_backend("tkinter")


if __name__ == '__main__':
    sys.exit(main())
