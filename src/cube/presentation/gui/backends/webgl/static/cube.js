/**
 * WebGL Cube Client — Smart 3D renderer
 *
 * Receives cube STATE from server, builds and owns the 3D model locally.
 * Renders at 60fps on the GPU with no per-frame server dependency.
 *
 * Visual target: cube-solver.com quality
 * - Rounded rectangle stickers
 * - Dark gaps between stickers
 * - MeshStandardMaterial with proper lighting
 * - Smooth orbit controls
 * - Client-side face rotation animation
 */

// ═══════════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════════

const BACKGROUND_COLOR = 0x2a2a2a;
const BODY_COLOR = 0x1a1a1a;
const STICKER_GAP = 0.10;        // fraction of cell size for gap
const CORNER_RADIUS = 0.10;      // fraction of cell size for rounded corners
const STICKER_DEPTH = 0.02;      // extrude depth relative to cell size

// PBR color palette — keyed by color name from server's color_map message.
// Overrides server RGB values that wash out under MeshStandardMaterial lighting.
// Only colors listed here are adjusted; unlisted colors use server values as-is.
const PBR_COLOR_OVERRIDES = {
    'orange': [255, 100, 0],   // server sends (255,165,0) which looks too yellow under PBR
};

// Face definitions: normal direction, right/up axes for sticker placement
const FACE_DEFS = {
    U: { axis: 'y', sign: +1, right: [1, 0, 0], up: [0, 0, -1] },
    D: { axis: 'y', sign: -1, right: [1, 0, 0], up: [0, 0,  1] },
    F: { axis: 'z', sign: +1, right: [1, 0, 0], up: [0, 1,  0] },
    B: { axis: 'z', sign: -1, right: [-1, 0, 0], up: [0, 1,  0] },
    R: { axis: 'x', sign: +1, right: [0, 0, -1], up: [0, 1,  0] },
    L: { axis: 'x', sign: -1, right: [0, 0,  1], up: [0, 1,  0] },
};

// ═══════════════════════════════════════════════════════════════════
//  GEOMETRY HELPERS
// ═══════════════════════════════════════════════════════════════════

/**
 * Create a rounded rectangle shape for sticker faces.
 */
function createRoundedRectShape(w, h, r) {
    const shape = new THREE.Shape();
    shape.moveTo(-w/2 + r, -h/2);
    shape.lineTo(w/2 - r, -h/2);
    shape.quadraticCurveTo(w/2, -h/2, w/2, -h/2 + r);
    shape.lineTo(w/2, h/2 - r);
    shape.quadraticCurveTo(w/2, h/2, w/2 - r, h/2);
    shape.lineTo(-w/2 + r, h/2);
    shape.quadraticCurveTo(-w/2, h/2, -w/2, h/2 - r);
    shape.lineTo(-w/2, -h/2 + r);
    shape.quadraticCurveTo(-w/2, -h/2, -w/2 + r, -h/2);
    return shape;
}

// ═══════════════════════════════════════════════════════════════════
//  CUBE MODEL
// ═══════════════════════════════════════════════════════════════════

class CubeModel {
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

        // No body mesh — sticker extrusion sides provide the dark gap appearance,
        // and removing the body avoids gray showing through during rotation animations.

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

// ═══════════════════════════════════════════════════════════════════
//  ANIMATION QUEUE
// ═══════════════════════════════════════════════════════════════════

class AnimationQueue {
    constructor(cubeModel) {
        this.cubeModel = cubeModel;
        this.queue = [];
        this.currentAnim = null;
        this.pendingState = null;  // State to apply after all animations
    }

    /**
     * Enqueue an animation event from the server.
     */
    enqueue(event, state) {
        this.queue.push({ event, state });
        if (!this.currentAnim) {
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
        this.queue = [];
        if (this.pendingState) {
            this.cubeModel.updateFromState(this.pendingState);
            this.pendingState = null;
        }
    }

    /**
     * Flush queue and apply latest state.
     */
    flush(state) {
        this.currentAnim = null;
        this.queue = [];
        if (state) {
            this.cubeModel.updateFromState(state);
        }
    }

    /**
     * Update animation progress (called each frame).
     * Returns true if an animation is active.
     */
    update() {
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
            return this.currentAnim !== null;
        }

        return true;
    }

