# WebGL Frontend — Design

## Frontend Module Structure (ES Modules)

The browser client uses native ES modules with an import map for Three.js:

```
static/
  index.html              <- import map + <script type="module">
  js/
    main.js               <- Entry point, wires all components
    constants.js           <- Colors, FACE_DEFS, geometry helpers
    AppState.js            <- Central state store (unified snapshot receiver)
    CubeModel.js           <- Three.js geometry + sticker colors
    AnimationQueue.js      <- Animation state machine (queue + easing)
    ArrowGuide.js          <- Visual drag-direction arrows
    FaceTurnHandler.js     <- Drag/click-to-turn on stickers
    OrbitControls.js       <- Camera orbit/pan/zoom
    WsClient.js            <- WebSocket connect/send/reconnect
    Toolbar.js             <- DOM toolbar + overlays + keyboard
```

## Data Flow — Unified State Snapshot

The server sends a single `state` message containing ALL application state
after every state change. The client applies this snapshot atomically.

```
Server state change (any)
  -> ClientSession._build_state_snapshot()   <- gather ALL state
  -> send_state()                            <- ONE JSON message

WsClient receives 'state' message
  -> AppState.applyServerSnapshot(msg)       <- update ALL fields
  -> Toolbar.updateFromState(appState)       <- update DOM from state
  -> HistoryPanel.updateFromState(appState)  <- update history UI
  -> CubeModel.updateFromState(latestState)  <- update 3D (if not animating)
```

### Separate event messages (NOT state, real-time events)

```
animation_start  (server → client)   Start a 3D face rotation
animation_done   (client → server)   Animation finished, ack
play_next_redo   (client → server)   Request next forward move
play_next_undo   (client → server)   Request next backward move
play_empty       (server → client)   No more moves to play
flush_queue      (server → client)   Clear pending animations
color_map        (server → client)   One-time on connect (static)
```

### State ownership

| State | Owner | Notes |
|-------|-------|-------|
| Cube, history, config, is_playing | Server (in snapshot) | Single source of truth |
| currentAnim, queue, playbackMode | Client (AnimationQueue) | Rendering concern |
| _stopRequested | Client (AnimationQueue) | Client remembers to stop after current |
| Camera, orbit controls | Client (OrbitControls) | Pure rendering |
| Stop button enabled | Derived: server.isPlaying OR client.hasAnimation | Both sides considered |

## Module Dependencies

```
constants.js        <- no deps (+ THREE)
AppState.js         <- no deps
CubeModel.js        <- THREE, constants
AnimationQueue.js   <- THREE
ArrowGuide.js       <- THREE, constants
FaceTurnHandler.js  <- THREE, constants, ArrowGuide
OrbitControls.js    <- THREE
WsClient.js         <- no deps
Toolbar.js          <- no deps (DOM only)
main.js             <- imports all above, wires together
```
