"""No-op annotation for non-animation scenarios."""
from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING, ContextManager, Tuple

from .AnnotationProtocol import AnnotationProtocol, SupportsAnnotation, _HEAD

if TYPE_CHECKING:
    from .AnnotationProtocol import AdditionalMarker, AnnWhat
    from cube.application.commands.Operator import Operator


class NoopAnnotation(AnnotationProtocol):
    """No-op implementation of AnnotationProtocol.

    Used when animation is disabled. Always returns nullcontext().
    """

    def __init__(self, op: "Operator | None" = None) -> None:
        self._op = op

    def annotate(
        self,
        *elements: Tuple["SupportsAnnotation", "AnnWhat"],
        additional_markers: list["AdditionalMarker"] | None = None,
        h1: _HEAD = None,
        h2: _HEAD = None,
        h3: _HEAD = None,
        animation: bool = True,
    ) -> ContextManager[None]:
        # Even without animation, emit HeadingAlg so it appears in the queue
        if h1 is not None and self._op is not None:
            h1_text: str = h1() if callable(h1) else h1  # type: ignore[assignment]
            if h1_text:
                from cube.domain.algs.HeadingAlg import HeadingAlg
                self._op.play(HeadingAlg(h1_text))
        return nullcontext()
