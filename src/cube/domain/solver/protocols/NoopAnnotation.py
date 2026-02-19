"""No-op annotation for non-animation scenarios."""
from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING, ContextManager, Tuple

from .AnnotationProtocol import AnnotationProtocol, SupportsAnnotation, _HEAD

if TYPE_CHECKING:
    from .AnnotationProtocol import AdditionalMarker, AnnWhat


class NoopAnnotation(AnnotationProtocol):
    """No-op implementation of AnnotationProtocol.

    Used when animation is disabled. Always returns nullcontext().
    """

    def annotate(
        self,
        *elements: Tuple["SupportsAnnotation", "AnnWhat"],
        additional_markers: list["AdditionalMarker"] | None = None,
        h1: _HEAD = None,
        h2: _HEAD = None,
        h3: _HEAD = None,
        animation: bool = True,
    ) -> ContextManager[None]:
        return nullcontext()
