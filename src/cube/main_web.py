"""
Web browser-based GUI entry point for the Cube Solver.

This module uses the web backend which renders the cube in a browser
via WebSocket communication.

Usage:
    python -m cube.main_web
    python -m cube.main_web --debug-all
    python -m cube.main_web --quiet
    python -m cube.main_web --cube-size 5
"""
import sys
from cube.main_any_backend import main as main_any


def main():
    """Main entry point for the web-based GUI."""
    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=web")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
