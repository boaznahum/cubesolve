"""Operator protocol - interface for algorithm execution."""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ContextManager, Protocol

from cube.utils.SSCode import SSCode
from cube.utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
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

    @property
    def sp(self) -> IServiceProvider:
        """Get the service provider."""
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
    def count(self) -> int:
        """Number of moves executed so far."""
        ...

    @property
    def app_state(self) -> "ApplicationAndViewState":
        """Application and view state."""
        ...

    def enter_single_step_mode(self, code: SSCode | None = None) -> None:
        """
        Enable single-step mode for debugging.

        When enabled, animation will pause after each algorithm and wait
        for user input (Space key or GUI button) before continuing.

        Args:
            code: Optional SSCode identifying the trigger point. If provided,
                  single-step mode is only enabled if the code is enabled in
                  config (SS_CODES). If None, always enters single-step mode.

        Use this at critical points in solver code to inspect cube state:
            self._op.enter_single_step_mode(SSCode.NxN_CORNER_PARITY_FIX)
        """
        ...
