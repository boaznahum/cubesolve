"""Tests for algorithm transformation by whole-cube rotations.

Verifies T(W, A) = WA such that W' A W ≡ WA.
"""
import pytest

from cube.domain.algs.Algs import Algs
from cube.domain.algs.alg_transform import (
    FacePermutation,
    compute_permutation,
    transform,
    transform_by_permutation,
)
from cube.domain.model._elements import AxisName
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from tests.test_utils import _test_sp
from tests.utils._alg_utils import assert_algs_equivalent


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FacePermutation unit tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestFacePermutation:

    def test_identity(self):
        p = FacePermutation.identity()
        for f in FaceName:
            assert p(f) == f

    def test_y_single(self):
        """Y: F→L, L→B, B→R, R→F, U→U, D→D"""
        p = FacePermutation.from_axis(AxisName.Y, 1)
        assert p(FaceName.F) == FaceName.L
        assert p(FaceName.L) == FaceName.B
        assert p(FaceName.B) == FaceName.R
        assert p(FaceName.R) == FaceName.F
        assert p(FaceName.U) == FaceName.U
        assert p(FaceName.D) == FaceName.D

    def test_y_prime(self):
        """Y' (n=-1 → n%4=3): F→R, R→B, B→L, L→F"""
        p = FacePermutation.from_axis(AxisName.Y, -1)
        assert p(FaceName.F) == FaceName.R
        assert p(FaceName.R) == FaceName.B
        assert p(FaceName.B) == FaceName.L
        assert p(FaceName.L) == FaceName.F

    def test_x_single(self):
        """X: F→U, U→B, B→D, D→F, R→R, L→L"""
        p = FacePermutation.from_axis(AxisName.X, 1)
        assert p(FaceName.F) == FaceName.U
        assert p(FaceName.U) == FaceName.B
        assert p(FaceName.B) == FaceName.D
        assert p(FaceName.D) == FaceName.F
        assert p(FaceName.R) == FaceName.R
        assert p(FaceName.L) == FaceName.L

    def test_z_single(self):
        """Z: U→R, R→D, D→L, L→U, F→F, B→B"""
        p = FacePermutation.from_axis(AxisName.Z, 1)
        assert p(FaceName.U) == FaceName.R
        assert p(FaceName.R) == FaceName.D
        assert p(FaceName.D) == FaceName.L
        assert p(FaceName.L) == FaceName.U
        assert p(FaceName.F) == FaceName.F
        assert p(FaceName.B) == FaceName.B

    def test_y2_is_double(self):
        """Y2: F→B, B→F, L→R, R→L"""
        p = FacePermutation.from_axis(AxisName.Y, 2)
        assert p(FaceName.F) == FaceName.B
        assert p(FaceName.B) == FaceName.F
        assert p(FaceName.L) == FaceName.R
        assert p(FaceName.R) == FaceName.L

    def test_four_rotations_is_identity(self):
        for axis in AxisName:
            p = FacePermutation.from_axis(axis, 4)
            assert p.is_identity(), f"{axis} * 4 should be identity"

    def test_compose_y_y_prime_is_identity(self):
        y = FacePermutation.from_axis(AxisName.Y, 1)
        yp = FacePermutation.from_axis(AxisName.Y, -1)
        result = y.then(yp)
        assert result.is_identity()

    def test_compose_is_associative(self):
        x = FacePermutation.from_axis(AxisName.X, 1)
        y = FacePermutation.from_axis(AxisName.Y, 1)
        z = FacePermutation.from_axis(AxisName.Z, 1)
        # (X then Y) then Z == X then (Y then Z)
        left = x.then(y).then(z)
        right = x.then(y.then(z))
        for f in FaceName:
            assert left(f) == right(f)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# compute_permutation tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestComputePermutation:

    def test_single_y_prime(self):
        p = compute_permutation(Algs.Y.prime)
        assert p(FaceName.F) == FaceName.R

    def test_single_x(self):
        p = compute_permutation(Algs.X)
        assert p(FaceName.F) == FaceName.U

    def test_y2(self):
        p = compute_permutation(Algs.Y * 2)
        assert p(FaceName.F) == FaceName.B

    def test_sequence_y_x(self):
        """Y then X: F →(Y) L →(X) L (X doesn't move L)"""
        p = compute_permutation(Algs.Y + Algs.X)
        assert p(FaceName.F) == FaceName.L  # Y sends F→L, X keeps L

    def test_rejects_non_whole_cube(self):
        with pytest.raises(ValueError, match="whole-cube rotations"):
            compute_permutation(Algs.R)

    def test_noop(self):
        p = compute_permutation(Algs.NOOP)
        assert p.is_identity()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: face moves
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformFaceMoves:

    def test_y_prime_f_is_r(self):
        """User's example: T(Y', F) = R"""
        result = transform(Algs.Y.prime, Algs.F)
        assert str(result) == "R"

    def test_y_prime_r_is_b(self):
        result = transform(Algs.Y.prime, Algs.R)
        assert str(result) == "B"

    def test_y_prime_b_is_l(self):
        result = transform(Algs.Y.prime, Algs.B)
        assert str(result) == "L"

    def test_y_prime_l_is_f(self):
        result = transform(Algs.Y.prime, Algs.L)
        assert str(result) == "F"

    def test_y_prime_u_unchanged(self):
        result = transform(Algs.Y.prime, Algs.U)
        assert str(result) == "U"

    def test_x_f_is_u(self):
        result = transform(Algs.X, Algs.F)
        assert str(result) == "U"

    def test_z_u_is_r(self):
        result = transform(Algs.Z, Algs.U)
        assert str(result) == "R"

    def test_preserves_prime(self):
        """T(Y', F') = R'"""
        result = transform(Algs.Y.prime, Algs.F.prime)
        assert str(result) == "R'"

    def test_preserves_double(self):
        """T(Y', F2) = R2"""
        result = transform(Algs.Y.prime, Algs.F * 2)
        assert_algs_equivalent(result, Algs.R * 2, cube_size=3)

    def test_identity_rotation(self):
        """T(identity, A) = A"""
        result = transform(Algs.NOOP, Algs.R)
        assert str(result) == "R"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: slice moves
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformSliceMoves:

    def test_y_prime_m_is_s(self):
        """M rotates like L. Y' sends L→F. S rotates like F. So M → S."""
        result = transform(Algs.Y.prime, Algs.M)
        assert_algs_equivalent(result, Algs.S, cube_size=3)

    def test_y_prime_s_is_m_prime(self):
        """S rotates like F. Y' sends F→R. R is opposite of L (M's face).
        So S → M' (negated direction)."""
        result = transform(Algs.Y.prime, Algs.S)
        assert_algs_equivalent(result, Algs.M.prime, cube_size=3)

    def test_y_prime_e_unchanged(self):
        """E rotates like D. Y' keeps D fixed. So E → E."""
        result = transform(Algs.Y.prime, Algs.E)
        assert_algs_equivalent(result, Algs.E, cube_size=3)

    def test_x_e_is_s(self):
        """E rotates like D. X sends D→F. S rotates like F. So E → S."""
        result = transform(Algs.X, Algs.E)
        assert_algs_equivalent(result, Algs.S, cube_size=3)

    def test_x_m_unchanged(self):
        """M rotates like L. X keeps L fixed. So M → M."""
        result = transform(Algs.X, Algs.M)
        assert_algs_equivalent(result, Algs.M, cube_size=3)

    def test_z_m_is_e_prime(self):
        """M rotates like L. Z sends L→U. U is opposite of D (E's face).
        So M → E' (negated)."""
        result = transform(Algs.Z, Algs.M)
        assert_algs_equivalent(result, Algs.E.prime, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: wide moves
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformWideMoves:

    def test_y_prime_rw_is_bw(self):
        """Y' sends R→B, so Rw → Bw"""
        result = transform(Algs.Y.prime, Algs.Rw)
        assert_algs_equivalent(result, Algs.Bw, cube_size=5)

    def test_x_fw_is_uw(self):
        """X sends F→U, so Fw → Uw"""
        result = transform(Algs.X, Algs.Fw)
        assert_algs_equivalent(result, Algs.Uw, cube_size=5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: whole-cube rotations within A
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformWholeCubeMoves:

    def test_y_prime_x_stays_x(self):
        """X rotates like R. Y' sends R→B. B is opposite of F (Z's face).
        So X → Z' (negated)."""
        result = transform(Algs.Y.prime, Algs.X)
        assert_algs_equivalent(result, Algs.Z.prime, cube_size=3)

    def test_x_y_becomes_z(self):
        """Y rotates like U. X sends U→B. B is opposite of F (Z's face).
        So Y → Z' (negated)."""
        result = transform(Algs.X, Algs.Y)
        assert_algs_equivalent(result, Algs.Z.prime, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: sequences
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformSequences:

    def test_sexy_move_under_y_prime(self):
        """T(Y', R U R' U') should be equivalent to B R B' R'
        (Y' maps R→B and U→U)"""
        sexy = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        result = transform(Algs.Y.prime, sexy)
        expected = Algs.B + Algs.U + Algs.B.prime + Algs.U.prime
        assert_algs_equivalent(result, expected, cube_size=3)

    def test_transform_preserves_algorithm_effect(self):
        """T(Y', R U R' U') under Y' conjugation should equal R U R' U'"""
        sexy = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        transformed = transform(Algs.Y.prime, sexy)
        # Identity: W' A W = WA → Y (R U R' U') Y' = transformed
        conjugated = Algs.Y + sexy + Algs.Y.prime
        assert_algs_equivalent(conjugated, transformed, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Conjugation identity verification: W' A W ≡ T(W, A)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestConjugationIdentity:
    """Verify the core identity: W' A W produces the same cube state as T(W, A)."""

    @pytest.mark.parametrize("w,a", [
        (Algs.Y.prime, Algs.F),
        (Algs.Y.prime, Algs.R),
        (Algs.Y.prime, Algs.U),
        (Algs.X, Algs.F),
        (Algs.X, Algs.U),
        (Algs.Z, Algs.R),
        (Algs.Z, Algs.U),
        (Algs.Y * 2, Algs.F),
        (Algs.X.prime, Algs.D),
    ])
    def test_conjugation_equals_transform_single_moves(self, w, a):
        """W' A W should produce the same state as T(W, A)."""
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    @pytest.mark.parametrize("w,a", [
        (Algs.Y.prime, Algs.M),
        (Algs.Y.prime, Algs.S),
        (Algs.X, Algs.E),
        (Algs.Z, Algs.M),
    ])
    def test_conjugation_equals_transform_slice_moves(self, w, a):
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    @pytest.mark.parametrize("w", [
        Algs.Y.prime,
        Algs.X,
        Algs.Z,
        Algs.Y * 2,
    ])
    def test_conjugation_equals_transform_sequence(self, w):
        """Verify identity holds for a multi-move algorithm."""
        a = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime  # sexy move
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    @pytest.mark.parametrize("w", [
        Algs.Y.prime,
        Algs.X,
        Algs.Z,
    ])
    def test_conjugation_on_5x5(self, w):
        """Verify identity holds on 5x5 cubes too."""
        a = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Push-through identity: A W = W T(W, A)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPushThroughIdentity:
    """Verify: A W = W T(W, A) — rotations can be pushed through algorithms."""

    @pytest.mark.parametrize("w,a", [
        (Algs.Y.prime, Algs.F),
        (Algs.Y.prime, Algs.R),
        (Algs.X, Algs.F),
        (Algs.Z, Algs.U),
    ])
    def test_push_through_single(self, w, a):
        wa = transform(w, a)
        # a + w should equal w + wa
        left = a + w
        right = w + wa
        assert_algs_equivalent(left, right, cube_size=3)

    def test_push_through_sequence(self):
        w = Algs.Y.prime
        a = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        wa = transform(w, a)
        left = a + w
        right = w + wa
        assert_algs_equivalent(left, right, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Composed rotations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestComposedRotations:

    def test_y_prime_then_x(self):
        """Compose Y' then X and verify the identity still holds."""
        w = Algs.Y.prime + Algs.X
        a = Algs.F
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    def test_multiple_rotations(self):
        """Y' X Z applied to a sequence."""
        w = Algs.Y.prime + Algs.X + Algs.Z
        a = Algs.R + Algs.U + Algs.F
        wa = transform(w, a)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    def test_double_y(self):
        """Y2 applied to F should give B."""
        result = transform(Algs.Y * 2, Algs.F)
        assert_algs_equivalent(result, Algs.B, cube_size=3)
