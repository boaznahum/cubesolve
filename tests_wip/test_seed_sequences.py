"""Test the seed sequence loading functionality."""
from __future__ import annotations

import pytest

from tests_wip.seed_sequences import load_seeds, list_seed_files


def test_load_seeds_from_example() -> None:
    """Test loading seeds from example file."""
    # Load first 10 seeds from example_20.txt
    seeds = load_seeds("example_20", 10)
    assert len(seeds) == 10
    assert all(isinstance(s, int) for s in seeds)
    assert all(0 <= s < 2**31 for s in seeds)


def test_load_seeds_exact_count() -> None:
    """Test loading exactly all seeds."""
    seeds = load_seeds("example_20.txt", 20)
    assert len(seeds) == 20


def test_load_seeds_too_many() -> None:
    """Test requesting more seeds than available fails."""
    with pytest.raises(ValueError, match="only contains 20 seeds"):
        load_seeds("example_20", 100)


def test_load_seeds_file_not_found() -> None:
    """Test loading from non-existent file fails."""
    with pytest.raises(FileNotFoundError, match="Seed file not found"):
        load_seeds("nonexistent_999", 10)


def test_list_seed_files() -> None:
    """Test listing available seed files."""
    files = list_seed_files()
    assert isinstance(files, list)

    # Should at least have the example file
    filenames = [name for name, _ in files]
    assert "example_20.txt" in filenames

    # Check counts are correct
    for filename, count in files:
        if filename == "example_20.txt":
            assert count == 20
