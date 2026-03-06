from cube.domain.algs import Algs, Alg, WholeCubeAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.model import Corner, PartColorsID, Color
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider


class _2x2L1Corners(SolverHelper):
    """Layer 1 corner solver for 2x2 cubes (beginner method).

    IMPORTANT — No face colors:
        A 2x2 cube has no center pieces, so faces have no inherent color.
        This solver must NEVER access ``Face.color``, ``self.white_face``,
        ``cube.color_2_face()``, or any other API that reads face colors
        (even through a ``FacesColorsProvider``).

        Instead, the solver works entirely with *corner sticker colors*
        (``Part.face_color``, ``Part.is_face_color``, ``Part.colors_id``)
        and the configured start color (``self.cmn.white``).

        The caller (``_L1``) sets up a ``FacesColorsProvider`` for its own
        bookkeeping, but this class does not rely on it.
    """

    __slots__: list[str] = []

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_2x2L1Corners")


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

        # not true, maybe it is not on up face !!!
        white_color: Color = self.cmn.white

        with self.op.with_query_restore_state():
            for i in range(4):
                if not self._is_fru_solved(white_color):
                    return False
                if i < 3:
                    self.op.play(Algs.U)

        return True


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

            self._do_corners()

    def _do_corners(self) -> None:
        """Solve all four L1 corners using a reference-corner approach.

        Since a 2x2 cube has no fixed centers, there are no predefined face colors.
        Instead, this method picks an arbitrary corner containing the white color as
        a reference, positions it at FLU with white facing up, then solves the
        remaining three corners (FRU) one at a time by rotating U between solves.
        """

        white_color: Color = self.cmn.white

        with self._logger.tab(lambda : f"Doing L1 {white_color}  Corners"):


            # In 2x2 we don't have face colors, so what we have to do is to pick reference corenr and
            # solve all according to it
            # this is very not efficiency, but is a start

            # in optimization, we will try to find one that already face up on top
            first_corner = self.cube.cqr.find_corner(lambda c: white_color in c.colors_id)

            first_color_id: PartColorsID = first_corner.colors_id

            # ok now we need to bring it
            with self._logger.tab(lambda : f"Bringing first reference {first_color_id} to FLU"):
                self._bring_corner_face_to_flu_color_up(first_color_id, white_color)



            # so what left to be done
            # we need three time to fix the FRU corner in which the FLU is reference
            for _ in range(2):
                self._solve_fru_corner(white_color)
                self.op.play(Algs.U)

            # third time
            self._solve_fru_corner(white_color)


    def _is_fru_solved(self, white_color: Color) -> bool:
        """Check whether the FRU corner is correctly solved relative to the FLU reference.

        Determines the expected FRU corner by reading the front-face color from
        FLU, then finds the corner that has both white and front colors (but not
        the third FLU color). Returns True only if that corner is at FRU with
        the correct color orientation.

        Returns False early if FLU doesn't have exactly 3 distinct colors
        (e.g. during initial positioning before the reference corner is set).
        """

        cube = self.cube
        front = cube.front
        front_color: Color = cube.flu.face_color(front)
        flu_other_color_set = self.cube.flu.colors_id - {white_color, front_color}


        if len(flu_other_color_set) > 1:
            return False

        assert len(flu_other_color_set) == 1

        flu_other_color = next(iter(flu_other_color_set))

        def is_fru_target(c: Corner) -> bool:
            cid = c.colors_id
            return white_color in cid and front_color in cid and flu_other_color not in cid

        source_corner: Corner = self.cube.cqr.find_corner(is_fru_target)

        if source_corner is not cube.fru:
            return False

        if source_corner.face_color(front) != front_color:
            return False

        if source_corner.face_color(cube.up) != white_color:
            return False

        return True




    def _solve_fru_corner(self, white_color: Color) -> None:
        """Solve the FRU corner while preserving the FLU reference corner.

        Identifies which corner belongs at FRU by reading the front-face color
        from the FLU reference corner, then finding the corner with white and
        front colors (excluding the third FLU color).

        Moves the target corner to FRD (bringing it down from top if needed),
        then applies one of two insertion algorithms depending on whether white
        faces front or right. If white faces down, an extra setup move flips it
        to a side face first.
        """

        if self._is_fru_solved(white_color):
            return

        # find the right corner
        front_color: Color = self.cube.flu.face_color(self.cube.front)
        flu_other_color_set = self.cube.flu.colors_id - { white_color , front_color}
        assert len(flu_other_color_set) == 1
        flu_other_color = next(iter(flu_other_color_set))

        def is_fru_target(c: Corner) -> bool:
            cid = c.colors_id
            return white_color in cid and front_color in cid and flu_other_color not in cid

        source_corner: Corner = self.cube.cqr.find_corner(is_fru_target)

        # no faces so we cannot check for match

        source_corner_id: PartColorsID = source_corner.colors_id

        with self._logger.tab(lambda : f"Solving FRU <-- {[*source_corner_id]}"):


            _source_corner: Corner | None = None

            # source corner
            def sc() -> Corner:
                nonlocal _source_corner
                if not _source_corner or _source_corner.colors_id != source_corner_id:
                    _source_corner = self.cube.find_corner_by_colors(source_corner_id)
                assert _source_corner
                return _source_corner

            wf: Face = self.cube.up


            # now bring source cornet into under it  FRD

            if sc().on_face(wf):
                self.debug(f"LO-Corners C1. source {sc()} is on top")
                self._bring_top_corner_to_f_r_d(sc())
            else:
                self.debug(f"LO-Corners C2. source {sc()} is on bottom")
                self._bring_bottom_corner_to_f_r_d(sc())

            # Now source is on FRD
            assert self.cube.frd is sc()

            # is the white is on the down
            if sc().face_color(wf.opposite) == white_color:
                self.debug(f"{white_color} is on bottom")
                self.op.play(Algs.R.prime + Algs.D.prime * 2 + Algs.R + Algs.D)
                assert self.cube.front.corner_bottom_right is sc()
                assert sc().face_color(wf.opposite) != white_color

            if sc().face_color(wf.cube.front) == white_color:
                self.op.play(Algs.D.prime + Algs.R.prime + Algs.D + Algs.R)
            else:
                self.op.play(Algs.D + Algs.F + Algs.D.prime + Algs.F.prime)

            assert self._is_fru_solved(white_color)

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

                corner = cube.find_corner_by_colors(corner_id)
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







