# WebGL Algorithm Text Editor — Session Notes

## Task Overview

Implement a non-modal algorithm text editor in the WebGL backend. Users type cube algorithms (e.g., "R U R' U'"), get real-time parse validation, and can preview/apply them to the cube.

### UI Design
- Keyboard icon button in toolbar to enter edit mode
- Editable text box with debounced parse validation (150ms)
- 4 buttons: **Play** (preview from initial state), **Apply** (update initial state), **Cancel** (restore + dismiss), **OK** (play with animation + dismiss)
- Play and OK are green/red based on parse validity
- Non-modal: cube stays visible, some toolbar buttons remain accessible
- Reuses paint-mode pattern: swap toolbars, hide history panel

### Architecture
- **FSM:** Added `EDITING` state, `ENTER_EDIT`/`EXIT_EDIT` events
- **Snapshot/restore:** Undo-based (save `len(op._history)`, undo back to it on restore). NOT color-repaint (that doesn't reverse Part rotations).
- **AM (AnimationManager):** Works independently of FSM — animations play via AM queue regardless of FSM state
- **Pull model:** Server sends one animation at a time, waits for client ack

## Files Modified

### Python (server restart required)
- `src/cube/presentation/gui/backends/webgl/FlowStateMachine.py` — EDITING state, transitions, button table
- `src/cube/presentation/gui/backends/webgl/ClientSession.py` — Edit mode handlers, snapshot/restore, queue-drained callback
- `src/cube/presentation/gui/backends/webgl/SessionState.py` — `edit_mode`, `edit_alg_text` fields
- `src/cube/presentation/gui/backends/webgl/CubeStateSerializer.py` — `extract_cube_color_names()` (unused, kept for future)

### JS/HTML/CSS (browser refresh only)
- `static/js/AlgEditor.js` — **NEW** — Editor module with overlay, input, button states, keyboard shortcuts
- `static/index.html` — Keyboard icon button, edit toolbar div
- `static/js/main.js` — AlgEditor integration, message handlers
- `static/js/AppState.js` — `editMode`, `editAlgText` fields
- `static/js/Toolbar.js` — Edit button enable/disable
- `static/styles.css` — Editor styles

### Tests
- `tests/webgl/test_flow_state_machine.py` — `TestEditMode` class (15 tests), `test_reset_session_from_editing`

## Commits

1. `6d125294` — "Add algorithm text editor for WebGL backend" — Initial implementation with all features

## Bugs Found and Fixed

### Bug #1 — Play doesn't respect animation state
**Reported:** User said "i asked the play/apply to obey the animation state"
**Root cause:** `_handle_edit_play` always executed without animation (hardcoded `False`)
**Fix:** Use `op.animation_enabled` to decide whether to animate Play

### Bug #2 — Play doesn't start from initial state
**Reported:** User said "play doesnt start from initial state"
**Root cause:** First implementation used `apply_cube_colors()` which only repaints stickers but doesn't reverse Part rotations. When moves were played, Parts physically moved but colors were just repainted. Playing again would rotate wrong Parts.
**Fix:** Switched from color-repaint snapshot to undo-based restore: save `len(op._history)` on enter, undo back to that length on restore.

### Bug #3 — Stop not available during edit mode animation
**Reported:** User said "stop is not available while playing"
**Root cause:** EDITING state didn't allow STOP event in FSM transitions
**Fix:** Added `FlowEvent.STOP: FlowState.EDITING` to transitions and `FlowState.EDITING` to stop's button table

### Bug #4 — After OK, stop stays enabled
**Reported:** User said "when i press ok, the stop is enabled, why?"
**Root cause:** OK used EXIT_EDIT → READY → PLAY_ALL flow, leaving FSM in PLAYING state with stop visible
**Fix:** OK now stays in EDITING during animation. Added `_edit_ok_pending` flag. `on_queue_drained` callback auto-exits EDITING when animations finish. No intermediate PLAYING state.

### Bug #5 — OK replays algorithm that was already previewed via Play
**Reported:** User said "when i press OK it play again, cant you know what you have played already?"
**Root cause:** Both Play and OK always restore to snapshot and replay. After Play previews "U L", OK restores and replays "U L" — user sees it twice.
**Fix:** Added `_edit_preview_text` field that tracks which algorithm is currently "live" on the cube. Set after successful Play, cleared on restore. When OK is pressed and text matches preview, skip replay — just accept current state and exit.

### Bug #6 — After OK, undo-all is disabled despite moves in history
**Reported:** User said "undo all is disabled, But U L is in the queue"
**Root cause:** In `AlgEditor.js`, the OK click handler called `this.exit()` immediately, before the server processed the message and sent updated state. Client exited edit mode and rendered toolbar before FSM had fully transitioned — allowed_actions was stale.
**Fix:** Removed `this.exit()` from OK click handler. Server sends `editMode=false` via state update when it exits EDITING, and `applyState()` calls `exit()` at that point. Server drives the UI, not the client.

### Bug #7 — Rewind-all stops after one move (pre-existing, not edit-mode specific)
**Reported:** User said "now undo all stop after one movement"
**Root cause:** `OpAnnotation._w_slice_edges_annotate()` always plays `Algs.AM` (MarkerMeetAlg) in its finally block, even when there are no marker slots. During undo with animation, `Operator.play()` wraps `_do_animation()` in `ann.annotate(h3=str(alg))`. The annotation context manager's finally block unconditionally calls `op.play(Algs.AM)`, which queues a MarkerMeetAlg in the AM. Since the main move's animation has already set `_waiting_for_client=True`, the MarkerMeetAlg sits in the queue. When the client acks the main animation via `play_next_undo`, the AM processes the spurious MarkerMeetAlg → sends `marker_meet` to client → sets `_waiting_for_client=True` again. `_handle_play_next` sees AM not idle and returns without popping the next undo. The client then sends `animation_done` for the marker_meet, but nobody sends another `play_next_undo` → rewind stalls.
**Fix:** Guard `op.play(Algs.AM)` and the final `op.play(Algs.AN)` in `_w_slice_edges_annotate` with `if slots:` — only play marker meet/annotation algs when there are actual marker slots to clean up.
**File:** `src/cube/application/commands/OpAnnotation.py`

## Key Design Decisions

1. **Undo-based restore** (not color repaint) — Only way to properly reverse Part rotations
2. **Server drives edit mode exit** — Client should not call `exit()` on OK; wait for server `editMode=false`
3. **`_edit_ok_pending` + queue-drained** — Avoids needing complex FSM states like EDITING_ANIMATING
4. **`_edit_preview_text` tracking** — Avoids redundant replay when Play→OK with same text
5. **STOP allowed in EDITING** — User can cancel animations during edit preview

## Current Status

- All 7 bugs above are fixed and committed
- Debug prints removed from ClientSession.py
- Version: 1.63.5

## Next Steps

- User to test rewind-all fix (restart server + refresh browser)
- Run all checks if further changes needed
