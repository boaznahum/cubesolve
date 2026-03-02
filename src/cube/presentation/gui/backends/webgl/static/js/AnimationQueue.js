/**
 * Animation queue — manages face rotation animations with easing.
 *
 * Receives animation events from the server, queues them, and plays
 * them sequentially at 60fps using temporary Three.js rotation groups.
 *
 * Assist mode: when assistDelayMs > 0, shows a brief move indicator
 * preview before each animation starts (via callbacks).
 */

import * as THREE from 'three';

export class AnimationQueue {
    constructor(cubeModel, sendFn) {
        this.cubeModel = cubeModel;
        this._send = sendFn || (() => {});  // WebSocket send function
        this.queue = [];
        this.currentAnim = null;
        this.pendingState = null;  // State to apply after all animations
        this._stopRequested = false;
        this._onDebugUpdate = null;  // callback(alg, layers, count) for debug overlay
        this._onAllDone = null;      // callback() when queue drains and no animation

        // Assist preview: show move indicator before each animation
        this.assistDelayMs = 400;    // default on; 0 = off, >0 = preview duration in ms
        this._onAssistShow = null;   // callback(face, layers, direction)
        this._onAssistHide = null;   // callback()
        this._previewState = null;   // { startTime, event, state, face, speedMult }

        // Playback mode: null = single move, 'forward' = playing redo, 'backward' = rewinding
        this.playbackMode = null;
    }

    /**
     * Start playback mode — after each animation finishes, request the next move.
     * @param {'forward' | 'backward'} direction
     */
    startPlayback(direction) {
        this.playbackMode = direction;
        this._stopRequested = false;  // Clear stale stop from previous session
    }

    /**
     * Stop playback mode — next _finishCurrent sends animation_done instead of play_next.
     */
    stopPlayback() {
        this.playbackMode = null;
    }

    /**
     * Enqueue an animation event from the server.
     */
    enqueue(event, state) {
        this.queue.push({ event, state });
        if (!this.currentAnim && !this._previewState) {
            this._processNext();
        }
    }

    /**
     * Apply a state immediately (no animation).
     */
    applyState(state) {
        this.cubeModel.updateFromState(state);
    }

    /**
     * Stop all animations and snap to the latest state.
     */
    stop() {
        this.currentAnim = null;
        if (this._previewState) {
            this._previewState = null;
            if (this._onAssistHide) this._onAssistHide();
        }
        this.queue = [];
        this._stopRequested = false;
        if (this.pendingState) {
            this.cubeModel.updateFromState(this.pendingState);
            this.pendingState = null;
        }
    }

    /**
     * Flush queue — graceful stop: clear queue, let currentAnim finish.
     */
    flush(state) {
        this.queue = [];
        if (this._previewState) {
            this._previewState = null;
            if (this._onAssistHide) this._onAssistHide();
        }
    }

    /**
     * Request stop after current animation finishes.
     */
    requestStop() {
        this._stopRequested = true;
        this.queue = [];
        if (this._previewState) {
            this._previewState = null;
            if (this._onAssistHide) this._onAssistHide();
        }
    }

    /**
     * Update animation progress (called each frame).
     * Returns true if an animation is active.
     */
    update() {
        // Handle assist preview phase — wait for delay then start rotation
        if (this._previewState) {
            const elapsed = performance.now() - this._previewState.startTime;
            if (elapsed >= this.assistDelayMs) {
                const { event, state, face, speedMult } = this._previewState;
                this._previewState = null;
                if (this._onAssistHide) this._onAssistHide();
                this._startRotation(event, state, face, speedMult);
            }
            return true;
        }

        if (!this.currentAnim) return false;

        const anim = this.currentAnim;
        const elapsed = performance.now() - anim.startTime;
        let t = Math.min(elapsed / anim.duration, 1.0);

        // Ease in-out cubic
        t = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

        // Apply rotation to the temp group
        const angle = anim.targetAngle * t;
        anim.tempGroup.quaternion.setFromAxisAngle(anim.axis, angle);

        if (elapsed >= anim.duration) {
            this._finishCurrent();
            return this.currentAnim !== null || this._previewState !== null;
        }

        return true;
    }