    _processNext() {
        if (this.queue.length === 0) {
            this.currentAnim = null;
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
        this._updateDebugOverlay(event.alg || face, layers, affected.length);

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
        // x-axis: R CW = -π/2, L CW = +π/2
        // y-axis: U CW = +π/2, D CW = -π/2
        // z-axis: F CW = -π/2, B CW = +π/2
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
        // layers = 0-based column indices from the negative side of the axis.
        // E.g. on a 4x4: R→[3], L→[0], M[1]→[1], M→[1,2]
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
        // Column c has its center at: (c + 0.5) * cellSize - half
        const targetPositions = layers.map(col => (col + 0.5) * cellSize - half);
        const tol = cellSize * 0.45;  // generous but no overlap between layers

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

    _updateDebugOverlay(alg, layers, affectedCount) {
        const el = document.getElementById('debug-overlay');
        if (!el) return;
        el.innerHTML = `
            <span class="seg">
                <span class="seg-label">Alg</span>
                <span class="seg-value">${alg}</span>
            </span>
            <span class="seg">
                <span class="seg-label">Layers</span>
                <span class="seg-value">[${layers.join(',')}]</span>
            </span>
            <span class="seg">
                <span class="seg-label">Stickers</span>
                <span class="seg-value">${affectedCount}</span>
            </span>
        `;
    }
}

// ═══════════════════════════════════════════════════════════════════
//  ARROW GUIDE (visual drag-direction arrows on sticker touch)
// ═══════════════════════════════════════════════════════════════════

/**
 * Draws two sets of 3D arrows on the cube face when a sticker is touched:
 *   - Row arrows (orange): drag horizontally → rotate the row
 *   - Column arrows (cyan): drag vertically → rotate the column
 *
 * Arrows appear on touch, then the non-active set hides once drag
 * direction is detected.  All arrows are removed on pointer-up.
 */
class ArrowGuide {
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

// ═══════════════════════════════════════════════════════════════════
//  FACE TURN HANDLER (drag-to-turn on sticker)
// ═══════════════════════════════════════════════════════════════════

/**
 * Handles mouse/touch drag-to-turn and click-to-rotate on cube stickers.
 *
 * Drag workflow:
 *   1. On pointer-down, raycast to see if a sticker was hit.
 *   2. Accumulate drag until threshold (15 px).
 *   3. Project drag vector onto face right/up axes in screen space.
 *   4. Send {type:'mouse_face_turn', ...} to the server which computes the algorithm.
 */
class FaceTurnHandler {
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

// ═══════════════════════════════════════════════════════════════════
//  ORBIT CONTROLS (simple implementation)
// ═══════════════════════════════════════════════════════════════════

class OrbitControls {
    constructor(camera, domElement, faceTurnHandler, sendFn) {
        this.camera = camera;
        this.domElement = domElement;
        this._faceTurn = faceTurnHandler;
        this._sendFn = sendFn;

        // Default camera angles
        this._defaultPhi = Math.PI / 4;
        this._defaultTheta = Math.PI / 6;
        this._defaultRadius = 8;

        this.spherical = new THREE.Spherical(this._defaultRadius, this._defaultPhi, this._defaultTheta);
        this.target = new THREE.Vector3(0, 0, 0);
        this.panOffset = new THREE.Vector3(0, 0, 0);

        this.rotateSpeed = 0.005;
        this.panSpeed = 0.01;
        this.zoomSpeed = 0.1;
        this.minDistance = 3;
        this.maxDistance = 30;

        this._isDragging = false;
        this._isPanning = false;
        this._lastX = 0;
        this._lastY = 0;

        this._bindEvents();
        this.update();
    }

    /**
     * Reset camera to default position, keeping distance appropriate for cube size.
     */
    reset() {
        this.spherical.phi = this._defaultPhi;
        this.spherical.theta = this._defaultTheta;
        this.panOffset.set(0, 0, 0);
        this.update();
    }

    _bindEvents() {
        const el = this.domElement;
        const ft = this._faceTurn;

        // ── Mouse events ──

        el.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this._lastX = e.clientX;
            this._lastY = e.clientY;

            if (e.button === 0) {
                if (e.altKey || e.metaKey) {
                    // Alt/Meta + left-click → pan
                    this._isPanning = true;
                } else if (e.shiftKey || e.ctrlKey) {
                    // Shift/Ctrl + click → handled on mouseup (click-to-rotate)
                    ft.start(e.clientX, e.clientY);
                } else {
                    // Left-click: try face turn first, orbit if miss
                    if (!ft.start(e.clientX, e.clientY)) {
                        this._isDragging = true;
                    }
                }
            } else if (e.button === 2) {
                // Right-click → orbit
                this._isDragging = true;
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (ft.isActive) {
                ft.onDrag(e.clientX, e.clientY);
                return;
            }

            if (!this._isDragging && !this._isPanning) return;

            const dx = e.clientX - this._lastX;
            const dy = e.clientY - this._lastY;
            this._lastX = e.clientX;
            this._lastY = e.clientY;

            if (this._isDragging) {
                this.spherical.theta -= dx * this.rotateSpeed;
                this.spherical.phi -= dy * this.rotateSpeed;
                this.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, this.spherical.phi));
            } else if (this._isPanning) {
                const panX = -dx * this.panSpeed;
                const panY = dy * this.panSpeed;
                const offset = new THREE.Vector3();
                offset.setFromMatrixColumn(this.camera.matrix, 0).multiplyScalar(panX);
                this.panOffset.add(offset);
                offset.setFromMatrixColumn(this.camera.matrix, 1).multiplyScalar(panY);
                this.panOffset.add(offset);
            }

            this.update();
        });

        window.addEventListener('mouseup', (e) => {
            if (ft.isActive) {
                const clickHit = ft.end();
                // Click-to-rotate: Shift → CW, Ctrl → CCW
                if (clickHit && (e.shiftKey || e.ctrlKey)) {
                    const prime = e.ctrlKey;
                    const cmd = 'ROTATE_' + clickHit.face + (prime ? '_PRIME' : '');
                    this._sendFn({ type: 'command', name: cmd });
                }
            }
            this._isDragging = false;
            this._isPanning = false;
        });

        el.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 1 : -1;
            this.spherical.radius *= (1 + delta * this.zoomSpeed);
            this.spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this.spherical.radius));
            this.update();
        }, { passive: false });

        el.addEventListener('contextmenu', (e) => e.preventDefault());

        // ── Touch events (mobile: iPhone, Android, iPad) ──
        this._touchState = null;  // null | 'rotate' | 'pinch' | 'face_turn'
        this._lastPinchDist = 0;
        this._lastTouchCenter = { x: 0, y: 0 };

        el.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                const tx = e.touches[0].clientX;
                const ty = e.touches[0].clientY;
                // Try face turn first; fall back to orbit
                if (ft.start(tx, ty)) {
                    this._touchState = 'face_turn';
                } else {
                    this._touchState = 'rotate';
                }
                this._lastX = tx;
                this._lastY = ty;
            } else if (e.touches.length === 2) {
                // If a face turn was in progress, cancel it
                if (this._touchState === 'face_turn') ft.end();
                this._touchState = 'pinch';
                this._lastPinchDist = this._touchDist(e.touches);
                this._lastTouchCenter = this._touchCenter(e.touches);
            }
        }, { passive: false });

        el.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (this._touchState === 'face_turn' && e.touches.length === 1) {
                ft.onDrag(e.touches[0].clientX, e.touches[0].clientY);
            } else if (this._touchState === 'rotate' && e.touches.length === 1) {
                const dx = e.touches[0].clientX - this._lastX;
                const dy = e.touches[0].clientY - this._lastY;
                this._lastX = e.touches[0].clientX;
                this._lastY = e.touches[0].clientY;
                this.spherical.theta -= dx * this.rotateSpeed;
                this.spherical.phi -= dy * this.rotateSpeed;
                this.spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, this.spherical.phi));
                this.update();
            } else if (this._touchState === 'pinch' && e.touches.length === 2) {
                // Pinch zoom
                const dist = this._touchDist(e.touches);
                const scale = this._lastPinchDist / dist;
                this.spherical.radius *= scale;
                this.spherical.radius = Math.max(this.minDistance, Math.min(this.maxDistance, this.spherical.radius));
                this._lastPinchDist = dist;
                // Two-finger pan
                const center = this._touchCenter(e.touches);
                const dx = center.x - this._lastTouchCenter.x;
                const dy = center.y - this._lastTouchCenter.y;
                this._lastTouchCenter = center;
                const panX = -dx * this.panSpeed;
                const panY = dy * this.panSpeed;
                const offset = new THREE.Vector3();
                offset.setFromMatrixColumn(this.camera.matrix, 0).multiplyScalar(panX);
                this.panOffset.add(offset);
                offset.setFromMatrixColumn(this.camera.matrix, 1).multiplyScalar(panY);
                this.panOffset.add(offset);
                this.update();
            }
        }, { passive: false });

        el.addEventListener('touchend', () => {
            if (this._touchState === 'face_turn') ft.end();
            this._touchState = null;
        });
        el.addEventListener('touchcancel', () => {
            if (this._touchState === 'face_turn') ft.end();
            this._touchState = null;
        });
    }

    _touchDist(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    _touchCenter(touches) {
        return {
            x: (touches[0].clientX + touches[1].clientX) / 2,
            y: (touches[0].clientY + touches[1].clientY) / 2,
        };
    }

    update() {
        const pos = new THREE.Vector3().setFromSpherical(this.spherical);
        const target = this.target.clone().add(this.panOffset);
        this.camera.position.copy(pos.add(target));
        this.camera.lookAt(target);
    }

    /**
     * Adjust camera distance for different cube sizes.
     */
    setForCubeSize(size) {
        this.spherical.radius = size * 2.5;
        this.update();
    }
}

