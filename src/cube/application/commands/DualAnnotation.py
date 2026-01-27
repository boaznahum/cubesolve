"""Dual annotation support for shadow cube → real cube piece mapping.

This module provides DualAnnotation which maps annotation elements from a shadow
cube to corresponding elements on the real cube, enabling annotations to appear
on the real cube while solver logic operates on the shadow cube.

See docs/design/dual_operator_annotations.md for design details.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import nullcontext
from typing import TYPE_CHECKING, ContextManager, Tuple, cast

from cube.domain.model._elements import PartColorsID
from cube.domain.model.Corner import Corner
from cube.domain.model.Edge import Edge
from cube.domain.model.Part import Part
from cube.domain.model.PartEdge import PartEdge
from cube.domain.model.PartSlice import PartSlice
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.protocols.AnnotationProtocol import (
    AdditionalMarker,
    SupportsAnnotation,
    _HEAD,
)

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

    from .DualOperator import DualOperator

from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol


class DualAnnotation:
    """
    Annotation implementation that maps shadow cube pieces to real cube pieces.

    When the solver annotates a piece from the shadow cube, this class:
    1. Maps the shadow piece to the corresponding real cube piece (by position)
    2. Delegates to the real operator's annotation

    The mapping happens once at annotation start. After that, markers travel
    with the piece via c_attributes (for AnnWhat.Moved).

    Design Decision D2: Map by position (accessor name).
    Design Decision D8: PartColorsID is found on the real cube.
    """

    __slots__ = ["_dual_op", "_real_op", "_shadow_cube", "_real_cube"]

    def __init__(self, dual_op: "DualOperator") -> None:
        """
        Create a DualAnnotation.

        Args:
            dual_op: The DualOperator that owns this annotation.
        """
        self._dual_op = dual_op
        self._real_op: OperatorProtocol = dual_op._real_op
        self._shadow_cube: Cube = dual_op._shadow_cube
        self._real_cube: Cube = self._real_op.cube

    def annotate(
        self,
        *elements: Tuple[SupportsAnnotation, AnnWhat],
        additional_markers: list[AdditionalMarker] | None = None,
        h1: _HEAD = None,
        h2: _HEAD = None,
        h3: _HEAD = None,
        animation: bool = True
    ) -> ContextManager[None]:
        """
        Annotate elements, mapping shadow pieces to real pieces.

        Args:
            elements: Tuples of (element, AnnWhat) to annotate.
                      Elements are from shadow cube but will be mapped to real cube.
            additional_markers: Optional list of (element, AnnWhat, factory_method) tuples
                for custom markers. Factory method is only called if animation is enabled.
                Elements will be mapped from shadow cube to real cube.
            h1, h2, h3: Optional header text (passed through unchanged).
            animation: Whether to animate (passed through to real annotation).

        Returns:
            Context manager for the annotation scope.
        """
        if not self._dual_op.animation_enabled or not animation:
            return nullcontext()

        # Map all elements from shadow cube to real cube
        mapped_elements: list[Tuple[SupportsAnnotation, AnnWhat]] = []
        for element, what in elements:
            mapped = self._map_element(element, what)
            if mapped is not None:
                mapped_elements.append((mapped, what))

        # Map additional_markers elements from shadow to real cube
        mapped_additional: list[AdditionalMarker] | None = None
        if additional_markers:
            mapped_additional = []
            for element, what, factory in additional_markers:
                mapped = self._map_element(element, what)
                if mapped is not None:
                    mapped_additional.append((mapped, what, factory))

        # Delegate to real operator's annotation
        return self._real_op.annotation.annotate(
            *mapped_elements,
            additional_markers=mapped_additional,
            h1=h1,
            h2=h2,
            h3=h3,
            animation=animation
        )

    def _map_element(
        self,
        element: SupportsAnnotation,
        what: AnnWhat
    ) -> SupportsAnnotation | None:
        """
        Map an annotation element from shadow cube to real cube.

        Handles all element types recursively:
        - Part (Edge, Corner): Map by position accessor
        - PartSlice: Map parent Part, get corresponding slice
        - PartEdge: Map parent PartSlice, get corresponding edge
        - PartColorsID (frozenset): Find by colors on real cube
        - Iterable/Iterator: Map each element
        - Callable: Call, then map result

        Args:
            element: The element to map (from shadow cube).
            what: The annotation type (Moved, FixedPosition, Both).

        Returns:
            The mapped element (on real cube), or None if mapping fails.
        """
        # PartColorsID (frozenset of colors) - find on real cube (D8)
        if isinstance(element, frozenset):
            # PartColorsID - find piece with these colors on real cube
            colors_id = cast(PartColorsID, element)
            if what in (AnnWhat.Moved, AnnWhat.Both):
                return self._real_cube.find_part_by_colors(colors_id)
            else:  # FixedPosition
                return self._real_cube.find_part_by_pos_colors(colors_id)

        # Part (Edge or Corner) - map by position (D2)
        if isinstance(element, Part):
            return self._map_part(element)

        # PartSlice - map parent Part, get corresponding slice
        if isinstance(element, PartSlice):
            return self._map_part_slice(element)

        # PartEdge - map parent PartSlice, get corresponding edge
        if isinstance(element, PartEdge):
            return self._map_part_edge(element)

        # Iterable (but not string/frozenset) - map each element
        if isinstance(element, (Iterable, Iterator)) and not isinstance(element, (str, frozenset)):
            return [self._map_element(e, what) for e in element]  # type: ignore

        # Callable - call it, then map the result
        if callable(element):
            result = element()
            return self._map_element(result, what)

        # Unknown type - return as-is (may cause issues downstream)
        return element  # type: ignore[return-value]

    # Mapping from EdgeName.value to Cube property name
    # EdgeName uses ordering like "UR" but Cube uses "ru"
    _EDGE_NAME_TO_PROPERTY: dict[str, str] = {
        "FL": "fl",
        "FU": "fu",
        "FR": "fr",
        "FD": "fd",
        "BL": "bl",
        "BU": "bu",
        "BR": "br",
        "BD": "bd",
        "UR": "ru",  # EdgeName.UR -> cube.ru
        "RD": "rd",
        "DL": "dl",
        "LU": "lu",
    }

    def _map_part(self, shadow_part: Part) -> Part:
        """
        Map a Part from shadow cube to real cube by position.

        Args:
            shadow_part: A Part (Edge or Corner) from the shadow cube.

        Returns:
            The Part at the same position on the real cube.
        """
        if isinstance(shadow_part, Edge):
            # Edge.name returns EdgeName enum (e.g., EdgeName.FU)
            # EdgeName.value is the string (e.g., "FU")
            # Need to map to Cube property name (some are different, e.g., UR -> ru)
            edge_name = shadow_part.name.value
            accessor = self._EDGE_NAME_TO_PROPERTY.get(edge_name, edge_name.lower())
        elif isinstance(shadow_part, Corner):
            # Corner.name returns CornerName enum (e.g., CornerName.FLU)
            # CornerName.value is the string (e.g., "FLU")
            accessor = shadow_part.name.value.lower()
        else:
            # Center - use the face name
            # Centers are accessed via face, e.g., cube.front.center
            # For now, raise an error - centers shouldn't be annotated in 3x3 solver
            raise ValueError(f"Cannot map Center from shadow cube: {shadow_part}")

        return getattr(self._real_cube, accessor)

    def _map_part_slice(self, shadow_slice: PartSlice) -> PartSlice:
        """
        Map a PartSlice from shadow cube to real cube.

        The slice index is preserved - if it's slice 0 on shadow, it maps to
        slice 0 on real (even though real cube may have more slices).

        Args:
            shadow_slice: A PartSlice from the shadow cube.

        Returns:
            The corresponding PartSlice on the real cube.
        """
        # Get the parent Part and map it
        shadow_part = shadow_slice.parent
        real_part = self._map_part(shadow_part)

        # Get the slice index and find corresponding slice on real part
        # For 3x3 shadow, there's only one slice (index doesn't matter)
        # For real cube, we annotate ALL slices (the whole edge)
        # Actually, just return the first slice - the annotation system
        # will iterate all slices when processing a Part
        return real_part.get_slice(shadow_slice.index)

    def _map_part_edge(self, shadow_edge: PartEdge) -> PartEdge:
        """
        Map a PartEdge from shadow cube to real cube.

        Args:
            shadow_edge: A PartEdge from the shadow cube.

        Returns:
            The corresponding PartEdge on the real cube.
        """
        # Get the parent PartSlice and map it
        shadow_slice = shadow_edge.parent
        real_slice = self._map_part_slice(shadow_slice)

        # Find the edge on the same face
        shadow_face = shadow_edge.face
        for real_edge in real_slice.edges:
            if real_edge.face.name == shadow_face.name:
                return real_edge

        # Fallback - return first edge (shouldn't happen)
        return real_slice.edges[0]
