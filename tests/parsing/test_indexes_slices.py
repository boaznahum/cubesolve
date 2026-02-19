"""Tests for slice index operations."""
import pytest

from cube.domain.algs import Algs
from cube.application.AbstractApp import AbstractApp
from cube.domain.model.CubeQueries2 import CubeQueries2


def test_slice_play_and_inverse():
    """Test that playing a slice algorithm and its inverse returns to original state."""
    n = 8

    app = AbstractApp.create_app(n)
    cube = app.cube

    alg = Algs.scramble(cube.size, 4)
    alg.play(cube)

    state = CubeQueries2(cube).get_sate()

    slices = [1, 2, 5, 6]
    slice_alg = Algs.M[slices]

    slice_alg.play(cube)
    slice_alg.prime.play(cube)

    assert cube.cqr.compare_state(state)
