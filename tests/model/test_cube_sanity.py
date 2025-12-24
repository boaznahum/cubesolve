"""Tests for CubeSanity validation.

These tests verify that CubeSanity.do_sanity correctly detects invalid cube states,
particularly wrong color distributions.
"""

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.Cube3x3Colors import Cube3x3Colors, EdgeColors, CornerColors
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model._part import EdgeName, CornerName
from tests.test_utils import TestServiceProvider


# Shared service provider for all tests
_sp = TestServiceProvider()


class TestCubeSanityDetectsInvalidCubes:
    """Test that sanity check catches cubes with wrong color distribution."""

    def test_sanity_passes_on_solved_cube(self) -> None:
        """Sanity check should pass on a valid solved cube."""
        cube = Cube(size=3, sp=_sp)
        assert cube.is_sanity(force_check=True)

    def test_sanity_passes_after_scramble(self) -> None:
        """Sanity check should pass after scrambling (colors are just moved)."""
        cube = Cube(size=3, sp=_sp)
        # Do some moves
        cube.front.rotate(1)
        cube.right.rotate(1)
        cube.up.rotate(-1)
        assert cube.is_sanity(force_check=True)

    def test_sanity_fails_with_duplicate_edge_color(self) -> None:
        """Sanity should fail when an edge has a color that creates invalid distribution.

        If we change the FU edge (normally Blue-Yellow) to have White-Yellow,
        we now have two White-Yellow edges (FU and one of the original WY edges),
        and we're missing Blue-Yellow. This breaks edge distribution.

        This test mimics how the solver creates shadow cubes:
        1. Get valid colors as snapshot
        2. Modify to create invalid state
        3. Apply to a FRESH cube - sanity check should fail
        """
        # Get valid colors from a source cube
        source_cube = Cube(size=3, sp=_sp)
        colors_3x3 = source_cube.get_3x3_colors()

        # Modify FU edge: change its F-face color from Blue to White
        # This creates a duplicate (White-Yellow edge already exists)
        invalid_colors = colors_3x3.with_edge_color(EdgeName.FU, FaceName.F, Color.WHITE)

        # Create a FRESH target cube (like shadow cube in solver)
        target_cube = Cube(size=3, sp=_sp)

        # Applying invalid colors to fresh cube should fail sanity
        with pytest.raises(AssertionError, match="Invalid cube state"):
            target_cube.set_3x3_colors(invalid_colors)

    def test_sanity_fails_with_duplicate_corner(self) -> None:
        """Sanity should fail when a corner has colors that create a duplicate.

        If we change FRU corner to have same colors as another corner,
        we have duplicate corners which is invalid.

        This test mimics how the solver creates shadow cubes:
        1. Get valid colors as snapshot
        2. Modify to create invalid state
        3. Apply to a FRESH cube - sanity check should fail
        """
        # Get valid colors from a source cube
        source_cube = Cube(size=3, sp=_sp)
        colors_3x3 = source_cube.get_3x3_colors()

        # Change FRU corner (Blue-Red-Yellow) to look like FLU (Blue-Orange-Yellow)
        # by changing R face from Red to Orange
        invalid_colors = colors_3x3.with_corner_color(CornerName.FRU, FaceName.R, Color.ORANGE)

        # Create a FRESH target cube (like shadow cube in solver)
        target_cube = Cube(size=3, sp=_sp)

        # Applying invalid colors to fresh cube should fail sanity
        with pytest.raises(AssertionError, match="Invalid cube state"):
            target_cube.set_3x3_colors(invalid_colors)

    def test_sanity_fails_with_impossible_corner_colors(self) -> None:
        """Sanity should fail when corner has impossible color combination.

        A corner can never have opposite colors (White-Yellow, Red-Orange, Blue-Green)
        because opposite faces never share a corner.

        This test mimics how the solver creates shadow cubes:
        1. Get valid colors as snapshot
        2. Modify to create invalid state
        3. Apply to a FRESH cube - sanity check should fail
        """
        # Get valid colors from a source cube
        source_cube = Cube(size=3, sp=_sp)
        colors_3x3 = source_cube.get_3x3_colors()

        # Change FRU corner to have White-Yellow (opposites!) on two of its faces
        # FRU normally is Blue-Red-Yellow
        # Change F (Blue) to White - now it's White-Red-Yellow
        # Change U (Yellow) to White - now it's White-Red-White (two whites!)
        invalid_colors = colors_3x3.with_corner_color(CornerName.FRU, FaceName.F, Color.WHITE)
        invalid_colors = invalid_colors.with_corner_color(CornerName.FRU, FaceName.U, Color.WHITE)

        # Create a FRESH target cube (like shadow cube in solver)
        target_cube = Cube(size=3, sp=_sp)

        # Applying invalid colors to fresh cube should fail sanity
        with pytest.raises(AssertionError, match="Invalid cube state"):
            target_cube.set_3x3_colors(invalid_colors)

    def test_sanity_passes_on_4x4(self) -> None:
        """Sanity should pass on valid 4x4 cube."""
        cube = Cube(size=4, sp=_sp)
        assert cube.is_sanity(force_check=True)

        # After moves
        cube.front.rotate(1)
        cube.right.rotate(1)
        assert cube.is_sanity(force_check=True)

    def test_sanity_passes_on_5x5(self) -> None:
        """Sanity should pass on valid 5x5 cube."""
        cube = Cube(size=5, sp=_sp)
        assert cube.is_sanity(force_check=True)


class TestCubeSanityForceCheck:
    """Test the force_check parameter behavior."""

    def test_force_check_runs_regardless_of_config(self) -> None:
        """force_check=True should run validation even with check disabled."""
        cube = Cube(size=3, sp=_sp)

        # Even if we could disable config, force_check should still work
        result = cube.is_sanity(force_check=True)
        assert result is True

    def test_is_sanity_returns_bool(self) -> None:
        """is_sanity should return True/False, not raise."""
        cube = Cube(size=3, sp=_sp)

        result = cube.is_sanity(force_check=True)
        assert isinstance(result, bool)
        assert result is True
