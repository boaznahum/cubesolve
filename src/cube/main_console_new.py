"""
Console-based entry point for the Cube Solver.

This module uses the console backend for text-based rendering.
All CLI options are inherited from main_any_backend.

Note: The original main_console/main_c.py is a standalone console
application. This module uses the unified backend architecture.

Usage:
    python -m cube.main_console_new
    python -m cube.main_console_new --debug-all
    python -m cube.main_console_new --quiet
"""
import sys
from cube.main_any_backend import main as main_any


def main():
    """Main entry point for the console-based interface."""
    # Insert default backend and disable animation if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=console")
    # Console doesn't support animation
    if "--no-animation" not in sys.argv:
        sys.argv.append("--no-animation")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
