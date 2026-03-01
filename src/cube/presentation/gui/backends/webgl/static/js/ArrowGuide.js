/**
 * Visual drag-direction arrows on sticker touch.
 *
 * Draws two sets of 3D arrows on the cube face when a sticker is touched:
 *   - Row arrows (orange): drag horizontally → rotate the row
 *   - Column arrows (cyan): drag vertically → rotate the column
 *
 * Arrows appear on touch, then the non-active set hides once drag
 * direction is detected.  All arrows are removed on pointer-up.
 */

import * as THREE from 'three';
import { FACE_DEFS } from './constants.js';

export class ArrowGuide {
    constructor(cubeModel, scene) {
        this.cubeModel = cubeModel;
        this.group = new THREE.Group();
        // Add to scene (not cubeGroup) so arrows survive cube rebuilds
        scene.add(this.group);
        this._rowGroup = null;
        this._colGroup = null;
    }

    /**
     * Show arrow guides for the given sticker position on a face.
     */
    show(face, row, col) {
        this.hide();

        const def = FACE_DEFS[face];
        if (!def) return;

        const size = this.cubeModel.size;
        const cellSize = this.cubeModel.cellSize;
        const half = size * cellSize / 2;

        const right = new THREE.Vector3(...def.right);
        const up    = new THREE.Vector3(...def.up);
        const normal = new THREE.Vector3();
        if (def.axis === 'x') normal.set(def.sign, 0, 0);
        else if (def.axis === 'y') normal.set(0, def.sign, 0);
        else normal.set(0, 0, def.sign);

        const lift   = half + 0.08;   // slightly above face surface
        const margin = 0.15;          // inset from face edges

        const rowY = (row + 0.5) * cellSize - half;
        const colX = (col + 0.5) * cellSize - half;

        // ── Row arrow (horizontal, orange) ──
        const rowStart = new THREE.Vector3()
            .addScaledVector(right, -half + margin)
            .addScaledVector(up, rowY)
            .addScaledVector(normal, lift);
        const rowEnd = new THREE.Vector3()
            .addScaledVector(right, half - margin)
            .addScaledVector(up, rowY)
            .addScaledVector(normal, lift);
        this._rowGroup = this._createDoubleArrow(rowStart, rowEnd, 0xff8800);
        this.group.add(this._rowGroup);

        // ── Column arrow (vertical, cyan) ──
        const colStart = new THREE.Vector3()
            .addScaledVector(right, colX)
            .addScaledVector(up, -half + margin)
            .addScaledVector(normal, lift);
        const colEnd = new THREE.Vector3()
            .addScaledVector(right, colX)
            .addScaledVector(up, half - margin)
            .addScaledVector(normal, lift);
        this._colGroup = this._createDoubleArrow(colStart, colEnd, 0x00bbff);
        this.group.add(this._colGroup);
    }

    /**
     * Show only the active direction.
     * @param {'row'|'col'|null} direction  null → show both
     */
    setActiveDirection(direction) {
        if (this._rowGroup) this._rowGroup.visible = (direction === 'row' || direction === null);
        if (this._colGroup) this._colGroup.visible = (direction === 'col' || direction === null);
    }

    /** Remove all arrows and dispose geometry. */
    hide() {
        while (this.group.children.length > 0) {
            const child = this.group.children[0];
            this.group.remove(child);
            child.traverse(obj => {
                if (obj.geometry) obj.geometry.dispose();
                if (obj.material) {
                    if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
                    else obj.material.dispose();
                }
            });
        }
        this._rowGroup = null;
        this._colGroup = null;
    }

    get isVisible() { return this._rowGroup !== null; }

    /**
     * Build a double-ended arrow (shaft + arrowhead at each end).
     * Uses MeshBasicMaterial with depthTest:false so arrows render on top.
     */
    _createDoubleArrow(start, end, color) {
        const group = new THREE.Group();
        const dir = end.clone().sub(start).normalize();
        const len = start.distanceTo(end);

        const mat = new THREE.MeshBasicMaterial({
            color,
            transparent: true,
            opacity: 0.85,
            depthTest: false,
        });

        const headHeight = 0.20;
        const headRadius = 0.08;
        const shaftRadius = 0.025;

        // ── Shaft (cylinder between the two arrowheads) ──
        const shaftLen = Math.max(0.01, len - headHeight * 2);
        const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, shaftLen, 6);
        const shaft = new THREE.Mesh(shaftGeo, mat);
        shaft.renderOrder = 999;
        const mid = start.clone().add(end).multiplyScalar(0.5);
        shaft.position.copy(mid);
        shaft.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        group.add(shaft);

        // ── Arrowhead at "end" (pointing start→end) ──
        const headGeo = new THREE.ConeGeometry(headRadius, headHeight, 8);
        const head1 = new THREE.Mesh(headGeo, mat);
        head1.renderOrder = 999;
        head1.position.copy(end.clone().addScaledVector(dir, -headHeight / 2));
        head1.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        group.add(head1);

        // ── Arrowhead at "start" (pointing end→start) ──
        const head2 = new THREE.Mesh(headGeo, mat);
        head2.renderOrder = 999;
        head2.position.copy(start.clone().addScaledVector(dir, headHeight / 2));
        head2.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().negate());
        group.add(head2);

        return group;
    }
}
