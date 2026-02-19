"""Annotation protocol - interface for solver visualization."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Callable, ContextManager, Protocol, Tuple, TypeAlias, runtime_checkable

if TYPE_CHECKING:
    from cube.application.markers._marker_creator_protocol import MarkerCreator
    from cube.domain.model._elements import PartColorsID
    from cube.domain.model.PartSlice import PartSlice
    from cube.domain.model.Part import Part
    from cube.domain.model.PartEdge import PartEdge
    from cube.domain.solver.AnnWhat import AnnWhat

# Type alias for annotation-supported elements
_ANN_BASE_ELEMENT: TypeAlias = "Part | PartColorsID | PartSlice | PartEdge"

_ANN_ELEMENT_0: TypeAlias = "_ANN_BASE_ELEMENT | Iterator[_ANN_BASE_ELEMENT] | Iterable[_ANN_BASE_ELEMENT] | Callable[[], _ANN_BASE_ELEMENT]"

_ANN_ELEMENT_1: TypeAlias = "_ANN_ELEMENT_0 | Iterator[_ANN_ELEMENT_0] | Iterable[_ANN_ELEMENT_0] | Callable[[], _ANN_ELEMENT_0]"

SupportsAnnotation: TypeAlias = "_ANN_ELEMENT_1 | Iterator[_ANN_ELEMENT_1] | Iterable[_ANN_ELEMENT_1] | Callable[[], _ANN_ELEMENT_1]"

_HEAD: TypeAlias = "str | Callable[[], str] | None"

# Type alias for additional markers with custom MarkerCreator
# Tuple of (element, AnnWhat, factory_method that returns MarkerCreator)
# Element can be any SupportsAnnotation type (Part, PartSlice, PartEdge, etc.)
AdditionalMarker: TypeAlias = "Tuple[SupportsAnnotation, AnnWhat, Callable[[], MarkerCreator]]"


@runtime_checkable
class AnnotationProtocol(Protocol):
    """
    Protocol defining what domain solvers need for annotation/visualization.

    This allows domain layer to depend on an interface rather than
    the concrete OpAnnotation class in application layer.
    """

    def annotate(
        self,
        *elements: Tuple["SupportsAnnotation", "AnnWhat"],
        additional_markers: list["AdditionalMarker"] | None = None,
        h1: _HEAD = None,
        h2: _HEAD = None,
        h3: _HEAD = None,
        animation: bool = True
    ) -> ContextManager[None]:
        """
        Context manager to annotate elements during solving.

        Args:
            elements: Tuples of (element, AnnWhat) to annotate
            additional_markers: Optional list of (PartEdge, AnnWhat, factory_method) tuples
                for custom markers. Factory method is only called if animation is enabled.
            h1, h2, h3: Optional header text
            animation: Whether to animate

        Returns:
            Context manager for the annotation scope
        """
        ...
