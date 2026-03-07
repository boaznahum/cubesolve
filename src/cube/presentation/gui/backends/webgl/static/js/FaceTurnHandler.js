/**
 * Face turn handler — drag-to-turn and click-to-rotate on cube stickers.
 *
 * Drag workflow:
 *   1. On pointer-down, raycast to see if a sticker was hit.
 *   2. Accumulate drag until threshold (15 px).
 *   3. Project drag vector onto face right/up axes in screen space.
 *   4. Send {type:'mouse_face_turn', ...} to the server which computes the algorithm.
 */

import * as THREE from 'three';
import { FACE_DEFS } from './constants.js';
import { ArrowGuide } from './ArrowGuide.js';

export class FaceTurnHandler {
    constructor(cubeModel, camera, canvas, animQueue, sendFn, scene) {
        this.cubeModel = cubeModel;
        this.camera = camera;
        this.canvas = canvas;
        this.animQueue = animQueue;
        this._send = sendFn;

        this._raycaster = new THREE.Raycaster();
        this.arrowGuide = new ArrowGuide(cubeModel, scene);

        // State
        this._active = false;
        this._hitSticker = null;   // { face, row, col, gridIndex }
        this._startX = 0;
        this._startY = 0;
        this._turnSent = false;
    }

    /** True when animations are playing — face turns are blocked. */
    get blocked() {
        return this.animQueue.currentAnim !== null || this.animQueue.queue.length > 0;
    }

    /**
     * Try to start a face-turn gesture at the given pointer position.
     * @returns {boolean} true if a sticker was hit (caller should NOT orbit).
     */
    start(clientX, clientY) {
        if (this.blocked) return false;

        const hit = this._pickSticker(clientX, clientY);
        if (!hit) return false;

        this._active = true;
        this._hitSticker = hit;
        this._startX = clientX;
        this._startY = clientY;
        this._turnSent = false;

        // Show both arrow guides on the touched sticker
        if (FaceTurnHandler.SHOW_ARROW_GUIDES)
            this.arrowGuide.show(hit.face, hit.row, hit.col);
        return true;
    }

    /** Feed drag deltas while active. */
    onDrag(clientX, clientY) {
        if (!this._active || this._turnSent) return;

        const dx = clientX - this._startX;
        const dy = clientY - this._startY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // Preview: show which direction once drag > 5 px
        if (dist >= 5) {
            const { dotRight, dotUp } = this._computeFaceDots(dx, dy);
            const direction = Math.abs(dotRight) > Math.abs(dotUp) ? 'row' : 'col';
            this.arrowGuide.setActiveDirection(direction);
        }

        // Execute turn once drag > 15 px
        if (dist < 15) return;
        this._executeTurn(dx, dy);
        this._turnSent = true;
    }

    /**
     * End the gesture.
     * @returns {{ face, row, col } | null} the hit sticker if it was a click (no turn sent).
     */
    end() {
        const hit = this._hitSticker;
        const wasTurn = this._turnSent;
        this._active = false;
        this._hitSticker = null;
        this._turnSent = false;
        this.arrowGuide.hide();
        return wasTurn ? null : hit;
    }

    get isActive() { return this._active; }

    /** Master switch for arrow guides — set to false to disable. */
    static SHOW_ARROW_GUIDES = false;

    // ── Raycasting ──

    _pickSticker(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const mouse = new THREE.Vector2(
            ((clientX - rect.left) / rect.width) * 2 - 1,
            -((clientY - rect.top) / rect.height) * 2 + 1,
        );
        this._raycaster.setFromCamera(mouse, this.camera);

        const allMeshes = [];
        for (const meshes of Object.values(this.cubeModel.stickers)) {
            allMeshes.push(...meshes);
        }
        const hits = this._raycaster.intersectObjects(allMeshes);
        return hits.length > 0 ? hits[0].object.userData : null;
    }

    // ── Face-axis projection ──

    /**
     * Project a screen-space drag vector onto the face's right/up axes.
     * Returns { dotRight, dotUp } where the dominant component tells
     * whether the drag is along the row (dotRight) or column (dotUp).
     */
    _computeFaceDots(dragX, dragY) {
        const face = this._hitSticker.face;
        const def = FACE_DEFS[face];
        if (!def) return { dotRight: 0, dotUp: 0 };

        const size = this.cubeModel.size;
        const half = size * this.cubeModel.cellSize / 2;

        const normal = new THREE.Vector3();
        if (def.axis === 'x') normal.set(def.sign, 0, 0);
        else if (def.axis === 'y') normal.set(0, def.sign, 0);
        else normal.set(0, 0, def.sign);
        const faceCenter = normal.clone().multiplyScalar(half);

        const rightEnd = faceCenter.clone().add(new THREE.Vector3(...def.right));
        const upEnd    = faceCenter.clone().add(new THREE.Vector3(...def.up));

        const cNDC = faceCenter.clone().project(this.camera);
        const rNDC = rightEnd.clone().project(this.camera);
        const uNDC = upEnd.clone().project(this.camera);

        const screenRight = new THREE.Vector2(
            rNDC.x - cNDC.x, -(rNDC.y - cNDC.y),
        ).normalize();
        const screenUp = new THREE.Vector2(
            uNDC.x - cNDC.x, -(uNDC.y - cNDC.y),
        ).normalize();

        const dragVec = new THREE.Vector2(dragX, dragY);
        return {
            dotRight: dragVec.dot(screenRight),
            dotUp:    dragVec.dot(screenUp),
        };
    }

    // ── Turn computation ──

    _executeTurn(dragX, dragY) {
        const { dotRight, dotUp } = this._computeFaceDots(dragX, dragY);

        const size = this.cubeModel.size;
        const { si, sx, sy } = this._computeSubIndices(
            this._hitSticker.row, this._hitSticker.col, size,
        );

        this._send({
            type: 'mouse_face_turn',
            face: this._hitSticker.face,
            row: this._hitSticker.row,
            col: this._hitSticker.col,
            si, sx, sy,
            on_left_to_right: dotRight,
            on_left_to_top: dotUp,
        });
    }

    /**
     * Compute edge slice index (si) and center sub-indices (sx, sy)
     * from grid position for NxN cubes.
     */
    _computeSubIndices(row, col, size) {
        const last = size - 1;
        const isCorner = (row === 0 || row === last) && (col === 0 || col === last);
        const isEdgeRow = (row === 0 || row === last) && col > 0 && col < last;
        const isEdgeCol = (col === 0 || col === last) && row > 0 && row < last;

        let si = -1, sx = -1, sy = -1;
        if (isEdgeRow) {
            si = col - 1;
        } else if (isEdgeCol) {
            si = row - 1;
        } else if (!isCorner) {
            // Center piece
            sx = col - 1;
            sy = row - 1;
        }
        return { si, sx, sy };
    }
}
