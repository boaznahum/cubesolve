"""
Test derivation of _TRANSFORMATION_TABLE from slice geometry.

This test verifies that we can derive the transformation table dynamically
using symbolic corner analysis instead of relying on the hardcoded table.

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
        layout = cube.layout
        mismatches: list[str] = []
        matches = 0

        for (source, target), expected in _TRANSFORMATION_TABLE.items():
            derived = layout.derive_transform_type(source, target)

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
        derived = cube.layout.derive_transform_type(source, target)

        print(f"\n({source.name}, {target.name}):")
        print(f"  Expected: {expected}")
        print(f"  Derived:  {derived}")

        assert derived == expected

    def test_derive_returns_none_for_same_face(self, cube: Cube):
        """Test that same face returns None."""
        for face in FaceName:
            result = cube.layout.derive_transform_type(face, face)
            assert result is None, f"Expected None for {face} -> {face}"

    def test_derive_handles_opposite_faces(self, cube: Cube):
        """Test that opposite faces return correct transforms (via 2 rotations)."""
        # Expected from hardcoded table:
        # F↔B: ROT_180 (via M slice, two 90° rotations)
        # U↔D: IDENTITY (via M or S slice, two 90° rotations)
        # L↔R: IDENTITY (via E or S slice, two 90° rotations)
        opposite_expected = {
            (FaceName.F, FaceName.B): TransformType.ROT_180,
            (FaceName.B, FaceName.F): TransformType.ROT_180,
            (FaceName.U, FaceName.D): TransformType.IDENTITY,
            (FaceName.D, FaceName.U): TransformType.IDENTITY,
            (FaceName.L, FaceName.R): TransformType.IDENTITY,
            (FaceName.R, FaceName.L): TransformType.IDENTITY,
        }
        for (source, target), expected in opposite_expected.items():
            result = cube.layout.derive_transform_type(source, target)
            assert result == expected, f"Expected {expected} for {source} -> {target}, got {result}"
