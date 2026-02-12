"""Shared fixtures and utilities for Big LBL solver tests.

Scrambles: Uses same seeds as test_all_solvers.py (0-9, 101, 202, 303, random)
Cube sizes: Skips even cubes for Big LBL (not fully tested)
"""
from __future__ import annotations

import time
from random import Random

import pytest

# =============================================================================
# Scramble Configuration (same as test_all_solvers.py)
# =============================================================================

# GUI keyboard scramble seeds (keys 0-9)
GUI_SCRAMBLE_SEEDS: list[int] = list(range(10))  # 0, 1, 2, ..., 9

# Additional test seeds for extra coverage, ond ones that we find in random seed
L1_FULL_FAILURES_SEED=[137658025, 1794630359, 1838264046]
ADDITIONAL_SCRAMBLE_SEEDS: list[int] = [101, 202, 303, 124826159] + L1_FULL_FAILURES_SEED

# All predefined scramble seeds
PREDEFINED_SCRAMBLE_SEEDS: list[int] = GUI_SCRAMBLE_SEEDS + ADDITIONAL_SCRAMBLE_SEEDS

# Cube sizes to test (odd only for Big LBL, even not fully supported)
CUBE_SIZES_ODD: list[int] = [3, 5, 7]
CUBE_SIZES_EVEN: list[int] = [4, 6, 8, 10, 12]
CUBE_SIZES_ALL: list[int] = [3, 4, 5, 6, 7, 8]
N_RANDOM_SEEDS = 1000 # zero when we detect in above seeds


def get_scramble_params() -> list[tuple[str, int]]:
    """Generate scramble parameters for test parametrization.

    Random seeds are generated at import time using a UUID-based RNG.
    Each random seed appears in the test name (e.g. rnd_1839271), so
    if a test fails you can copy the seed into ADDITIONAL_SCRAMBLE_SEEDS
    to reproduce it permanently.
    """
    params: list[tuple[str, int]] = []
    for seed in PREDEFINED_SCRAMBLE_SEEDS:
        params.append((f"seed_{seed}", seed))

    # Seed from current minute — deterministic across xdist workers (they start
    # within the same second), but varies between test sessions.
    base_seed = int(time.time()) // 60
    rng = Random(base_seed)
    for _ in range(N_RANDOM_SEEDS):
        seed = rng.randint(0, 2**31 - 1)
        params.append((f"rnd_{seed}", seed))

    return params


def skip_even_cubes(cube_size: int) -> None:
    """Skip test for even cube sizes (Big LBL doesn't fully support them)."""
    if cube_size != 3 and cube_size % 2 == 0:
        pytest.skip("Big LBL: Even cubes not fully tested")
