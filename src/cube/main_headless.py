"""
Headless entry point for the Cube Solver.

This module uses the headless backend for testing and automation.
Delegates to main_any_backend with --backend=headless.

Useful for:
- Unit testing
- Benchmarking solver algorithms
- Batch processing / scripting
- CI/CD pipelines

Usage:
    python -m cube.main_headless --key-sequence="1?q"
"""
import sys
from cube.main_any_backend import main as any_main


def main():
    """Main entry point for headless operation."""
    sys.argv.extend(["--backend", "headless"])
    return any_main()


if __name__ == '__main__':
    sys.exit(main() or 0)
