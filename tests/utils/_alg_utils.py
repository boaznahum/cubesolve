"""
Algorithm comparison utilities for tests.

Provides robust methods to verify two algorithms are semantically equivalent
by comparing their effects on cube state.
"""
from cube.domain.algs.Alg import Alg
from cube.domain.algs.Scramble import scramble
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


def assert_algs_equivalent(alg1: Alg, alg2: Alg, cube_size: int, *, expect_equal: bool = True) -> None:
    """Assert that two algorithms produce the same (or different) cube state.

    Verification method:
    1. Scramble two cubes identically, apply alg1 to one and alg2 to the other,
       verify they reach the same (or different) state.
    2. (Only when expect_equal=True) Scramble a cube, apply alg1 then alg2 inverse,
       verify it returns to the scrambled state.

    Args:
        alg1: First algorithm
        alg2: Second algorithm
        cube_size: Size of the cube to test on
        expect_equal: If True, assert states match. If False, assert they differ.
    """
    scramble_alg = scramble(cube_size, seed=42, n=20)

    # Method 1: scramble + alg1 vs scramble + alg2 → compare states
    cube1 = Cube(cube_size, sp=_test_sp)
    cube2 = Cube(cube_size, sp=_test_sp)

    scramble_alg.play(cube1)
    scramble_alg.play(cube2)

    alg1.play(cube1)
    alg2.play(cube2)

    s1 = cube1.cqr.get_sate()
    s2 = cube2.cqr.get_sate()
    states_equal = cube1.cqr.compare_states(s1, s2)

    if expect_equal:
        assert states_equal, (
            f"Algs produce different states on {cube_size}x{cube_size}: "
            f"'{alg1}' vs '{alg2}'"
        )
    else:
        assert not states_equal, (
            f"Algs should produce different states on {cube_size}x{cube_size}: "
            f"'{alg1}' vs '{alg2}'"
        )
        return  # No point checking method 2 when expecting different

    # Method 2: scramble + alg1 + alg2' → back to scrambled state
    cube3 = Cube(cube_size, sp=_test_sp)
    scramble_alg.play(cube3)
    s_scrambled = cube3.cqr.get_sate()

    alg1.play(cube3)
    alg2.inv().play(cube3)

    s_after = cube3.cqr.get_sate()
    assert cube3.cqr.compare_states(s_scrambled, s_after), (
        f"alg1 + alg2' does not return to scrambled state on {cube_size}x{cube_size}: "
        f"'{alg1}' vs '{alg2}'"
    )
