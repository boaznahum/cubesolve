import re
from typing import TYPE_CHECKING, TypeAlias

from cube.domain.exceptions import InternalSWError
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg
    from cube.domain.algs.SeqAlg import SeqAlg

_Alg: TypeAlias = "Alg"
_SeqAlg: TypeAlias = "SeqAlg"


def parse_alg(s: str, *, compat_3x3: bool = False) -> _Alg:
    """
    this is very naive patch version
    Currently doesn't support exp N and exp '  (only U2, U',...)

    Supports:
    - Simple moves: R, U, R', R2, etc.
    - Slice moves: M, E, S, M', E2, etc.
    - Wide moves: Rw, r, Lw', etc.
    - Slice notation: [1:2]M, [1]R, [1:]S, etc.
    - Sequences: [R U R' U'], (R U) 2

    Args:
        s: The algorithm string to parse.
        compat_3x3: When True, bare "M" is treated as all middle slices ([:]M),
            matching standard 3x3 notation where M = all middle slices.
            When False (default), bare "M" returns MiddleSliceAlg (single middle slice).
    """

    # We capture, so we get the splitters two, such as '(' ')', we need to ignore the spaces
    # Empty matches for the pattern split the string only when not adjacent to a previous empty match.
    # https://docs.python.org/3/library/re.html#re.split
    # example:
    #  ["R'", ' ', 'U2', ' ', '', '(', 'R', ' ', 'U', ' ', "R'", ' ', 'U', ')', '', ' ', 'R']
    #
    # Updated to also split on [ and ] for sequence brackets, and ' for prime modifiers
    # Note: Slice notation [1:2]M is handled specially - the [ before digits is not a bracket
    pattern = r"(\s+|\(|\)|\[|\]|')"
    tokens = re.split(pattern, s)

    p = _Parser(s, tokens, compat_3x3=compat_3x3)

    return p.parse()


class _Parser:

    def __init__(self, original: str, tokens: list[str], *, compat_3x3: bool = False) -> None:
        super().__init__()
        self._tokens = tokens
        self._original = original
        self._compat_3x3 = compat_3x3

    def parse(self) -> _SeqAlg:
        result: list[Alg] = []
        self._parse(result, False)

        from cube.domain.algs.Algs import Algs

        return Algs.seq_alg(None, *result)

    def _parse(self, result: list[_Alg], nested: bool, bracket_type: str = "("):

        while True:
            token = self.next_token()
            if not token:
                break

            if token == "(" or token == "[":
                # Check if [ is a slice prefix or sequence bracket
                if token == "[":
                    # Peek at next token to see if it's slice notation (only digits/colons/commas/minus)
                    # vs a sequence bracket containing a digit-prefixed move like [3Rw ...]
                    next_tok = self.peek_token()
                    if next_tok and re.match(r'^[\d:,\-]+$', next_tok):
                        # This is slice notation [1:2]M - collect tokens until ] and build slice
                        slice_tokens = self._collect_slice_tokens()
                        # Next token should be the algorithm
                        alg_token = self.next_token()
                        if not alg_token:
                            raise InternalSWError(f"Expected algorithm after slice in {self._original}")
                        # Combine slice notation with algorithm token
                        combined = "[" + slice_tokens + "]" + alg_token
                        at = _token_to_alg(combined, compat_3x3=self._compat_3x3)
                        result.append(at)
                        continue
                # Otherwise treat [ as sequence bracket like (
                # Create a new result list for the nested sequence
                nested_result: list[Alg] = []
                self._parse(nested_result, True, token)
                # Wrap nested items in a SeqAlg so it can be multiplied as a unit
                from cube.domain.algs.Algs import Algs
                nested_seq = Algs.seq_alg(None, *nested_result)
                result.append(nested_seq)

            elif token == ')' or token == ']':
                if not nested:
                    raise InternalSWError(f"Unexpected '{token}' in {self._original}")
                # Verify matching bracket type
                expected = ']' if bracket_type == '[' else ')'
                if token != expected:
                    raise InternalSWError(f"Mismatched brackets: expected '{expected}' but got '{token}' in {self._original}")
                return  # Exit nested parse
            elif token == "'":
                # Prime modifier for previous result (e.g., [R U]')
                if not result:
                    raise InternalSWError(f"Unexpected prime modifier in {self._original}")
                prev = result.pop()
                at = prev.prime
                result.append(at)
            elif token.isdigit():
                if not result:
                    raise InternalSWError(f"Unexpected multiplier {token} in {self._original}")
                prev = result.pop()
                at = prev * int(token)
                result.append(at)

            else:
                at = _token_to_alg(token, compat_3x3=self._compat_3x3)
                result.append(at)

    def _collect_slice_tokens(self) -> str:
        """Collect tokens until ] for slice notation."""
        parts: list[str] = []
        while True:
            token = self.next_token()
            if not token:
                raise InternalSWError(f"Unclosed slice bracket in {self._original}")
            if token == "]":
                break
            parts.append(token)
        return "".join(parts)

    def peek_token(self) -> str | None:
        """Peek at next non-empty token without consuming it."""
        tokens = self._tokens
        for i, t in enumerate(tokens):
            if t:
                t = t.strip()
                if t:
                    return t
        return None

    def next_token(self) -> str | None:
        """

        :return: Non-empty toke or None
        """
        tokens = self._tokens
        while tokens:
            t = tokens.pop(0)

            if t:
                t = t.strip()
                if t:
                    return t

        return None


