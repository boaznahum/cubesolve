"""
WebGL browser-based GUI entry point for the Cube Solver.

This module uses the webgl backend which renders the cube entirely
client-side using Three.js. The server sends cube state updates
instead of per-frame rendering commands.

Usage:
    python -m cube.main_webgl
    python -m cube.main_webgl --open-browser
    python -m cube.main_webgl --debug-all
    python -m cube.main_webgl --quiet
    python -m cube.main_webgl --cube-size 5
"""
import sys

from cube.main_any_backend import main as main_any


def main() -> int:
    """Main entry point for the WebGL-based GUI."""
    # Extract --open-browser before passing to main parser
    open_browser: bool = "--open-browser" in sys.argv
    if open_browser:
        sys.argv.remove("--open-browser")

    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=webgl")

    # Set flag for the event loop to pick up
    from cube.presentation.gui.backends.webgl import WebglEventLoop
    WebglEventLoop._default_open_browser = open_browser  # type: ignore[attr-defined]

    return main_any()


if __name__ == '__main__':
    sys.exit(main())
