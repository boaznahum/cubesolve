import pytest

from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube import config


@pytest.fixture(autouse=True)
def reset_sanity_config():
    """Reset sanity config before each test to ensure clean state."""
    original = config.CHECK_CUBE_SANITY
    yield
    config.CHECK_CUBE_SANITY = original


@pytest.mark.parametrize("cube_size", [3, 5])
@pytest.mark.parametrize("sanity_check", [True, False])
def test_scramble_and_solve(cube_size: int, sanity_check: bool):
    """Test that a scrambled cube can be solved correctly."""
    config.CHECK_CUBE_SANITY = sanity_check

    app = AbstractApp.create_non_default(cube_size, animation=False)
    cube = app.cube

    alg = Algs.scramble(cube.size, 4)
    alg.play(cube)

    result = app.slv.solve()

    assert cube.solved, f"Cube of size {cube_size} should be solved"

    # Log solve details (visible with pytest -v)
    print(f"\nCube size: {cube_size}, Sanity: {sanity_check}")
    print(f"  corner swap: {result.was_corner_swap}")
    print(f"  even edge parity: {result.was_even_edge_parity}")
    print(f"  partial edge parity: {result.was_partial_edge_parity}")
    print(f"  move count: {app.op.count}")


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_scramble_by_seed_and_solve(seed: int):
    """
    Test scramble with specific seeds and solve - mirrors GUI test sequences.

    This test uses the same scramble seeds as the GUI tests to ensure
    the solver works correctly for these specific scramble patterns.

    Matches GUI test: GUIKeys.SCRAMBLE_1 + GUIKeys.SOLVE + GUIKeys.QUIT
    Which calls: app.scramble(seed, None, animation=False) then app.slv.solve()
    """
    app = AbstractApp.create_non_default(cube_size=3, animation=False)

    # Use app.scramble() same as GUI - this resets op and uses op.play()
    app.scramble(scramble_key=seed, scramble_size=None, animation=False, verbose=True)

    result = app.slv.solve(animation=False)

    assert app.cube.solved, f"Cube should be solved after scramble seed {seed}"

    print(f"\nScramble seed {seed} test:")
    print(f"  corner swap: {result.was_corner_swap}")
    print(f"  even edge parity: {result.was_even_edge_parity}")
    print(f"  partial edge parity: {result.was_partial_edge_parity}")
    print(f"  move count: {app.op.count}")


