/**
 * Central application state store.
 *
 * Extends EventTarget so any component can listen for 'change' events.
 * Phase 1: holds state previously scattered across CubeClient properties.
 * Phase 2+: will support undo/redo queue.
 */
export class AppState extends EventTarget {
    constructor() {
        super();
        this.cubeSize = 3;
        this.solverName = '';
        this.solverList = [];
        this.debugMode = true;
        this.animationEnabled = true;
        this.isPlaying = false;
        this.moveCount = 0;
        this.status = 'connecting';
        this.version = '';
        this.clientCount = 0;
        this.sessionId = null;
        this.latestState = null;
    }

    update(patch) {
        Object.assign(this, patch);
        this.dispatchEvent(new CustomEvent('change', { detail: patch }));
    }
}
