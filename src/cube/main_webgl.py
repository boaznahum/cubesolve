"""
WebGL browser-based GUI entry point for the Cube Solver.

This module uses the webgl backend which renders the cube entirely
client-side using Three.js. The server sends cube state updates
instead of per-frame rendering commands.

Usage:
    python -m cube.main_webgl
    python -m cube.main_webgl --debug-all
    python -m cube.main_webgl --quiet
    python -m cube.main_webgl --cube-size 5
"""
import sys

from cube.main_any_backend import main as main_any


def main():
    """Main entry point for the WebGL-based GUI."""
    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=webgl")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
