from typing import Callable, TypeVar

from app_exceptions import InternalSWError
from cube import Cube
from cube_face import Face
from elements import PartSlice, CenterSlice

T=TypeVar("T")
Pred=Callable[[T], bool]

class CubeQueries:

    @staticmethod
    def find_face(cube: Cube, pred:Pred[Face]) -> Face:

        s: PartSlice
        for f in cube.faces:
            if pred(f):
                return f

        raise InternalSWError(f"Can't find face with pred {pred}")

    @staticmethod
    def find_slice(cube: Cube, slice_unique_id: int) -> PartSlice:

        s: PartSlice
        for f in cube.faces:
            for s in f.slices:
                if s.unique_id == slice_unique_id:
                    return s

        raise InternalSWError(f"Can't find slice with unique id {slice_unique_id}")

    @staticmethod
    def find_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice | None:

        s: CenterSlice
        for f in cube.faces:
            for s in f.center.all_slices:
                if pred(s):
                    return s

        return None


