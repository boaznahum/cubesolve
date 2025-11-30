from typing import Tuple

from cube import config
from cube.algs import Alg, Algs, FaceAlg
from cube.app.app_exceptions import InternalSWError
from cube.model import Part
from cube.solver.common.BaseSolver import BaseSolver
from cube.solver.common.SolverElement import StepSolver


def use(_):
    pass


_status = None


class PLL(StepSolver):
    """
    Credits:
        https://cubingcheatsheet.com/algs3x_pll.html
        https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/permutate-the-last-layer-pll/

    """

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)
        self._set_debug_prefix("PLL")

    @property
    def is_solved(self):
        return Part.all_match_faces(self.yellow_face.parts)

    def is_rotate_and_solved(self):
        """
        Can be solved only by rotate
        :return:
        """
        return self.cqr.rotate_face_and_check(self.yellow_face, lambda: self.is_solved) >= 0

    def solve(self):

        if self.is_solved:
            return  # avoid rotating cube

        with self.ann.annotate(h1="PLL"):
            self._solve()

    def _solve(self):

        # maybe need only rotation

        if self._rotate_and_solve():
            return True  # done

        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_pll()

        assert self.is_solved

    def _rotate_and_solve(self):
        rotate_alg = self.cqr.rotate_face_and_check_get_alg(self.cmn.white_face.opposite,
                                                            lambda: self.is_solved)

        if rotate_alg:
            self.play(rotate_alg)

        return rotate_alg

    def _do_pll(self):

        description_alg = self._search_pll_alg()

        if description_alg is None:

            self._do_pll_parity()
            # in rare cases after parity it is solved with rotation only
            # so we don't recognize the state
            if self._rotate_and_solve():
                return True  # done

            description_alg = self._search_pll_alg()

        if description_alg is None:
            raise InternalSWError(f"Unknown PLL state")

        search_alg, description, alg = description_alg

        self.debug(f"Found PLL alg '{description}' {alg}")

        self.play((search_alg + alg).simplify())

        self._rotate_and_solve()  # because all our searching U

        assert self.is_solved

    def _search_pll_alg(self) -> Tuple[Alg, str, Alg] | None:

        """
        We need both Y and U !!!
        :return:
        """

        rotate_while_search = config.SOLVER_PLL_ROTATE_WHILE_SEARCH

        search_alg: Alg = Algs.no_op()

        try:
            for y in range(4):

                for u in range(4):

                    description_alg: Tuple[str, Alg] | None = self._get_state_alg()

                    if description_alg is not None:
                        return search_alg.simplify(), description_alg[0], description_alg[1]

                    if rotate_while_search:
                        self.play(Algs.U)  #
                    else:
                        Algs.U.play(self.cube)
                        search_alg += Algs.U

                # well we want to rotate, to leave cube in original state so it is easier to debug
                if rotate_while_search:
                    self.play(Algs.Y)  #
                else:
                    Algs.Y.play(self.cube)
                    search_alg = search_alg + Algs.Y

        finally:
            search_alg.simplify().inv().play(self.cube)

        return None

    def _get_state_alg(self) -> Tuple[str, Alg] | None:

        d_alg = self._get_state_alg_raw()

        if not d_alg:
            return None

        alg = d_alg[1]
        description = d_alg[0]
        self.debug(f"Found (raw) alg: {description} : {alg}")

        if isinstance(alg, str):
            alg = Algs.parse(alg)

        return description, alg

    def _get_state_alg_raw(self) -> Tuple[str, Alg | str] | None:
        """

        Credits to https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/orient-the-last-layer-oll/
                    https://cubingcheatsheet.com/algs3x_pll.html

        :return:
        """

        cube = self.cube

        def is_r0(permute: Tuple[Part, ...]):
            """
            permute = p1, p2, p3
            --> belongs
            p1 --> p2 --p3 --> p1
            :param permute: p1, p2 [p3]
            :return:
            """

            assert len(permute) > 1
            p: Part
            for i, p in enumerate(permute[:-1]):

                if p.required_position is not permute[i + 1]:
                    return False
            return permute[-1].required_position is permute[0]  # p3-->p1

        def is_r(*permutes: Tuple[Part, ...]):
            """
            --> belongs
            p1 --> p2 --p3 --> p1
            :param permutes: see :is_r0
            :return:
            """

            others = set(cube.up.parts)

            for permute in permutes:
                if not is_r0(permute):
                    return False
                others -= set(permute)

            return all(p.in_position for p in others)

        lu = cube.lu
        bu = cube.bu
        ru = cube.ru
        fu = cube.fu

        flu = cube.flu
        blu = cube.blu
        bru = cube.bru
        fru = cube.fru

        # Edges Only
        if is_r((ru, lu, fu)):
            return "Ua Perm", "M2' U M U2 M' U M2'"
        elif is_r((lu, ru, fu)):
            return "Ub Perm", "M2' U' M U2' M' U' M2'"

        elif is_r((lu, fu), (bu, ru)):
            return "Z Perm", "(M2' U' M2' U') M' (U2 M2' U2) M'"

        elif is_r((lu, ru), (fu, bu)):
            return "H Perm", "(M2' U M2') U2 (M2' U M2')"

        # Corners Only
        elif is_r((blu, bru, fru)):
            return "Aa Perm", "x (R' U R') D2 (R U' R') D2 R2 x'"

        elif is_r((blu, fru, bru)):
            return "Ab Perm", "x R2' D2 (R U R') D2 (R U' R) x'"

        elif is_r((flu, blu), (fru, bru)):
            return "E Perm", "x' (R U' R' D) (R U R' D') (R U R' D) (R U' R' D') x"

        # Swap Adjacent Corners

        elif is_r((lu, bu), (fru, bru)):
            return "Ra Perm", "y' (L U2 L' U2) L F' (L' U' L U) L F L2' U"

        elif is_r((blu, bru), (fu, ru)):
            return "Rb Perm", "(R' U2 R U2') R' F (R U R' U') R' F' R2 U'"

        elif is_r((blu, bru), (lu, bu)):
            return "Ja Perm", "y' (L' U' L F) (L' U' L U) L F' L2' U L U'"

        elif is_r((fru, bru), (fu, ru)):
            return "Jb Perm", "(R U R' F') (R U R' U') R' F R2 U' R' U'"

        elif is_r((lu, ru), (bru, fru)):
            return "T Perm", "(R U R' U') R' F R2 U' R' U' R U R' F'"

        elif is_r((fu, bu), (fru, bru)):
            return "F Perm", "(R' U' F') (R U R' U') (R' F R2 U') (R' U' R U) (R' U R)"

        # Swap Diagonal Corners

        elif is_r((blu, fru), (bu, ru)):
            return "V Perm", "(R' U R' U') y (R' F' R2 U') (R' U R' F) R F"

        elif is_r((blu, fru), (lu, bu)):
            return "Y Perm", "F (R U' R' U') (R U R' F') (R U R' U') (R' F R F')"

        elif is_r((flu, bru), (lu, ru)):
            return "Na Perm", "(R U R' U) (R U R' F') (R U R' U') (R' F R2 U') R' U2 (R U' R')"

        elif is_r((blu, fru), (lu, ru)):
            return "Nb Perm", "(R' U R U') (R' F' U' F) (R U R' F) R' F' (R U' R)"

        # Double Cycles

        elif is_r((flu, blu, bru), (lu, ru, bu)):
            return "Ga Perm", "R2 U (R' U R' U') (R U' R2) D U' (R' U R D') U"

        elif is_r((flu, bru, blu), (ru, lu, bu)):
            return "Gb Perm", "(F' U' F) (R2 u R' U) (R U' R u') R2'"

        elif is_r((blu, flu, fru), (lu, ru, fu)):
            return "Gc Perm", "R2 U' (R U' R U) (R' U R2 D') (U R U' R') D U'"
        elif is_r((flu, blu, bru), (lu, fu, bu)):
            return "Gd Perm", "(R U R') y' (R2 u' R U') (R' U R' u) R2"

        else:
            return None

    def _do_pll_parity(self)  -> None:
        """
        I'm handing only Swap 2 Edges Diagonal and repeating PLL
        :return:
        """
        #  https://cubingcheatsheet.com/algs6x.html

        # Swap 2 Edges Diagonal
        # 6x6
        # 2-3Rw2 U2 2-3Rw2 1-3Uw2 2-3Rw2 1-3Uw 2-3Uw R2 (U R U) (R' U' R' U') (R' U R' U')

        # 4x4

        size = self.cube.size
        assert size % 2 == 0

        U: FaceAlg = Algs.U
        R = Algs.R
        rw: Alg = Algs.R[2:size // 2]
        rw2: Alg = rw * 2
        uwx: Alg = U[1:size // 2]
        uwy = U[2:size // 2]

        with self.annotate(h2="PLL Parity"):
            #     2-3Rw2 U2    2-3Rw2 1-3Uw2  2-3Rw2 1-3Uw 2-3Uw R2 (U R U) (R' U' R' U') (R' U R' U')
            # I tried to remove the last part
            #  but in some case it doesn't bring again to pre PLL
            # In this way I handle only
            alg = rw2 + U * 2 + rw2 + uwx * 2 + rw2 + uwx + uwy + Algs.parse("R2 (U R U) (R' U' R' U') (R' U R' U')")
            self.play(alg)
