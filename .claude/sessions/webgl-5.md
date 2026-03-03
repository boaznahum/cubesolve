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

## Assist Arrows for Keyboard Operations (v1.20.1)
- Found bug: `state` message arriving during assist preview phase overwrites arrows
- Fix: Added `get isBusy()` getter to `AnimationQueue` (includes `_previewState`)
- Used `!animQueue.isBusy` in both state handler conditions in `main.js`
- User tested all 12 basic face moves — all arrows correct

## Red Undo Assist Arrows (v1.20.2)
- Server tags `animation_start` with `is_undo` flag
- Client renders undo assist arrows in red (`0xcc0000`) instead of black

## Fix: Mouse M-Slices Reversed on U/D (v1.20.5)
- Bug: vertical drag on middle column of U/D faces produced reversed M-slice
- Root cause: `_slice_on_edge_alg()` was missing `inv = True` in the `is_bottom_or_top` branch for U/D
- Fix: Added `inv = True` to the U/D `is_bottom_or_top` branch in `ClientSession.py`

## Universal Undo Flag (v1.20.5)
- User complained undo from keyboard didn't show red arrows
- Root cause: `_is_undo` flag was scattered across individual callers, missing keyboard undo
- Fix: Wrap `op.undo` once at init time so ALL undo paths automatically set the flag

## Assist Checkbox Bugs (v1.20.5)
- Bug 1: Unchecking assist stole keyboard focus (INPUT tag check in keydown handler)
  - Fix: `chkAssist.blur()` after change event
- Bug 2: Any server state update reset assist checkbox to server value
  - Fix: `_assistLocalOverride` tracks user's local toggle, skips server overwrite
- Bug 3: Static arrows still showed when assist was off
  - Fix: `isAssistActive()` helper in main.js gates ALL arrow-showing

## Commits
- `d8a0239c` — Fix assist arrows hidden during keyboard operations (v1.20.1)
- `7e80137b` — Red assist arrows for undo operations (v1.20.2)
- `5202f838` — Fix reversed mouse E-slices on U/D faces (v1.20.3) — REVERTED
- `3ac29861` — Revert wrong E-slice fix
- `0e05d2a5` — Fix M-slice direction, universal undo flag, assist checkbox bugs (v1.20.5)

## Next: Remove Legacy Message Handlers
- Delete `handleMessage()`, `_updateToolbar()`, `_updateTextOverlays()` from Toolbar.js
- Delete legacy `case` branches from main.js `default:` handler
- Server-side: remove any `send_*()` methods that only sent legacy individual messages

## Flow State Machine (v1.21)

### Goal
Replace scattered boolean flags (`_fast_playing`, `_redo_is_solver`, `_redo_tainted`, `playbackMode`,
`_pendingSolveAndPlay`, `_stopRequested`) across 6+ files with a single explicit state machine owned
by the server. The client reads `machine_state` and `allowedActions` from the snapshot — no reasoning,
no conditions, no bugs.

### States (7)
IDLE, READY, SOLVING, PLAYING, REWINDING, ANIMATING, STOPPING

### What Was Done
- **FlowStateMachine.py** (NEW): Pure-logic FSM with FlowState/FlowEvent enums, static transition table,
  static button enable table, guard conditions, metadata (redo_source, redo_tainted, auto_play)
- **SessionState.py**: Added `machine_state`, `allowed_actions` fields
- **ClientSession.py**: Major refactoring — replaced all boolean flags with `_fsm: FlowStateMachine`,
  all commands route through FSM, `reattach()` uses `send_reconnect()` (fixes reconnect bug),
  wired `_on_queue_drained` callback for single-move ANIM_DONE transitions
- **WebglAnimationManager.py**: Added `_on_queue_drained` callback, updated stale comments
- **AppState.js**: Added `machineState`, `allowedActions`
- **HistoryPanel.js**: Replaced button logic with `allowedActions` lookup, removed `_isPlaying`
- **Toolbar.js**: Removed `_pendingSolveAndPlay`, stop button uses `allowedActions`
- **main.js**: Removed auto-play logic, added state-machine-driven playback sync
- **index.html**: Added reset-session button with refresh icon
- **test_flow_state_machine.py** (NEW): 53 unit tests for FSM

### Bugs Fixed
1. **Reconnect play button disabled**: `reattach()` → `send_reconnect()` → always IDLE/READY
2. **Stop button timing**: enabled iff state in {ANIMATING, PLAYING, REWINDING}
3. **Solve-and-play flag stuck**: FSM auto-transitions SOLVING → PLAYING
4. **Single redo/undo stuck in ANIMATING**: `_on_queue_drained` callback fires ANIM_DONE
5. **Reset session**: works from ANY state → IDLE

### Tests
- 53 FSM unit tests pass
- 65 WebGL E2E tests pass (including previously failing `test_scramble_solution_step_through`)
- 11,401 non-GUI tests pass
- All static checks pass (ruff, mypy, pyright)

## Known Bugs (to investigate)
- User reports: "cube in startup whole gray" — could not reproduce
- User reports: "pressing solve stuck the application" — could not reproduce

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
