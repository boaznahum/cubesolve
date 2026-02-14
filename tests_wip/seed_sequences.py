"""Load seed sequences from files for reproducible testing.

This module provides utilities to load seed sequences from files in the
tests_wip/sequences/ directory. Seed files are text files with one seed
per line (ignoring comments starting with #).
"""
from __future__ import annotations

from pathlib import Path


def load_seeds(filename: str, n: int) -> list[int]:
    """Load up to n seeds from a seed sequence file.

    Args:
        filename: Name of file in tests_wip/sequences/
                 Can be:
                   - Full name: "s1_1000.txt" or "s1_1000"
                   - Base name: "s1" (will try to find "s1_<count>.txt")
        n: Number of seeds to load

    Returns:
        List of seeds (up to n seeds)

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If n > available seeds in file

    Example:
        # These are all equivalent:
        seeds = load_seeds("s1_1000", 100)      # Exact file name
        seeds = load_seeds("s1_1000.txt", 100)  # With extension
        seeds = load_seeds("s1", 1000)          # Base name, will find s1_1000.txt
    """
    # Find the file
    sequences_dir = Path(__file__).parent / "sequences"

    # Try multiple strategies to find the file
    candidates = []

    # Strategy 1: Exact filename (with or without .txt)
    if filename.endswith('.txt'):
        candidates.append(sequences_dir / filename)
        candidates.append(sequences_dir / filename[:-4])  # without .txt
    else:
        candidates.append(sequences_dir / f"{filename}.txt")
        candidates.append(sequences_dir / filename)

    # Strategy 2: Try filename_<n>.txt (generated file pattern)
    if not filename.endswith('.txt'):
        candidates.append(sequences_dir / f"{filename}_{n}.txt")

    # Find first existing file
    filepath = None
    for candidate in candidates:
        if candidate.exists():
            filepath = candidate
            break

    # Strategy 3: If still not found, try to find any file matching base pattern
    # For example: load_seeds("s1", 10) should find s1_1000.txt if it has enough seeds
    if filepath is None and not filename.endswith('.txt'):
        # Look for files matching pattern: filename_*.txt
        pattern_files = list(sequences_dir.glob(f"{filename}_*.txt"))
        if pattern_files:
            # Use the first one (they're sorted by default)
            filepath = pattern_files[0]

    if filepath is None:
        raise FileNotFoundError(
            f"Seed file not found for: {filename!r} with n={n}\n"
            f"Tried:\n" +
            "\n".join(f"  - {c.name}" for c in candidates) +
            f"\n\nAvailable files:\n" +
            "\n".join(f"  - {f.name}" for f in sequences_dir.glob("*.txt"))
        )

    # Read seeds from file (skip comment lines)
    seeds: list[int] = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                seeds.append(int(line))

    # Check we have enough seeds
    if n > len(seeds):
        raise ValueError(
            f"Requested {n} seeds but file {filepath.name} only contains {len(seeds)} seeds"
        )

    # Return first n seeds
    return seeds[:n]


def list_seed_files() -> list[tuple[str, int]]:
    """List all available seed files with their counts.

    Returns:
        List of (filename, count) tuples

    Example:
        for filename, count in list_seed_files():
            print(f"{filename}: {count} seeds")
    """
    sequences_dir = Path(__file__).parent / "sequences"

    if not sequences_dir.exists():
        return []

    files: list[tuple[str, int]] = []
    for filepath in sequences_dir.glob("*.txt"):
        # Count non-comment lines
        count = 0
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    count += 1
        files.append((filepath.name, count))

    return sorted(files)
