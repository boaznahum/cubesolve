"""Query-not-found exception family.

Base exception for queries that fail to find a matching element.
Subclasses provide specific context for different query types.
"""


class QueryNotFound(Exception):
    """Base class for query-not-found errors."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SliceEdgeNotFound(QueryNotFound):
    """find_slice_edge failed to locate a matching PartEdge."""

    def __init__(self, parts: object, pred: object) -> None:
        super().__init__(f"No such edge in {parts} for pred {pred}")
        self.parts = parts
        self.pred = pred
