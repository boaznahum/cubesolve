"""Unit tests for the WebGL Flow State Machine.

Tests the FSM in isolation — no browser, no WebSocket, no cube domain.
Verifies all transitions, guards, button tables, and edge cases.
"""

from __future__ import annotations

import pytest

from cube.presentation.gui.backends.webgl.FlowStateMachine import (
    FlowEvent,
    FlowState,
    FlowStateMachine,
)


# -- Fixtures --

@pytest.fixture
def fsm() -> FlowStateMachine:
    """Fresh state machine starting in IDLE."""
    return FlowStateMachine()


def _advance_to_ready(fsm: FlowStateMachine) -> None:
    """Advance FSM from IDLE → SOLVING → READY."""
    fsm.send(FlowEvent.SOLVE)
    fsm.send(FlowEvent.SOLVE_DONE, has_redo=True, has_history=False)
    assert fsm.state == FlowState.READY


def _advance_to_playing(fsm: FlowStateMachine) -> None:
    """Advance FSM from IDLE → READY → PLAYING."""
    _advance_to_ready(fsm)
    fsm.send(FlowEvent.PLAY_ALL)
    assert fsm.state == FlowState.PLAYING


def _advance_to_animating(fsm: FlowStateMachine) -> None:
    """Advance FSM from IDLE → READY → ANIMATING (single redo)."""
    _advance_to_ready(fsm)
    fsm.send(FlowEvent.PLAY_NEXT)
    assert fsm.state == FlowState.ANIMATING


# -- Basic transition tests --

