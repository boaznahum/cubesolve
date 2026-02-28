/**
 * 3D cube model — builds and owns Three.js geometry for an NxN Rubik's cube.
 */

import * as THREE from 'three';
import {
    BODY_COLOR, STICKER_GAP, CORNER_RADIUS,
    PBR_COLOR_OVERRIDES, FACE_DEFS, createRoundedRectShape,
} from './constants.js';

export class CubeModel {
    constructor(scene) {
        this.scene = scene;
        this.cubeGroup = new THREE.Group();
        this.scene.add(this.cubeGroup);
        // Color corrections: "r,g,b" → [r,g,b] built from server color_map + PBR_COLOR_OVERRIDES
        this.colorCorrections = {};

        this.size = 3;
        this.cellSize = 1.0;
        this.stickers = {};  // {faceName: [meshes in row-major order]}
        this.faceGroups = {};

        this.build(3);
    }

    /**
     * Build or rebuild the cube geometry for a given size.
     */
    build(size) {
        // Clear existing
        while (this.cubeGroup.children.length > 0) {
            const child = this.cubeGroup.children[0];
            this.cubeGroup.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
        }
        this.stickers = {};
        this.faceGroups = {};

        this.size = size;
        // Keep total physical size constant regardless of N — cube fits the same view
        const TARGET_TOTAL_SIZE = 3.0;
        this.cellSize = TARGET_TOTAL_SIZE / size;
        const totalSize = TARGET_TOTAL_SIZE;
        const half = totalSize / 2;

        // Create stickers for each face — flat rounded rectangles
        const gap = STICKER_GAP * this.cellSize;
        const stickerSize = this.cellSize - gap;
        const cornerR = CORNER_RADIUS * this.cellSize;

        const stickerShape = createRoundedRectShape(stickerSize, stickerSize, cornerR);
        // Extrude stickers inward to create "cubie" depth that fills gaps during rotation
        const stickerDepth = this.cellSize * 0.45;
        const stickerGeo = new THREE.ExtrudeGeometry(stickerShape, {
            depth: stickerDepth,
            bevelEnabled: false,
        });

        // Dark material for sticker sides/back (looks like cubie plastic)
        const sideMat = new THREE.MeshStandardMaterial({
            color: BODY_COLOR,
            roughness: 0.8,
            metalness: 0.1,
            side: THREE.DoubleSide,
        });

        for (const [faceName, def] of Object.entries(FACE_DEFS)) {
            const faceGroup = new THREE.Group();
            this.cubeGroup.add(faceGroup);
            this.faceGroups[faceName] = faceGroup;
            this.stickers[faceName] = [];

            const right = new THREE.Vector3(...def.right);
            const up = new THREE.Vector3(...def.up);
            // Normal directly from axis + sign (cross product was buggy for negative faces)
            const normal = new THREE.Vector3();
            if (def.axis === 'x') normal.set(def.sign, 0, 0);
            else if (def.axis === 'y') normal.set(0, def.sign, 0);
            else normal.set(0, 0, def.sign);

            for (let row = 0; row < size; row++) {
                for (let col = 0; col < size; col++) {
                    const faceMat = new THREE.MeshStandardMaterial({
                        color: 0x888888,
                        roughness: 0.3,
                        metalness: 0.05,
                        side: THREE.DoubleSide,
                    });
                    // Material array: [caps (front/back), sides]
                    // ExtrudeGeometry group 0 = caps, group 1 = side walls
                    const mesh = new THREE.Mesh(stickerGeo, [faceMat, sideMat]);

                    // Position: face surface + offset for row/col
                    // Grid: row 0 is bottom (server convention), col 0 is left
                    const cx = (col + 0.5) * this.cellSize - half;
                    const cy = (row + 0.5) * this.cellSize - half;

                    // Place sticker so the extruded back face sits on the cube surface.
                    // ExtrudeGeometry goes from z=0 to z=depth along local Z (=normal).
                    // Offset inward by depth so the outer cap is at the surface.
                    const STICKER_LIFT = 0.005;
                    const pos = new THREE.Vector3();
                    pos.addScaledVector(right, cx);
                    pos.addScaledVector(up, cy);
                    pos.addScaledVector(normal, half + STICKER_LIFT - stickerDepth);
                    mesh.position.copy(pos);

                    // Orient sticker: face outward along normal
                    // Build basis matrix: columns = right, up, forward
                    const mat4 = new THREE.Matrix4();
                    mat4.makeBasis(right, up, normal);
                    mesh.quaternion.setFromRotationMatrix(mat4);

                    // Store metadata for raycasting/face turns
                    mesh.userData = {
                        face: faceName,
                        row: row,
                        col: col,
                        gridIndex: row * size + col,
                    };

                    faceGroup.add(mesh);
                    this.stickers[faceName].push(mesh);
                }
            }
        }
    }

