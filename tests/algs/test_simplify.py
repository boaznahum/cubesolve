"""Tests for algorithm simplification and flattening."""
import pytest
from typing import Iterable

from cube.application import _config as config
from cube.domain import algs
from cube.domain.algs import Algs, Alg
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


def _compare_two_algs(cube_size: int, algs1: Iterable[Alg], algs2: Iterable[Alg]):
    """Compare two sequences of algorithms produce the same cube state."""
    cube = Cube(cube_size, sp=_test_sp)

    for alg in algs1:
        alg.play(cube)

    s1 = cube.cqr.get_sate()

    cube.reset()
    for alg in algs2:
        alg.play(cube)

    s2 = cube.cqr.get_sate()

    assert cube.cqr.compare_states(s1, s2)


def _compare_inv(cube_size: int, algs_list: Iterable[Alg]):
    """Test that applying algorithms then their inverse returns to original state."""
    cube = Cube(cube_size, sp=_test_sp)

    scramble = Algs.scramble(cube_size)
    scramble.play(cube)

    s1 = cube.cqr.get_sate()

    for alg in algs_list:
        alg.play(cube)

    inv = Algs.seq_alg(None, *algs_list).inv()
    inv.play(cube)

    assert cube.cqr.compare_state(s1)


def _test_simplify(alg: Alg, cube_size: int):
    """Test that simplifying an algorithm produces equivalent results."""
    cube = Cube(cube_size, sp=_test_sp)
    scramble = Algs.scramble(cube.size, "1")

    simplified = alg.simplify()

    _compare_two_algs(cube_size, (scramble, alg), (scramble, simplified))
    _compare_inv(cube_size, (scramble, alg))

    return simplified


def _test_flatten(alg: Alg, cube_size: int):
    """Test that flattening an algorithm produces equivalent results."""
    config.CHECK_CUBE_SANITY = False

    cube = Cube(cube_size, sp=_test_sp)
    scramble = Algs.scramble(cube.size, "1")

    scramble.play(cube)
    alg.play(cube)
    s1 = cube.cqr.get_sate()

    flat = alg.flatten_alg()

    cube.reset()
    scramble.play(cube)
    flat.play(cube)

    assert cube.cqr.compare_state(s1)


def _test_simplify_flatten(alg: Alg, cube_size: int):
    """Test both simplify and flatten on an algorithm."""
    _test_simplify(alg, cube_size)
    _test_flatten(alg, cube_size)


class TestSimplify:
    """Tests for algorithm simplification."""

    def test_simplify_random_sequence(self):
        """Test simplification of a random sequence."""
        cube_size = 8
        config.CHECK_CUBE_SANITY = False

        alg = Algs.scramble(cube_size, seq_length=5000, seed=None)
        _test_simplify(alg, cube_size)

    def test_simplify_inverse(self):
        """Test simplification of an inverse algorithm."""
        cube_size = 8
        config.CHECK_CUBE_SANITY = False

        alg = (Algs.R * 2).inv()

        _test_simplify(alg, cube_size)
        _test_flatten(alg, cube_size)


class TestFlatten:
    """Tests for algorithm flattening."""

    def test_flatten_slice_move(self):
        """Test flattening of slice moves."""
        cube_size = 5
        alg = Algs.MM[2:2].prime * 2
        _test_flatten(alg, cube_size)

    def test_flatten_complex_sequence(self):
        """Test flattening of complex rotation sequences."""
        cube_size = 7

        cube = Cube(cube_size, sp=_test_sp)
        inv = cube.inv

        c = 2
        cc = 4

        rotate_on_cell = Algs.MM[inv(c) + 1:inv(c) + 1]
        rotate_on_second = Algs.MM[inv(cc) + 1:inv(cc) + 1]

        on_front_rotate = Algs.F.prime

        r1_mul = 2

        _algs = [
            rotate_on_cell.prime * r1_mul,
            on_front_rotate,
            rotate_on_second.prime * r1_mul,
            on_front_rotate.prime,
            rotate_on_cell * r1_mul,
            on_front_rotate,
            rotate_on_second * r1_mul,
            on_front_rotate.prime
        ]

        _test_flatten(algs.SeqAlg(None, *_algs), cube_size)
        _test_flatten(algs.SeqAlg(None, *_algs).inv(), cube_size)

    def test_flatten_scramble(self):
        """Test flattening of scramble algorithm."""
        cube_size = 7
        a = Algs.scramble(cube_size, "aaa")
        _test_flatten(a, cube_size)

    def test_flatten_adjacent_slices(self):
        """Test flattening of adjacent slice combinations."""
        cube_size = 7

        a = Algs.R[1:2] + Algs.R[2:3]
        _test_simplify_flatten(a, cube_size)

        a = Algs.R[1:2] + Algs.R[1:2]
        _test_simplify_flatten(a, cube_size)


