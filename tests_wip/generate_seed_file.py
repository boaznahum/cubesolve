"""Generate seed sequence files for reproducible test runs.

Usage:
    python -m tests_wip.generate_seed_file <name> <count>

Example:
    python -m tests_wip.generate_seed_file failures_8x 100
    Creates: tests_wip/sequences/failures_8x_100.txt with 100 random seeds
"""
from __future__ import annotations

import sys
from pathlib import Path
from random import Random
import time


def generate_seed_file(name: str, count: int, base_seed: int | None = None) -> Path:
    """Generate a seed sequence file.

    Args:
        name: Name prefix for the file (e.g., "failures_8x")
        count: Number of seeds to generate
        base_seed: Optional seed for RNG (uses current time if None)

    Returns:
        Path to the created file

    The file format is simple text with one seed per line:
        # Generated: 2025-01-15 10:30:45
        # Base seed: 1234567890
        # Count: 100
        1234567890
        987654321
        ...
    """
    # Create sequences directory if it doesn't exist
    sequences_dir = Path(__file__).parent / "sequences"
    sequences_dir.mkdir(exist_ok=True)

    # Generate filename
    filename = sequences_dir / f"{name}_{count}.txt"

    # Generate seeds
    if base_seed is None:
        base_seed = int(time.time())

    rng = Random(base_seed)
    seeds = [rng.randint(0, 2**31 - 1) for _ in range(count)]

    # Write to file
    with open(filename, 'w') as f:
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Base seed: {base_seed}\n")
        f.write(f"# Count: {count}\n")
        for seed in seeds:
            f.write(f"{seed}\n")

    print(f"Created: {filename}")
    print(f"  Base seed: {base_seed}")
    print(f"  Seeds: {count}")

    return filename


def main() -> None:
    """Command-line interface."""
    if len(sys.argv) < 3:
        print("Usage: python -m tests_wip.generate_seed_file <name> <count> [base_seed]")
        print()
        print("Example:")
        print("  python -m tests_wip.generate_seed_file failures_8x 100")
        print("  python -m tests_wip.generate_seed_file edge_cases 50 12345")
        sys.exit(1)

    name = sys.argv[1]
    count = int(sys.argv[2])
    base_seed = int(sys.argv[3]) if len(sys.argv) > 3 else None

    generate_seed_file(name, count, base_seed)


if __name__ == "__main__":
    main()