    _processNext() {
        if (this.queue.length === 0) {
            this.currentAnim = null;
            if (this._onAllDone) this._onAllDone();
            return;
        }

        // If queue is getting long, speed up
        let speedMult = 1.0;
        if (this.queue.length > 10) speedMult = 0.3;
        else if (this.queue.length > 5) speedMult = 0.6;

        const { event, state } = this.queue.shift();
        this.pendingState = state;

        // Normalize face name: server may send uppercase X/Y/Z or bracket-prefixed "[2:2]M"
        let face = event.face;
        const caseMap = {'X':'x', 'Y':'y', 'Z':'z'};
        if (caseMap[face]) {
            face = caseMap[face];
        } else if (face && face.length > 1) {
            // Handle sliced alg format like "[2:2]M" — scan for face letter
            const known = 'RLUDFBMESxyz';
            for (const ch of face) {
                if (known.includes(ch)) { face = ch; break; }
            }
        }

        // Assist preview: show indicator and delay before starting rotation
        if (this.assistDelayMs > 0 && this._onAssistShow) {
            this._onAssistShow(face, event.layers || [0], event.direction || 1);
            this._previewState = {
                startTime: performance.now(),
                event, state, face, speedMult
            };
            return;
        }

        this._startRotation(event, state, face, speedMult);
    }

    _startRotation(event, state, face, speedMult) {
        const duration = (event.duration_ms || 300) * speedMult;
        const direction = event.direction || 1;

        // Determine rotation axis and angle
        const axisInfo = this._getRotationAxis(face, direction);
        if (!axisInfo) {
            // Unknown face — just apply state
            this.cubeModel.updateFromState(state);
            this._processNext();
            return;
        }

        // Create temporary group at rotation pivot
        const tempGroup = new THREE.Group();
        const size = this.cubeModel.size;
        const half = size * this.cubeModel.cellSize / 2;
        const pivotMap = {
            'R': [half, 0, 0], 'L': [-half, 0, 0],
            'U': [0, half, 0], 'D': [0, -half, 0],
            'F': [0, 0, half], 'B': [0, 0, -half],
            // Slice moves and whole-cube: pivot at center
            'M': [0, 0, 0], 'E': [0, 0, 0], 'S': [0, 0, 0],
            'x': [0, 0, 0], 'y': [0, 0, 0], 'z': [0, 0, 0],
        };
        const pivot = pivotMap[face];
        if (pivot) tempGroup.position.set(...pivot);
        this.cubeModel.cubeGroup.add(tempGroup);

        const layers = event.layers || [0];
        const affected = this._getAffectedStickers(face, layers);

        // Debug: show animation info
        console.log(`ANIM: alg=${event.alg} type=${event.alg_type} face=${face} layers=[${layers}] affected=${affected.length} size=${size}`);
        if (this._onDebugUpdate) {
            this._onDebugUpdate(event.alg || face, layers, affected.length);
        }

        for (const mesh of affected) {
            tempGroup.attach(mesh);  // preserves world position, recalcs local
        }

        this.currentAnim = {
            tempGroup: tempGroup,
            affected: affected,
            axis: axisInfo.axis,
            targetAngle: axisInfo.angle,
            duration: duration,
            startTime: performance.now(),
            state: state,
        };
    }