class TestSimplifyFlatten:
    """Combined simplify and flatten tests."""

    def test_complex_sequence(self):
        """Test simplify/flatten on complex sequences."""
        cube = Cube(6, sp=_test_sp)

        alg = Algs.R[3:3] + Algs.D[3:4] + Algs.SS + Algs.L[2:2]
        _test_simplify_flatten(alg, cube.size)

        alg = Algs.B[5:5]
        _test_simplify_flatten(alg, cube.size)

        alg = Algs.R[3:3]
        _test_simplify_flatten(alg, cube.size)

    def test_total_simplify_inverse_cancels(self):
        """Test that a - a simplifies to empty."""
        cube_size = 5
        alg = Algs.scramble(cube_size)

        s = _test_simplify(alg - alg, cube_size)
        _compare_two_algs(cube_size, (Algs.no_op(),), (s,))


class TestDisjointSliceMerge:
    """Tests for merging disjoint slices during simplification."""

    def test_disjoint_face_slices_same_n(self):
        """R[1,2]*1 + R[3,4]*1 -> R[1,2,3,4]*1 (one alg instead of two)."""
        cube_size = 7
        alg = Algs.R[1:2] + Algs.R[3:4]
        s = _test_simplify(alg, cube_size)
        # Should merge into a single alg
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"

    def test_disjoint_face_slices_explicit_indices(self):
        """R[1,3]*1 + R[2,4]*1 -> R[1,2,3,4]*1."""
        cube_size = 7
        alg = Algs.R[1, 3] + Algs.R[2, 4]
        s = _test_simplify(alg, cube_size)
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"

    def test_disjoint_face_slices_same_n_prime(self):
        """R[1:2]' + R[3:4]' -> R[1,2,3,4]' (prime moves merge too)."""
        cube_size = 7
        alg = Algs.R[1:2].prime + Algs.R[3:4].prime
        s = _test_simplify(alg, cube_size)
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"

    def test_disjoint_face_slices_double(self):
        """R[1:2]*2 + R[3:4]*2 -> R[1,2,3,4]*2."""
        cube_size = 7
        alg = (Algs.R[1:2] * 2) + (Algs.R[3:4] * 2)
        s = _test_simplify(alg, cube_size)
        assert s.count() == 2, f"Expected 2 (half turn), got {s.count()}: {s}"

    def test_disjoint_different_n_no_merge(self):
        """R[1:2]*2 + R[3:4]*1 should NOT merge (n=2 vs n=1, different mod 4)."""
        cube_size = 7
        # R[1:2]*2 flattens to 2x R[1:2]*1, which combines to R[1:2] with n=2
        # Then R[3:4]*1 has n=1 → different n%4, no merge
        alg = (Algs.R[1:2] * 2) + Algs.R[3:4]
        s = _test_simplify(alg, cube_size)
        # R[1:2] n=2 and R[3:4] n=1 can't merge → count = 2 + 1 = 3
        assert s.count() == 3, f"Expected 3 (2+1), got {s.count()}: {s}"

    def test_overlapping_slices_no_merge(self):
        """R[1:3]*1 + R[2:4]*1 should NOT merge (overlapping slices)."""
        cube_size = 7
        alg = Algs.R[1:3] + Algs.R[2:4]
        s = _test_simplify(alg, cube_size)
        # Overlapping - should stay as 2 algs
        assert s.count() == 2, f"Expected 2, got {s.count()}: {s}"

    def test_different_faces_no_merge(self):
        """R[1:2]*1 + L[3:4]*1 should NOT merge (different faces)."""
        cube_size = 7
        alg = Algs.R[1:2] + Algs.L[3:4]
        s = _test_simplify(alg, cube_size)
        assert s.count() == 2, f"Expected 2, got {s.count()}: {s}"

    def test_cascading_merge_three_algs(self):
        """R[1,2]*1 + R[3,4]*1 + R[5]*1 -> R[1,2,3,4,5]*1."""
        cube_size = 8  # need enough slices
        alg = Algs.R[1:2] + Algs.R[3:4] + Algs.R[5:5]
        s = _test_simplify(alg, cube_size)
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"

    def test_disjoint_slice_alg_merge(self):
        """M[1]*1 + M[2]*1 -> M[1,2]*1 for slice algs."""
        cube_size = 7
        alg = Algs.MM[1:1] + Algs.MM[2:2]
        s = _test_simplify(alg, cube_size)
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"

    def test_congruent_n_mod4_merge(self):
        """R[1:2]*1 + R[3:4]*5 should merge (both ≡ 1 mod 4)."""
        cube_size = 7
        alg = Algs.R[1:2] + (Algs.R[3:4] * 5)
        s = _test_simplify(alg, cube_size)
        # n=5 ≡ 1 mod 4, so both are effectively *1 → merge to single alg
        assert s.count() == 1, f"Expected 1 move, got {s.count()}: {s}"
