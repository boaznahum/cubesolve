"""
Test that R[1, 2, 3] tuple slice syntax is supported.
This test was written due to pyright warning that only slice object is supported.
"""
import pytest

from cube.algs import Algs


def test_tuple_slice_syntax():
    """Test that R[1, 2, 3] tuple syntax works."""
    R = Algs.R

    Rx = R[1, 2, 3]

    # Should be able to convert to string without error
    result = str(Rx)
    assert result is not None
