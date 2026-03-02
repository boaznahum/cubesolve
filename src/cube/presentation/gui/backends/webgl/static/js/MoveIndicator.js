/**
 * Visual move indicators — per-sticker chevrons on ALL affected stickers.
 *
 * Places a dark chevron on every sticker that will move during the next
 * rotation, pointing in the direction that sticker will travel.
 * Works for face moves, slice moves, multi-layer, and non-contiguous layers.
 *
 * Inspired by cube-solver.com's approach.
 */

import * as THREE from 'three';
import { FACE_DEFS } from './constants.js';

// Rotation axis and angle sign (matching AnimationQueue._getRotationAxis)
// For direction=1 (CW looking from outside), returns the actual rotation
// axis direction and whether the angle is negative (CW) or positive (CCW).
function getAxisAndSign(face) {
    // angle = -PI/2 for CW → sign = -1
    // angle = +PI/2 for CCW → sign = +1
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

// Map face/slice to axis component name
const FACE_TO_AXIS_COMPONENT = {
    R: 'x', L: 'x', M: 'x',
    U: 'y', D: 'y', E: 'y',
    F: 'z', B: 'z', S: 'z',
};

/**
 * Create a chevron ">" outline shape pointing along +X.
 */
function createChevronShape(size) {
    const s = size / 2;
    const t = s * 0.65;
    const shape = new THREE.Shape();
    shape.moveTo(-s * 0.6, s);
    shape.lineTo(s * 0.6, 0);
    shape.lineTo(-s * 0.6, -s);
    shape.lineTo(-s * 0.6 + t, -s + t * 0.75);
    shape.lineTo(s * 0.6 - t, 0);
    shape.lineTo(-s * 0.6 + t, s - t * 0.75);
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

        // Direction sign: info.sign is for direction=1
        let sign = info.sign;
        if (direction === -1) sign = -sign;
        // direction=2 (180): pick one direction
        const axisVec = new THREE.Vector3(...info.axis);

        const size = this.cubeModel.size;
        const cellSize = this.cubeModel.cellSize;
        const half = size * cellSize / 2;
        const tol = cellSize * 0.45;

        // Target positions along the rotation axis
        const targets = layers.map(col => (col + 0.5) * cellSize - half);

        // Chevron geometry + material (extruded for 3D depth/visibility)
        const chevronSize = cellSize * 0.85;
        const shape = createChevronShape(chevronSize);
        const extrudeDepth = cellSize * 0.06;
        const geo = new THREE.ExtrudeGeometry(shape, {
            depth: extrudeDepth,
            bevelEnabled: false,
        });

        const mat = new THREE.MeshBasicMaterial({
            color: isUndo ? 0xcc0000 : 0x000000,
            transparent: true,
            opacity: 0.92,
            depthTest: true,
            side: THREE.DoubleSide,
        });
        this._materials.push(mat);

        // For face moves (R,L,U,D,F,B), skip the face's own stickers —
        // only show on perpendicular faces' side edges (like cube-solver.com).
        const skipFace = ['R', 'L', 'U', 'D', 'F', 'B'].includes(face) ? face : null;

        // Find all affected stickers and place chevrons
        for (const [faceName, meshes] of Object.entries(this.cubeModel.stickers)) {
            if (skipFace && faceName === skipFace) continue;
            const def = FACE_DEFS[faceName];
            if (!def) continue;

            const faceNormal = new THREE.Vector3();
            if (def.axis === 'x') faceNormal.set(def.sign, 0, 0);
            else if (def.axis === 'y') faceNormal.set(0, def.sign, 0);
            else faceNormal.set(0, 0, def.sign);

            const lift = half + 0.005;

            for (const stickerMesh of meshes) {
                const pos = stickerMesh.position;
                const v = pos[axisComp];

                // Check if this sticker is in an affected layer
                let affected = false;
                for (const target of targets) {
                    if (Math.abs(v - target) < tol) {
                        affected = true;
                        break;
                    }
                }
                if (!affected) continue;

                // Compute rotation tangent at this sticker's position
                // velocity = sign * cross(axis, position)
                const tangent = new THREE.Vector3().crossVectors(axisVec, pos).normalize();
                tangent.multiplyScalar(sign);

                if (tangent.length() < 0.01) continue;

                // Position the chevron on the face surface at this sticker
                const row = stickerMesh.userData.row;
                const col = stickerMesh.userData.col;
                const right = new THREE.Vector3(...def.right);
                const up = new THREE.Vector3(...def.up);

                const cx = (col + 0.5) * cellSize - half;
                const cy = (row + 0.5) * cellSize - half;
                const chevronPos = new THREE.Vector3();
                chevronPos.addScaledVector(right, cx);
                chevronPos.addScaledVector(up, cy);
                chevronPos.addScaledVector(faceNormal, lift);

                // Project tangent onto the face plane (remove normal component)
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
        this._phase += dt * 2.0;
        const opacity = 0.75 + 0.17 * (0.5 + 0.5 * Math.sin(this._phase));
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