    /**
     * Build color correction map from server's color_map message.
     * For each color name that has a PBR override, maps "r,g,b" → [r,g,b].
     */
    buildColorCorrections(colorMap) {
        this.colorCorrections = {};
        for (const [name, rgb] of Object.entries(colorMap)) {
            if (PBR_COLOR_OVERRIDES[name]) {
                const key = `${rgb[0]},${rgb[1]},${rgb[2]}`;
                this.colorCorrections[key] = PBR_COLOR_OVERRIDES[name];
            }
        }
    }

    /**
     * Update sticker colors from server state.
     * colors: flat array of [r,g,b] in row-major order (row 0 = bottom)
     */
    updateFaceColors(faceName, colors) {
        const meshes = this.stickers[faceName];
        if (!meshes) return;

        for (let i = 0; i < meshes.length && i < colors.length; i++) {
            let [r, g, b] = colors[i];
            // Apply PBR color corrections (built from server color_map)
            const key = `${r},${g},${b}`;
            if (this.colorCorrections[key]) [r, g, b] = this.colorCorrections[key];
            // Material is either a single material or [faceMat, sideMat] array
            const mat = Array.isArray(meshes[i].material) ? meshes[i].material[0] : meshes[i].material;
            mat.color.setRGB(r / 255, g / 255, b / 255, THREE.SRGBColorSpace);
        }
    }

    /**
     * Update all faces from a cube_state message.
     */
    updateFromState(state) {
        if (state.size !== this.size) {
            this.build(state.size);
        }
        for (const [faceName, colors] of Object.entries(state.faces)) {
            this.updateFaceColors(faceName, colors);
        }
    }

    /**
     * Reset all sticker positions/orientations to canonical locations.
     * Called after animation to undo reparenting drift.
     */
    resetPositions() {
        const size = this.size;
        const half = size * this.cellSize / 2;
        const STICKER_LIFT = 0.005;
        const stickerDepth = this.cellSize * 0.45;

        for (const [faceName, def] of Object.entries(FACE_DEFS)) {
            const right = new THREE.Vector3(...def.right);
            const up = new THREE.Vector3(...def.up);
            const normal = new THREE.Vector3();
            if (def.axis === 'x') normal.set(def.sign, 0, 0);
            else if (def.axis === 'y') normal.set(0, def.sign, 0);
            else normal.set(0, 0, def.sign);

            const meshes = this.stickers[faceName];
            if (!meshes) continue;

            // Ensure stickers are parented to their face group
            const faceGroup = this.faceGroups[faceName];

            for (const mesh of meshes) {
                const row = mesh.userData.row;
                const col = mesh.userData.col;

                const cx = (col + 0.5) * this.cellSize - half;
                const cy = (row + 0.5) * this.cellSize - half;

                const pos = new THREE.Vector3();
                pos.addScaledVector(right, cx);
                pos.addScaledVector(up, cy);
                pos.addScaledVector(normal, half + STICKER_LIFT - stickerDepth);
                mesh.position.copy(pos);

                const mat4 = new THREE.Matrix4();
                mat4.makeBasis(right, up, normal);
                mesh.quaternion.setFromRotationMatrix(mat4);

                // Re-parent to face group if needed
                if (mesh.parent !== faceGroup) {
                    faceGroup.attach(mesh);
                    mesh.position.copy(pos);
                    mesh.quaternion.setFromRotationMatrix(mat4);
                }
            }
        }
    }
}
