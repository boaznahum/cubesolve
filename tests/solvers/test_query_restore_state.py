"""
Tests for with_query_restore_state context manager.

This context manager should:
1. Set _in_query_mode = True (skip texture updates)
2. Disable animation
3. On exit: undo all moves, restore cube to original state
4. Support nesting
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.application.commands.Operator import Operator
from cube.domain.algs.Algs import Algs
from cube.domain.model.Cube import Cube

from tests.test_utils import _test_sp


class TestQueryRestoreState:
    """Tests for with_query_restore_state context manager."""

    def test_cube_state_restored_after_context(self, test_sp) -> None:
        """Test that cube state is restored after exiting context."""
        # Setup
        app = AbstractApp.create_app(cube_size=3)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)

        # Scramble cube
        scramble1 = Algs.scramble(3, seed=42)
        op.play(scramble1)

        # Take state snapshot
        state_before = cube.cqr.get_sate()
        history_len_before = len(op.history())

        # Enter context, scramble again, exit
        with op.with_query_restore_state():
            scramble2 = Algs.scramble(3, seed=123)
            op.play(scramble2)

            # Inside context, cube should be different
            state_inside = cube.cqr.get_sate()
            assert not cube.cqr.compare_states(state_before, state_inside), \
                "Cube state should be different inside context after scramble"

        # After context, state should be restored
        state_after = cube.cqr.get_sate()
        assert cube.cqr.compare_states(state_before, state_after), \
            "Cube state should be restored after exiting context"

        # History should also be restored
        assert len(op.history()) == history_len_before, \
            "History length should be restored after exiting context"

    def test_query_mode_flag_set_inside_context(self, test_sp) -> None:
        """Test that _in_query_mode flag is True inside context."""
        app = AbstractApp.create_app(cube_size=3)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)

        # Before context
        assert not cube._in_query_mode, "Should not be in query mode before context"

        with op.with_query_restore_state():
            assert cube._in_query_mode, "Should be in query mode inside context"

        # After context
        assert not cube._in_query_mode, "Should not be in query mode after context"

    def test_nested_contexts_restore_correctly(self, test_sp) -> None:
        """Test that nested contexts restore state correctly."""
        app = AbstractApp.create_app(cube_size=3)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)

        # Initial scramble
        op.play(Algs.scramble(3, seed=42))
        state_outer = cube.cqr.get_sate()

        with op.with_query_restore_state():
            # Outer context - do some moves
            op.play(Algs.U)
            state_after_outer_move = cube.cqr.get_sate()

            with op.with_query_restore_state():
                # Inner context - do more moves
                op.play(Algs.R)

                # Verify _in_query_mode is still True
                assert cube._in_query_mode, "Should still be in query mode in nested context"

            # After inner context, should restore to state_after_outer_move
            state_after_inner_exit = cube.cqr.get_sate()
            assert cube.cqr.compare_states(state_after_outer_move, state_after_inner_exit), \
                "State should be restored after inner context exits"

            # _in_query_mode should still be True (outer context)
            assert cube._in_query_mode, "Should still be in query mode after inner context"

        # After outer context, should restore to state_outer
        state_final = cube.cqr.get_sate()
        assert cube.cqr.compare_states(state_outer, state_final), \
            "State should be restored after outer context exits"

        # _in_query_mode should be False
        assert not cube._in_query_mode, "Should not be in query mode after all contexts"

    def test_animation_disabled_inside_context(self, test_sp) -> None:
        """Test that animation is disabled inside context."""
        app = AbstractApp._create_app(cube_size=3, animation=True)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)

        # Enable animation
        op.toggle_animation_on(True)

        with op.with_query_restore_state():
            # Animation should be disabled inside context
            assert not op.animation_enabled, "Animation should be disabled inside context"

        # Animation state after context depends on implementation
        # (may or may not restore - check what's expected)

    def test_state_restored_even_on_exception(self, test_sp) -> None:
        """Test that state is restored even if exception occurs inside context."""
        app = AbstractApp.create_app(cube_size=3)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)

        # Scramble cube
        op.play(Algs.scramble(3, seed=42))
        state_before = cube.cqr.get_sate()

        # Enter context, do moves, raise exception
        with pytest.raises(ValueError):
            with op.with_query_restore_state():
                op.play(Algs.U)
                op.play(Algs.R)
                raise ValueError("Test exception")

        # State should still be restored
        state_after = cube.cqr.get_sate()
        assert cube.cqr.compare_states(state_before, state_after), \
            "State should be restored even after exception"

        # _in_query_mode should be False
        assert not cube._in_query_mode, "Should not be in query mode after exception"
