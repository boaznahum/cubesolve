import re
from typing import TYPE_CHECKING, TypeAlias

from cube.domain.exceptions import InternalSWError

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg
    from cube.domain.algs.SeqAlg import SeqAlg

_Alg: TypeAlias = "Alg"
_SeqAlg: TypeAlias = "SeqAlg"


def parse_alg(s: str) -> _Alg:
    """
    this is very naive patch version
    Currently doesn't support exp N and exp '  (only U2, U',...)
    """

    # We capture, so we get the spliteres two, such as '(' ')', we need to ignore the spaces
    # Empty matches for the pattern split the string only when not adjacent to a previous empty match.
    # https://docs.python.org/3/library/re.html#re.split
    # example:
    #  ["R'", ' ', 'U2', ' ', '', '(', 'R', ' ', 'U', ' ', "R'", ' ', 'U', ')', '', ' ', 'R']
    pattern = r"(\s+|\(|\))"
    tokens = re.split(pattern, s)

    p = _Parser(s, tokens)

    return p.parse()


class _Parser:

    def __init__(self, original: str, tokens: list[str]) -> None:
        super().__init__()
        self._tokens = tokens
        self._original = original

    def parse(self) -> _SeqAlg:
        result: list[Alg] = []
        self._parse(result, False)

        from cube.domain.algs.Algs import Algs

        return Algs.seq_alg(None, *result)

    def _parse(self, result: list[_Alg], nested: bool):

        from cube.domain.algs.Algs import Algs

        alg = Algs.no_op()

        while True:
            token = self.next_token()
            if not token:
                break

            if token == "(":
                self._parse(result, True)

            elif token == ')':
                if not nested:
                    raise InternalSWError(f"Un expected ')' in {self._original} ")
            elif token.isdigit():
                if not result:
                    raise InternalSWError(f"Un expected multiplier {token} in {self._original} ")
                prev = result.pop()
                at = prev * int(token)
                result.append(at)

            else:
                at = _token_to_alg(token)
                result.append(at)

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


def _token_to_alg(t) -> _Alg:
    from cube.domain import algs
    from cube.domain.algs import Algs

    if t.endswith("'"):
        alg = _token_to_alg(t[:-1])
        return alg.prime

    if t.endswith("2"):
        alg = _token_to_alg(t[:-1])
        return alg * 2

    simple = Algs.Simple

    for s in simple:
        code = s.code

        if code == t:
            return s

        if isinstance(s, algs.WholeCubeAlg):
            # x==X
            if code.lower() == t:
                return s

        if isinstance(s, algs.FaceAlg):
            if code.lower() == t:
                return _token_to_alg(code + "w")

    else:
        raise InternalSWError(f"Unknown token {t}")
