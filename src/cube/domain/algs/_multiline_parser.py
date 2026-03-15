"""Multi-line algorithm preprocessor with variable support.

Supports:
    - Comments: lines starting with #
    - Variable assignments: $name = R U R' U'
    - Integer assignments: $I = 1
    - Variable references: $name expands inline
    - Prime of variables: $name' → inverse of expanded alg
    - Integer expressions in slices: [$I:$I+1]M → [1:2]M
    - Repetition: $alg * $n or $alg * 5

The preprocessor expands all variables and expressions, then passes
the resulting single-line string to parse_alg().
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from cube.domain.exceptions import InternalSWError

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg


def preprocess_multiline(text: str) -> str:
    """Preprocess multi-line algorithm text into a single algorithm string.

    Handles variable assignments, substitutions, integer expressions,
    and repetition operators. Returns a string ready for parse_alg().

    Args:
        text: Multi-line algorithm text

    Returns:
        Single-line algorithm string with all variables expanded

    Raises:
        ValueError: If text is empty or contains only comments/assignments
        InternalSWError: If variable references are invalid
    """
    variables: dict[str, str] = {}  # $name -> value string
    int_vars: dict[str, int] = {}   # $name -> integer value (subset of variables)
    alg_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Skip empty lines, comments, and %directives (metadata like %name=)
        if not line or line.startswith("#") or line.startswith("%"):
            continue

        # Check for variable assignment: $name = value
        assign_match = re.match(r'^\$(\w+)\s*=\s*(.+)$', line)
        if assign_match:
            var_name = assign_match.group(1)
            var_value = assign_match.group(2).strip()
            variables[var_name] = var_value
            # Check if it's a pure integer
            try:
                int_vars[var_name] = int(var_value)
            except ValueError:
                pass
            continue

        # This is an algorithm line — expand variables and expressions
        expanded = _expand_line(line, variables, int_vars)
        if expanded:
            alg_lines.append(expanded)

    if not alg_lines:
        return ""

    return " ".join(alg_lines)


def parse_multiline(text: str, *, compat_3x3: bool = False) -> Alg:
    """Parse multi-line algorithm text with variable support.

    This is the full pipeline: preprocess → parse_alg.
    Returns identity (empty SeqAlg) for texts with only comments/assignments/metadata.

    Args:
        text: Multi-line algorithm text
        compat_3x3: Passed through to parse_alg

    Returns:
        Parsed Alg object (identity if no algorithm lines)
    """
    from cube.domain.algs.Algs import Algs
    from cube.domain.algs._parser import parse_alg

    expanded = preprocess_multiline(text)
    if not expanded:
        return Algs.NOOP
    return parse_alg(expanded, compat_3x3=compat_3x3)


def _expand_line(line: str, variables: dict[str, str], int_vars: dict[str, int]) -> str:
    """Expand a single algorithm line by substituting variables and expressions.

    Handles:
        - $var → expanded value
        - $var' → ( expanded value )'  (wrapped for prime)
        - [$expr:$expr]X → [evaluated:evaluated]X
        - $alg * $n or $alg * 5 → (expanded) N
    """
    # Handle repetition: $var * $n  or  $var * 5  or  (stuff) * $n
    # Must be checked before general variable expansion
    rep_match = re.match(r'^(.+?)\s*\*\s*(\$\w+|\d+)\s*$', line)
    if rep_match:
        lhs = rep_match.group(1).strip()
        rhs = rep_match.group(2).strip()

        # Resolve the count
        if rhs.startswith("$"):
            rhs_name = rhs[1:]
            if rhs_name not in int_vars:
                raise InternalSWError(f"Variable {rhs} is not defined or not an integer")
            count = int_vars[rhs_name]
        else:
            count = int(rhs)

        # Expand the LHS
        expanded_lhs = _expand_variables(lhs, variables, int_vars)
        # Wrap in parens and multiply: (R' D' R D) 5
        return f"({expanded_lhs}) {count}"

    # General variable expansion (handles $var, $var', and [$expr] notation)
    return _expand_variables(line, variables, int_vars)


def _expand_variables(text: str, variables: dict[str, str], int_vars: dict[str, int]) -> str:
    """Expand all $variable references in text.

    Handles:
        - $var → value
        - $var' → (value)' — wraps in parens so prime applies to whole expansion
        - [$expr:$expr+1] → [1:2] — evaluates integer expressions inside brackets
    """
    # First, expand integer expressions inside square brackets: [$I:$I+1]
    text = _expand_bracket_expressions(text, int_vars)

    # Then expand algorithm variables: $var and $var'
    # Pattern: $word optionally followed by ' (prime)
    # Process longer variable names first to avoid partial matches
    sorted_vars = sorted(variables.keys(), key=len, reverse=True)
    for var_name in sorted_vars:
        var_value = variables[var_name]

        # Replace $var' → (value)' (prime of expanded alg)
        text = text.replace(f"${var_name}'", f"({var_value})'")

        # Replace $var → value (plain expansion)
        text = text.replace(f"${var_name}", var_value)

    # Check for unresolved variables
    unresolved = re.findall(r'\$(\w+)', text)
    if unresolved:
        raise InternalSWError(f"Undefined variable(s): {', '.join('$' + v for v in unresolved)}")

    return text


def _expand_bracket_expressions(text: str, int_vars: dict[str, int]) -> str:
    """Expand integer expressions inside square brackets.

    Handles patterns like [$I:$I+1] → [1:2] where $I=1.
    Supports +, -, * operators with integer variables.
    """
    def replace_bracket(m: re.Match[str]) -> str:
        content = m.group(1)
        # Only process if it contains $ references
        if "$" not in content:
            return m.group(0)

        # Evaluate each part separated by : or ,
        parts: list[str] = []
        for segment in re.split(r'([:, ])', content):
            if segment in (":", ",", " "):
                parts.append(segment)
            elif "$" in segment:
                parts.append(str(_eval_int_expr(segment, int_vars)))
            else:
                parts.append(segment)

        return "[" + "".join(parts) + "]"

    return re.sub(r'\[([^\]]*\$[^\]]*)\]', replace_bracket, text)


def _eval_int_expr(expr: str, int_vars: dict[str, int]) -> int:
    """Evaluate a simple integer expression like $I, $I+1, $I-1, $I*2.

    Only supports: $var, $var+N, $var-N, $var*N, N+$var, N-$var, N*$var
    """
    expr = expr.strip()

    # Try simple $var
    simple_match = re.match(r'^\$(\w+)$', expr)
    if simple_match:
        name = simple_match.group(1)
        if name not in int_vars:
            raise InternalSWError(f"Variable ${name} is not defined or not an integer")
        return int_vars[name]

    # Try $var OP N or N OP $var
    op_match = re.match(r'^\$(\w+)\s*([+\-*])\s*(\d+)$', expr)
    if op_match:
        name, op, num_str = op_match.group(1), op_match.group(2), op_match.group(3)
        if name not in int_vars:
            raise InternalSWError(f"Variable ${name} is not defined or not an integer")
        val = int_vars[name]
        num = int(num_str)
        if op == "+":
            return val + num
        elif op == "-":
            return val - num
        elif op == "*":
            return val * num

    # Try N OP $var
    op_match2 = re.match(r'^(\d+)\s*([+\-*])\s*\$(\w+)$', expr)
    if op_match2:
        num_str, op, name = op_match2.group(1), op_match2.group(2), op_match2.group(3)
        if name not in int_vars:
            raise InternalSWError(f"Variable ${name} is not defined or not an integer")
        val = int_vars[name]
        num = int(num_str)
        if op == "+":
            return num + val
        elif op == "-":
            return num - val
        elif op == "*":
            return num * val

    raise InternalSWError(f"Cannot evaluate integer expression: {expr}")
