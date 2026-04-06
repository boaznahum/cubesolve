"""Tests for algorithm transformation by whole-cube rotations.

═══════════════════════════════════════════════════════════════════════════
THEOREM (Algorithm Transformation by Whole-Cube Rotation)
═══════════════════════════════════════════════════════════════════════════

Let W = w₁ w₂ … wₙ be a sequence of whole-cube rotations (X, Y, Z and
their primes/multiples), and let A be any cube algorithm.

Define T(W, A) = WA as the algorithm obtained by remapping every atomic
move in A through the face permutation P_W induced by W.

Then the following identities hold on any NxN cube:

  (1) Conjugation:    W' A W  ≡  T(W, A)
  (2) Push-through:   A W     ≡  W T(W, A)
  (3) Composition:    T(W₁ W₂, A)  ≡  T(W₂, T(W₁, A))

where ≡ means "produces identical cube state from any starting position".

───────────────────────────────────────────────────────────────────────────
LEMMAS (used to establish the theorem)
───────────────────────────────────────────────────────────────────────────

Lemma 1 (Face Permutation):
    Each whole-cube rotation w ∈ {X, Y, Z, X', Y', Z', X2, Y2, Z2}
    induces a permutation P_w on the 6 face names {U, D, F, B, L, R}.
    The content movement tables are:
        X (like R): F→U→B→D→F,  R,L fixed
        Y (like U): F→L→B→R→F,  U,D fixed
        Z (like F): U→R→D→L→U,  F,B fixed
    Primes reverse the cycle. Doubles compose twice.

Lemma 2 (Permutation Composition):
    For W = w₁ w₂ … wₙ, the induced permutation is:
        P_W = P_wₙ ∘ P_wₙ₋₁ ∘ … ∘ P_w₁
    Applied left-to-right: P_W(f) = P_wₙ(…P_w₂(P_w₁(f))…)

Lemma 3 (Face Move Transform):
    For a face move A on face f with rotation count n:
        T(W, A) = face_move(P_W(f), n)
    The rotation count n (including sign for prime) is preserved because
    the whole-cube rotation preserves the orientation of the face relative
    to the viewer (CW from outside remains CW from outside).

Lemma 4 (Slice Move Transform):
    A slice S with rotation face r_S (M→L, E→D, S→F) transforms to:
        - If P_W(r_S) is itself a slice rotation face → same slice, same n
        - If P_W(r_S) is the OPPOSITE of a slice rotation face → that slice, negated n
    This is because slice rotation direction is defined relative to a face,
    and opposite faces have opposite "looking from outside" orientations.

Lemma 5 (Whole-Cube Rotation Transform):
    Same rule as Lemma 4, using axis faces (X→R, Y→U, Z→F) instead of
    slice rotation faces.

Lemma 6 (Sequence Homomorphism):
    T(W, A₁ A₂ … Aₖ) = T(W, A₁) T(W, A₂) … T(W, Aₖ)
    The transform distributes over sequences, because conjugation distributes:
        W' (A₁ A₂) W = (W' A₁ W)(W' A₂ W)

───────────────────────────────────────────────────────────────────────────
TEST STRATEGY
───────────────────────────────────────────────────────────────────────────

1. Unit tests: verify FacePermutation tables and composition (Lemmas 1-2)
2. Targeted tests: verify each move type transform rule (Lemmas 3-5)
3. Randomized tests: generate random W (whole-cube scrambles) and random A
   (full scrambles from the existing scramble generator), verify the
   conjugation and push-through identities hold on actual cubes (Theorem).
   This provides high-confidence black-box validation.
═══════════════════════════════════════════════════════════════════════════
"""
import pytest
from random import Random

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.algs.Scramble import scramble as cube_scramble
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
from cube.domain.algs.alg_transform import compute_permutation
from cube.domain.algs.face_permutation import FacePermutation
from cube.domain.model._elements import AxisName
from cube.domain.model.Cube import Cube
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Part import Part
from tests.test_utils import _test_sp
from tests.utils._alg_utils import assert_algs_equivalent


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers: random whole-cube rotation sequences
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# All atomic whole-cube rotations and their primes
_WHOLE_CUBE_MOVES: list[Alg] = [
    Algs.X, Algs.X.prime, Algs.X * 2,
    Algs.Y, Algs.Y.prime, Algs.Y * 2,
    Algs.Z, Algs.Z.prime, Algs.Z * 2,
]


