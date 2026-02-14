"""Shared fixtures and utilities for Big LBL solver tests.

Scrambles: Uses same seeds as test_all_solvers.py (0-9, 101, 202, 303, random)
Cube sizes: Skips even cubes for Big LBL (not fully tested)
"""
from __future__ import annotations

import time
from random import Random

import pytest

from tests_wip.seed_sequences import load_seeds

# =============================================================================
# Scramble Configuration (same as test_all_solvers.py)
# =============================================================================

# GUI keyboard scramble seeds (keys 0-9)
GUI_SCRAMBLE_SEEDS: list[int] = list(range(10))  # 0, 1, 2, ..., 9

# Additional test seeds for extra coverage, ond ones that we find in random seed
FULL_FAILURES_SEED=[
    # ☑️ Test reproducible,❌ not gui
 1781991940, # cube_size = 8, scramble_name = 'rnd_1781991940', scramble_seed = 1781991940 ☑️ ❌
 1037976487, # cube_size = 10, scramble_name = 'rnd_1037976487', scramble_seed = 1037976487
966854415, #cube_size = 10, scramble_name = 'rnd_966854415', scramble_seed = 966854415
1293174359, #cube_size = 10, scramble_name = 'rnd_1293174359', scramble_seed = 1293174359

1781991940, #cube_size = 8, scramble_name = 'seed_1781991940', scramble_seed = 1781991940
1263619961, # cube_size = 12, scramble_name = 'rnd_1263619961', scramble_seed = 1263619961 ☑️
1233752804, # cube_size = 12, scramble_name = 'rnd_1233752804', scramble_seed = 1233752804 ☑️
    ]

ADDITIONAL_SCRAMBLE_SEEDS: list[int] = [] + FULL_FAILURES_SEED

# All predefined scramble seeds
PREDEFINED_SCRAMBLE_SEEDS: list[int] = GUI_SCRAMBLE_SEEDS + ADDITIONAL_SCRAMBLE_SEEDS

# Cube sizes to test (odd only for Big LBL, even not fully supported)
CUBE_SIZES_ODD: list[int] = [3, 5, 7]
CUBE_SIZES_EVEN: list[int] = [4, 6, 8, 10, 12]
CUBE_SIZES_ALL: list[int] = [3, 4, 5, 6, 7, 8]
N_RANDOM_SEEDS =  0  # 10000 # zero when we detect in above seeds

# =============================================================================
# Seed Sequence Configuration
# =============================================================================
# Load seeds from pre-generated files in tests_wip/sequences/
# Set SEED_SEQUENCE_FILE to None to disable, or to a tuple (filename, count)
# to load count seeds from the specified file.
#
# Example:
#   SEED_SEQUENCE_CONFIG = ("failures_8x_100", 50)  # Load first 50 seeds
#   SEED_SEQUENCE_CONFIG = None                      # Disable
SEED_SEQUENCE_CONFIG: tuple[str, int] | None = ("s1", 500)  # ("example_100", 50)


def get_scramble_params() -> list[tuple[str, int]]:
    """Generate scramble parameters for test parametrization.

    Random seeds are generated at import time using a UUID-based RNG.
    Each random seed appears in the test name (e.g. rnd_1839271), so
    if a test fails you can copy the seed into ADDITIONAL_SCRAMBLE_SEEDS
    to reproduce it permanently.

    Additionally, loads seeds from SEED_SEQUENCE_CONFIG if configured.
    """
    params: list[tuple[str, int]] = []
    seen_seeds: set[int] = set()  # Track seeds to eliminate duplicates

    # Add predefined seeds
    for seed in PREDEFINED_SCRAMBLE_SEEDS:
        if seed not in seen_seeds:
            params.append((f"seed_{seed}", seed))
            seen_seeds.add(seed)

    # Load seeds from sequence file if configured
    if SEED_SEQUENCE_CONFIG is not None:
        filename, count = SEED_SEQUENCE_CONFIG
        try:
            file_seeds = load_seeds(filename, count)
            for seed in file_seeds:
                if seed not in seen_seeds:
                    # Use 'seq_' prefix to distinguish from other seeds
                    params.append((f"seq_{seed}", seed))
                    seen_seeds.add(seed)
        except (FileNotFoundError, ValueError) as e:
            # Warn but don't fail - tests can still run with other seeds
            print(f"Warning: Failed to load seed sequence: {e}")

    # Generate random seeds
    base_seed = int(time.time()) // 60
    rng = Random(base_seed)
    for _ in range(N_RANDOM_SEEDS):
        seed = rng.randint(0, 2**31 - 1)
        if seed not in seen_seeds:
            params.append((f"rnd_{seed}", seed))
            seen_seeds.add(seed)

    return params


def skip_even_cubes(cube_size: int) -> None:
    """Skip test for even cube sizes (Big LBL doesn't fully support them)."""
    if cube_size != 3 and cube_size % 2 == 0:
        pytest.skip("Big LBL: Even cubes not fully tested")