def _parse_slice_prefix(t: str) -> tuple[str, slice | list[int] | None]:
    """
    Parse slice prefix from token.

    Formats:
        [1:2]M  -> ("M", slice(1, 2))
        [1:]M   -> ("M", slice(1, None))
        [1:1]M  -> ("M", slice(1, 1))
        [1,2,3]M -> ("M", [1, 2, 3])
        M       -> ("M", None)

    Returns:
        (base_token, slice_spec) where slice_spec is None if no slice prefix
    """
    if not t.startswith("["):
        return t, None

    # Find closing bracket
    bracket_end = t.find("]")
    if bracket_end == -1:
        raise InternalSWError(f"Unclosed bracket in token: {t}")

    slice_str = t[1:bracket_end]  # Content between [ and ]
    base_token = t[bracket_end + 1:]  # Everything after ]

    if not base_token:
        raise InternalSWError(f"No algorithm after slice in token: {t}")

    # Parse slice content
    if ":" in slice_str:
        # Range notation: [start:stop] or [start:] or [:stop]
        parts = slice_str.split(":")
        if len(parts) != 2:
            raise InternalSWError(f"Invalid slice format: {slice_str}")

        start_str, stop_str = parts
        start = int(start_str) if start_str else None
        stop = int(stop_str) if stop_str else None
        return base_token, slice(start, stop)

    elif "," in slice_str:
        # List notation: [1,2,3]
        indices = [int(x.strip()) for x in slice_str.split(",")]
        return base_token, indices

    else:
        # Single index: [1] -> slice(1, 1)
        index = int(slice_str)
        return base_token, slice(index, index)


