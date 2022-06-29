from enum import Enum, unique


VIEWER_ANNOTATION_KEY="annotation"

@unique
class VMarker(Enum):
    C0 = "C0" # for debugging face tracker
    C1 = "C1"
    C2 = "C2"
