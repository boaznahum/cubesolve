from cube.domain.algs import Algs, Alg, WholeCubeAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.model import Corner, Part, PartColorsID, Color
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider


class _2x2L1Corners(SolverHelper):
    __slots__: list[str] = []

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_2x2L1Corners")


    def _is_corners(self) -> bool:
        return Part.all_match_faces(self.white_face.corners)

    def is_corners(self) -> bool:
        """Check if Layer 1 corners are solved, accounting for whole-layer rotation.

        This method handles a rare edge case (~1 in 5000 solves) where the four
        corners are correctly positioned and oriented relative to each other, but
        the entire Layer 1 (including the cross) is rotated by 90°, 180°, or 270°
        relative to the rest of the cube.

        The method tries all four possible rotations (0°, 90°, 180°, 270°) and
        returns true if ANY rotation results in both corners AND cross being
        correctly aligned. This prevents false positives where corners appear
        solved but the layer needs rotation to align the cross with middle layer.

        Args:

        Returns:
            True if corners are solved (possibly after layer rotation to align cross).
            False if corners need solving.

        Note:
            This happens during big cube Layer-by-Layer solving when centers and
            edges are solved independently before corners, allowing the whole layer
            to end up rotated while corners remain correctly positioned.
        """

        wf: Face = self.white_face

        return self.cqr.rotate_face_and_check(wf, lambda: self._is_corners()) >= 0

    def solve(self) -> None:
        """Solve Layer 1 corners using the beginner method.

        Positions and orients all four Layer 1 corners correctly. Must be called
        AFTER the Layer 1 cross is solved, as corner solving preserves the cross.

        Args:

        Note:
            If corners are already solved (checked via is_corners()), this method
            returns immediately without making any moves.
        """

        if self.is_corners():
            return


        with self.ann.annotate(h1="Doing L1 Corners"):

            # in 2x2 we dont have faces colors so we just bring all up
            # we will optimize it to first bring the most solved face up
            #self.cmn.bring_face_up(self.white_face)

            self._do_corners()

    def _do_corners(self) -> None:

        white_color: Color = self.cmn.white

        with self._logger.tab(lambda : f"Doing L1 {white_color}  Corners"):


            # In 2x2 we don't have face colors, so what we have to do is to pick reference corenr and
            # solve all according to it
            # this is very not efficiency, but is a start

            # in optimization, we will try to find one that already face up on top
            first_corner = self.cube.cqr.find_corner(lambda c: white_color in c.colors_id)

            first_color_id: PartColorsID = first_corner.colors_id

            # ok now we need to bring it
            self.debug(lambda : f"Bringing {first_color_id} to FLU")
            self._bring_corner_face_to_flu_color_up(first_color_id, white_color)

            assert False, "That all I know for now"


            # # the colors ID of 4 corners
            # # the ids of where the corner are , not the color of the corners, so all must have some l1 on them
            # # we use codes because maybe position will be changed during the algorithm
            # color_codes: Sequence[PartColorsID] = Part.parts_id_by_pos(wf.corners)
            #
            # for code in color_codes:
            #     with self._logger.tab(lambda : f"Corner:{code}"):
            #         self._solve_corner(code)

    def _solve_corner(self, corner_id: PartColorsID):

        with self.ann.annotate(
                (corner_id, AnnWhat.Moved), (self.cube.front.corner_top_right, AnnWhat.FixedPosition),
                h2=lambda: f"Bringing {self.cube.find_corner_by_colors(corner_id).name_n_colors} to "
                           f"{self.cube.front.corner_top_right.name} "):
            self.__solve_corner(corner_id)

    def __solve_corner(self, corner_id: PartColorsID):

        _source_corner: Corner | None = None

        _target_corner: Corner | None = None

        # source corner
        def sc() -> Corner:
            nonlocal _source_corner
            if not _source_corner or _source_corner.colors_id != corner_id:
                _source_corner = self.cube.find_corner_by_colors(corner_id)
            return _source_corner

        # target corner
        def tc() -> Corner:
            nonlocal _target_corner
            if not _target_corner or _target_corner.position_id != corner_id:
                _target_corner = self.cube.find_corner_by_pos_colors(corner_id)
            return _target_corner

        if sc().match_faces:
            # because we have cross, so if it matches then it is in position
            return

        wf: Face = self.cube.up


        # Bring the target position FRU - Where
        self._bring_l1_target_corner_to_front_right_up(tc())

        # now bring source cornet into under it  FRD

        if sc().on_face(wf):
            self.debug(f"LO-Corners C1. source {sc()} is on top")
            self._bring_top_corner_to_f_r_d(sc())
        else:
            self.debug(f"LO-Corners C2. source {sc()} is on bottom")
            self._bring_bottom_corner_to_f_r_d(sc())

        # Now source is on FRD
        assert self.cube.front.corner_bottom_right is sc()

        # is the white is on the down
        if sc().face_color(wf.opposite) == wf.color:
            self.debug(f"{wf.color} is on bottom")
            self.op.play(Algs.R.prime + Algs.D.prime * 2 + Algs.R + Algs.D)
            assert self.cube.front.corner_bottom_right is sc()
            assert sc().face_color(wf.opposite) != wf.color

        if sc().face_color(wf.cube.front) == wf.color:
            self.op.play(Algs.D.prime + Algs.R.prime + Algs.D + Algs.R)
        else:
            self.op.play(Algs.D + Algs.F + Algs.D.prime + Algs.F.prime)

        assert sc().match_faces

    def _bring_l1_target_corner_to_front_right_up(self, c: Corner):
        """
        Preservers top layer cross

        :param c:
        :return:
        """

        wf: Face = self.cube.up
        assert c.on_face(wf)

        if wf.corner_bottom_right is c:
            return

        if wf.corner_top_right is c:
            return self.op.play(Algs.Y)

        if wf.corner_top_left is c:
            return self.op.play(Algs.Y * 2)

        if wf.corner_bottom_left is c:
            return self.op.play(-Algs.Y)

        raise ValueError(f"{c} is not on {wf}")

    def _bring_top_corner_to_f_r_d(self, c: Corner):
        """
        Preservers top layer cross
        doesn't preserve bottom layer
        we assume corner is on top

        :param c:
        :return:
        """

        wf: Face = self.cube.up
        assert c.on_face(wf)

        saved_id = c.colors_id

        if wf.corner_bottom_right is c:
            self.op.play(-Algs.R + -Algs.D + Algs.R)

        elif wf.corner_top_right is c:
            self.op.play(-Algs.B + -Algs.D + Algs.B)

        elif wf.corner_top_left is c:
            self.op.play(Algs.B + -Algs.D + - Algs.B)

        elif wf.corner_bottom_left is c:
            self.op.play(-Algs.F + -Algs.D + Algs.F)

        else:
            raise ValueError(f"{c} is not on {wf}")

        c = self.cube.find_corner_by_colors(saved_id)
        # now it is on button
        self._bring_bottom_corner_to_f_r_d(c)

    def _bring_bottom_corner_to_f_r_d(self, c: Corner):
        """
        doesn't preserve bottom layer

        Corner is on button need some D rotations to bring it to FRD position

        :param c:
        :return:
        """

        f: Face = self.cube.down
        assert c.on_face(f)

        if f.corner_top_right is c:
            pass  # nothing to do

        elif f.corner_bottom_right is c:
            self.op.play(-Algs.D)

        elif f.corner_bottom_left is c:
            self.op.play(-Algs.D * 2)

        elif f.corner_top_left is c:
            self.op.play(Algs.D)

        else:
            raise ValueError(f"{c} is not on {f}")

    def _bring_corner_face_to_flu_color_up(self, corner_id: PartColorsID, required_color: Color):

        """
        Position a corner at FLU with the required color facing up.

        Uses whole-cube rotations to orient the cube so that the face currently
        holding ``required_color`` becomes the Up face, then rotates U to place
        the corner at FLU. Verifies the result with assertions before returning.

        Algorithm (iterative, max 3 attempts):
          1. Find the corner by its color-id (position may change between iterations
             due to whole-cube rotations).
          2. If ``required_color`` is already on the Up face:
             - Rotate U to move the corner to FLU (U', U2, or U depending on position).
             - Assert the corner is at FLU with the correct color facing up.
             - Return.
          3. Otherwise, determine which face ``required_color`` is currently on,
             use ``Face2FaceTranslator`` to derive a whole-cube rotation that maps
             that face to Up, apply the simplified alg, and retry from step 1.

        :param corner_id: The color-id that uniquely identifies the corner.
        :param required_color: The color that must end up on the Up face.
        :raises InternalSWError: If the corner cannot be positioned within 3 iterations.
        """

        cube = self.cube
        target_face: Face = cube.up

        assert required_color in corner_id


        iteration = 0
        while iteration < 3:
            iteration += 1


            corner: Corner = cube.find_corner_by_colors(corner_id)


            # if it is already on up, just make sure color is up
            if corner.is_face_color(target_face) is required_color:
                # now just need to rotate
                # on which corner it ?

                if corner is cube.flu:
                    pass
                elif corner is cube.blu:
                    self.op.play(Algs.U.prime)
                elif corner is cube.bru:
                    self.op.play(Algs.U*2)
                elif corner is cube.fru:
                    self.op.play(Algs.U)
                else:
                    raise InternalSWError(f"How can it be ? {corner} is not on {target_face}")

                corner: Corner = cube.find_corner_by_colors(corner_id)
                assert corner is cube.flu
                assert corner.is_face_color(target_face) is required_color

                return None

            else:

                # must find see assert above
                on_face = corner.face_of_actual_color(required_color)

                # it is on different face
                result: list[tuple[WholeCubeAlg, int, Alg]] = Face2FaceTranslator.derive_whole_cube_alg_source_to_target(self.cube.layout, on_face.name, target_face.name)

                assert result
                alg: Alg = result[0][2].simplify()
                self.op.play(alg)
                continue # try again

        raise InternalSWError("Too many iterations")






