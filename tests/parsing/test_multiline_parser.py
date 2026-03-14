"""Tests for the multi-line algorithm preprocessor with variables."""
import pytest

from cube.domain.algs import Algs
from cube.domain.algs._multiline_parser import preprocess_multiline, parse_multiline
from cube.domain.exceptions import InternalSWError
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


class TestPreprocessor:
    """Tests for preprocess_multiline — the variable expansion layer."""

    def test_simple_passthrough(self) -> None:
        """Lines without variables pass through unchanged."""
        result = preprocess_multiline("R U R' U'")
        assert result == "R U R' U'"

    def test_comments_stripped(self) -> None:
        result = preprocess_multiline("# comment\nR U\n# another\nR'")
        assert result == "R U R'"

    def test_empty_lines_stripped(self) -> None:
        result = preprocess_multiline("\n\nR U\n\nR'\n\n")
        assert result == "R U R'"

    def test_variable_assignment_and_reference(self) -> None:
        result = preprocess_multiline("$setup = R U R'\n$setup")
        assert result == "R U R'"

    def test_variable_prime(self) -> None:
        """$var' should expand to (value)' for prime."""
        result = preprocess_multiline("$setup = R U R'\n$setup'")
        assert result == "(R U R')'"

    def test_setup_and_prime(self) -> None:
        """Full setup/execute/teardown pattern."""
        result = preprocess_multiline(
            "$setup = X Y L R\n"
            "$setup\n"
            "U R L\n"
            "$setup'"
        )
        assert result == "X Y L R U R L (X Y L R)'"

    def test_integer_variable(self) -> None:
        result = preprocess_multiline("$I = 1\n[$I:$I+1]M2")
        assert result == "[1:2]M2"

    def test_integer_expression_subtraction(self) -> None:
        result = preprocess_multiline("$I = 3\n[$I-1:$I]M")
        assert result == "[2:3]M"

    def test_integer_expression_multiply(self) -> None:
        result = preprocess_multiline("$I = 2\n[$I*2]R")
        assert result == "[4]R"

    def test_repetition_with_integer_var(self) -> None:
        result = preprocess_multiline(
            "$n = 5\n$corner = R' D' R D\n$corner * $n"
        )
        assert result == "(R' D' R D) 5"

    def test_repetition_with_literal_count(self) -> None:
        result = preprocess_multiline("$corner = R' D' R D\n$corner * 3")
        assert result == "(R' D' R D) 3"

    def test_repetition_inline_alg(self) -> None:
        """Repetition with inline alg (no variable on LHS)."""
        result = preprocess_multiline("R U R' U' * 6")
        assert result == "(R U R' U') 6"

    def test_multiple_variables(self) -> None:
        result = preprocess_multiline(
            "$a = R U\n$b = L D\n$a $b"
        )
        assert result == "R U L D"

    def test_variable_used_multiple_times(self) -> None:
        result = preprocess_multiline("$m = R U\n$m $m $m")
        assert result == "R U R U R U"

    def test_undefined_variable_raises(self) -> None:
        with pytest.raises(InternalSWError, match="Undefined variable"):
            preprocess_multiline("$undefined")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            preprocess_multiline("")

    def test_only_comments_raises(self) -> None:
        with pytest.raises(ValueError):
            preprocess_multiline("# comment only")

    def test_only_assignments_raises(self) -> None:
        with pytest.raises(ValueError):
            preprocess_multiline("$x = R U")

    def test_complex_slice_expression(self) -> None:
        """Test [$I:$I+1] with larger numbers."""
        result = preprocess_multiline("$I = 5\n[$I:$I+2]M")
        assert result == "[5:7]M"

    def test_comments_between_assignments(self) -> None:
        result = preprocess_multiline(
            "# Define setup\n"
            "$setup = R U R'\n"
            "# Now use it\n"
            "$setup U2 $setup'"
        )
        assert result == "R U R' U2 (R U R')'"

    def test_percent_name_directive_ignored(self) -> None:
        """%name= lines are metadata and should be ignored by the parser."""
        result = preprocess_multiline("%name=myAlg\nR U R'")
        assert result == "R U R'"

    def test_percent_name_with_variables(self) -> None:
        result = preprocess_multiline(
            "%name=setup_test\n"
            "$s = R U\n"
            "$s R'"
        )
        assert result == "R U R'"


class TestParseMultilineIntegration:
    """Integration tests — preprocess + parse + execute on a real cube."""

    def test_setup_solve_pattern(self) -> None:
        """$setup / moves / $setup' should return cube to pre-move state
        (only the middle moves remain applied)."""
        cube = Cube(3, sp=_test_sp)
        state_before = cube.cqr.get_sate()

        alg = parse_multiline(
            "$setup = R U R'\n"
            "$setup\n"
            "$setup'"
        )
        alg.play(cube)
        # setup + setup' = identity
        assert cube.cqr.compare_state(state_before)

    def test_repetition_execution(self) -> None:
        """(R' D' R D) * 6 = identity on 3x3."""
        cube = Cube(3, sp=_test_sp)
        state_before = cube.cqr.get_sate()

        alg = parse_multiline(
            "$corner = R' D' R D\n"
            "$corner * 6"
        )
        alg.play(cube)
        assert cube.cqr.compare_state(state_before)

    def test_integer_slice_on_big_cube(self) -> None:
        """Test [$I:$I+1]M on a 5x5 cube."""
        cube = Cube(5, sp=_test_sp)
        state_before = cube.cqr.get_sate()

        alg = parse_multiline("$I = 1\n[$I:$I+1]M2 [$I:$I+1]M2")
        alg.play(cube)
        # M2 M2 = identity
        assert cube.cqr.compare_state(state_before)

    def test_algs_parse_multiline_with_variables(self) -> None:
        """Test that Algs.parse_multiline delegates to the new preprocessor."""
        alg = Algs.parse_multiline(
            "$s = R U\n"
            "$s R' U'"
        )
        cube = Cube(3, sp=_test_sp)
        state_before = cube.cqr.get_sate()
        alg.play(cube)
        alg.prime.play(cube)
        assert cube.cqr.compare_state(state_before)

    def test_backward_compat_no_variables(self) -> None:
        """Existing multiline format (no variables) still works."""
        alg = Algs.parse_multiline("""
            # comment
            R U R'

            # another
            U' L' U L
        """)
        cube = Cube(3, sp=_test_sp)
        state_before = cube.cqr.get_sate()
        alg.play(cube)
        alg.prime.play(cube)
        assert cube.cqr.compare_state(state_before)
