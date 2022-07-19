from typing import Optional, Tuple

from cube.algs import Alg, Algs
from cube.app_exceptions import InternalSWError
from cube.model import Part
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.solver_element import StepSolver


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

        rotate_alg = self.cqr.rotate_face_and_check_get_alg(self.cmn.white_face.opposite,
                                                            lambda: self.is_solved)

        if rotate_alg:
            self.play(rotate_alg)
            return  # done

        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_pll()

        assert self.is_solved

    def _do_pll(self):

        description_alg = self._search_pll_alg()

        if description_alg is None:
            raise InternalSWError(f"Unknown PLL state")

        description, alg = description_alg

        self.debug(f"Found PLL alg '{description}' {alg}")

        self.play(alg)

        assert self.is_solved

    def _search_pll_alg(self) -> Tuple[str, Alg] | None:

        """
        We need both Y and U !!!
        :return:
        """

        for y in range(4):

            for u in range(4):

                description_alg: tuple[str, Alg] | None = self._get_state_alg()

                if description_alg is not None:
                    return description_alg

                self.play(Algs.U)  #

            # well we want to rotate, to leave cube in original state so it is easier to debug
            self.play(Algs.Y)  #

        return None

    def _get_state_alg(self) -> Optional[Tuple[str, Alg]]:

        d_alg = self._get_state_alg_raw()

        if not d_alg:
            return None

        alg = d_alg[1]
        description = d_alg[0]
        self.debug(f"Found (raw) alg: {description} : {alg}")

        if isinstance(alg, str):
            alg = Algs.parse(alg)

        return description, alg

    def _get_state_alg_raw(self) -> Optional[Tuple[str, Alg | str]]:
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

                if not p.required_position is permute[i + 1]:
                    return False
            return permute[-1].required_position is permute[0]  # p3-->p1

        def is_r(*permutes: Tuple[Part, ...]):
            """
            --> belongs
            p1 --> p2 --p3 --> p1
            :param p1:
            :param p2:
            :param p3:
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


        if is_r((ru, lu, fu)):
            return "Ua Perm", "M2' U M U2 M' U M2'"
        elif is_r((lu, ru, fu)):
            return "Ub Perm", "M2' U' M U2' M' U' M2'"

        elif is_r((flu, blu, bru), (lu, ru, bu)):
            return "Ga Perm", "R2 U (R' U R' U') (R U' R2) D U' (R' U R D') U"

        elif is_r((flu, bru, blu), (ru, lu, bu)):
            return "Gb Perm", "(F' U' F) (R2 u R' U) (R U' R u') R2'"

        elif is_r((blu, flu, fru),(lu, ru, fu)):
            return "Gc Perm", "R2 U' (R U' R U) (R' U R2 D') (U R U' R') D U'"
        elif is_r((flu, blu, bru),(lu, fu, bu)):
            return "Gd Perm", "(R U R') y' (R2 u' R U') (R' U R' u) R2"

        else:
            return None
