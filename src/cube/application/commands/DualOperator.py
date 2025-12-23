"""Dual Operator for shadow cube + real cube synchronized execution.

This module provides DualOperator which wraps both a shadow cube and a real
operator, enabling solver annotations to appear on the real cube while the
solver logic operates on the shadow cube.

See docs/design/dual_operator_annotations.md for design details.
"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from cube.domain.algs.Alg import Alg
from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.utils.SSCode import SSCode

from .DualAnnotation import DualAnnotation

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
    from cube.domain.model.Cube import Cube


class DualOperator(OperatorProtocol):
    """
    Operator that synchronizes a shadow cube with a real cube.

    When solvers call play(), the algorithm is executed on both cubes:
    - Shadow cube: Direct execution (query mode, no animation)
    - Real cube: Via real operator (with animation and annotations)

    This enables the solver to operate on a simple 3x3 shadow cube while
    the user sees the moves animated on the actual NxN cube with full
    annotation support (h1/h2/h3 text, visual markers).

    Design Decisions:
    - D1: op.cube returns shadow cube (solver logic uses this)
    - D2: Pieces mapped by position (see DualAnnotation)
    - D4: Play on both cubes in sequence
    - D5: history() delegates to real operator
    - D6: undo() delegates to real operator only
    - D7: with_animation() passes through to real operator
    """

    __slots__ = [
        "_shadow_cube",
        "_real_op",
        "_annotation",
    ]

    def __init__(self, shadow_cube: "Cube", real_op: OperatorProtocol) -> None:
        """
        Create a DualOperator.

        Args:
            shadow_cube: The shadow 3x3 cube for solver logic.
            real_op: The real operator wrapping the NxN cube.
        """
        self._shadow_cube = shadow_cube
        self._real_op = real_op
        self._annotation = DualAnnotation(self)

    @property
    def cube(self) -> "Cube":
        """
        Return the shadow cube for solver logic.

        Design Decision D1: Solver logic operates on the shadow cube.
        The solver accesses cube positions, checks states, etc. on this cube.
        """
        return self._shadow_cube

    @property
    def annotation(self) -> DualAnnotation:
        """
        Return the dual annotation that maps shadow → real pieces.
        """
        return self._annotation

    @property
    def animation_enabled(self) -> bool:
        """
        Return whether animation is enabled on the real operator.
        """
        return self._real_op.animation_enabled

    @property
    def app_state(self) -> "ApplicationAndViewState":
        """
        Return the app state from the real operator.
        """
        return self._real_op.app_state

    def play(self, alg: Alg, inv: Any = False, animation: Any = True) -> None:
        """
        Execute algorithm on both shadow and real cubes.

        Design Decision D4: Play on both cubes in sequence.

        1. Play on shadow cube (direct, no animation)
        2. Play on real cube via real operator (with animation)

        Args:
            alg: The algorithm to execute.
            inv: Whether to invert the algorithm.
            animation: Whether to animate (passed to real operator).
        """
        # Invert if needed
        if inv:
            alg = alg.inv()

        # 1. Play on shadow cube (direct execution, no operator overhead)
        alg.play(self._shadow_cube, False)

        # 2. Play on real cube via real operator (with animation/history)
        self._real_op.play(alg, inv=False, animation=animation)

    def history(self, *, remove_scramble: bool = False) -> Sequence[Alg]:
        """
        Return operation history from the real operator.

        Design Decision D5: Delegate to real operator.
        """
        return self._real_op.history(remove_scramble=remove_scramble)

    def undo(self, animation: bool = True) -> Alg | None:
        """
        Undo the last operation on the real cube only.

        Design Decision D6: Delegate to real operator only.
        When user presses undo, the solver is done. Shadow cube state
        becomes stale, but that's OK - it's no longer needed.

        Args:
            animation: Whether to animate the undo.

        Returns:
            The algorithm that was undone, or None if history is empty.
        """
        return self._real_op.undo(animation)

    @contextmanager
    def with_animation(self, animation: bool | None = None) -> Generator[None, None, None]:
        """
        Context manager to control animation on the real operator.

        Design Decision D7: Respect solver's choice, pass through.
        If solver disables animation for certain moves, that's intentional.

        Args:
            animation: None = don't change, True/False = force on/off.

        Yields:
            None
        """
        with self._real_op.with_animation(animation):
            yield

    @contextmanager
    def save_history(self) -> Generator[None, None, None]:
        """
        Context manager to save and restore history on the real operator.

        Yields:
            None
        """
        with self._real_op.save_history():
            yield

    @contextmanager
    def with_query_restore_state(self) -> Generator[None, None, None]:
        """
        Context manager for query operations with auto-rollback.

        This is complex for DualOperator because we need to:
        1. Save shadow cube state
        2. Delegate to real operator's query mode
        3. Restore shadow cube state on exit

        For now, we raise NotImplementedError - the current use case
        (CageNxNSolver) doesn't use query mode inside the shadow solve.

        Yields:
            None
        """
        # Save shadow cube history position
        # Note: Shadow cube doesn't have operator history, so we'd need
        # to track moves ourselves. For now, just delegate to real op.
        # The shadow cube state will drift, but that's acceptable for
        # the current use case.
        with self._real_op.with_query_restore_state():
            yield

    def log(self, *s: Any) -> None:
        """
        Log operation to the real operator's log.
        """
        self._real_op.log(*s)

    def enter_single_step_mode(self, code: SSCode | None = None) -> None:
        """
        Enable single-step mode on the real operator.

        Args:
            code: Optional SSCode to filter by.
        """
        self._real_op.enter_single_step_mode(code)