class TestBasicTransitions:
    """Test valid transitions from each state."""

    def test_starts_in_idle(self, fsm: FlowStateMachine) -> None:
        assert fsm.state == FlowState.IDLE

    def test_idle_to_solving(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.SOLVE)
        assert fsm.state == FlowState.SOLVING

    def test_idle_to_animating_via_scramble(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.SCRAMBLE)
        assert fsm.state == FlowState.ANIMATING

    def test_idle_to_animating_via_face_turn(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.FACE_TURN)
        assert fsm.state == FlowState.ANIMATING

    def test_idle_size_change(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.SIZE_CHANGE)
        assert fsm.state == FlowState.IDLE

    def test_solving_to_ready(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.SOLVE)
        assert fsm.send(FlowEvent.SOLVE_DONE, has_redo=True, has_history=False)
        assert fsm.state == FlowState.READY

    def test_ready_to_playing(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.PLAY_ALL)
        assert fsm.state == FlowState.PLAYING

    def test_ready_to_rewinding(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.REWIND_ALL)
        assert fsm.state == FlowState.REWINDING

    def test_ready_to_animating_via_play_next(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.PLAY_NEXT)
        assert fsm.state == FlowState.ANIMATING

    def test_ready_to_animating_via_undo(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.UNDO)
        assert fsm.state == FlowState.ANIMATING

    def test_ready_to_idle_via_reset(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.RESET)
        assert fsm.state == FlowState.IDLE

    def test_playing_to_stopping(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert fsm.send(FlowEvent.STOP)
        assert fsm.state == FlowState.STOPPING

    def test_playing_anim_done_loops(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert fsm.send(FlowEvent.ANIM_DONE)
        assert fsm.state == FlowState.PLAYING  # stays in PLAYING

    def test_playing_queue_empty_to_idle(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert fsm.send(FlowEvent.QUEUE_EMPTY, has_redo=False, has_history=False)
        assert fsm.state == FlowState.IDLE

    def test_playing_queue_empty_to_ready(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert fsm.send(FlowEvent.QUEUE_EMPTY, has_redo=False, has_history=True)
        assert fsm.state == FlowState.READY

    def test_animating_anim_done_to_ready(self, fsm: FlowStateMachine) -> None:
        _advance_to_animating(fsm)
        assert fsm.send(FlowEvent.ANIM_DONE, has_redo=True, has_history=True)
        assert fsm.state == FlowState.READY

    def test_animating_anim_done_to_idle(self, fsm: FlowStateMachine) -> None:
        _advance_to_animating(fsm)
        assert fsm.send(FlowEvent.ANIM_DONE, has_redo=False, has_history=False)
        assert fsm.state == FlowState.IDLE

    def test_stopping_anim_done_to_ready(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        fsm.send(FlowEvent.STOP)
        assert fsm.state == FlowState.STOPPING
        assert fsm.send(FlowEvent.ANIM_DONE, has_redo=True, has_history=True)
        assert fsm.state == FlowState.READY


# -- Illegal transition tests --

class TestIllegalTransitions:
    """Test that illegal events are rejected (state unchanged)."""

    def test_idle_cannot_stop(self, fsm: FlowStateMachine) -> None:
        assert not fsm.send(FlowEvent.STOP)
        assert fsm.state == FlowState.IDLE

    def test_idle_cannot_play_all(self, fsm: FlowStateMachine) -> None:
        assert not fsm.send(FlowEvent.PLAY_ALL)
        assert fsm.state == FlowState.IDLE

    def test_idle_cannot_undo(self, fsm: FlowStateMachine) -> None:
        assert not fsm.send(FlowEvent.UNDO)
        assert fsm.state == FlowState.IDLE

    def test_solving_cannot_play(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.SOLVE)
        assert not fsm.send(FlowEvent.PLAY_ALL)
        assert fsm.state == FlowState.SOLVING

    def test_playing_cannot_scramble(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert not fsm.send(FlowEvent.SCRAMBLE)
        assert fsm.state == FlowState.PLAYING

    def test_playing_cannot_undo(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        assert not fsm.send(FlowEvent.UNDO)
        assert fsm.state == FlowState.PLAYING

    def test_stopping_cannot_stop_again(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        fsm.send(FlowEvent.STOP)
        assert not fsm.send(FlowEvent.STOP)
        assert fsm.state == FlowState.STOPPING


# -- RESET_SESSION from every state --

class TestResetSession:
    """RESET_SESSION must work from every state."""

    @pytest.mark.parametrize("setup_fn,expected_before", [
        (None, FlowState.IDLE),
        (lambda f: f.send(FlowEvent.SOLVE), FlowState.SOLVING),
        (_advance_to_ready, FlowState.READY),
        (_advance_to_playing, FlowState.PLAYING),
        (_advance_to_animating, FlowState.ANIMATING),
    ])
    def test_reset_session_from_state(
        self, fsm: FlowStateMachine,
        setup_fn: object,
        expected_before: FlowState,
    ) -> None:
        if setup_fn is not None:
            setup_fn(fsm)  # type: ignore[operator]
        assert fsm.state == expected_before
        assert fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.state == FlowState.IDLE

    def test_reset_session_from_editing(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.state == FlowState.EDITING
        assert fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.state == FlowState.IDLE

    def test_reset_session_clears_metadata(self, fsm: FlowStateMachine) -> None:
        fsm.redo_source = "solver"
        fsm.redo_tainted = True
        fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.redo_source == "undo"
        assert fsm.redo_tainted is False

    def test_reset_session_from_stopping(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        fsm.send(FlowEvent.STOP)
        assert fsm.state == FlowState.STOPPING
        assert fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.state == FlowState.IDLE

    def test_reset_session_from_rewinding(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        fsm.send(FlowEvent.REWIND_ALL)
        assert fsm.state == FlowState.REWINDING
        assert fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.state == FlowState.IDLE


# -- RECONNECT --

class TestReconnect:
    """RECONNECT always transitions to IDLE or READY based on queue."""

    def test_reconnect_with_redo_goes_to_ready(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        result = fsm.send_reconnect(has_redo=True)
        assert result == FlowState.READY
        assert fsm.state == FlowState.READY

    def test_reconnect_without_redo_goes_to_idle(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        result = fsm.send_reconnect(has_redo=False)
        assert result == FlowState.IDLE
        assert fsm.state == FlowState.IDLE

    def test_reconnect_clears_auto_play(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.SOLVE_AND_PLAY)
        assert fsm._auto_play is True
        fsm.send_reconnect(has_redo=True)
        assert fsm._auto_play is False

    def test_reconnect_from_idle(self, fsm: FlowStateMachine) -> None:
        """Even from IDLE, reconnect works."""
        result = fsm.send_reconnect(has_redo=False)
        assert result == FlowState.IDLE


# -- Solve and play --

class TestSolveAndPlay:
    """SOLVE_AND_PLAY → SOLVING → PLAYING (auto transition)."""

    def test_solve_and_play_auto_transitions_to_playing(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.SOLVE_AND_PLAY)
        assert fsm.state == FlowState.SOLVING
        assert fsm._auto_play is True
        assert fsm.send(FlowEvent.SOLVE_DONE, has_redo=True, has_history=False)
        assert fsm.state == FlowState.PLAYING

    def test_solve_without_play_goes_to_ready(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.SOLVE)
        assert fsm._auto_play is False
        assert fsm.send(FlowEvent.SOLVE_DONE, has_redo=True, has_history=False)
        assert fsm.state == FlowState.READY


# -- Button table tests --

class TestButtonTable:
    """Verify allowed_actions returns correct values for each state."""

    def test_idle_allows_scramble_solve(self, fsm: FlowStateMachine) -> None:
        a = fsm.allowed_actions(has_redo=False, has_history=False)
        assert a["scramble"] is True
        assert a["solve"] is True
        assert a["stop"] is False
        assert a["play_all"] is False
        assert a["undo"] is False

    def test_ready_allows_play_undo(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        a = fsm.allowed_actions(has_redo=True, has_history=True)
        assert a["play_all"] is True
        assert a["play_next"] is True
        assert a["undo"] is True
        assert a["rewind_all"] is True
        assert a["stop"] is False

    def test_ready_play_disabled_without_redo(self, fsm: FlowStateMachine) -> None:
        """Data guard: play_all requires has_redo even in READY."""
        _advance_to_ready(fsm)
        a = fsm.allowed_actions(has_redo=False, has_history=True)
        assert a["play_all"] is False
        assert a["play_next"] is False
        assert a["undo"] is True  # undo uses has_history

    def test_ready_undo_disabled_without_history(self, fsm: FlowStateMachine) -> None:
        """Data guard: undo requires has_history even in READY."""
        _advance_to_ready(fsm)
        a = fsm.allowed_actions(has_redo=True, has_history=False)
        assert a["undo"] is False
        assert a["play_all"] is True

    def test_playing_allows_stop(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        a = fsm.allowed_actions(has_redo=True, has_history=True)
        assert a["stop"] is True
        assert a["scramble"] is False
        assert a["play_all"] is False
        assert a["undo"] is False

    def test_animating_allows_stop(self, fsm: FlowStateMachine) -> None:
        _advance_to_animating(fsm)
        a = fsm.allowed_actions(has_redo=True, has_history=True)
        assert a["stop"] is True

    def test_stopping_disallows_stop(self, fsm: FlowStateMachine) -> None:
        _advance_to_playing(fsm)
        fsm.send(FlowEvent.STOP)
        a = fsm.allowed_actions(has_redo=True, has_history=True)
        assert a["stop"] is False

    def test_reset_session_always_allowed(self, fsm: FlowStateMachine) -> None:
        """reset_session should be allowed in ALL states."""
        for setup_fn in [None, lambda f: f.send(FlowEvent.SOLVE), _advance_to_ready, _advance_to_playing]:
            machine = FlowStateMachine()
            if setup_fn:
                setup_fn(machine)
            a = machine.allowed_actions(has_redo=True, has_history=True)
            assert a["reset_session"] is True, f"reset_session not allowed in {machine.state}"


# -- Redo metadata --

class TestRedoMetadata:
    """Test redo_source and redo_tainted metadata tracking."""

    def test_default_metadata(self, fsm: FlowStateMachine) -> None:
        assert fsm.redo_source == "undo"
        assert fsm.redo_tainted is False

    def test_metadata_survives_transitions(self, fsm: FlowStateMachine) -> None:
        fsm.redo_source = "solver"
        fsm.redo_tainted = True
        fsm.send(FlowEvent.SOLVE)
        assert fsm.redo_source == "solver"
        assert fsm.redo_tainted is True

    def test_reset_session_clears_metadata(self, fsm: FlowStateMachine) -> None:
        fsm.redo_source = "solver"
        fsm.redo_tainted = True
        fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.redo_source == "undo"
        assert fsm.redo_tainted is False


# -- Transition listener --

class TestTransitionListener:
    """Test the on_transition callback mechanism."""

    def test_listener_called_on_transition(self, fsm: FlowStateMachine) -> None:
        calls: list[tuple[FlowState, FlowState, FlowEvent]] = []
        fsm.on_transition(lambda new, old, event: calls.append((new, old, event)))
        fsm.send(FlowEvent.SOLVE)
        assert len(calls) == 1
        assert calls[0] == (FlowState.SOLVING, FlowState.IDLE, FlowEvent.SOLVE)

    def test_listener_not_called_on_rejection(self, fsm: FlowStateMachine) -> None:
        calls: list[tuple[FlowState, FlowState, FlowEvent]] = []
        fsm.on_transition(lambda new, old, event: calls.append((new, old, event)))
        fsm.send(FlowEvent.STOP)  # illegal from IDLE
        assert len(calls) == 0

    def test_listener_called_on_reconnect(self, fsm: FlowStateMachine) -> None:
        calls: list[tuple[FlowState, FlowState, FlowEvent]] = []
        fsm.on_transition(lambda new, old, event: calls.append((new, old, event)))
        fsm.send_reconnect(has_redo=True)
        assert len(calls) == 1
        assert calls[0] == (FlowState.READY, FlowState.IDLE, FlowEvent.RECONNECT)


# -- Edit mode tests --

class TestEditMode:
    """Test EDITING state transitions and gating."""

    def test_idle_to_editing(self, fsm: FlowStateMachine) -> None:
        assert fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.state == FlowState.EDITING

    def test_ready_to_editing(self, fsm: FlowStateMachine) -> None:
        _advance_to_ready(fsm)
        assert fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.state == FlowState.EDITING

    def test_editing_exit_to_idle(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.send(FlowEvent.EXIT_EDIT, has_redo=False, has_history=False)
        assert fsm.state == FlowState.IDLE

    def test_editing_exit_to_ready_with_redo(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.send(FlowEvent.EXIT_EDIT, has_redo=True, has_history=False)
        assert fsm.state == FlowState.READY

    def test_editing_exit_to_ready_with_history(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.send(FlowEvent.EXIT_EDIT, has_redo=False, has_history=True)
        assert fsm.state == FlowState.READY

    def test_editing_blocks_scramble(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert not fsm.send(FlowEvent.SCRAMBLE)
        assert fsm.state == FlowState.EDITING

    def test_editing_blocks_solve(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert not fsm.send(FlowEvent.SOLVE)
        assert fsm.state == FlowState.EDITING

    def test_editing_blocks_face_turn(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert not fsm.send(FlowEvent.FACE_TURN)
        assert fsm.state == FlowState.EDITING

    def test_editing_blocks_play_all(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert not fsm.send(FlowEvent.PLAY_ALL)
        assert fsm.state == FlowState.EDITING

    def test_editing_blocks_undo(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert not fsm.send(FlowEvent.UNDO)
        assert fsm.state == FlowState.EDITING

    def test_editing_allows_reset_session(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.send(FlowEvent.RESET_SESSION)
        assert fsm.state == FlowState.IDLE

    def test_editing_enter_edit_allowed_in_button_table(self, fsm: FlowStateMachine) -> None:
        a = fsm.allowed_actions(has_redo=False, has_history=False)
        assert a["enter_edit"] is True

    def test_editing_enter_edit_blocked_during_editing(self, fsm: FlowStateMachine) -> None:
        fsm.send(FlowEvent.ENTER_EDIT)
        a = fsm.allowed_actions(has_redo=False, has_history=False)
        assert a["enter_edit"] is False

    def test_editing_blocks_all_cube_actions(self, fsm: FlowStateMachine) -> None:
        """No cube manipulation actions should be allowed in EDITING."""
        fsm.send(FlowEvent.ENTER_EDIT)
        a = fsm.allowed_actions(has_redo=True, has_history=True)
        assert a["scramble"] is False
        assert a["solve"] is False
        assert a["play_all"] is False
        assert a["undo"] is False
        assert a["face_turn"] is False
        assert a["size_change"] is False
        # But these should work
        assert a["reset_session"] is True
        assert a["speed_change"] is True

    def test_full_edit_cycle(self, fsm: FlowStateMachine) -> None:
        """Full cycle: IDLE → EDITING → EXIT → READY → PLAY_ALL."""
        assert fsm.send(FlowEvent.ENTER_EDIT)
        assert fsm.state == FlowState.EDITING
        # Exit with redo (algorithm was enqueued)
        assert fsm.send(FlowEvent.EXIT_EDIT, has_redo=True, has_history=False)
        assert fsm.state == FlowState.READY
        # Can now play the algorithm
        assert fsm.send(FlowEvent.PLAY_ALL)
        assert fsm.state == FlowState.PLAYING
