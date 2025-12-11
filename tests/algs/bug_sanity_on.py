"""Test for sanity check functionality."""
import pytest

from cube.application import _config as config
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from tests.conftest import _test_sp


def test_sanity_check_enabled():
    """Test basic operation with sanity check enabled."""
    config.CHECK_CUBE_SANITY = True

    cube = Cube(3, sp=_test_sp)

    alg = Algs.U
    alg.play(cube)

    # If we get here without exception, sanity check passed
    assert True
