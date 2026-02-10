"""Shared fixtures and utilities for Big LBL solver tests.

Scrambles: Uses same seeds as test_all_solvers.py (0-9, 101, 202, 303, random)
Cube sizes: Skips even cubes for Big LBL (not fully tested)
"""
from __future__ import annotations

import uuid

import pytest

# =============================================================================
# Scramble Configuration (same as test_all_solvers.py)
# =============================================================================

# GUI keyboard scramble seeds (keys 0-9)
GUI_SCRAMBLE_SEEDS: list[int] = list(range(10))  # 0, 1, 2, ..., 9

# Additional test seeds for extra coverage
ADDITIONAL_SCRAMBLE_SEEDS: list[int] = [101, 202, 303]

# All predefined scramble seeds
PREDEFINED_SCRAMBLE_SEEDS: list[int] = GUI_SCRAMBLE_SEEDS + ADDITIONAL_SCRAMBLE_SEEDS

# Cube sizes to test (odd only for Big LBL, even not fully supported)
CUBE_SIZES_ODD: list[int] = [3, 5, 7]
CUBE_SIZES_EVEN: list[int] = list(range(4, 12, 2))
CUBE_SIZES_ALL: list[int] = [3, 5, 7]


def get_scramble_params() -> list[tuple[str, int | None]]:
    """Generate scramble parameters for test parametrization."""
    params: list[tuple[str, int | None]] = []
    for seed in PREDEFINED_SCRAMBLE_SEEDS:
        params.append((f"seed_{seed}", seed))
    params.append(("random", None))
    return params


def skip_even_cubes(cube_size: int) -> None:
    """Skip test for even cube sizes (Big LBL doesn't fully support them)."""
    if cube_size != 3 and cube_size % 2 == 0:
        pytest.skip("Big LBL: Even cubes not fully tested")


@pytest.fixture(scope="session")
def session_random_seed() -> int:
    """Generate a unique random seed for this test session."""
    return uuid.uuid4().int % (2**31)
