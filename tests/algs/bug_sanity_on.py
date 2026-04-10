"""Test for sanity check functionality."""
import pytest

from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from tests.test_utils import StubServiceProvider


def test_sanity_check_enabled():
    """Test basic operation with sanity check enabled."""
    sp = StubServiceProvider()
    sp.config.check_cube_sanity = True

    cube = Cube(3, sp=sp)

    alg = Algs.U
    alg.play(cube)

    # If we get here without exception, sanity check passed
    assert True
