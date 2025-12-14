"""
Fixtures for solver tests.

Provides parametrization data for testing all solvers across:
- Multiple cube sizes
- Predefined reproducible scrambles (seeded)
- One unique random scramble per test session

Solver skip reasons are checked in priority order (None = supported, string = skip):
1. not_testable - skip all tests
2. only_3x3 - skip non-3x3 tests
3. skip_3x3 - skip 3x3 tests
4. skip_even - skip even-sized cube tests (4x4, 6x6, ...)
5. skip_odd - skip odd-sized cube tests (5x5, 7x7, ...)
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from cube.domain.solver.SolverName import SolverName, SolverMeta

if TYPE_CHECKING:
    pass

# =============================================================================
# Test Configuration
# =============================================================================

# Cube sizes to test (start with 3, can extend to [3, 4, 5] later)
CUBE_SIZES: list[int] = [3, 4, 5, 8]

# Predefined scramble seeds for reproducible tests
# Each seed produces the same scramble every time
PREDEFINED_SCRAMBLE_SEEDS: list[int] = [101, 202, 303]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def session_random_seed() -> int:
    """Generate a unique random seed for this test session.

    This seed is:
    - Unique per test session (won't repeat across runs)
    - Consistent within a session (all tests using it get same scramble)
    - Bounded to a reasonable int range for the Random class
    """
    return uuid.uuid4().int % (2**31)


@pytest.fixture
def all_solver_names() -> list[SolverName]:
    """Return all available solver names."""
    return list(SolverName)


# =============================================================================
# Solver Skip Logic
# =============================================================================

def check_solver_skip(solver_name: SolverName, cube_size: int) -> str | None:
    """
    Check if a solver should be skipped for a given cube size.

    Returns skip reason if should skip, None otherwise.

    Checks reasons in priority order:
    1. not_testable
    2. only_3x3
    3. skip_3x3
    4. skip_even
    5. skip_odd
    """
    meta: SolverMeta = solver_name.meta

    # 1. Check if not testable at all
    if meta.not_testable:
        return meta.not_testable

    # 2. Check if solver only supports 3x3
    if meta.only_3x3 and cube_size != 3:
        return meta.only_3x3

    # 3. Check if 3x3 should be skipped
    if meta.skip_3x3 and cube_size == 3:
        return meta.skip_3x3

    # 4. Check even-sized cubes (4x4, 6x6, 8x8, ...)
    if meta.skip_even and cube_size != 3 and cube_size % 2 == 0:
        return meta.skip_even

    # 5. Check odd-sized cubes > 3 (5x5, 7x7, 9x9, ...)
    if meta.skip_odd and cube_size != 3 and cube_size % 2 == 1:
        return meta.skip_odd

    return None


def skip_if_not_supported(solver_name: SolverName, cube_size: int) -> None:
    """Skip test if solver doesn't support this cube size."""
    skip_reason = check_solver_skip(solver_name, cube_size)
    if skip_reason:
        pytest.skip(skip_reason)


# =============================================================================
# Parametrization Helpers
# =============================================================================

def get_scramble_params() -> list[tuple[str, int | None]]:
    """Generate scramble parameters for test parametrization.

    Returns list of (name, seed) tuples:
    - Predefined seeds: ("seed_101", 101), ("seed_202", 202), etc.
    - Random: ("random", None) - actual seed comes from session_random_seed fixture
    """
    params: list[tuple[str, int | None]] = []

    # Add predefined scrambles
    for seed in PREDEFINED_SCRAMBLE_SEEDS:
        params.append((f"seed_{seed}", seed))

    # Add random scramble marker (actual seed injected via fixture)
    params.append(("random", None))

    return params


def get_solver_names() -> list[SolverName]:
    """Get all solver names for parametrization."""
    return list(SolverName)


def get_cube_sizes() -> list[int]:
    """Get all cube sizes for parametrization."""
    return CUBE_SIZES