    _finishCurrent() {
        if (!this.currentAnim) return;

        const anim = this.currentAnim;

        // Reparent stickers back to cubeGroup before removing temp group
        // (resetPositions will fix their positions afterwards)
        for (const mesh of anim.affected) {
            this.cubeModel.cubeGroup.attach(mesh);
        }

        // Remove temp group
        this.cubeModel.cubeGroup.remove(anim.tempGroup);

        // Apply new state (colors) and reset positions to canonical
        if (anim.state) {
            this.cubeModel.updateFromState(anim.state);
        }
        this.cubeModel.resetPositions();

        this.currentAnim = null;

        if (this._stopRequested) {
            this._stopRequested = false;
            // Send animation_done for the completed animation (server needs ack)
            this._send({ type: 'animation_done' });
            return;  // Don't process next or request more — stop was requested
        }

        // In playback mode, request the next move from server
        if (this.playbackMode === 'forward') {
            this._send({ type: 'play_next_redo' });
        } else if (this.playbackMode === 'backward') {
            this._send({ type: 'play_next_undo' });
        } else {
            // Single move — tell server this animation is done
            this._send({ type: 'animation_done' });
        }

        this._processNext();
    }

    _getRotationAxis(face, direction) {
        const size = this.cubeModel.size;
        const half = size * this.cubeModel.cellSize / 2;

        // Determine angle based on direction
        let angle;
        if (direction === 2 || direction === -2) {
            angle = Math.PI;
        } else if (direction === -1) {
            angle = Math.PI / 2;
        } else {
            angle = -Math.PI / 2;
        }

        // Map face to rotation axis
        // Convention: CW when looking at face from outside the cube
        const map = {
            'R': { axis: new THREE.Vector3(1, 0, 0), angle: angle },
            'L': { axis: new THREE.Vector3(1, 0, 0), angle: -angle },
            'U': { axis: new THREE.Vector3(0, 1, 0), angle: angle },
            'D': { axis: new THREE.Vector3(0, 1, 0), angle: -angle },
            'F': { axis: new THREE.Vector3(0, 0, 1), angle: angle },
            'B': { axis: new THREE.Vector3(0, 0, 1), angle: -angle },
            // Slice moves (M follows L, E follows D, S follows F)
            'M': { axis: new THREE.Vector3(1, 0, 0), angle: -angle },
            'E': { axis: new THREE.Vector3(0, 1, 0), angle: -angle },
            'S': { axis: new THREE.Vector3(0, 0, 1), angle: angle },
            // Whole cube rotations (x follows R, y follows U, z follows F)
            'x': { axis: new THREE.Vector3(1, 0, 0), angle: angle },
            'y': { axis: new THREE.Vector3(0, 1, 0), angle: angle },
            'z': { axis: new THREE.Vector3(0, 0, 1), angle: angle },
        };

        return map[face] || null;
    }

    _getAffectedStickers(face, layers) {
        // Select stickers whose position along the rotation axis matches
        // any of the given physical layer columns.
        const size = this.cubeModel.size;
        const cellSize = this.cubeModel.cellSize;
        const half = size * cellSize / 2;

        // Whole-cube rotations: ALL stickers
        if (['x', 'y', 'z'].includes(face)) {
            const affected = [];
            for (const meshes of Object.values(this.cubeModel.stickers)) {
                affected.push(...meshes);
            }
            return affected;
        }

        // Map face/slice name to rotation axis
        const axisMap = {
            'R': 'x', 'L': 'x', 'M': 'x',
            'U': 'y', 'D': 'y', 'E': 'y',
            'F': 'z', 'B': 'z', 'S': 'z',
        };
        const axis = axisMap[face];
        if (!axis) return [];

        // Convert layer columns to target positions along the axis
        const targetPositions = layers.map(col => (col + 0.5) * cellSize - half);
        const tol = cellSize * 0.45;

        const affected = [];
        for (const meshes of Object.values(this.cubeModel.stickers)) {
            for (const mesh of meshes) {
                const v = mesh.position[axis];
                for (const target of targetPositions) {
                    if (Math.abs(v - target) < tol) {
                        affected.push(mesh);
                        break;
                    }
                }
            }
        }
        return affected;
    }
}
