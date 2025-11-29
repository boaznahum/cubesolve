"""
Console-based entry point for the Cube Solver.

This module uses the console backend for text-based rendering.

Note: The original main_console/main_c.py is a standalone console
application. This module uses the unified backend architecture.

Usage:
    python -m cube.main_console_new
"""
import sys
from cube.main_any_backend import run_with_backend


def main():
    """Main entry point for the console-based interface."""
    # Console doesn't support animation
    return run_with_backend("console", animation=False)


if __name__ == '__main__':
    sys.exit(main())
