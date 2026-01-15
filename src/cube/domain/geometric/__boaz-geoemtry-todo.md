# in cube.domain.geometric.Face2FaceTranslator.Face2FaceTranslator.translate_source_from_target

I dont understand 
        # Map slice to whole-cube axis: M->X(R), E->Y(U), S->Z(F)
        slice_to_axis: dict[SliceName, FaceName] = {
            SliceName.M: FaceName.R,  # M -> X
            SliceName.E: FaceName.U,  # E -> Y
            SliceName.S: FaceName.F,  # S -> Z
        }

why it works ?

class SliceName(Enum):
    """
        See: https://alg.cubing.net/?alg=m and https://ruwix.com/the-rubiks-cube/notation/advanced/
    """
    S = "S"  # Standing - middle between F and B, rotates like F
    M = "M"  # Middle - middle between L and R, rotates like L (standard notation)
    E = "E"  # Equator - middle between U and D, rotates like D

class AxisName(Enum):
    """
    Whole cube Axis name
    """
    X = "X"  # Over R , against M
    Y = "Y"  # over U , against E
    Z = "Z"  # Over F,  With S


# cache f2f results in cube cache


