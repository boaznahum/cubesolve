"""
Headless entry point for the Cube Solver.

This module uses the headless backend for testing and automation.

Useful for:
- Unit testing
- Benchmarking solver algorithms
- Batch processing / scripting
- CI/CD pipelines

Usage:
    python -m cube.main_headless

For key sequence injection, use main_any_backend directly:
    python -m cube.main_any_backend --backend=headless --key-sequence="1?Q"
"""
import sys
from cube.main_any_backend import run_with_backend


def main():
    """Main entry point for headless operation."""
    return run_with_backend("headless")


if __name__ == '__main__':
    sys.exit(main())
