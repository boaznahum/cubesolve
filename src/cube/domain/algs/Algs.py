from typing import Sequence

from cube.domain.algs._parser import parse_alg
from cube.domain.algs.Alg import Alg
from cube.domain.algs.AnnotationAlg import AnnotationAlg
from cube.domain.algs.FaceAlg import _B, _D, _F, _L, _R, _U, FaceAlg
from cube.domain.algs.Scramble import _Scramble, _scramble
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.algs.MiddleSliceAlg import MiddleSliceAlg
from cube.domain.algs.SliceAlg import _E, _M, _S, SliceAlg
from cube.domain.algs.WholeCubeAlg import _X, _Y, _Z
from cube.domain.algs.WideLayerAlg import ALL_BUT_LAST, WideLayerAlg
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

    API: Algs.MM.get_face_name() → L, Algs.EE.get_face_name() → D, Algs.SS.get_face_name() → F

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
    LLw = WideLayerAlg(FaceName.L, ALL_BUT_LAST)

    B = _B()
    BBw = WideLayerAlg(FaceName.B, ALL_BUT_LAST)

    D = _D()
    DDw = WideLayerAlg(FaceName.D, ALL_BUT_LAST)

    R = _R()
    RRw = WideLayerAlg(FaceName.R, ALL_BUT_LAST)
    # X, Y, Z: Identity/naming only - _X() binds to AxisName.X (just gives the alg its name).
    # Geometric relationships (X↔R axis, direction) are defined in CubeLayout.get_axis_face()
    X = _X()
    M = MiddleSliceAlg(SliceName.M)   # Single middle slice. str() = "M".
    MM = _M()   # All middle slices (sliceable). str() = "[:]M".
    U = _U()
    UUw = WideLayerAlg(FaceName.U, ALL_BUT_LAST)
    Y = _Y()  # See X comment above for X/Y/Z design notes
    E = MiddleSliceAlg(SliceName.E)   # Single middle slice over D axis. str() = "E".
    EE = _E()   # All middle slices over D axis (sliceable). str() = "[:]E".

    F = _F()
    FFw = WideLayerAlg(FaceName.F, ALL_BUT_LAST)
    Z = _Z()  # See X comment above for X/Y/Z design notes
    S = MiddleSliceAlg(SliceName.S)   # Single middle slice over F axis. str() = "S".
    SS = _S()   # All middle slices over F axis (sliceable). str() = "[:]S".

    # =========================================================================
    # Adaptive Wide Moves — all-but-last layers
    # =========================================================================
    # These move face + ALL inner layers, adapting to cube size at play time.
    # str() = "[:-1]Rw" / "[:-1]r"
    #
    # RRw and rr are identical in behavior (both use WideLayerAlg with ALL_BUT_LAST).
    # RRw uses uppercase+w form: [:-1]Rw (WCA official notation)
    # rr uses lowercase form: [:-1]r (informal notation)
    # Both kept as sugar for readability in solver code.
    #
    # On 3x3: moves 2 layers (face + 1 inner)
    # On NxN: moves N-1 layers (face + all inner), opposite face stays fixed
    #
    # Used by CFOP F2L to work correctly on shadow 3x3 AND real NxN cubes.
    # =========================================================================
    dd = WideLayerAlg(FaceName.D, ALL_BUT_LAST, lowercase=True)
    uu = WideLayerAlg(FaceName.U, ALL_BUT_LAST, lowercase=True)
    rr = WideLayerAlg(FaceName.R, ALL_BUT_LAST, lowercase=True)
    ll = WideLayerAlg(FaceName.L, ALL_BUT_LAST, lowercase=True)  # noqa: E741
    ff = WideLayerAlg(FaceName.F, ALL_BUT_LAST, lowercase=True)
    bb = WideLayerAlg(FaceName.B, ALL_BUT_LAST, lowercase=True)

    # =========================================================================
    # Standard Wide Moves (WCA notation)
    # =========================================================================
    # Rw = r = 2 outermost layers (default). 3Rw = 3r = 3 layers.
    # See WideLayerAlg.py for detailed documentation.
    # =========================================================================
    Rw = WideLayerAlg(FaceName.R)
    Lw = WideLayerAlg(FaceName.L)
    Uw = WideLayerAlg(FaceName.U)
    Dw = WideLayerAlg(FaceName.D)
    Fw = WideLayerAlg(FaceName.F)
    Bw = WideLayerAlg(FaceName.B)
    r = WideLayerAlg(FaceName.R, lowercase=True)
    l = WideLayerAlg(FaceName.L, lowercase=True)  # noqa: E741
    u = WideLayerAlg(FaceName.U, lowercase=True)
    d = WideLayerAlg(FaceName.D, lowercase=True)
    f = WideLayerAlg(FaceName.F, lowercase=True)
    b = WideLayerAlg(FaceName.B, lowercase=True)

    _NO_OP = SeqAlg(None)
    NOOP = _NO_OP  # Public alias for no-op algorithm

    @staticmethod
    def seq_alg(name: str | None, *algs: Alg) -> SeqAlg:
        return SeqAlg(name, *algs)

    @staticmethod
    def seq(*algs: Alg) -> SeqAlg:
        return SeqAlg(None, *algs)

    Simple: Sequence[NSimpleAlg] = [L, Lw,
                                    R, Rw, X, MM,
                                    U, Uw, EE, Y,
                                    F, Fw, Z, SS,
                                    B, Bw,
                                    D, Dw,
                                    # Standard wide moves (lowercase form)
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
                return cls.EE

            case SliceName.S:
                return cls.SS

            case SliceName.M:
                return cls.MM

            case _:
                raise InternalSWError(f"Unknown slice name {slice_name}")

    @classmethod
    def no_op(cls) -> Alg:
        return Algs._NO_OP

    @classmethod
    def parse(cls, alg: str, *, compat_3x3: bool = False) -> Alg:
        return parse_alg(alg, compat_3x3=compat_3x3)

    @classmethod
    def parse_multiline(cls, text: str) -> Alg:
        """Parse a multi-line algorithm string.

        Supports:
            - Lines starting with # are comments (ignored)
            - Empty lines are ignored (use for readability)
            - All non-empty, non-comment lines are concatenated into ONE algorithm

        Example:
            alg = Algs.parse_multiline('''
                # Flip FU edge
                U'2 B'
                R' U R
            ''')

        Args:
            text: Multi-line string containing the algorithm

        Returns:
            Parsed Alg object

        Raises:
            ValueError: If text is empty or contains only comments
        """
        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)

        if not lines:
            raise ValueError("Algorithm text is empty or contains only comments")

        return parse_alg(" ".join(lines))