def _random_whole_cube_sequence(seed: int, length: int = 5) -> Alg:
    """Generate a random whole-cube rotation sequence W.

    Draws from {X, X', X2, Y, Y', Y2, Z, Z', Z2} uniformly.
    Returns a SeqAlg of whole-cube moves.
    """
    rnd = Random(seed)
    moves = [rnd.choice(_WHOLE_CUBE_MOVES) for _ in range(length)]
    return SeqAlg(None, *moves)


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
        result = Algs.F.transform(Algs.Y.prime)
        assert str(result) == "R"

    def test_y_prime_r_is_b(self):
        result = Algs.R.transform(Algs.Y.prime)
        assert str(result) == "B"

    def test_y_prime_b_is_l(self):
        result = Algs.B.transform(Algs.Y.prime)
        assert str(result) == "L"

    def test_y_prime_l_is_f(self):
        result = Algs.L.transform(Algs.Y.prime)
        assert str(result) == "F"

    def test_y_prime_u_unchanged(self):
        result = Algs.U.transform(Algs.Y.prime)
        assert str(result) == "U"

    def test_x_f_is_u(self):
        result = Algs.F.transform(Algs.X)
        assert str(result) == "U"

    def test_z_u_is_r(self):
        result = Algs.U.transform(Algs.Z)
        assert str(result) == "R"

    def test_preserves_prime(self):
        """T(Y', F') = R'"""
        result = Algs.F.prime.transform(Algs.Y.prime)
        assert str(result) == "R'"

    def test_preserves_double(self):
        """T(Y', F2) = R2"""
        result = (Algs.F * 2).transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.R * 2, cube_size=3)

    def test_identity_rotation(self):
        """T(identity, A) = A"""
        result = Algs.R.transform(Algs.NOOP)
        assert str(result) == "R"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: slice moves
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformSliceMoves:

    def test_y_prime_m_is_s(self):
        """M rotates like L. Y' sends L→F. S rotates like F. So M → S."""
        result = Algs.M.transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.S, cube_size=3)

    def test_y_prime_s_is_m_prime(self):
        """S rotates like F. Y' sends F→R. R is opposite of L (M's face).
        So S → M' (negated direction)."""
        result = Algs.S.transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.M.prime, cube_size=3)

    def test_y_prime_e_unchanged(self):
        """E rotates like D. Y' keeps D fixed. So E → E."""
        result = Algs.E.transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.E, cube_size=3)

    def test_x_e_is_s(self):
        """E rotates like D. X sends D→F. S rotates like F. So E → S."""
        result = Algs.E.transform(Algs.X)
        assert_algs_equivalent(result, Algs.S, cube_size=3)

    def test_x_m_unchanged(self):
        """M rotates like L. X keeps L fixed. So M → M."""
        result = Algs.M.transform(Algs.X)
        assert_algs_equivalent(result, Algs.M, cube_size=3)

    def test_z_m_is_e_prime(self):
        """M rotates like L. Z sends L→U. U is opposite of D (E's face).
        So M → E' (negated)."""
        result = Algs.M.transform(Algs.Z)
        assert_algs_equivalent(result, Algs.E.prime, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: wide moves
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformWideMoves:

    def test_y_prime_rw_is_bw(self):
        """Y' sends R→B, so Rw → Bw"""
        result = Algs.Rw.transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.Bw, cube_size=5)

    def test_x_fw_is_uw(self):
        """X sends F→U, so Fw → Uw"""
        result = Algs.Fw.transform(Algs.X)
        assert_algs_equivalent(result, Algs.Uw, cube_size=5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: whole-cube rotations within A
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformWholeCubeMoves:

    def test_y_prime_x_stays_x(self):
        """X rotates like R. Y' sends R→B. B is opposite of F (Z's face).
        So X → Z' (negated)."""
        result = Algs.X.transform(Algs.Y.prime)
        assert_algs_equivalent(result, Algs.Z.prime, cube_size=3)

    def test_x_y_becomes_z(self):
        """Y rotates like U. X sends U→B. B is opposite of F (Z's face).
        So Y → Z' (negated)."""
        result = Algs.Y.transform(Algs.X)
        assert_algs_equivalent(result, Algs.Z.prime, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transform: sequences
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTransformSequences:

    def test_sexy_move_under_y_prime(self):
        """T(Y', R U R' U') should be equivalent to B R B' R'
        (Y' maps R→B and U→U)"""
        sexy = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        result = sexy.transform(Algs.Y.prime)
        expected = Algs.B + Algs.U + Algs.B.prime + Algs.U.prime
        assert_algs_equivalent(result, expected, cube_size=3)

    def test_transform_preserves_algorithm_effect(self):
        """T(Y', R U R' U') under Y' conjugation should equal R U R' U'"""
        sexy = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        transformed = sexy.transform(Algs.Y.prime)
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
        wa = a.transform(w, cube_size=3)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    @pytest.mark.parametrize("w,a", [
        (Algs.Y.prime, Algs.M),
        (Algs.Y.prime, Algs.S),
        (Algs.X, Algs.E),
        (Algs.Z, Algs.M),
    ])
    def test_conjugation_equals_transform_slice_moves(self, w, a):
        wa = a.transform(w, cube_size=3)
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
        wa = a.transform(w, cube_size=3)
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
        wa = a.transform(w, cube_size=5)
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
        wa = a.transform(w, cube_size=3)
        # a + w should equal w + wa
        left = a + w
        right = w + wa
        assert_algs_equivalent(left, right, cube_size=3)

    def test_push_through_sequence(self):
        w = Algs.Y.prime
        a = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
        wa = a.transform(w, cube_size=3)
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
        wa = a.transform(w, cube_size=3)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    def test_multiple_rotations(self):
        """Y' X Z applied to a sequence."""
        w = Algs.Y.prime + Algs.X + Algs.Z
        a = Algs.R + Algs.U + Algs.F
        wa = a.transform(w, cube_size=3)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)

    def test_double_y(self):
        """Y2 applied to F should give B."""
        result = Algs.F.transform(Algs.Y * 2)
        assert_algs_equivalent(result, Algs.B, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ULTIMATE RANDOMIZED TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# These tests generate random W (whole-cube rotation sequences) and
# random A (full algorithm scrambles) and verify the theorem identities
# hold on actual cube state comparisons.
#
# This is the strongest form of validation: no hand-picked cases,
# no string comparison — pure black-box cube-state equivalence.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTheoremConjugationRandomized:
    """Theorem identity (1): W' A W ≡ T(W, A)

    Verified with:
      - W: random whole-cube rotation sequences (X, Y, Z, primes, doubles)
      - A: random algorithm scrambles from the existing scramble generator
           (face moves, slices, wide moves, with inv/mul modifiers)

    By Lemma 6 (sequence homomorphism), if the identity holds for each
    atomic move type, it holds for any sequence. These tests provide
    empirical confirmation across diverse random combinations.

    Rules applied (Lemmas 3-5):
      - Face moves: face name remapped by P_W, rotation count preserved
      - Slice moves: rotation face remapped, direction negated if mapped to opposite
      - Wide moves: face name remapped, layer count preserved
      - Whole-cube moves in A: axis face remapped, same direction/opposite logic
      - Inv/Mul: transform distributes through wrappers
      - Sequences: transform applies element-wise (Lemma 6)
    """

    @pytest.mark.parametrize("seed", range(20))
    def test_conjugation_random_w_random_a_3x3(self, seed: int):
        """Random W (whole-cube seq) × random A (scramble) on 3×3."""
        w = _random_whole_cube_sequence(seed=seed * 100, length=5)
        a = cube_scramble(cube_size=3, seed=seed * 100 + 1, n=20)

        wa = a.transform(w, cube_size=3)
        conjugated = w.inv() + a + w

        assert_algs_equivalent(conjugated, wa, cube_size=3)

    @pytest.mark.parametrize("seed", range(10))
    def test_conjugation_random_w_random_a_5x5(self, seed: int):
        """Random W × random A on 5×5 — tests sliced moves and wide layers."""
        w = _random_whole_cube_sequence(seed=seed * 200, length=4)
        a = cube_scramble(cube_size=5, seed=seed * 200 + 1, n=15)

        wa = a.transform(w, cube_size=5)
        conjugated = w.inv() + a + w

        assert_algs_equivalent(conjugated, wa, cube_size=5)


class TestTheoremPushThroughRandomized:
    """Theorem identity (2): A W ≡ W T(W, A)

    The "push-through" form: a whole-cube rotation W can be moved from
    the right side of A to the left, if every move in A is transformed.

    Practical meaning: given any algorithm ending with rotations, you can
    move all rotations to the front and rewrite the moves. This is used
    to eliminate mid-algorithm cube rotations.
    """

    @pytest.mark.parametrize("seed", range(20))
    def test_push_through_random_w_random_a_3x3(self, seed: int):
        """A W ≡ W T(W, A) with random W and A on 3×3."""
        w = _random_whole_cube_sequence(seed=seed * 300, length=5)
        a = cube_scramble(cube_size=3, seed=seed * 300 + 1, n=20)

        wa = a.transform(w, cube_size=3)

        left = a + w       # original: do A then W
        right = w + wa     # transformed: do W then T(W,A)

        assert_algs_equivalent(left, right, cube_size=3)

    @pytest.mark.parametrize("seed", range(10))
    def test_push_through_random_w_random_a_5x5(self, seed: int):
        """A W ≡ W T(W, A) with random W and A on 5×5."""
        w = _random_whole_cube_sequence(seed=seed * 400, length=4)
        a = cube_scramble(cube_size=5, seed=seed * 400 + 1, n=15)

        wa = a.transform(w, cube_size=5)

        left = a + w
        right = w + wa

        assert_algs_equivalent(left, right, cube_size=5)


class TestTheoremCompositionRandomized:
    """Theorem identity (3): T(W₁ W₂, A) ≡ T(W₂, T(W₁, A))

    Composing two rotations and transforming once must equal transforming
    twice in sequence. This follows from Lemma 2 (permutation composition):
        P_{W₁W₂} = P_{W₂} ∘ P_{W₁}

    Verified by:
      - Generating two independent random rotation sequences W₁, W₂
      - Generating a random algorithm A
      - Comparing T(W₁W₂, A) vs T(W₂, T(W₁, A)) on actual cube state
    """

    @pytest.mark.parametrize("seed", range(15))
    def test_composition_random_3x3(self, seed: int):
        """T(W₁W₂, A) ≡ T(W₂, T(W₁, A)) on 3×3."""
        w1 = _random_whole_cube_sequence(seed=seed * 500, length=3)
        w2 = _random_whole_cube_sequence(seed=seed * 500 + 1, length=3)
        a = cube_scramble(cube_size=3, seed=seed * 500 + 2, n=20)

        # One-shot: transform by the composed rotation
        composed_w = w1 + w2
        one_shot = a.transform(composed_w, cube_size=3)

        # Two-step: transform by W₁ first, then by W₂
        two_step = a.transform(w1, cube_size=3).transform(w2, cube_size=3)

        assert_algs_equivalent(one_shot, two_step, cube_size=3)


class TestTheoremAllSingleMovesAllAxes:
    """Exhaustive verification: every single atomic move under every axis rotation.

    For each of the 6 basic whole-cube rotations {X, X', Y, Y', Z, Z'}
    and each of the atomic moves in Algs.Simple (face, wide, slice, axis),
    verify the conjugation identity W' A W ≡ T(W, A) on 3×3.

    This is the exhaustive base case that, combined with Lemma 6
    (sequence homomorphism), guarantees correctness for all algorithms.
    """

    _ALL_ROTATIONS = [
        Algs.X, Algs.X.prime,
        Algs.Y, Algs.Y.prime,
        Algs.Z, Algs.Z.prime,
    ]

    @pytest.mark.parametrize("w", _ALL_ROTATIONS,
                             ids=lambda w: str(w))
    @pytest.mark.parametrize("a", Algs.Simple,
                             ids=lambda a: str(a))
    def test_conjugation_all_single_moves(self, w: Alg, a: Alg):
        """W' A W ≡ T(W, A) for every (W, A) pair."""
        wa = a.transform(w, cube_size=3)
        conjugated = w.inv() + a + w
        assert_algs_equivalent(conjugated, wa, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSFORMATION PRINCIPLE DEMONSTRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# The Transformation Principle:
#   If algorithm A acts on piece-set S₁, and W is a whole-cube rotation
#   such that W(S₁) = S₂, then T(W, A) acts on S₂.
#
# Demonstrated using a real L3 algorithm from the 3x3 beginner solver:
#   _ru = R U R' U R U2 R' U
# This algorithm swaps two adjacent U-layer edges while preserving
# L1, L2, and U-edge orientation.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# L3 edge-swap algorithm from _L3Cross._ru:
#   R U R' U R U2 R' U
# On a solved cube, this swaps the FU and LU edges (while disrupting L3 corners).
_L3_RU = Algs.R + Algs.U + Algs.R.prime + Algs.U + Algs.R + (Algs.U * 2) + Algs.R.prime + Algs.U


def _l1_solved(cube: Cube) -> bool:
    """Check that L1 (white face cross + corners) is solved."""
    white = cube.face(FaceName.D)  # white is on D for standard orientation
    return Part.all_match_faces(white.edges) and Part.all_match_faces(white.corners)


def _l2_solved(cube: Cube) -> bool:
    """Check that all 4 middle-layer edges are solved."""
    up = cube.face(FaceName.U)
    down = cube.face(FaceName.D)
    edges = []
    for fn in [FaceName.F, FaceName.R, FaceName.B, FaceName.L]:
        f = cube.face(fn)
        for e in f.edges:
            if not e.on_face(up) and not e.on_face(down):
                if e not in edges:
                    edges.append(e)
    return Part.all_match_faces(edges)


class TestTransformationPrinciple:
    """Transformation Principle: T(W, A) acts on S₂ = W(S₁).

    Uses the L3 edge-swap algorithm R U R' U R U2 R' U from the beginner
    solver (_L3Cross._ru). On a solved cube this swaps FU ↔ LU edges
    (while disrupting L3 corners but preserving edge orientation).

    S₁ = {FU, LU}

    Y' maps: F→R, L→F, so Y'({FU, LU}) = {RU, FU}

    The four Y variants:
        | W   | S₂ = W({FU,LU}) | Swaps     |
        |-----|-----------------|-----------|
        | —   | {FU, LU}        | FU ↔ LU   |
        | Y'  | {RU, FU}        | RU ↔ FU   |
        | Y2  | {BU, RU}        | BU ↔ RU   |
        | Y   | {LU, BU}        | LU ↔ BU   |

    Each test verifies:
      - The expected pair is swapped
      - The other two U-edges remain solved
      - L1 and L2 remain solved
    """

    def test_original_swaps_fu_lu(self):
        """Baseline: _ru swaps FU ↔ LU on a solved cube."""
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        # Before: all edges match
        assert up.edge_bottom.match_faces  # FU
        assert up.edge_right.match_faces   # RU
        assert up.edge_top.match_faces     # BU
        assert up.edge_left.match_faces    # LU

        _L3_RU.play(cube)

        # After: FU and LU are swapped
        assert not up.edge_bottom.match_faces  # FU — swapped
        assert not up.edge_left.match_faces    # LU — swapped
        # RU and BU preserved
        assert up.edge_right.match_faces   # RU — unchanged
        assert up.edge_top.match_faces     # BU — unchanged
        # L1 and L2 preserved
        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y_prime_transform_swaps_ru_fu(self):
        """Transformation Principle: T(Y', _ru) swaps RU ↔ FU.

        Y' maps: F→R, L→F
        So Y'({FU, LU}) = {RU, FU}
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _L3_RU.transform(Algs.Y.prime, cube_size=3)
        transformed.play(cube)

        # RU and FU are swapped (S₂)
        assert not up.edge_right.match_faces   # RU — swapped
        assert not up.edge_bottom.match_faces  # FU — swapped
        # BU and LU preserved (not in S₂)
        assert up.edge_top.match_faces     # BU — unchanged
        assert up.edge_left.match_faces    # LU — unchanged
        # L1 and L2 preserved
        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y2_transform_swaps_bu_ru(self):
        """T(Y2, _ru) swaps BU ↔ RU.

        Y2 maps: F→B, L→R
        So Y2({FU, LU}) = {BU, RU}
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _L3_RU.transform(Algs.Y * 2, cube_size=3)
        transformed.play(cube)

        # BU and RU are swapped (S₂)
        assert not up.edge_top.match_faces     # BU — swapped
        assert not up.edge_right.match_faces   # RU — swapped
        # FU and LU preserved
        assert up.edge_bottom.match_faces  # FU — unchanged
        assert up.edge_left.match_faces    # LU — unchanged
        # L1 and L2 preserved
        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y_transform_swaps_lu_bu(self):
        """T(Y, _ru) swaps LU ↔ BU.

        Y maps: F→L, L→B
        So Y({FU, LU}) = {LU, BU}
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _L3_RU.transform(Algs.Y, cube_size=3)
        transformed.play(cube)

        # LU and BU are swapped (S₂)
        assert not up.edge_left.match_faces    # LU — swapped
        assert not up.edge_top.match_faces     # BU — swapped
        # FU and RU preserved
        assert up.edge_bottom.match_faces  # FU — unchanged
        assert up.edge_right.match_faces   # RU — unchanged
        # L1 and L2 preserved
        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_all_four_y_variants(self):
        """One algorithm generates all 4 adjacent edge-swap variants via Y and Y'.

        Both Y and Y' are tested — the principle is not specific to either direction.

        | W   | S₂ = W({FU,LU}) | Swaps     |
        |-----|-----------------|-----------|
        | —   | {FU, LU}        | FU ↔ LU   |
        | Y   | {LU, BU}        | LU ↔ BU   |
        | Y'  | {RU, FU}        | RU ↔ FU   |
        | Y2  | {BU, RU}        | BU ↔ RU   |
        """
        rotations = [Algs.NOOP, Algs.Y, Algs.Y.prime, Algs.Y * 2]
        # Expected swapped pair for each rotation (as edge positions on U face)
        # edge_bottom=FU, edge_right=RU, edge_top=BU, edge_left=LU
        expected_swapped = [
            ("edge_bottom", "edge_left"),    # FU, LU
            ("edge_left", "edge_top"),       # LU, BU  (Y)
            ("edge_right", "edge_bottom"),   # RU, FU  (Y')
            ("edge_top", "edge_right"),      # BU, RU  (Y2)
        ]
        all_edges = {"edge_bottom", "edge_right", "edge_top", "edge_left"}

        for w, (e1, e2) in zip(rotations, expected_swapped):
            cube = Cube(3, sp=_test_sp)
            up = cube.face(FaceName.U)

            transformed = _L3_RU.transform(w, cube_size=3)
            transformed.play(cube)

            # The two edges in S₂ are swapped
            assert not getattr(up, e1).match_faces, f"W={w}: {e1} should be swapped"
            assert not getattr(up, e2).match_faces, f"W={w}: {e2} should be swapped"

            # The other two edges are preserved
            for e in all_edges - {e1, e2}:
                assert getattr(up, e).match_faces, f"W={w}: {e} should be preserved"

            # L1 and L2 always preserved (Y rotations keep S₂ within U layer)
            assert _l1_solved(cube), f"W={w}: L1 should be solved"
            assert _l2_solved(cube), f"W={w}: L2 should be solved"

    @pytest.mark.parametrize("w", [
        Algs.X, Algs.X.prime,
        Algs.Y, Algs.Y.prime,
        Algs.Z, Algs.Z.prime,
        Algs.X + Algs.Y,
        Algs.Z.prime + Algs.X,
    ], ids=lambda w: str(w))
    def test_conjugation_holds_for_all_axes(self, w):
        """The principle works for ALL rotations, not just Y.

        For any W: W' · A · W ≡ T(W, A).
        This is the conjugation identity applied to a real L3 algorithm.

        X and Z rotations move U-layer edges across layers (e.g., FU→BU,
        LU→BL), so we don't check L1/L2 — we verify equivalence directly.
        """
        transformed = _L3_RU.transform(w, cube_size=3)
        conjugated = w.inv() + _L3_RU + w
        assert_algs_equivalent(conjugated, transformed, cube_size=3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSFORMATION PRINCIPLE: 3-CORNER CYCLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# The 3-corner cycle from CommonOp.top_3_corner_cycle:
#   U R U' L' U R' U' L
# Cycles three U-layer corners: FLU → BRU → BLU → FLU
# Leaves FRU fixed.
#
# S₁ = {FLU, BRU, BLU}, fixed corner = FRU
#
# This is a more complex test than the edge swap:
# - It's a 3-cycle (not a 2-swap)
# - It involves corners (3 stickers each, not 2)
# - We verify the cycle direction is preserved under transform
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 3-corner cycle: U R U' L' U R' U' L
# Cycles FLU → BRU → BLU → FLU, fixes FRU
_CORNER_3_CYCLE = (
    Algs.U + Algs.R + Algs.U.prime + Algs.L.prime
    + Algs.U + Algs.R.prime + Algs.U.prime + Algs.L
)


def _corner_is_solved(corner) -> bool:
    """Check if a corner is in its solved position (all stickers match faces)."""
    return corner.match_faces


class TestTransformationPrinciple3CornerCycle:
    """Transformation Principle applied to the 3-corner cycle U R U' L' U R' U' L.

    On a solved cube, this cycles three U-layer corners:
        FLU → BRU → BLU → FLU
    leaving FRU fixed.

    Corner positions on U face (looking down):
        corner_top_left = BLU     corner_top_right = BRU
        corner_bottom_left = FLU  corner_bottom_right = FRU

    S₁ = {FLU, BRU, BLU}

    Under Y rotations:
        | W   | S₂ = W(S₁)           | Fixed corner |
        |-----|----------------------|--------------|
        | —   | {FLU, BRU, BLU}      | FRU          |
        | Y'  | {FRU, BLU, FLU}      | BRU          |
        | Y   | {BLU, FRU, BRU}      | FLU          |
        | Y2  | {BRU, FLU, FRU}      | BLU          |
    """

    def test_original_cycles_three_corners(self):
        """Baseline: the 3-cycle moves FLU, BRU, BLU and fixes FRU."""
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        _CORNER_3_CYCLE.play(cube)

        # FRU is fixed (the corner not in the cycle)
        assert _corner_is_solved(up.corner_bottom_right), "FRU should be fixed"

        # The three cycled corners are disturbed
        assert not _corner_is_solved(up.corner_bottom_left), "FLU should be cycled"
        assert not _corner_is_solved(up.corner_top_right), "BRU should be cycled"
        assert not _corner_is_solved(up.corner_top_left), "BLU should be cycled"

        # L1 and L2 are preserved (the cycle only touches U-layer corners)
        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y_prime_transform_shifts_cycle(self):
        """T(Y', 3-cycle): cycles FRU, BLU, FLU — fixes BRU.

        Y' maps: F→R, R→B, B→L, L→F
        S₂ = Y'({FLU, BRU, BLU}) = {RFU, LBU, FLU}
        Fixed: Y'(FRU) = BRU (= corner_top_right)
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _CORNER_3_CYCLE.transform(Algs.Y.prime, cube_size=3)
        transformed.play(cube)

        # BRU is the fixed corner under Y' transform
        assert _corner_is_solved(up.corner_top_right), "BRU should be fixed"

        # The other three are cycled
        assert not _corner_is_solved(up.corner_bottom_right), "FRU should be cycled"
        assert not _corner_is_solved(up.corner_top_left), "BLU should be cycled"
        assert not _corner_is_solved(up.corner_bottom_left), "FLU should be cycled"

        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y_transform_shifts_cycle(self):
        """T(Y, 3-cycle): cycles BLU, FRU, BRU — fixes FLU.

        Y maps: F→L, L→B, B→R, R→F
        S₂ = Y({FLU, BRU, BLU}) = {BLU, FRU, BRU}
        Fixed: Y(FRU) = FLU (= corner_bottom_left)
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _CORNER_3_CYCLE.transform(Algs.Y, cube_size=3)
        transformed.play(cube)

        # FLU is the fixed corner under Y transform
        assert _corner_is_solved(up.corner_bottom_left), "FLU should be fixed"

        # The other three are cycled
        assert not _corner_is_solved(up.corner_top_left), "BLU should be cycled"
        assert not _corner_is_solved(up.corner_bottom_right), "FRU should be cycled"
        assert not _corner_is_solved(up.corner_top_right), "BRU should be cycled"

        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_y2_transform_shifts_cycle(self):
        """T(Y2, 3-cycle): cycles BRU, FLU, FRU — fixes BLU.

        Y2 maps: F→B, B→F, L→R, R→L
        S₂ = Y2({FLU, BRU, BLU}) = {BRU, FLU, FRU}
        Fixed: Y2(FRU) = BLU (= corner_top_left)
        """
        cube = Cube(3, sp=_test_sp)
        up = cube.face(FaceName.U)

        transformed = _CORNER_3_CYCLE.transform(Algs.Y * 2, cube_size=3)
        transformed.play(cube)

        # BLU is the fixed corner under Y2 transform
        assert _corner_is_solved(up.corner_top_left), "BLU should be fixed"

        # The other three are cycled
        assert not _corner_is_solved(up.corner_top_right), "BRU should be cycled"
        assert not _corner_is_solved(up.corner_bottom_left), "FLU should be cycled"
        assert not _corner_is_solved(up.corner_bottom_right), "FRU should be cycled"

        assert _l1_solved(cube)
        assert _l2_solved(cube)

    def test_all_four_y_variants_each_fixes_different_corner(self):
        """Each Y rotation fixes a different corner — one full orbit."""
        corner_attrs = [
            "corner_bottom_left",   # FLU
            "corner_bottom_right",  # FRU
            "corner_top_right",     # BRU
            "corner_top_left",      # BLU
        ]
        rotations = [Algs.NOOP, Algs.Y.prime, Algs.Y, Algs.Y * 2]
        # Which corner is fixed for each rotation
        expected_fixed = [
            "corner_bottom_right",  # original: FRU fixed
            "corner_top_right",     # Y': BRU fixed
            "corner_bottom_left",   # Y: FLU fixed
            "corner_top_left",      # Y2: BLU fixed
        ]

        for w, fixed_attr in zip(rotations, expected_fixed):
            cube = Cube(3, sp=_test_sp)
            up = cube.face(FaceName.U)

            transformed = _CORNER_3_CYCLE.transform(w, cube_size=3)
            transformed.play(cube)

            # The fixed corner is solved
            fixed_corner = getattr(up, fixed_attr)
            assert _corner_is_solved(fixed_corner), (
                f"W={w}: {fixed_attr} should be fixed"
            )

            # The other three are NOT solved (they were cycled)
            for attr in corner_attrs:
                if attr != fixed_attr:
                    corner = getattr(up, attr)
                    assert not _corner_is_solved(corner), (
                        f"W={w}: {attr} should be cycled"
                    )

            # L1 and L2 preserved
            assert _l1_solved(cube), f"W={w}: L1 should be solved"
            assert _l2_solved(cube), f"W={w}: L2 should be solved"

    def test_applying_3_times_restores_cube(self):
        """A 3-cycle applied 3 times = identity. Same for transforms."""
        for w in [Algs.NOOP, Algs.Y, Algs.Y.prime, Algs.Y * 2]:
            cube = Cube(3, sp=_test_sp)
            transformed = _CORNER_3_CYCLE.transform(w, cube_size=3)

            # Apply 3 times
            transformed.play(cube)
            transformed.play(cube)
            transformed.play(cube)

            # All corners should be back to solved
            up = cube.face(FaceName.U)
            for attr in ["corner_bottom_left", "corner_bottom_right",
                         "corner_top_left", "corner_top_right"]:
                assert _corner_is_solved(getattr(up, attr)), (
                    f"W={w}: {attr} should be restored after 3 applications"
                )

    @pytest.mark.parametrize("w", [
        Algs.X, Algs.X.prime,
        Algs.Y, Algs.Y.prime,
        Algs.Z, Algs.Z.prime,
        Algs.X + Algs.Y,
        Algs.Z.prime + Algs.X,
    ], ids=lambda w: str(w))
    def test_conjugation_holds_for_all_axes(self, w):
        """W' · 3-cycle · W ≡ T(W, 3-cycle) for all rotation axes."""
        transformed = _CORNER_3_CYCLE.transform(w, cube_size=3)
        conjugated = w.inv() + _CORNER_3_CYCLE + w
        assert_algs_equivalent(conjugated, transformed, cube_size=3)
