# Bug Fix: Block Face Rotations During Solve/Play

## Bug Description

During solve playing or queue playing, the user can still press face rotation keys (F, U, R, L, D, B, etc.), click face rotation toolbar buttons, or mouse-drag to rotate faces. This corrupts the solver state because moves get injected into the cube while the solver's redo queue is being played back.

## Root Cause Analysis

The FSM already defines `face_turn` as only allowed in `{IDLE, READY}` states. The problem is that **not all code paths check the FSM before executing a face turn**.

### Current Gating (Asymmetric)

| Action Path | Pre-gated by FSM? | Details |
|---|---|---|
| **Mouse drag** | YES | `ClientSession._handle_mouse_face_turn()` line 917: `if not self._fsm.send(FlowEvent.FACE_TURN): return` |
| **Keyboard keys** | NO | `inject_command()` executes the command first, sends `FACE_TURN` event AFTER |
| **Toolbar buttons** | PARTIAL | Client disables buttons via `allowedActions.face_turn`, but if somehow sent, server doesn't gate |
| **Command msg from client** | NO | `_handle_command()` maps to Command and calls `inject_command()` without FSM check |

### The Fix Point

`ClientSession.inject_command()` (line ~1302) is the single entry point for all face rotation commands. The fix should go here — check FSM **before** executing the command, not after.

## Plan

### Step 1: Identify Face Rotation Commands

In `inject_command()`, we need to know which commands are face rotations. These are all the `ROTATE_*` and `SLICE_*` commands:

```
ROTATE_R, ROTATE_R_PRIME, ROTATE_L, ROTATE_L_PRIME,
ROTATE_U, ROTATE_U_PRIME, ROTATE_D, ROTATE_D_PRIME,
ROTATE_F, ROTATE_F_PRIME, ROTATE_B, ROTATE_B_PRIME,
SLICE_M, SLICE_M_PRIME, SLICE_E, SLICE_E_PRIME,
SLICE_S, SLICE_S_PRIME
```

Also possibly wide moves and cube rotations (X, Y, Z) — need to check if these should also be blocked.

### Step 2: Add FSM Gate in `inject_command()`

In `ClientSession.inject_command()`, before the generic `command.execute(ctx)` call (~line 1302), add:

```python
# Gate face rotations by FSM state
if command.is_face_turn:  # or check against a set of commands
    if not self._fsm.send(FlowEvent.FACE_TURN):
        self.send_state()  # update client (buttons may need refresh)
        return
```

This ensures:
- During PLAYING/REWINDING/SOLVING/ANIMATING/STOPPING → rotation is rejected
- During IDLE/READY → rotation proceeds normally
- The existing post-execution `FACE_TURN` event (line 1313-1314) becomes redundant for gating but still useful for state transitions

### Step 3: Decide What Counts as a "Face Turn"

Need to decide:
- **ROTATE_* commands**: Definitely block (F, U, R, L, D, B face turns)
- **SLICE_* commands**: Definitely block (M, E, S slices)
- **Cube rotations (X, Y, Z)**: Maybe allow? They don't change the cube state, just the view. But they DO change face assignments. **Recommendation: Block them too** during play — they could confuse the solver.
- **Wide moves (Rw, Lw, etc.)**: Block — they modify cube state.

### Step 4: Implementation Options

**Option A: Add `is_face_turn` property to Command enum**
- Clean, declarative
- Each Command knows if it's a face turn
- Easy to maintain

**Option B: Define a set in ClientSession**
```python
_FACE_TURN_COMMANDS: frozenset[Command] = frozenset({
    Commands.ROTATE_R, Commands.ROTATE_R_PRIME,
    # ... all rotation commands
})
```
- Keep it local to the WebGL backend
- No changes to shared Command code

**Recommendation: Option B** — keeps the change scoped to the WebGL backend, doesn't modify shared domain code.

### Step 5: Frontend Hardening (Belt + Suspenders)

The toolbar buttons are already disabled via `allowedActions.face_turn`. But we should also:

1. **In `FaceTurnHandler.js`**: Check `allowedActions.face_turn` in the `blocked` getter (currently only checks animation queue):
```javascript
get blocked() {
    if (this.paintMode) return false;
    const state = this._appState;
    if (state.allowedActions && !state.allowedActions.face_turn) return true;
    return this.animQueue.currentAnim !== null || this.animQueue.queue.length > 0;
}
```

2. **In keyboard handler** (wherever key→command mapping happens on client): Could suppress sending face rotation key events when `face_turn` is not allowed. But this is optional since the server gate is the real fix.

### Step 6: Handle the Post-Execution FACE_TURN Event

After adding the pre-gate, the existing code at line 1313-1314:
```python
if len(self._app.op.history()) > history_len_before:
    self._fsm.send(FlowEvent.FACE_TURN)
```

This still serves a purpose: it transitions the FSM state when a face turn IS allowed and executed (e.g., from IDLE to... well, FACE_TURN from IDLE stays IDLE). Check the FSM transition table to see if this is needed. If FACE_TURN from IDLE→IDLE and READY→READY (no-op transitions), then the pre-gate `send(FACE_TURN)` already handles the state check, and the post-execution event is harmless but redundant.

**Check:** Does FACE_TURN cause any meaningful transition?
- From FSM: `IDLE: {FACE_TURN: IDLE}`, `READY: {FACE_TURN: READY}` — stays in same state
- So the post-execution event is a no-op. BUT the pre-gate `send()` returns True/False which is the gating mechanism.

**Important:** The pre-gate call to `self._fsm.send(FlowEvent.FACE_TURN)` will "consume" the event. The post-execution call would be a second `send()` — but since we're already in IDLE/READY and FACE_TURN→same state, it's harmless. No change needed.

## Files to Modify

1. **`ClientSession.py`** (~line 1300): Add FSM gate before `command.execute(ctx)` for face turn commands
2. **`FaceTurnHandler.js`** (~line 39): Add `allowedActions.face_turn` check to `blocked` getter
3. **`ClientSession.py`**: Define `_FACE_TURN_COMMANDS` frozenset

## Testing

- Start a solve, during playback press F/R/U keys → should be ignored
- Start a solve, during playback try mouse drag rotate → should be blocked (already works)
- Start a solve, during playback click F/R/U toolbar buttons → should be disabled (already works via UI)
- After solve completes (IDLE/READY), verify face rotations work normally
- After stop during play, verify face rotations work again

## Risk Assessment

- **Low risk**: FSM already defines the correct allowed states for `face_turn`
- **No FSM changes needed**: The state machine already has the right rules
- **Server-side gate is authoritative**: Client-side hardening is defense-in-depth
- **No solver code changes**: Only the command dispatch path changes
