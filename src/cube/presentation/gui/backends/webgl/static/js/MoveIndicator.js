/**
 * Visual move indicators — per-sticker chevrons flush ON sticker faces.
 *
 * Places a semi-transparent chevron on every sticker that will move
 * during the next rotation, pointing in the direction of travel.
 * Chevrons sit directly on the sticker surface (not floating above)
 * using polygonOffset to prevent z-fighting.
 *
 * Works for face moves, slice moves, multi-layer, and non-contiguous layers.
 */

import * as THREE from 'three';
import { FACE_DEFS } from './constants.js';

// Rotation axis and angle sign (matching AnimationQueue._getRotationAxis)
function getAxisAndSign(face) {
    const map = {
        R: { axis: [1, 0, 0], sign: -1 },
        L: { axis: [1, 0, 0], sign: +1 },
        U: { axis: [0, 1, 0], sign: -1 },
        D: { axis: [0, 1, 0], sign: +1 },
        F: { axis: [0, 0, 1], sign: -1 },
        B: { axis: [0, 0, 1], sign: +1 },
        M: { axis: [1, 0, 0], sign: +1 },
        E: { axis: [0, 1, 0], sign: +1 },
        S: { axis: [0, 0, 1], sign: -1 },
    };
    return map[face] || null;
}

const FACE_TO_AXIS_COMPONENT = {
    R: 'x', L: 'x', M: 'x',
    U: 'y', D: 'y', E: 'y',
    F: 'z', B: 'z', S: 'z',
};

/**
 * Create a clean arrow/chevron shape pointing along +X.
 * Smaller, sleeker design that looks engraved on the sticker.
 */
function createChevronShape(size) {
    const s = size * 0.42;
    const w = s * 0.32;   // stroke width
    const shape = new THREE.Shape();
    // Outer chevron
    shape.moveTo(-s * 0.5, s * 0.8);
    shape.lineTo(s * 0.5, 0);
    shape.lineTo(-s * 0.5, -s * 0.8);
    // Inner cutout (makes it an outline)
    shape.lineTo(-s * 0.5 + w, -s * 0.8 + w * 0.85);
    shape.lineTo(s * 0.5 - w * 1.1, 0);
    shape.lineTo(-s * 0.5 + w, s * 0.8 - w * 0.85);
    shape.closePath();
    return shape;
}

export class MoveIndicator {
    constructor(cubeModel, scene) {
        this.cubeModel = cubeModel;
        this.scene = scene;
        this.group = new THREE.Group();
        this.scene.add(this.group);

        this._phase = 0;
        this._materials = [];
        this._highlightedStickers = [];  // stickers whose color we dimmed
        this._visible = false;
        this._currentMoveKey = null;
    }

