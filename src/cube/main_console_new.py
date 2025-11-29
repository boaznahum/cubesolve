"""
Console-based entry point for the Cube Solver.

This module uses the console backend for text-based rendering.
Delegates to main_any_backend with --backend=console.

Note: The original main_console/main_c.py is a standalone console
application. This module uses the unified backend architecture.

Usage:
    python -m cube.main_console_new
"""
import sys
from cube.main_any_backend import main as any_main


def main():
    """Main entry point for the console-based interface."""
    # Console doesn't support animation
    sys.argv.extend(["--backend", "console", "--no-animation"])
    return any_main()


if __name__ == '__main__':
    sys.exit(main() or 0)