def _token_to_alg(t: str, *, compat_3x3: bool = False) -> _Alg:
    """
    Parse a token to algorithm.

    Order of operations:
    1. Parse slice prefix [start:stop] if present
    2. Parse modifiers from base token (', 2, '2, '3, etc.)
    3. Get the simple base algorithm
    4. Apply slice to base algorithm FIRST
    5. Apply modifiers (prime, multiply) to sliced algorithm

    Examples:
        [1:2]M   -> M[1:2]
        [1:2]M'  -> M[1:2].prime
        [1:2]M'3 -> (M[1:2].prime) * 3
        [1:2]M2  -> M[1:2] * 2
    """
    # First, check for slice prefix [start:stop]
    base_token, slice_spec = _parse_slice_prefix(t)

    # Parse modifiers from base token
    # Format can be: CODE, CODE', CODE2, CODE'2, CODE'3, etc.
    modifiers: list[str] = []  # List of modifiers to apply in order

    # Extract all trailing modifiers (work backwards)
    remaining = base_token
    while remaining:
        if remaining.endswith("'"):
            modifiers.insert(0, "prime")  # Insert at front to maintain order
            remaining = remaining[:-1]
        elif remaining[-1].isdigit():
            # Find all trailing digits
            i = len(remaining) - 1
            while i > 0 and remaining[i - 1].isdigit():
                i -= 1
            num = remaining[i:]
            modifiers.insert(0, f"mul:{num}")
            remaining = remaining[:i]
        else:
            break

    # Get base simple algorithm
    if not remaining:
        raise InternalSWError(f"Empty base token in: {t}")

    # Check for digit prefix on wide moves: nRw or nr (e.g., 3Rw, 3r)
    import re as _re
    base_alg: _Alg
    _wide_match = _re.match(r'^(\d+)(.+)$', remaining)
    if _wide_match:
        _n_layers = int(_wide_match.group(1))
        _inner_code = _wide_match.group(2)
        try:
            _inner_alg = _token_to_alg_no_slice(_inner_code)
        except InternalSWError:
            _inner_alg = None
        from cube.domain.algs.WideLayerAlg import WideLayerAlg
        if _inner_alg is not None and isinstance(_inner_alg, WideLayerAlg):
            base_alg = _inner_alg.with_layers(_n_layers)
        else:
            base_alg = _token_to_alg_no_slice(remaining)
    else:
        base_alg = _token_to_alg_no_slice(remaining)

    # Track whether the original token had a slice prefix (for bare-token checks below)
    had_slice_prefix = slice_spec is not None

    # Apply slice to base algorithm FIRST (before modifiers)
    if slice_spec is not None:
        # Special case: [:-1]Rw or [:-1]r → all-but-last wide move (RRw/rr)
        # Simple list lookup returns WideLayerAlg — swap to ALL_BUT_LAST mode.
        if isinstance(slice_spec, slice) and slice_spec.start is None and slice_spec.stop == -1:
            from cube.domain.algs.WideLayerAlg import WideLayerAlg
            if isinstance(base_alg, WideLayerAlg):
                base_alg = _wide_to_all_but_last(base_alg)
                slice_spec = None  # Consumed — don't apply as regular slice
            else:
                raise InternalSWError(f"[:-1] notation only supported for wide moves (Rw/r), got {base_alg}")

        if slice_spec is not None:
            # If base_alg is a MiddleSliceAlg (e.g., M), swap to the sliceable MM
            # so that [:]M, [1]M etc. work on the all-slices alg
            from cube.domain.algs.MiddleSliceAlg import MiddleSliceAlg
            if isinstance(base_alg, MiddleSliceAlg):
                base_alg = base_alg.get_base_alg()

            from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
            if not isinstance(base_alg, SliceAbleAlg):
                raise InternalSWError(f"Slice notation not supported for {base_alg}")
            # [:]X means "all slices" — keep the unsliced SliceAlg so str() = "[:]M"
            if isinstance(slice_spec, slice) and slice_spec.start is None and slice_spec.stop is None:
                pass  # base_alg stays as unsliced SliceAlg (e.g., Algs.MM)
            elif isinstance(slice_spec, slice):
                base_alg = base_alg[slice_spec.start:slice_spec.stop]
            else:
                base_alg = base_alg[slice_spec]

    # For bare SliceAlg tokens without explicit slice prefix (e.g., "M" not "[:]M"):
    # - compat_3x3=True: keep as _M/_E/_S (all middle slices) — for 3x3 solver algs on big cubes
    # - compat_3x3=False: M/E/S → MiddleSliceAlg (single middle slice)
    if not had_slice_prefix:
        from cube.domain.algs.SliceAlg import SliceAlg
        if isinstance(base_alg, SliceAlg) and not compat_3x3:
            from cube.domain.algs.Algs import Algs
            match base_alg.slice_name:
                case SliceName.M:
                    base_alg = Algs.M
                case SliceName.E:
                    base_alg = Algs.E
                case SliceName.S:
                    base_alg = Algs.S

    # For bare WideLayerAlg tokens (e.g., "Rw", "r"):
    # - compat_3x3=True: swap to all-but-last (RRw/rr) for CFOP solver algs on big cubes
    # - compat_3x3=False: keep as standard 2-layer wide move
    if not had_slice_prefix and compat_3x3:
        from cube.domain.algs.WideLayerAlg import WideLayerAlg
        if isinstance(base_alg, WideLayerAlg):
            base_alg = _wide_to_all_but_last(base_alg)

    # Apply modifiers in order
    result = base_alg
    for mod in modifiers:
        if mod == "prime":
            result = result.prime
        elif mod.startswith("mul:"):
            n = int(mod[4:])
            result = result * n

    return result


def _token_to_alg_no_slice(t: str) -> _Alg:
    """Convert a simple token (no slice, no prime, no x2) to an algorithm."""
    from cube.domain import algs
    from cube.domain.algs import Algs

    simple = Algs.Simple

    # First pass: check exact matches (including WideLayerAlg like 'r', 'u', etc.)
    for s in simple:
        if s.code == t:
            return s

    # Second pass: check case-insensitive matches for WholeCubeAlg (x == X)
    for s in simple:
        if isinstance(s, algs.WholeCubeAlg):
            if s.code.lower() == t:
                return s

    # Third pass: check if lowercase face letter should map to wide (r -> Rw)
    # This is for backward compatibility, but only if not already matched
    # as WideLayerAlg in the first pass
    for s in simple:
        if isinstance(s, algs.FaceAlg):
            if s.code.lower() == t:
                return _token_to_alg_no_slice(s.code + "w")

    raise InternalSWError(f"Unknown token {t}")


def _wide_to_all_but_last(wide: _Alg) -> _Alg:
    """Convert a WideLayerAlg to all-but-last mode (layers=ALL_BUT_LAST).

    Used for [:-1]Rw notation and compat_3x3 mode.
    """
    from cube.domain.algs.WideLayerAlg import ALL_BUT_LAST, WideLayerAlg
    assert isinstance(wide, WideLayerAlg)
    return wide.with_layers(ALL_BUT_LAST)
