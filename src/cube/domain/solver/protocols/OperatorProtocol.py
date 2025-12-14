"""Operator protocol - interface for algorithm execution."""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Sequence
from typing import Protocol, TYPE_CHECKING, Any, ContextManager

from cube.application.state import ApplicationAndViewState

if TYPE_CHECKING:
    from cube.domain.algs.Alg import Alg
    from cube.domain.model.Cube import Cube
    from .AnnotationProtocol import AnnotationProtocol


class OperatorProtocol(Protocol, metaclass=ABCMeta):
    """
    Protocol defining what domain solvers need from an operator.

    This allows domain layer to depend on an interface rather than
    the concrete Operator class in application layer.
    """

    @property
    def cube(self) -> "Cube":
        """The cube being operated on."""
        ...

    def play(self, alg: "Alg", inv: Any = False, animation: Any = True) -> None:
        """Execute an algorithm on the cube."""
        ...

    def history(self, *, remove_scramble: bool = False) -> Sequence["Alg"]:
        """Get the operation history."""
        ...

    def undo(self, animation: bool = True) -> "Alg | None":
        """Undo the last operation."""
        ...

    def with_animation(self, animation: bool | None = None) -> ContextManager[None]:
        """Context manager to control animation."""
        ...

    def save_history(self) -> ContextManager[None]:
        """Context manager to save and restore history."""
        ...

    def with_query_restore_state(self) -> ContextManager[None]:
        """
        Context manager for query operations with auto-rollback.

        Combines:
        - Query mode (_in_query_mode = True, skips texture updates)
        - Animation disabled
        - Auto-rollback: undoes all moves on exit
        - Supports nesting
        """
        ...

    @property
    def annotation(self) -> "AnnotationProtocol":
        """Get the annotation object."""
        ...

    def log(self, *s: Any) -> None:
        """Log operation."""
        ...

    @property
    def animation_enabled(self) -> bool:
        """Whether animation is enabled."""
        ...

    @property
    def app_state(self) -> ApplicationAndViewState:
        """Application and view state."""
        ...
