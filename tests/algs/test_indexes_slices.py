"""Tests for slice index operations."""
import pytest

from cube.algs import Algs
from cube.app.AbstractApp import AbstractApp
from cube.model.CubeQueries2 import CubeQueries2


def test_slice_play_and_inverse():
    """Test that playing a slice algorithm and its inverse returns to original state."""
    n = 8

    app = AbstractApp.create_non_default(n, animation=False)
    cube = app.cube

    alg = Algs.scramble(cube.size, 4)
    alg.play(cube)

    state = CubeQueries2(cube).get_sate()

    slices = [1, 2, 5, 6]
    slice_alg = Algs.M[slices]

    slice_alg.play(cube)
    slice_alg.prime.play(cube)

    assert cube.cqr.compare_state(state)
