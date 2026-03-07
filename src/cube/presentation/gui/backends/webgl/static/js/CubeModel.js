/**
 * 3D cube model — builds and owns Three.js geometry for an NxN Rubik's cube.
 */

import * as THREE from 'three';
import {
    BODY_COLOR, STICKER_GAP, CORNER_RADIUS,
    PBR_COLOR_OVERRIDES, FACE_DEFS, createRoundedRectShape,
    SHADOW_OFFSETS, SHADOW_OPACITY,
} from './constants.js';
import { createMarkerGroup } from './MarkerRenderer.js';

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
        this.markerGroups = {};  // {faceName: [THREE.Group|null per sticker]}

        // Shadow faces: duplicate L/D/B at offset positions
        this.shadowGroup = new THREE.Group();
        this.scene.add(this.shadowGroup);
        this.shadowStickers = {};  // {faceName: [meshes]}
        this.shadowVisible = {};   // {faceName: bool}

        this.build(3);
    }

    /**
     * Build or rebuild the cube geometry for a given size.
     */
    build(size) {
        // Clear existing (including markers)
        this.clearAllMarkers();
        while (this.cubeGroup.children.length > 0) {
            const child = this.cubeGroup.children[0];
            this.cubeGroup.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
        }
        this.stickers = {};
        this.faceGroups = {};
        this.markerGroups = {};

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
            this.markerGroups[faceName] = [];

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
                    this.markerGroups[faceName].push(null);
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
            mat.color.setRGB(r / 255, g / 255, b / 255);
        }
        // Keep shadow face in sync
        this._updateShadowColors(faceName, colors);
    }

    /**
     * Update markers for one face from server state.
     * markers: flat array of (null | Array<markerDesc>) in row-major order
     */
    updateFaceMarkers(faceName, markers) {
        const meshes = this.stickers[faceName];
        if (!meshes || !markers) return;

        for (let i = 0; i < meshes.length && i < markers.length; i++) {
            const existing = this.markerGroups[faceName][i];
            const newData = markers[i];

            if (!newData) {
                // No markers — remove existing if present
                if (existing) {
                    this._disposeMarkerGroup(existing);
                    meshes[i].remove(existing);
                    this.markerGroups[faceName][i] = null;
                }
                continue;
            }

            // Remove old marker group before creating new one
            if (existing) {
                this._disposeMarkerGroup(existing);
                meshes[i].remove(existing);
            }

            // Create new marker group and add as child of sticker mesh
            const group = createMarkerGroup(newData, this.cellSize);
            meshes[i].add(group);
            this.markerGroups[faceName][i] = group;
        }
    }

    /**
     * Update all faces from a cube state.
     * Handles both old format (face → [colors]) and new format (face → {colors, markers}).
     */
    updateFromState(state) {
        if (state.size !== this.size) {
            this.build(state.size);
            this._rebuildShadows();
        }
        for (const [faceName, faceData] of Object.entries(state.faces)) {
            if (Array.isArray(faceData)) {
                // Old format: face data is just a flat color array
                this.updateFaceColors(faceName, faceData);
            } else {
                // New format: {colors: [...], markers: [...]}
                this.updateFaceColors(faceName, faceData.colors);
                if (faceData.markers) {
                    this.updateFaceMarkers(faceName, faceData.markers);
                }
            }
        }
    }

    /**
     * Remove and dispose all marker meshes from all faces.
     */
    clearAllMarkers() {
        for (const faceName of Object.keys(this.markerGroups)) {
            const groups = this.markerGroups[faceName];
            const meshes = this.stickers[faceName];
            if (!groups || !meshes) continue;

            for (let i = 0; i < groups.length; i++) {
                if (groups[i]) {
                    this._disposeMarkerGroup(groups[i]);
                    meshes[i].remove(groups[i]);
                    groups[i] = null;
                }
            }
        }
    }

    /**
     * Recursively dispose geometry and materials in a marker group.
     */
    _disposeMarkerGroup(group) {
        group.traverse((child) => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (child.material.map) child.material.map.dispose();
                child.material.dispose();
            }
        });
    }

    // ── Shadow faces ──

    /**
     * Toggle shadow face visibility for a given face (L, D, or B).
     */
    toggleShadow(faceName) {
        if (!SHADOW_OFFSETS[faceName]) return;
        this.shadowVisible[faceName] = !this.shadowVisible[faceName];
        if (this.shadowVisible[faceName]) {
            this._buildShadowFace(faceName);
        } else {
            this._removeShadowFace(faceName);
        }
    }

    /**
     * Build shadow stickers for one face at its offset position.
     */
    _buildShadowFace(faceName) {
        this._removeShadowFace(faceName);

        const def = FACE_DEFS[faceName];
        if (!def) return;
        const offset = SHADOW_OFFSETS[faceName];
        const size = this.size;
        const totalSize = 3.0;
        const half = totalSize / 2;
        const gap = STICKER_GAP * this.cellSize;
        const stickerSize = this.cellSize - gap;
        const cornerR = CORNER_RADIUS * this.cellSize;
        const stickerDepth = this.cellSize * 0.45;

        const stickerShape = createRoundedRectShape(stickerSize, stickerSize, cornerR);
        const stickerGeo = new THREE.ExtrudeGeometry(stickerShape, {
            depth: stickerDepth,
            bevelEnabled: false,
        });

        const sideMat = new THREE.MeshStandardMaterial({
            color: BODY_COLOR,
            roughness: 0.8,
            metalness: 0.1,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: SHADOW_OPACITY,
        });

        const right = new THREE.Vector3(...def.right);
        const up = new THREE.Vector3(...def.up);
        // Flip normal so shadow face faces the viewer
        const normal = new THREE.Vector3();
        if (def.axis === 'x') normal.set(-def.sign, 0, 0);
        else if (def.axis === 'y') normal.set(0, -def.sign, 0);
        else normal.set(0, 0, -def.sign);

        const meshes = [];
        const offsetVec = new THREE.Vector3(...offset);
        const STICKER_LIFT = 0.005;

        for (let row = 0; row < size; row++) {
            for (let col = 0; col < size; col++) {
                const faceMat = new THREE.MeshStandardMaterial({
                    color: 0x888888,
                    roughness: 0.3,
                    metalness: 0.05,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: SHADOW_OPACITY,
                });
                const mesh = new THREE.Mesh(stickerGeo, [faceMat, sideMat]);

                const cx = (col + 0.5) * this.cellSize - half;
                const cy = (row + 0.5) * this.cellSize - half;

                const pos = new THREE.Vector3();
                pos.addScaledVector(right, cx);
                pos.addScaledVector(up, cy);
                pos.addScaledVector(normal, -(half + STICKER_LIFT - stickerDepth));
                pos.add(offsetVec);
                mesh.position.copy(pos);

                // Orient: flip so face cap points outward (toward viewer)
                const mat4 = new THREE.Matrix4();
                mat4.makeBasis(right, up, normal);
                mesh.quaternion.setFromRotationMatrix(mat4);

                mesh.userData = { face: faceName, row, col, gridIndex: row * size + col };
                this.shadowGroup.add(mesh);
                meshes.push(mesh);
            }
        }

        this.shadowStickers[faceName] = meshes;

        // Apply current colors if available
        const realMeshes = this.stickers[faceName];
        if (realMeshes) {
            for (let i = 0; i < meshes.length && i < realMeshes.length; i++) {
                const srcMat = Array.isArray(realMeshes[i].material)
                    ? realMeshes[i].material[0] : realMeshes[i].material;
                const dstMat = Array.isArray(meshes[i].material)
                    ? meshes[i].material[0] : meshes[i].material;
                dstMat.color.copy(srcMat.color);
            }
        }
    }

    /**
     * Remove shadow stickers for one face.
     */
    _removeShadowFace(faceName) {
        const meshes = this.shadowStickers[faceName];
        if (!meshes) return;
        for (const mesh of meshes) {
            this.shadowGroup.remove(mesh);
            if (mesh.geometry) mesh.geometry.dispose();
            if (Array.isArray(mesh.material)) {
                mesh.material.forEach(m => m.dispose());
            } else if (mesh.material) {
                mesh.material.dispose();
            }
        }
        delete this.shadowStickers[faceName];
    }

    /**
     * Update shadow sticker colors to match real face.
     */
    _updateShadowColors(faceName, colors) {
        const meshes = this.shadowStickers[faceName];
        if (!meshes) return;
        for (let i = 0; i < meshes.length && i < colors.length; i++) {
            let [r, g, b] = colors[i];
            const key = `${r},${g},${b}`;
            if (this.colorCorrections[key]) [r, g, b] = this.colorCorrections[key];
            const mat = Array.isArray(meshes[i].material) ? meshes[i].material[0] : meshes[i].material;
            mat.color.setRGB(r / 255, g / 255, b / 255);
        }
    }

    /**
     * Rebuild all active shadow faces (after cube size change).
     */
    _rebuildShadows() {
        for (const faceName of Object.keys(SHADOW_OFFSETS)) {
            if (this.shadowVisible[faceName]) {
                this._buildShadowFace(faceName);
            }
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
