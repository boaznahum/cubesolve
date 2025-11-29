"""
Tkinter-based GUI entry point for the Cube Solver.

This module uses the tkinter backend for 2D isometric rendering.
Delegates to main_any_backend with --backend=tkinter.

Usage:
    python -m cube.main_tkinter
"""
import sys
from cube.main_any_backend import main as any_main


def main():
    """Main entry point for the tkinter-based GUI."""
    sys.argv.extend(["--backend", "tkinter"])
    return any_main()


if __name__ == '__main__':
    sys.exit(main() or 0)
