"""Test for sanity check functionality."""
import pytest

from cube import config
from cube.algs import Algs
from cube.model.Cube import Cube


def test_sanity_check_enabled():
    """Test basic operation with sanity check enabled."""
    config.CHECK_CUBE_SANITY = True

    cube = Cube(3)

    alg = Algs.U
    alg.play(cube)

    # If we get here without exception, sanity check passed
    assert True
