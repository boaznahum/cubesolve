from collections.abc import Iterator
from typing import Tuple

import algs
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs import Algs
from app_exceptions import InternalSWError
from cube_face import Face
from elements import FaceName, Color, CenterSlice


def use(_):
    pass


_status = None


class NxNCenters(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    def debug(self, *args):
        super().debug("NxX Centers:", args)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):

        # todo: check BOY
        return all((f.center.is3x3 for f in self.cube.faces))

    def solved(self) -> bool:
        """

        :return: if all centers have uniqe colors and it is a boy
        """

        return self._is_solved()

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        cube = self.cube
        n_slices = cube.n_slices

        # currently supports only odd
        assert n_slices % 2

        self._do_center(cube.front, cube.front.color)

    def _do_center(self, face: Face, color: Color):

        cmn = self.cmn

        cmn.bring_face_front(face)

        n = self.cube.n_slices
        n2 = n // 2

        center = face.center

        for r in range(0, n):  # 5: 3..4

            for j in range(n):
                cs: CenterSlice = center.get_center_slice((r, j))

                if cs.color != color:
                    self.debug(f"Need to fix slice {r}, {j}, {cs.color}")

                    self._fix_center_slice(cs, color)

        self.op.op(Algs.F * 2)

        for r in range(0, n):  # 5: 3..4

            for j in range(n2+1, n):
                cs: CenterSlice = center.get_center_slice((r, j))

                if cs.color != color:
                    self.debug(f"Need to fix slice {r}, {j}, {cs.color}")

                    self._fix_center_slice(cs, color)

    def _fix_center_slice(self, cs: CenterSlice, required_color):
        """
        Assume center slice is in front
        this is not optimized because it rotates faces
        :param cs:
        :return:
        """

        cube = self.cube
        r, j = cs.index
        self.debug(f"Fixing slice {r}, {j}, {cs.color}")

        # best sto start from up, currently we don't support back
        faces = [cube.up, cube.left, cube.down, cube.right]

        for f in faces:
            source = self._find_matching_slice(f, r, j, required_color)

            if source:
                self.debug(f"  Found matching piece {source} on {source.face}")
                self._fix_center_slice_from_source(cs, required_color, source)
                break

    def _fix_center_slice_from_source(self, cs: CenterSlice, required_color, source: CenterSlice):

        # before the rotation
        assert required_color == source.color

        self._bring_face_up_preserve_Front(source.face)

        # Because it was moved, index might be changed
        r, c = cs.index

        up = self.cube.up
        new_location_source = self._find_matching_slice(up, r, c, required_color)
        assert new_location_source
        source = new_location_source
        assert required_color == source.color

        self.debug(f" Source {source} is now on {source.face.name} {source.index}")

        # optimize it, can be done by less rotation, more math
        for _ in range(0, 4):
            if up.center.get_center_slice((r, c)).color == required_color:  # maybe it will find other :)
                break
            self.op.op(Algs.U)

        assert up.center.get_center_slice((r, c)).color == required_color

        self.debug(f" On  {source.face.name} , {(r,c)} is {up.center.get_center_slice((r, c)).color}")


        # this can be done, because Front and UP have the same coordinates system !!!
        # now do the communicator:
        n_slices = self.cube.n_slices

        inv = self.cube.inv
        R1 = Algs.M[inv(c) + 1:inv(c) + 1]
        R2 = Algs.M[inv(inv(c)) + 1:inv(inv(c)) + 1]

        F: algs.Alg
        if  c > n_slices // 2:
            # r indexes are inv of slice
            #  start from left to right, M from right to left
            F = Algs.F

        elif c < n_slices //2 :
            F = Algs.F.prime
        else:
            self.debug(f"Not yet supported {r}=={n_slices // 2}")
            return

        _algs = [R1.prime, F, R2.prime, F.prime, R1, F, R2, F.prime]
        for a in _algs:
            self.op.op(a)  # so I can debug

        x=0



    def _bring_face_up_preserve_Front(self, face):

        if face.name == FaceName.U:
            return

        self.debug(f"Need to bring {face} to up")

        match face.name:

            case FaceName.B:
                raise InternalSWError(f"{face.name} is not supported")

            case FaceName.L:
                # todo open range should be supported by slicing
                self.op.op(Algs.B[1:self.cube.n_slices + 1].prime)

            case _:
                raise InternalSWError(f"{face.name} Not yet supported")

    def _find_matching_slice(self, f: Face, r: int, c: int, required_color: Color) -> CenterSlice | None:

        for i in self._get_four_center_points(r, c):

            cs = f.center.get_center_slice(i)

            if cs.color == required_color:
                return cs

        return None

    def _get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        inv = self.cube.inv

        for _ in range(4):
            yield (r, c)
            (r, c) = (c, inv(r))
