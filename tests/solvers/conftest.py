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

from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    pass

# =============================================================================
# Test Configuration
# =============================================================================

# Cube sizes to test (start with 3, can extend to [3, 4, 5] later)
CUBE_SIZES: list[int] = [3, 4, 5, 8]

# GUI keyboard scramble seeds (keys 0-9) - same as ScrambleCommand(0-9)
GUI_SCRAMBLE_SEEDS: list[int] = list(range(10))  # 0, 1, 2, ..., 9

# Additional test seeds for extra coverage
ADDITIONAL_SCRAMBLE_SEEDS: list[int] = [101, 202, 303]

# All predefined scramble seeds
PREDEFINED_SCRAMBLE_SEEDS: list[int] = GUI_SCRAMBLE_SEEDS + ADDITIONAL_SCRAMBLE_SEEDS


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

def skip_if_not_supported(solver_name: SolverName, cube_size: int) -> None:
    """Skip test if solver doesn't support this cube size."""
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
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
