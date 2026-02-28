# Animation Queue & Stop Button — Design Document

## Problem

The stop button must be **enabled throughout a multi-move sequence** (solve,
scramble) and **disabled for single moves** (individual face rotations).

### Why client-only tracking fails

The server sends moves one at a time via timers. The client queue only ever
has 0 or 1 items. Checking `queue.length > 0` is useless for detecting a
multi-move sequence — the button flickers enabled for a fraction of a second
between atomic moves, then immediately disables.

**Root cause**: the server holds the full move queue. The client sees one move
at a time. Only the server knows whether a sequence is in progress.

### Approaches considered

| Approach | Verdict |
|----------|---------|
| **Client-only**: derive button state from `currentAnim && queue.length > 0` | Failed — client queue never has >1 items |
| **Server sends full queue upfront**: batch all moves to client | Rejected — breaks timer-paced playback; client would need its own timing logic |
| **Server sends move count**: `{type: "sequence_start", total: N}` | Over-engineered — client doesn't need the count, just start/stop |
| **Server sends `playing` boolean signal** | Chosen — minimal, 2 messages per sequence |

## Architecture

```
 Server (Python)                         Client (JS)
 ┌─────────────────────┐                 ┌────────────────────────┐
 │ WebglAnimationManager│                 │ AnimationQueue          │
 │                     │                 │                        │
 │ _move_queue: deque  │  WS messages   │ queue: [] (0-1 items)  │
 │ _is_processing: bool│ ──────────────→│ currentAnim            │
 │ _playing_sent: bool │                 │ _stopRequested: bool   │
 └─────────────────────┘                 └────────────────────────┘
```

### Who owns what

| Concern | Owner | Why |
|---------|-------|-----|
| Move queue (all pending moves) | Server | Moves enqueued synchronously from `Operator._play()` loop |
| Timer-paced dispatch (one move at a time) | Server | `schedule_once` fires `_process_next` after each animation duration |
| 60fps animation rendering | Client | Three.js runs in browser at GPU framerate |
| Stop button enabled/disabled | Server decides, client applies | Only server knows if sequence is in progress |
| Stop request (user clicks) | Client remembers, server cancels queue | Both sides cooperate |

## Data Flow

### Normal multi-move sequence (solve/scramble)

```
Server                                    Client
  │                                         │
  │  Operator._play() flattens alg          │
  │  into N moves, calls run_animation()    │
  │  for each in a tight loop               │
  │                                         │
  │  1st call: _is_processing=False         │
  │    → _process_next() dequeues move #1   │
  │    → sends animation_start + cube_state │
  │    → schedules timer, returns           │
  │  ─────── animation_start ──────────────→│  start animating move #1
  │                                         │
  │  2nd call: _is_processing=True          │
  │    → appends to queue                   │
  │    → _playing_sent was False            │
  │    → sends playing=true                 │
  │  ─────── playing: true ────────────────→│  btn-stop.disabled = false
  │                                         │
  │  3rd..Nth call: _is_processing=True     │
  │    → appends to queue                   │
  │    → _playing_sent already True, skip   │
  │                                         │
  │  ← timer fires →                       │
  │  _process_next() dequeues move #2       │
  │  ─────── animation_start ──────────────→│  start animating move #2
  │  ...repeats for each move...            │
  │                                         │
  │  _process_next(): queue empty           │
  │    → sends playing=false                │
  │  ─────── playing: false ───────────────→│  btn-stop.disabled = true
  │                                         │
```

### Single move (face rotation)

```
Server                                    Client
  │                                         │
  │  run_animation() called once            │
  │  _is_processing=False                   │
  │    → _process_next() dequeues it        │
  │    → sends animation_start              │
  │  ─────── animation_start ──────────────→│  animate face
  │                                         │
  │  timer fires, queue empty               │
  │  _playing_sent is False → no signal     │
  │                                         │  (stop button stays disabled)
```

### Stop pressed during animation

