from enum import Enum, unique
from typing import Any, Hashable, Sequence

_VIEWER_ANNOTATION_KEY = "annotation_marker"


@unique
class VMarker(Enum):
    C0 = "C0"  # for debugging face tracker
    C1 = "C1"
    C2 = "C2"


def viewer_add_view_marker(d: dict[Hashable, Any], marker: VMarker):
    ll: list[VMarker] | None = d.get(_VIEWER_ANNOTATION_KEY)

    if ll:
        ll.append(marker)
    else:
        d[_VIEWER_ANNOTATION_KEY] = [marker]


def viewer_remove_view_marker(d: dict[Hashable, Any], marker: VMarker):
    ll: list[VMarker] | None = d.get(_VIEWER_ANNOTATION_KEY)

    if ll:
        ll.remove(marker)
        if not ll:
            d.pop(_VIEWER_ANNOTATION_KEY)


def viewer_get_markers(d: dict[Hashable, Any]) -> Sequence[VMarker] | None:
    ll: list[VMarker] | None = d.get(_VIEWER_ANNOTATION_KEY)

    return ll
