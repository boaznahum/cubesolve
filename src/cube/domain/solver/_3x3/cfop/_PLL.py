from typing import Tuple

from cube.domain.algs import Algs, FaceAlg
from cube.domain.algs.Alg import Alg
from cube.domain.exceptions import (
    EvenCubeCornerSwapException,
    EvenCubeEdgeSwapParityException,
    InternalSWError,
)
from cube.domain.model import Part
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.SolverElement import StepSolver


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
            # Unknown PLL state - check what type of parity
            if self._is_corner_parity():
                # Corner parity: raise exception for orchestrator to fix
                self.debug("PLL: Corner parity detected (2 corners in position)")
                raise EvenCubeCornerSwapException()

            # Edge swap parity: fix internally and retry
            self._do_edge_swap_parity()
            if self._rotate_and_solve():
                return
            description_alg = self._search_pll_alg()

        if description_alg is None:
            raise InternalSWError("Unknown PLL state")

        search_alg, description, alg = description_alg

        self.debug(f"Found PLL alg '{description}' {alg}")

        self.play((search_alg + alg).simplify())

        self._rotate_and_solve()  # because all our searching U

        assert self.is_solved

    def _is_corner_parity(self) -> bool:
        """
        Check if cube has corner parity (2 corners in position on even cube).

        Also brings a corner to front-right position (same as L3Corners).
        This ensures the cube is in the expected state for fix_corner_parity().

        Returns:
            True if corner parity detected (2 corners in position on even cube)
        """
        if self.cube.n_slices % 2 != 0:
            return False  # Only even cubes can have parity

        yf = self.yellow_face

        # Find a corner in position and bring to front-right (like L3Corners does)
        in_position = None
        for c in yf.corners:
            if c.in_position:
                in_position = c
                break

        if in_position:
            # Bring to front-right via Y rotation
            if yf.corner_top_right is in_position:
                self.play(Algs.Y)
            elif yf.corner_top_left is in_position:
                self.play(Algs.Y * 2)
            elif yf.corner_bottom_left is in_position:
                self.play(Algs.Y.prime)
            # If corner_bottom_right, already in position

        corners_in_position = sum(c.in_position for c in yf.corners)
        return corners_in_position == 2

    def _do_edge_swap_parity(self) -> None:
        """
        Handle edge swap parity in PLL.

        This fixes the "Swap 2 Edges Diagonal" case that can occur on even cubes
        when edges are in an impossible permutation.

        For shadow 3x3 cubes (used by cage solver), we raise an exception instead
        of fixing locally - the cage solver will fix parity on the real cube.

        Note: This is handled internally (not via exception) because the reducer
        doesn't have a separate edge swap parity fix for PLL. OLL edge parity
        (orientation) is different from PLL edge parity (permutation).
        """
        size = self.cube.size

        # On shadow 3x3, raise exception for cage solver to handle
        if self.cube.is_even_cube_shadow:
            self.debug("PLL: Edge swap parity on shadow cube - raising exception")
            raise EvenCubeEdgeSwapParityException()

        assert size % 2 == 0, "Edge swap parity fix only works on even cubes"

        U: FaceAlg = Algs.U
        rw: Alg = Algs.R[2:size // 2]
        rw2: Alg = rw * 2
        uwx: Alg = U[1:size // 2]
        uwy = U[2:size // 2]

        with self.annotate(h2="PLL Edge Swap Parity"):
            # Swap 2 Edges Diagonal algorithm
            # https://cubingcheatsheet.com/algs6x.html
            alg = rw2 + U * 2 + rw2 + uwx * 2 + rw2 + uwx + uwy + Algs.parse("R2 (U R U) (R' U' R' U') (R' U R' U')")
            self.play(alg)

    def _search_pll_alg(self) -> Tuple[Alg, str, Alg] | None:

        """
        We need both Y and U !!!
        :return:
        """

        rotate_while_search = self.cube.config.solver_pll_rotate_while_search

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
