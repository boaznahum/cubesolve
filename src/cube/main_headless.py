"""
Headless entry point for the Cube Solver.

This module uses the headless backend for testing and automation.
All CLI options are inherited from main_any_backend.

Useful for:
- Unit testing
- Benchmarking solver algorithms
- Batch processing / scripting
- CI/CD pipelines

Usage:
    python -m cube.main_headless
    python -m cube.main_headless --key-sequence="1?Q"
    python -m cube.main_headless --debug-all
    python -m cube.main_headless --quiet
"""
import sys

from cube.main_any_backend import main as main_any


def main():
    """Main entry point for headless operation."""
    # Insert default backend if not specified
    if "--backend" not in sys.argv and "-b" not in sys.argv:
        sys.argv.insert(1, "--backend=headless")
    return main_any()


if __name__ == '__main__':
    sys.exit(main())
