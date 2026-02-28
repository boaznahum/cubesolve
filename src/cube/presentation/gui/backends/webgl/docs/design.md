# WebGL Frontend — Design

## Frontend Module Structure (ES Modules)

The browser client uses native ES modules with an import map for Three.js:

```
static/
  index.html              <- import map + <script type="module">
  js/
    main.js               <- Entry point, wires all components
    constants.js           <- Colors, FACE_DEFS, geometry helpers
    AppState.js            <- Central state store (EventTarget)
    CubeModel.js           <- Three.js geometry + sticker colors
    AnimationQueue.js      <- Animation state machine (queue + easing)
    ArrowGuide.js          <- Visual drag-direction arrows
    FaceTurnHandler.js     <- Drag/click-to-turn on stickers
    OrbitControls.js       <- Camera orbit/pan/zoom
    WsClient.js            <- WebSocket connect/send/reconnect
    Toolbar.js             <- DOM toolbar + overlays + keyboard
```

## Data Flow

```
WsClient receives message
  -> dispatches to handler
    -> AppState.update(patch)        <- central state change
      -> Toolbar listens -> updates DOM
      -> CubeModel listens -> updates 3D
    -> AnimationQueue.enqueue()      <- animation events
    -> CubeModel.updateFromState()   <- direct state updates
```

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
