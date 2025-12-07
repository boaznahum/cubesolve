"""Annotation protocol - interface for solver visualization."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol, TYPE_CHECKING, Callable, Tuple, ContextManager, TypeAlias

if TYPE_CHECKING:
    from cube.domain.model import Part, PartColorsID, PartEdge, PartSlice
    from cube.domain.solver.AnnWhat import AnnWhat

# Type alias for annotation-supported elements
_ANN_BASE_ELEMENT: TypeAlias = "Part | PartColorsID | PartSlice | PartEdge"

_ANN_ELEMENT_0: TypeAlias = "_ANN_BASE_ELEMENT | Iterator[_ANN_BASE_ELEMENT] | Iterable[_ANN_BASE_ELEMENT] | Callable[[], _ANN_BASE_ELEMENT]"

_ANN_ELEMENT_1: TypeAlias = "_ANN_ELEMENT_0 | Iterator[_ANN_ELEMENT_0] | Iterable[_ANN_ELEMENT_0] | Callable[[], _ANN_ELEMENT_0]"

SupportsAnnotation: TypeAlias = "_ANN_ELEMENT_1 | Iterator[_ANN_ELEMENT_1] | Iterable[_ANN_ELEMENT_1] | Callable[[], _ANN_ELEMENT_1]"

_HEAD: TypeAlias = "str | Callable[[], str] | None"


class AnnotationProtocol(Protocol):
    """
    Protocol defining what domain solvers need for annotation/visualization.

    This allows domain layer to depend on an interface rather than
    the concrete OpAnnotation class in application layer.
    """

    def annotate(
        self,
        *elements: Tuple["SupportsAnnotation", "AnnWhat"],
        h1: _HEAD = None,
        h2: _HEAD = None,
        h3: _HEAD = None,
        animation: bool = True
    ) -> ContextManager[None]:
        """
        Context manager to annotate elements during solving.

        Args:
            elements: Tuples of (element, AnnWhat) to annotate
            h1, h2, h3: Optional header text
            animation: Whether to animate

        Returns:
            Context manager for the annotation scope
        """
        ...
