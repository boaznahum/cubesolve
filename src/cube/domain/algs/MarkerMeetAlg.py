from typing import Self

from cube.domain.algs.AnnotationAlg import AnnotationAlg


class MarkerMeetAlg(AnnotationAlg):
    """Signal that source and target markers have met on the same sticker.

    When played, the WebGL animation manager sends a 'marker_meet' event
    to the client, which plays a brief flash/pulse animation before the
    markers are removed.

    Like AnnotationAlg, this does nothing to the cube model.
    """

    __slots__ = ("_duration_ms",)

    def __init__(self, duration_ms: int = 500) -> None:
        # AnnotationAlg.__init__ calls _freeze(), so we set our field first
        # via object.__setattr__ since SimpleAlg uses __slots__ with freeze
        object.__setattr__(self, "_duration_ms", duration_ms)
        super().__init__()

    @property
    def duration_ms(self) -> int:
        return self._duration_ms  # type: ignore[attr-defined]

    def __str__(self) -> str:
        return "MarkerMeetAlg"

    def simple_inverse(self) -> Self:
        return self
