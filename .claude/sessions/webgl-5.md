# Session: webgl-5 — Client-Initiated Pull Model

## Task
Replace server-driven playback loop with client-initiated pull model for WebGL animation.

## Key Insight
Client requests each move via `play_next_redo`/`play_next_undo`. Server responds with animation_start + state. Client sends next request after animation completes. `play_empty` signals end of queue.

## Files Modified

### Server
- **`ClientSession.py`**:
  - Added `play_next_redo`/`play_next_undo` message handlers
  - Added `_handle_play_next(forward)` — pops one move, handles non-animatable loops, sends play_empty when done
  - Added `send_play_empty()`
  - Deleted `_fast_play_redo`, `_fast_rewind`, `_fast_play_next`, `_finish_fast_play`
  - Deleted `_fast_forward` field
  - Simplified `animation_done` handler (no playback logic)
  - Simplified STOP_ANIMATION (cancel AM + send play_empty)
  - `solve_and_play` now just solves (client initiates play)

### Client
- **`AnimationQueue.js`**:
  - Added `playbackMode` (null|'forward'|'backward')
  - Added `startPlayback(direction)` / `stopPlayback()`
  - `_finishCurrent()`: sends `play_next_redo/undo` in playback mode, `animation_done` otherwise

- **`Toolbar.js`**:
  - Play/Rewind/Stop buttons use client-initiated pull
  - `solve_and_play` sets `_pendingSolveAndPlay` flag
  - Removed `_deferStopDisable()` (no longer needed)
  - `play_empty` handler calls `stopPlayback()`

- **`main.js`**:
  - Added `play_empty` message handler
  - `history_state` handler triggers auto-play after solve_and_play
  - HistoryPanel now receives `animQueue` for play/rewind buttons

- **`HistoryPanel.js`**:
  - Constructor takes `animQueue` parameter
  - Play/Rewind buttons send `play_next_redo`/`play_next_undo` directly

### Version
- `version.txt`: 1.18 → 1.19

## Status
- Implementation complete
- Ruff passes
- Needs manual testing and E2E test run
