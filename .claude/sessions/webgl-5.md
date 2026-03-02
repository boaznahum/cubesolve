# Session: webgl-5 — Unified State Snapshot + Client Pull Model

## Previous Work: Client-Initiated Pull Model (v1.19)
- Replaced server-driven playback loop with client-initiated pull model
- Client requests each move via `play_next_redo`/`play_next_undo`
- Server responds with animation_start + state
- `play_empty` signals end of queue

## Current Work: Unified State Snapshot (v1.20)

### Goal
Replace fragmented state management (~10 individual `send_*()` calls) with a single unified state snapshot pattern (Redux/Flux-like).

### What Was Done
- **SessionState.py** (NEW): `SessionStateSnapshot` dataclass with all server state fields + `to_json()`
- **ClientSession.py**: Added `_build_state_snapshot()` and `send_state()`, replaced ~30 scattered `send_*()` calls
- **WebglAnimationManager.py**: Replaced `send_cube_state()`/`send_text()` with `send_state()`
- **AppState.js**: Rewritten — full state store with `applyServerSnapshot(msg)`
- **main.js**: New `case 'state':` handler, simplified `play_empty`, kept event messages
- **Toolbar.js**: Added `updateFromState(appState)` — derives stop button from both server + client state
- **HistoryPanel.js**: Added `updateFromState(appState)`
- **design.md** + **animation-stop-design.md**: Updated to document new architecture

### Architecture
- **Server** sends ONE complete JSON `state` message after every state change
- **Client** applies snapshot atomically via `AppState.applyServerSnapshot(msg)`
- **Event messages** remain separate: `animation_start`, `animation_done`, `play_next_redo/undo`, `play_empty`, `flush_queue`, `color_map`
- **Stop button**: `disabled = !(server.isPlaying || client.hasActiveAnimation)`

### Tests
- All 5 checks pass (ruff, mypy, pyright, non-GUI tests, GUI tests)
- All 9 WebGL tests pass
- Added `tests/webgl/test_startup_state.py` — 3 tests for startup state

## Current Task: Assist Arrows for Keyboard Operations

### Goal
When assist is ON, show gesture/assist arrows for user keyboard operations too (not just queue playback). This helps debug the "some assists are in the wrong direction" issue by letting the user see arrow directions for every operation, independent of queue/undo/redo logic.

### Context
Currently the assist system has two modes:
1. **Static next-move indicators** — chevrons shown when idle, based on `state.nextMove` (peek at redo queue)
2. **Pre-animation assist preview** — brief arrow flash before each queued animation (`assistDelayMs`)

The pre-animation preview already fires for keyboard ops via `AnimationQueue._processNext()`, but the user wants to ensure arrows are clearly visible for all keyboard-initiated moves to verify direction correctness.

### Key Files
- `static/js/MoveIndicator.js` — renders chevron arrows on affected stickers
- `static/js/AnimationQueue.js` — manages assist preview delay before animations
- `static/js/main.js` — wires assist show/hide callbacks
- `ClientSession.py` — server-side command handling, `animation_start` message
- `WebglAnimationManager.py` — sends animation events with face/layers/direction

### What Was Done
- Found bug: `state` message arriving during assist preview phase overwrites arrows
  - `main.js` state handler checked `!animQueue.currentAnim && queue.length === 0` but missed `_previewState`
  - During preview: `currentAnim` is null, queue is empty (item dequeued into preview), so condition was true
  - `moveIndicator.show(state.nextMove)` with null nextMove → hid the assist arrows
- Fix: Added `get isBusy()` getter to `AnimationQueue` (includes `_previewState`)
- Used `!animQueue.isBusy` in both state handler conditions in `main.js`
- User tested all 12 basic face moves (F/F'/B/B'/U/U'/R/R'/L/L'/D/D') — all arrows correct

## Known Bugs (to investigate)
- User reports: "cube in startup whole gray" — could not reproduce in tests or Chrome
- User reports: "pressing solve stuck the application" — could not reproduce
- These may be related to stale browser state or server restart timing

## Key Files
```
src/cube/presentation/gui/backends/webgl/SessionState.py       (NEW)
src/cube/presentation/gui/backends/webgl/ClientSession.py       (modified)
src/cube/presentation/gui/backends/webgl/WebglAnimationManager.py (modified)
src/cube/presentation/gui/backends/webgl/static/js/AppState.js  (rewritten)
src/cube/presentation/gui/backends/webgl/static/js/main.js      (modified)
src/cube/presentation/gui/backends/webgl/static/js/Toolbar.js   (modified)
src/cube/presentation/gui/backends/webgl/static/js/HistoryPanel.js (modified)
tests/webgl/test_startup_state.py                                (NEW)
```
