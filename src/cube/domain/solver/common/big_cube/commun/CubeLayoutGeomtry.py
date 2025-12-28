from enum import Enum, auto

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.model import FaceName
from cube.domain.model.SliceName import SliceName


class CLGColRow(Enum):
    ROW = auto()
    COL = auto()

class CubeLayoutGeomtry:
    """
    All un solved geometry questions
    """


    @staticmethod
    def does_slice_cut_rows_or_columns(slice_name: SliceName, face_name: FaceName) -> CLGColRow:

        """
           Slice Traversal (content movement during rotation):
                M: F → U → B → D → F  (vertical cycle, like L rotation)
                E: R → B → L → F → R  (horizontal cycle, like D rotation)
                S: U → R → D → L → U  (around F/B axis, like F rotation)

        """
        # claude what is the Mathematica of this ???
        if slice_name == SliceName.M:
            return CLGColRow.ROW

        elif slice_name == SliceName.E:
            return CLGColRow.COL # slice cut the column so we check row

        elif slice_name == SliceName.S:

            if face_name in  [FaceName.R, FaceName.L]:
                # slice cut the rows so we take columns like in M
                return CLGColRow.ROW
            else:
                return CLGColRow.COL

        raise InternalSWError();