// ═══════════════════════════════════════════════════════════════════
//  MAIN CLIENT
// ═══════════════════════════════════════════════════════════════════

class CubeClient {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.statusEl = document.getElementById('status');
        this.animOverlay = document.getElementById('anim-overlay');
        this.statusOverlay = document.getElementById('status-overlay');

        // Three.js setup — responsive sizing
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: false,
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setClearColor(BACKGROUND_COLOR);
        this.renderer.outputEncoding = THREE.sRGBEncoding;

        this.scene = new THREE.Scene();

        // Camera
        this.camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);

        // Lighting
        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambient);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 8, 6);
        this.scene.add(dirLight);

        const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
        dirLight2.position.set(-3, -2, 4);
        this.scene.add(dirLight2);

        // Cube model
        this.cubeModel = new CubeModel(this.scene);

        // Animation queue
        this.animQueue = new AnimationQueue(this.cubeModel);

        // Face turn handler (drag-to-turn on sticker)
        this.faceTurnHandler = new FaceTurnHandler(
            this.cubeModel, this.camera, this.canvas, this.animQueue,
            (msg) => this._send(msg), this.scene,
        );

        // Orbit controls (with face turn integration)
        this.controls = new OrbitControls(
            this.camera, this.canvas, this.faceTurnHandler,
            (msg) => this._send(msg),
        );

        // Latest state (for applying after animation stop)
        this.latestState = null;

        // Version info
        this.version = '';
        this.clientCount = 0;

        // Responsive sizing
        this._resize();
        window.addEventListener('resize', () => this._resize());

        // Start render loop
        this._startRenderLoop();

        // Connect WebSocket
        this._connect();

        // Bind toolbar events
        this._bindToolbar();
        this._bindKeyboard();
    }

    _resize() {
        const wrapper = this.canvas.parentElement;
        const size = Math.min(wrapper.clientWidth, window.innerHeight - 120);
        this.renderer.setSize(size, size);
        this.camera.aspect = 1;
        this.camera.updateProjectionMatrix();
    }

    // ── WebSocket ──

    _connect() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/ws`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            this.statusEl.textContent = 'Connected';
            this.statusEl.className = 'connected';
            this.ws.send(JSON.stringify({ type: 'connected' }));
        };

        this.ws.onclose = () => {
            this.statusEl.textContent = 'Disconnected — refreshing...';
            this.statusEl.className = 'error';
            setTimeout(() => location.reload(), 2000);
        };

        this.ws.onerror = () => {
            this.statusEl.textContent = 'Connection error';
            this.statusEl.className = 'error';
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this._handleMessage(msg);
            } catch (e) {
                console.error('Parse error:', e);
            }
        };
    }

    _send(msg) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        }
    }

    _handleMessage(msg) {
        switch (msg.type) {
            case 'cube_state':
                this.latestState = msg;
                if (!this.animQueue.currentAnim && this.animQueue.queue.length === 0) {
                    this.cubeModel.updateFromState(msg);
                } else {
                    // Will be applied after animations complete
                    this.animQueue.pendingState = msg;
                }
                break;

            case 'animation_start':
                // Use embedded post-move state if available, fall back to latestState
                const animState = msg.state || this.latestState;
                if (animState) {
                    this.latestState = animState;
                    this.animQueue.enqueue(msg, animState);
                }
                break;

            case 'animation_stop':
                this.animQueue.stop();
                if (this.latestState) {
                    this.cubeModel.updateFromState(this.latestState);
                }
                break;

            case 'flush_queue':
                this.animQueue.flush(this.latestState);
                break;

            case 'text_update':
                this._updateTextOverlays(msg);
                break;

            case 'version':
                this.version = msg.version || '';
                this._updateStatusBar();
                break;

            case 'client_count':
                this.clientCount = msg.count || 0;
                this._updateStatusBar();
                break;

            case 'speed_update':
                document.getElementById('speed-slider').value = msg.value;
                document.getElementById('speed-value').textContent = msg.value;
                break;

            case 'size_update':
                document.getElementById('size-slider').value = msg.value;
                document.getElementById('size-value').textContent = msg.value;
                break;

            case 'color_map':
                this.cubeModel.buildColorCorrections(msg.colors);
                break;

            case 'toolbar_state':
                this._updateToolbar(msg);
                break;

            case 'session_id':
                // Could display session ID somewhere
                break;
        }
    }

    // ── Render loop ──

    _startRenderLoop() {
        const animate = () => {
            requestAnimationFrame(animate);

            // Update animations
            this.animQueue.update();

            // Render
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }

    // ── Text overlays ──

    _updateTextOverlays(msg) {
        // Animation text
        if (this.animOverlay) {
            let html = '';
            if (msg.animation) {
                for (const line of msg.animation) {
                    const style = `color:${line.color}; font-size:${line.size}px; font-weight:${line.bold ? 'bold' : 'normal'}`;
                    html += `<div class="anim-line" style="${style}">${this._esc(line.text)}</div>`;
                }
            }
            this.animOverlay.innerHTML = html;
        }

        // Status overlay
        if (this.statusOverlay) {
            let html = '';
            if (msg.solver) {
                html += `<span class="seg seg-solver"><span class="seg-label">Solver</span><span class="seg-value">${this._esc(msg.solver)}</span></span>`;
            }
            if (msg.status) {
                html += `<span class="seg seg-status"><span class="seg-label">Status</span><span class="seg-value">${this._esc(msg.status)}</span></span>`;
            }
            if (msg.moves !== undefined) {
                html += `<span class="seg seg-moves"><span class="seg-label">Moves</span><span class="seg-value">${msg.moves}</span></span>`;
            }
            this.statusOverlay.innerHTML = html;
        }
    }

    _updateStatusBar() {
        const parts = ['Connected'];
        if (this.version) parts[0] += ` v${this.version}`;
        if (this.clientCount > 0) parts[0] += ` #${this.clientCount}`;
        this.statusEl.textContent = parts[0];
        this.statusEl.className = 'connected';
    }

    _esc(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Toolbar ──

    _updateToolbar(msg) {
        // Debug toggle
        const btnDebug = document.getElementById('btn-debug');
        if (btnDebug) {
            btnDebug.textContent = msg.debug ? 'Dbg:ON' : 'Dbg:OFF';
            btnDebug.className = 'tb-btn ' + (msg.debug ? 'tb-on' : 'tb-off');
        }

        // Animation toggle
        const btnAnim = document.getElementById('btn-anim');
        if (btnAnim) {
            btnAnim.textContent = msg.animation ? 'Anim:ON' : 'Anim:OFF';
            btnAnim.className = 'tb-btn ' + (msg.animation ? 'tb-on' : 'tb-off');
        }

        // Solver list
        const sel = document.getElementById('solver-select');
        if (sel && msg.solver_list) {
            const currentVal = sel.value;
            sel.innerHTML = '';
            for (const name of msg.solver_list) {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = name;
                if (name === msg.solver_name) opt.selected = true;
                sel.appendChild(opt);
            }
        }

        // Slice selection display
        const sliceStart = msg.slice_start || 0;
        const sliceStop = msg.slice_stop || 0;
        this._updateSliceOverlay(sliceStart, sliceStop);
    }

    _updateSliceOverlay(start, stop) {
        const el = document.getElementById('debug-overlay');
        if (!el) return;
        if (start === 0 && stop === 0) {
            el.innerHTML = '';
            return;
        }
        el.innerHTML = `
            <span class="seg">
                <span class="seg-label">Slice</span>
                <span class="seg-value">[${start}:${stop}]</span>
            </span>
        `;
    }

    _bindToolbar() {
        // Command buttons
        document.querySelectorAll('[data-cmd]').forEach(btn => {
            btn.addEventListener('click', () => {
                this._send({ type: 'command', name: btn.dataset.cmd });
            });
        });

        // Solver dropdown
        document.getElementById('solver-select').addEventListener('change', (e) => {
            this._send({ type: 'set_solver', name: e.target.value });
        });

        // Speed slider
        document.getElementById('speed-slider').addEventListener('input', (e) => {
            document.getElementById('speed-value').textContent = e.target.value;
            this._send({ type: 'set_speed', value: parseInt(e.target.value) });
        });

        // Size slider
        document.getElementById('size-slider').addEventListener('input', (e) => {
            document.getElementById('size-value').textContent = e.target.value;
            this._send({ type: 'set_size', value: parseInt(e.target.value) });
        });
    }

    _bindKeyboard() {
        window.addEventListener('keydown', (e) => {
            // Don't capture when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

            // Camera reset: Alt+C (view reset) or Ctrl+C (cube + view reset)
            // Camera is client-side (OrbitControls), so handle here
            if (e.key.toLowerCase() === 'c' && (e.altKey || e.ctrlKey)) {
                this.controls.reset();
            }

            let modifiers = 0;
            if (e.shiftKey) modifiers |= 1;
            if (e.ctrlKey) modifiers |= 2;
            if (e.altKey) modifiers |= 4;

            this._send({
                type: 'key',
                code: e.keyCode,
                modifiers: modifiers,
                key: e.key,
            });

            // Allow browser shortcuts: F5 (refresh), F12 (dev tools), Ctrl+R (refresh),
            // Ctrl+Shift+I (dev tools), Ctrl+Shift+J (console)
            if (e.keyCode === 116 || e.keyCode === 123) return;  // F5, F12
            if (e.ctrlKey && (e.key === 'r' || e.key === 'R')) return;  // Ctrl+R
            if (e.ctrlKey && e.shiftKey && (e.key === 'i' || e.key === 'I' || e.key === 'j' || e.key === 'J')) return;
            e.preventDefault();
        });
    }
}

// ═══════════════════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════════════════

window.addEventListener('DOMContentLoaded', () => {
    window.cubeClient = new CubeClient();
});
