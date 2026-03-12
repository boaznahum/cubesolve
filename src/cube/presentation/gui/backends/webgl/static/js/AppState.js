/**
 * Central application state store — single source of truth.
 *
 * Receives complete state snapshots from the server via the 'state'
 * message type. All UI components listen for 'change' events and
 * derive their display from this store. No component holds its own
 * copy of server state.
 *
 * Client-only state (camera, animation queue, orbit controls) is NOT
 * stored here — those are rendering concerns, not application state.
 */
export class AppState extends EventTarget {
    constructor() {
        super();

        // -- Cube --
        this.cubeSize = 3;
        this.cubeSolved = false;
        this.cubeFaces = {};

        // -- Flow state machine --
        this.machineState = 'idle';
        this.allowedActions = {};

        // -- Playback (derived from machineState for backward compat) --
        this.isPlaying = false;

        // -- History --
        this.historyDone = [];
        this.historyRedo = [];
        this.redoSource = 'undo';  // 'solver' | 'undo'
        this.redoTainted = false;
        this.nextMove = null;

        // -- Speed --
        this.speedIndex = 0;
        this.speedStep = 0.5;
        this.speedD0 = 500;
        this.speedDn = 50;

        // -- Toolbar / Config --
        this.debug = false;
        this.animationEnabled = true;
        this.solverName = '';
        this.solverList = [];
        this.sliceStart = 0;
        this.sliceStop = 0;
        this.assistEnabled = true;
        this.assistDelayMs = 400;
        this.soundEnabled = false;
        this.operatorBufferMode = true;
        this.queueHeadingH1 = true;
        this.queueHeadingH2 = false;
        this.defaultScramble = '0';  // '0'-'9' or '*'

        // -- Text overlays --
        this.animationText = [];
        this.statusText = '';
        this.solverText = '';
        this.moveCount = 0;
        this.errorText = '';

        // -- Edit mode --
        this.editMode = false;
        this.editAlgText = '';

        // -- Meta --
        this.version = '';
        this.clientCount = 0;
        this.sessionId = null;

        // -- Connection (client-only) --
        this.status = 'connecting';

        // -- Latest raw cube_state for animation (client-only) --
        this.latestState = null;
    }

    /**
     * Apply a complete state snapshot from the server.
     * Extracts nested groups into flat properties.
     */
    applyServerSnapshot(msg) {
        const patch = {};

        // Cube
        if (msg.cube) {
            patch.cubeSize = msg.cube.size;
            patch.cubeSolved = msg.cube.solved;
            patch.cubeFaces = msg.cube.faces;
            // Also update latestState in cube_state format for AnimationQueue
            patch.latestState = {
                type: 'cube_state',
                size: msg.cube.size,
                solved: msg.cube.solved,
                faces: msg.cube.faces,
            };
        }

        // Flow state machine
        if (msg.machine_state !== undefined) {
            patch.machineState = msg.machine_state;
        }
        if (msg.allowed_actions !== undefined) {
            patch.allowedActions = msg.allowed_actions;
        }

        // Playback (derived from machine_state for backward compat)
        if (msg.is_playing !== undefined) {
            patch.isPlaying = msg.is_playing;
        }

        // History
        if (msg.history) {
            patch.historyDone = msg.history.done || [];
            patch.historyRedo = msg.history.redo || [];
            patch.redoSource = msg.history.redo_source || 'undo';
            patch.redoTainted = msg.history.redo_tainted || false;
            patch.nextMove = msg.history.next_move || null;
        }

        // Speed
        if (msg.speed) {
            patch.speedIndex = msg.speed.index;
            patch.speedStep = msg.speed.step;
            patch.speedD0 = msg.speed.d0;
            patch.speedDn = msg.speed.dn;
        }

        // Toolbar / Config
        if (msg.toolbar) {
            patch.debug = msg.toolbar.debug;
            patch.animationEnabled = msg.toolbar.animation;
            patch.solverName = msg.toolbar.solver_name;
            patch.solverList = msg.toolbar.solver_list;
            patch.sliceStart = msg.toolbar.slice_start;
            patch.sliceStop = msg.toolbar.slice_stop;
            patch.assistEnabled = msg.toolbar.assist_enabled;
            patch.assistDelayMs = msg.toolbar.assist_delay_ms;
            patch.soundEnabled = msg.toolbar.sound_enabled;
            patch.operatorBufferMode = msg.toolbar.operator_buffer_mode;
            patch.queueHeadingH1 = msg.toolbar.queue_heading_h1;
            patch.queueHeadingH2 = msg.toolbar.queue_heading_h2;
            patch.defaultScramble = msg.toolbar.default_scramble;
        }

        // Text
        if (msg.text) {
            patch.animationText = msg.text.animation || [];
            patch.statusText = msg.text.status || '';
            patch.solverText = msg.text.solver || '';
            patch.moveCount = msg.text.moves || 0;
            patch.errorText = msg.text.error || '';
        }

        // Edit mode
        if (msg.edit_mode !== undefined) patch.editMode = msg.edit_mode;
        if (msg.edit_alg_text !== undefined) patch.editAlgText = msg.edit_alg_text;

        // Meta
        if (msg.version !== undefined) patch.version = msg.version;
        if (msg.client_count !== undefined) patch.clientCount = msg.client_count;
        if (msg.session_id !== undefined) patch.sessionId = msg.session_id;

        this.update(patch);
    }

    /**
     * Apply a partial update and notify listeners.
     */
    update(patch) {
        Object.assign(this, patch);
        this.dispatchEvent(new CustomEvent('change', { detail: patch }));
    }
}
