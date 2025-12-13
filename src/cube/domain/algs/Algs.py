import warnings
from typing import Sequence

from cube.domain.algs.Alg import Alg
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.DoubleLayerAlg import DoubleLayerAlg
from cube.domain.algs.FaceAlg import FaceAlg, _L, _B, _D, _R, _U, _F
from cube.domain.algs.Scramble import _scramble, _Scramble
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.algs.SliceAlg import SliceAlg, _M, _E, _S
from cube.domain.algs.WholeCubeAlg import WholeCubeAlg, _X, _Y, _Z
from cube.domain.algs._parser import parse_alg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName
from cube.domain.model.cube_slice import SliceName


class Algs:
    """
    About Notations
    https://alg.cubing.net/

    E, S, M is according to the above


    X - OK
    Y - OK
    Z - OK


    """
    # When played, it simply refreshes GUI
    # So it used by annotation tools, after they changed some model(text, cube)
    AN: AnnotationAlg = AnnotationAlg()

    L: FaceAlg = _L()
    # noinspection PyPep8Naming
    Lw: DoubleLayerAlg = DoubleLayerAlg(L)

    B: FaceAlg = _B()
    Bw: DoubleLayerAlg = DoubleLayerAlg(B)

    D: FaceAlg = _D()
    Dw: DoubleLayerAlg = DoubleLayerAlg(D)

    R: FaceAlg = _R()
    Rw: DoubleLayerAlg = DoubleLayerAlg(R)
    X: WholeCubeAlg = _X()  # Entire cube or R
    M: SliceAlg = _M()  # Middle over L
    _MM: SliceAlg = _M().simple_mul(-1)  # Middle over L

    # noinspection PyPep8Naming
    @staticmethod
    def MM() -> SliceAlg:
        warnings.warn("Use M'", DeprecationWarning, 2)

        return Algs._MM

    U: FaceAlg = _U()
    Uw: DoubleLayerAlg = DoubleLayerAlg(U)
    Y: WholeCubeAlg = _Y()  # Entire over U
    E: SliceAlg = _E()  # Middle slice over D

    F: FaceAlg = _F()
    Fw: DoubleLayerAlg = DoubleLayerAlg(F)
    Z: WholeCubeAlg = _Z()  # Entire over F
    S: SliceAlg = _S()  # Middle over F

    _NO_OP: SeqAlg = SeqAlg(None)

    @staticmethod
    def seq_alg(name: str | None, *algs: Alg) -> SeqAlg:
        return SeqAlg(name, *algs)

    Simple: Sequence[NSimpleAlg] = [L, Lw,
                                    R, Rw, X, M,
                                    U, Uw, E, Y,
                                    F, Fw, Z, S,
                                    B, Bw,
                                    D, Dw,
                                    ]

    RU = SeqAlg("RU(top)", R, U, -R, U, R, U * 2, -R, U)

    UR = SeqAlg("UR(top)", U, R, -U, -L, U, -R, -U, L)

    RD = SeqAlg("RD(top)", ((R.prime + D.prime + R + D) * 2 + U) * 3)

    @staticmethod
    def lib() -> Sequence[Alg]:
        return [
            Algs.RU,
            Algs.UR
        ]

    @classmethod
    def scramble1(cls, cube_size):
        return _scramble(cube_size, "scramble1")

    @classmethod
    def scramble(cls, cube_size, seed=None, seq_length: int | None = None) -> SeqAlg:
        return _scramble(cube_size, seed, seq_length)

    @classmethod
    def is_scramble(cls, alg: Alg):
        return isinstance(alg, _Scramble)

    @classmethod
    def alg(cls, name, *algs: Alg) -> Alg:
        return SeqAlg(name, *algs)

    @classmethod
    def simplify(cls, *algs: Alg) -> Alg:
        return cls.alg(None, *algs).simplify()

    @classmethod
    def count(cls, *algs: Alg) -> int:
        return cls.alg(None, *algs).count()

    @classmethod
    def of_face(cls, face: FaceName) -> FaceAlg:

        match face:

            case FaceName.F:
                return cls.F

            case FaceName.B:
                return cls.B

            case FaceName.L:
                return cls.L

            case FaceName.R:
                return cls.R

            case FaceName.U:
                return cls.U

            case FaceName.D:
                return cls.D

            case _:
                raise InternalSWError(f"Unknown face name {face}")

    @classmethod
    def of_slice(cls, slice_name: SliceName) -> SliceAbleAlg:

        match slice_name:

            case SliceName.E:
                return cls.E

            case SliceName.S:
                return cls.S

            case SliceName.M:
                return cls.M

            case _:
                raise InternalSWError(f"Unknown slice name {slice_name}")

    @classmethod
    def no_op(cls) -> Alg:
        return Algs._NO_OP

    @classmethod
    def parse(cls, alg: str) -> Alg:
        return parse_alg(alg)
