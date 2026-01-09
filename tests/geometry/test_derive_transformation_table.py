"""
Test derivation of _TRANSFORMATION_TABLE from slice geometry.

This test verifies that we can derive the transformation table dynamically
using CubeWalkingInfo instead of relying on the hardcoded table.

Issue #55: Replace hard-coded lookup tables with mathematical derivation
"""

from __future__ import annotations

import pytest

from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.geometric.Face2FaceTranslator import (
    TransformType,
    _TRANSFORMATION_TABLE,
)
from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry
from tests.test_utils import _test_sp


class TestDeriveTransformationTable:
    """Test that we can derive the transformation table from geometry."""

    @pytest.fixture
    def cube(self) -> Cube:
        """Create a test cube."""
        return Cube(5, sp=_test_sp)

    def test_derive_all_entries(self, cube: Cube):
        """
        Compare derived transforms against the hardcoded table.

        This test verifies that our derivation algorithm produces
        the same results as the empirically-derived table.
        """
        mismatches: list[str] = []
        matches = 0

        for (source, target), expected in _TRANSFORMATION_TABLE.items():
            derived = _CubeLayoutGeometry.derive_transform_type(cube, source, target)

            if derived is None:
                mismatches.append(
                    f"({source.name}, {target.name}): Expected {expected.name}, got None"
                )
            elif derived != expected:
                mismatches.append(
                    f"({source.name}, {target.name}): Expected {expected.name}, got {derived.name}"
                )
            else:
                matches += 1

        # Report results
        print(f"\nMatches: {matches}/{len(_TRANSFORMATION_TABLE)}")
        if mismatches:
            print("Mismatches:")
            for m in mismatches:
                print(f"  {m}")

        assert not mismatches, f"Found {len(mismatches)} mismatches:\n" + "\n".join(mismatches)

    def test_derive_single_entry_debug(self, cube: Cube):
        """Debug test for a single entry - useful for investigating mismatches."""
        source, target = FaceName.F, FaceName.U
        expected = _TRANSFORMATION_TABLE.get((source, target))
        derived = _CubeLayoutGeometry.derive_transform_type(cube, source, target)

        print(f"\n({source.name}, {target.name}):")
        print(f"  Expected: {expected}")
        print(f"  Derived:  {derived}")

        assert derived == expected