```
Server                                    Client
  │                                         │
  │  (sequence in progress, moves queued)   │
  │                                         │  User clicks Stop
  │                                         │  → requestStop(): set _stopRequested,
  │                                         │    clear local queue
  │  ←──── command: stop ──────────────────│
  │                                         │
  │  inject_command(STOP_ANIMATION):        │
  │    → send_flush_queue()                 │
  │    → cancel_animation():                │
  │      clear _move_queue                  │
  │      send playing=false                 │
  │  ─────── flush_queue ──────────────────→│  animQueue.flush() — clears queue
  │  ─────── playing: false ───────────────→│  btn-stop.disabled = true
  │                                         │
  │                                         │  Current animation finishes naturally
  │                                         │  _finishCurrent():
  │                                         │    _stopRequested is true
  │                                         │    → clear flag, DON'T process next
  │                                         │    → apply pending state (snap to
  │                                         │      post-move position)
  │                                         │
```

## Server Implementation

### `WebglAnimationManager`

**State**: `_playing_sent: bool` — tracks whether `playing: true` has been sent
for the current sequence. Prevents duplicate messages.

**Transitions**:

| Event | Condition | Action |
|-------|-----------|--------|
| `run_animation()` | `_is_processing` and not `_playing_sent` | Send `playing: true`, set `_playing_sent = True` |
| `_process_next()` queue empty | `_playing_sent` is True | Send `playing: false`, set `_playing_sent = False` |
| `cancel_animation()` | `_playing_sent` is True | Send `playing: false`, set `_playing_sent = False` |

### Why `playing: true` is sent in `run_animation()`, not `_process_next()`

When `run_animation()` is called from the `Operator._play()` for-loop:

1. **1st call**: `_is_processing` is False → calls `_process_next()` which
   dequeues the move and schedules a timer. At this point, only 1 move has
   been enqueued, so we can't tell if it's a single move or the start of a
   sequence.

2. **2nd call**: `_is_processing` is True → the move is appended to the queue.
   Now we **know** it's a multi-move sequence. This is the right moment to
   send `playing: true`.

3. **3rd+ calls**: `_playing_sent` is already True → no redundant messages.

This avoids a false positive for single moves and avoids the need for
heuristics or timeouts.

## Client Implementation

### `AnimationQueue`

**State**: `_stopRequested: bool` — set when user clicks stop during an
active animation.

**Methods**:

| Method | Purpose |
|--------|---------|
| `requestStop()` | Set `_stopRequested = true`, clear local queue |
| `_finishCurrent()` | After animation completes: check `_stopRequested`. If set, clear flag and return (don't process next). Otherwise, call `_processNext()` |

### Stop button

The button starts `disabled` in HTML. Its state is controlled exclusively by
the server's `playing` message:

```js
case 'playing': {
    const btn = document.getElementById('btn-stop');
    if (btn) btn.disabled = !msg.value;
    break;
}
```

No client-side logic derives the button state from queue length or animation
state. The server is the single source of truth.

### Click handler

```js
if (btn.dataset.cmd === 'stop') {
    this.animQueue.requestStop();
}
// Always sends command to server (for server-side cancel)
this._send({ type: 'command', name: btn.dataset.cmd });
```

Both sides act: client remembers the stop (to halt local queue processing),
server clears its queue and sends `playing: false`.

## Message Protocol Addition

| Message | Direction | Fields | Description |
|---------|-----------|--------|-------------|
| `playing` | Server → Client | `value: bool` | Multi-move sequence started/ended |

Added to `ClientSession.send_playing(playing: bool)`.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Stop pressed with no animation | Button is disabled — can't click |
| Stop pressed during atomic move | `_stopRequested` set. Current move finishes. Next move not started. Server queue cleared. |
| Rapid stop-solve-stop | Each solve sends `playing: true`, each stop sends `playing: false`. `_playing_sent` flag prevents duplicates. |
| Network delay on stop command | Client immediately sets `_stopRequested` and clears local queue — animation stops locally even before server responds. Server `playing: false` arrives later as confirmation. |
| Single move during sequence | Not possible — keyboard/mouse input is not processed while a sequence is playing (server-side event loop is busy). |
| Event loop exit during sequence | `_process_next()` checks `event_loop.has_exit` and stops processing. `playing: false` is NOT sent (session is shutting down). |
