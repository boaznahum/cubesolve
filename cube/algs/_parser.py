from typing import TYPE_CHECKING, TypeAlias, Optional

from cube.app_exceptions import InternalSWError

if TYPE_CHECKING:
    from cube.algs import Alg

_Alg: TypeAlias = "Alg"


def parse_alg(s: str) -> _Alg:
    "this is very naive patch version"
    from ._algs import Algs

    tokens = s.split()

    alg = Algs.no_op()
    for t in tokens:
        at = _token_to_alg(t)
        if at:
            alg = alg + at

    return alg


def _token_to_alg(t) -> Optional[_Alg]:
    from cube import algs
    from cube.algs import Algs

    if t == "(" or t == ")":
        # till we support them
        return None

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