    show(moveData, opts) {
        if (!moveData) {
            this.hide();
            return;
        }

        const isUndo = opts?.isUndo || false;
        const key = `${moveData.face}|${moveData.direction}|${JSON.stringify(moveData.layers)}|${isUndo}`;
        if (this._visible && this._currentMoveKey === key) {
            return;
        }

        this.hide();
        this._currentMoveKey = key;

        const { face, layers, direction } = moveData;

        const info = getAxisAndSign(face);
        if (!info) return;

        const axisComp = FACE_TO_AXIS_COMPONENT[face];
        if (!axisComp) return;

        // Direction sign
        let sign = info.sign;
        if (direction === -1) sign = -sign;
        const axisVec = new THREE.Vector3(...info.axis);

        const size = this.cubeModel.size;
        const cellSize = this.cubeModel.cellSize;
        const half = size * cellSize / 2;
        const tol = cellSize * 0.45;
        const stickerDepth = cellSize * 0.45;

        // Target positions along the rotation axis
        const targets = layers.map(col => (col + 0.5) * cellSize - half);

        // Flat chevron geometry — sits ON the sticker face
        const chevronSize = cellSize;
        const shape = createChevronShape(chevronSize);
        const geo = new THREE.ShapeGeometry(shape);

        // Semi-transparent overlay with polygon offset to avoid z-fight
        const color = isUndo ? 0x200000 : 0x000000;
        const mat = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.92,
            depthTest: true,
            side: THREE.DoubleSide,
            polygonOffset: true,
            polygonOffsetFactor: -1,
            polygonOffsetUnits: -4,
        });
        this._materials.push(mat);

        // For face moves, skip the face's own stickers
        const skipFace = ['R', 'L', 'U', 'D', 'F', 'B'].includes(face) ? face : null;

        // Place chevrons flush on sticker faces
        for (const [faceName, meshes] of Object.entries(this.cubeModel.stickers)) {
            if (skipFace && faceName === skipFace) continue;
            const def = FACE_DEFS[faceName];
            if (!def) continue;

            const faceNormal = new THREE.Vector3();
            if (def.axis === 'x') faceNormal.set(def.sign, 0, 0);
            else if (def.axis === 'y') faceNormal.set(0, def.sign, 0);
            else faceNormal.set(0, 0, def.sign);

            // Place at the sticker cap surface (flush, not floating)
            const surfaceOffset = half + 0.005 + 0.001;

            for (const stickerMesh of meshes) {
                const pos = stickerMesh.position;
                const v = pos[axisComp];

                // Check if in affected layer
                let affected = false;
                for (const target of targets) {
                    if (Math.abs(v - target) < tol) {
                        affected = true;
                        break;
                    }
                }
                if (!affected) continue;

                // Dim the sticker to create a highlight band effect
                const stickerMat = Array.isArray(stickerMesh.material)
                    ? stickerMesh.material[0] : stickerMesh.material;
                if (stickerMat && stickerMat.color) {
                    // Save original color HSL
                    const hsl = {};
                    stickerMat.color.getHSL(hsl);
                    this._highlightedStickers.push({
                        mesh: stickerMesh,
                        origH: hsl.h, origS: hsl.s, origL: hsl.l,
                    });
                    // Slightly darken + desaturate to show "selected" state
                    stickerMat.color.setHSL(hsl.h, hsl.s * 0.7, hsl.l * 0.75);
                }

                // Compute tangent direction at sticker position
                const tangent = new THREE.Vector3().crossVectors(axisVec, pos).normalize();
                tangent.multiplyScalar(sign);
                if (tangent.length() < 0.01) continue;

                // Position chevron on the face surface
                const row = stickerMesh.userData.row;
                const col = stickerMesh.userData.col;
                const right = new THREE.Vector3(...def.right);
                const up = new THREE.Vector3(...def.up);

                const cx = (col + 0.5) * cellSize - half;
                const cy = (row + 0.5) * cellSize - half;
                const chevronPos = new THREE.Vector3();
                chevronPos.addScaledVector(right, cx);
                chevronPos.addScaledVector(up, cy);
                chevronPos.addScaledVector(faceNormal, surfaceOffset);

                // Project tangent onto face plane
                const projTangent = tangent.clone();
                projTangent.addScaledVector(faceNormal, -projTangent.dot(faceNormal));
                if (projTangent.length() < 0.01) continue;
                projTangent.normalize();

                // Orient: local X = projTangent, local Z = normal
                const tan2 = new THREE.Vector3().crossVectors(faceNormal, projTangent).normalize();
                const orient = new THREE.Matrix4().makeBasis(projTangent, tan2, faceNormal);
                const quat = new THREE.Quaternion().setFromRotationMatrix(orient);

                const mesh = new THREE.Mesh(geo, mat);
                mesh.renderOrder = 999;
                mesh.position.copy(chevronPos);
                mesh.quaternion.copy(quat);
                this.group.add(mesh);
            }
        }

        this._visible = true;
        this._phase = 0;
    }

    hide() {
        // Restore dimmed sticker colors
        for (const entry of this._highlightedStickers) {
            const stickerMat = Array.isArray(entry.mesh.material)
                ? entry.mesh.material[0] : entry.mesh.material;
            if (stickerMat && stickerMat.color) {
                stickerMat.color.setHSL(entry.origH, entry.origS, entry.origL);
            }
        }
        this._highlightedStickers = [];

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
        this._materials = [];
        this._visible = false;
        this._currentMoveKey = null;
    }

    updatePulse(dt) {
        if (!this._visible) return;
        this._phase += dt * 2.5;
        // Subtle pulse on the chevron opacity
        const opacity = 0.45 + 0.15 * (0.5 + 0.5 * Math.sin(this._phase));
        for (const mat of this._materials) {
            mat.opacity = opacity;
        }
    }

    get isVisible() { return this._visible; }

    dispose() {
        this.hide();
        this.scene.remove(this.group);
    }
}
