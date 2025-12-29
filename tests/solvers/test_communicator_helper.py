"""
Tests for CommunicatorHelper.
"""

from cube.domain.model.Cube import Cube
from cube.domain.solver.common.big_cube.CommunicatorHelper import CommunicatorHelper
from tests.test_utils import _test_sp


def test_create_helper_with_7x7_cube():
    """Create a 7x7 cube and instantiate the helper."""
    cube = Cube(7, sp=_test_sp)
    helper = CommunicatorHelper(cube)

    assert helper.n_slices == 5
