import warnings
from typing import Sequence

from cube.domain.algs._parser import parse_alg
from cube.domain.algs.Alg import Alg
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.DoubleLayerAlg import DoubleLayerAlg
from cube.domain.algs.FaceAlg import _B, _D, _F, _L, _R, _U, FaceAlg
from cube.domain.algs.Scramble import _Scramble, _scramble
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.algs.SliceAlg import _E, _M, _S, SliceAlg
from cube.domain.algs.WholeCubeAlg import _X, _Y, _Z
from cube.domain.algs.WideFaceAlg import _wb, _wd, _wf, _wl, _wr, _wu
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName
from cube.domain.model.cube_slice import SliceName


class Algs:
    """
    About Notations
    https://alg.cubing.net/

    ================================================================================
    SLICE ALGORITHMS (M, E, S)
    ================================================================================

    ┌──────┬────────────┬────────────────┬───────────────────────────────────────┐
    │Slice │   Axis     │ Affects Faces  │ Rotation Direction                    │
    ├──────┼────────────┼────────────────┼───────────────────────────────────────┤
    │  M   │  L ↔ R     │  F, U, B, D    │ Like L (clockwise when viewing L)     │
    │  E   │  U ↔ D     │  F, R, B, L    │ Like D (clockwise when viewing D)     │
    │  S   │  F ↔ B     │  U, R, D, L    │ Like F (clockwise when viewing F)     │
    └──────┴────────────┴────────────────┴───────────────────────────────────────┘

    API: Algs.M.get_face_name() → L, Algs.E.get_face_name() → D, Algs.S.get_face_name() → F

    Slice Traversal (content movement during rotation):
        M: F → U → B → D → F  (vertical cycle, like L rotation)
        E: R → B → L → F → R  (horizontal cycle, like D rotation)
        S: U → R → D → L → U  (around F/B axis, like F rotation)

    Slice Indexing (1-based, NOT 0-based!):
        For an NxN cube: n_slices = N - 2 (number of inner slices)
        Valid indices: 1, 2, ..., n_slices

        WARNING: E[0], M[0], S[0] are INVALID! Indices start at 1.
        Internally, normalize_slice_index() converts: public[i] → internal[i-1]

        Example for 5x5 cube (n_slices = 3):
            E[1]  - first inner slice (closest to D face)  → internal index 0
            E[2]  - middle slice                           → internal index 1
            E[3]  - last inner slice (closest to U face)   → internal index 2
            E     - all slices together

        Where Slice[1] begins (same side as reference face):
            M[1] - closest to L face (the reference face for M)
            E[1] - closest to D face (the reference face for E)
            S[1] - closest to F face (the reference face for S)

        Visual for 5x5 cube (M slice example, viewing from front):

                      L face                              R face
                         │                                   │
                         │   M[1]  M[2]  M[3]                │
                         │     ↓     ↓     ↓                 │
                         │   ┌───┐ ┌───┐ ┌───┐               │
                         └───┤   ├─┤   ├─┤   ├───────────────┘
                             │   │ │   │ │   │
                             └───┘ └───┘ └───┘
                              ↑           ↑
                         closest      closest
                          to L         to R

    ================================================================================
    WHOLE-CUBE ROTATIONS (X, Y, Z)
    ================================================================================

    ┌──────┬─────────────────┬────────────────────────────────────────────────────┐
    │Whole │ Implementation  │ Rotation Direction                                 │
    ├──────┼─────────────────┼────────────────────────────────────────────────────┤
    │  X   │ M' + R + L'     │ Like R (clockwise facing R) - OPPOSITE of M's L!   │
    │  Y   │ E' + U + D'     │ Like U (clockwise facing U) - OPPOSITE of E's D!   │
    │  Z   │ S + F + B'      │ Like F (clockwise facing F) - SAME as S's F!       │
    └──────┴─────────────────┴────────────────────────────────────────────────────┘

    ================================================================================
    """
    # When played, it simply refreshes GUI
    # So it used by annotation tools, after they changed some model(text, cube)
    AN = AnnotationAlg()

    L = _L()
    # noinspection PyPep8Naming
    Lw = DoubleLayerAlg(L)

    B = _B()
    Bw = DoubleLayerAlg(B)

    D = _D()
    Dw = DoubleLayerAlg(D)

    R = _R()
    Rw = DoubleLayerAlg(R)
    # X, Y, Z: Identity/naming only - _X() binds to AxisName.X (just gives the alg its name).
    # Geometric relationships (X↔R axis, direction) are defined in CubeLayout.get_axis_face()
    X = _X()
    M = _M()  # Middle slice over L axis. See class docstring for M/E/S details.
    _MM = _M().simple_mul(-1)  # Middle over L

    # noinspection PyPep8Naming
    @staticmethod
    def MM() -> SliceAlg:
        warnings.warn("Use M'", DeprecationWarning, 2)

        return Algs._MM

    U = _U()
    Uw = DoubleLayerAlg(U)
    Y = _Y()  # See X comment above for X/Y/Z design notes
    E = _E()  # Middle slice over D axis. See class docstring for M/E/S details.

    F = _F()
    Fw = DoubleLayerAlg(F)
    Z = _Z()  # See X comment above for X/Y/Z design notes
    S = _S()  # Middle slice over F axis. See class docstring for M/E/S details.

    # =========================================================================
    # Adaptive Wide Moves (lowercase notation)
    # =========================================================================
    # These move face + ALL inner layers, adapting to cube size at play time.
    # See WideFaceAlg.py for detailed documentation.
    #
    # On 3x3: same as uppercase (no inner layers)
    # On NxN: moves N-1 layers (face + all inner), opposite face stays fixed
    #
    # Used by CFOP F2L to work correctly on shadow 3x3 AND real NxN cubes.
    # =========================================================================
    d = _wd()  # D + all inner layers (U stays fixed)
    u = _wu()  # U + all inner layers (D stays fixed)
    r = _wr()  # R + all inner layers (L stays fixed)
    l = _wl()  # L + all inner layers (R stays fixed)  # noqa: E741 TODO: fix
    f = _wf()  # F + all inner layers (B stays fixed)
    b = _wb()  # B + all inner layers (F stays fixed)

    _NO_OP = SeqAlg(None)
    NOOP = _NO_OP  # Public alias for no-op algorithm

    @staticmethod
    def seq_alg(name: str | None, *algs: Alg) -> SeqAlg:
        return SeqAlg(name, *algs)

    @staticmethod
    def seq(*algs: Alg) -> SeqAlg:
        return SeqAlg(None, *algs)

    Simple: Sequence[NSimpleAlg] = [L, Lw,
                                    R, Rw, X, M,
                                    U, Uw, E, Y,
                                    F, Fw, Z, S,
                                    B, Bw,
                                    D, Dw,
                                    # Adaptive wide moves (lowercase)
                                    f, u, r, l, d, b,
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
    def of_slice(cls, slice_name: SliceName) -> SliceAlg:

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
