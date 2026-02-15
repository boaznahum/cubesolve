"""Load seed sequences from files for reproducible testing.

This module provides utilities to load seed sequences from files in the
tests/sequences/ directory. Seed files are text files with one seed
per line (ignoring comments starting with #).
"""
from __future__ import annotations

from pathlib import Path


def load_seeds(filename: str, n: int) -> list[int]:
    """Load up to n seeds from a seed sequence file.

    File lookup strategies (in order):
    1. Exact match: Try "<filename>.txt" and "<filename>"
    2. Pattern match: Try "<filename>_<n>.txt" (generated file naming)
    3. Fallback: Find any file matching "<filename>_*.txt" (uses first match)

    Args:
        filename: Name of file in tests/sequences/
                 Can be:
                   - Full name: "s1_1000.txt" or "s1_1000" → finds s1_1000.txt
                   - Base name: "s1" → tries s1_<n>.txt, then any s1_*.txt
        n: Number of seeds to load

    Returns:
        List of seeds (up to n seeds)

    Raises:
        FileNotFoundError: If no matching file exists
        ValueError: If n > available seeds in file

    Examples:
        # Load 1000 seeds - tries s1_1000.txt (exact match)
        seeds = load_seeds("s1", 1000)

        # Load 100 seeds - tries s1_100.txt, then fallback to s1_1000.txt
        seeds = load_seeds("s1", 100)

        # Explicit filename
        seeds = load_seeds("s1_1000", 50)      # Exact: s1_1000.txt
        seeds = load_seeds("s1_1000.txt", 50)  # Exact: s1_1000.txt
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


def get_scramble_params(
    predefined_seeds: list[int],
    seed_sequence_config: tuple[str, int] | None = None
) -> list[tuple[str, int]]:
    """Generate scramble parameters combining predefined seeds and sequence file.

    This is the common implementation used by both tests/solvers/conftest.py
    and tests_wip/big_lbl_2/conftest.py.

    Args:
        predefined_seeds: List of predefined seeds to include
        seed_sequence_config: Optional (filename, count) tuple to load from tests/sequences/
                             Uses load_seeds() with smart file lookup:
                             1. Exact match: "<filename>.txt" or "<filename>"
                             2. Pattern match: "<filename>_<count>.txt" (generated file naming)
                             3. Fallback: Any "<filename>_*.txt" (uses first match)

                             Examples:
                               ("s1", 1000) → tries s1_1000.txt (exact), then s1.txt
                               ("s1", 100)  → tries s1_100.txt, then any s1_*.txt
                               ("example_20", 50) → tries example_20.txt exactly

    Returns:
        List of (name, seed) tuples with duplicates removed.
        Sequence seeds are prefixed with "seq_" (e.g., "seq_12345")

    Example:
        params = get_scramble_params(
            predefined_seeds=[0, 1, 2, 101, 202],
            seed_sequence_config=("s1", 200)  # Load 200 seeds from s1_*.txt
        )
        # Returns: [("seed_0", 0), ("seed_1", 1), ..., ("seq_12345", 12345), ...]
    """
    params: list[tuple[str, int]] = []
    seen_seeds: set[int] = set()

    # Add predefined seeds
    for seed in predefined_seeds:
        if seed not in seen_seeds:
            params.append((f"seed_{seed}", seed))
            seen_seeds.add(seed)

    # Load seeds from sequence file if configured
    if seed_sequence_config is not None:
        filename, count = seed_sequence_config
        try:
            file_seeds = load_seeds(filename, count)
            for seed in file_seeds:
                if seed not in seen_seeds:
                    # Use 'seq_' prefix to distinguish from predefined seeds
                    params.append((f"seq_{seed}", seed))
                    seen_seeds.add(seed)
        except (FileNotFoundError, ValueError) as e:
            # Warn but don't fail - tests can still run with other seeds
            print(f"Warning: Failed to load seed sequence: {e}")

    return params
