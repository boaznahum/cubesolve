/**
 * Marker rendering — creates Three.js geometry for cube sticker markers.
 *
 * Each marker type (ring, filled_circle, cross, arrow, checkmark, etc.)
 * becomes a small Three.js Group that lives as a child of the sticker mesh.
 * Because markers are children of stickers, they automatically move during
 * face-turn animations (reparented via tempGroup.attach).
 *
 * All geometry is in sticker-local coordinates:
 *   - The sticker's local Z points along the face normal (from ExtrudeGeometry).
 *   - Markers are placed at small positive Z offsets above the sticker surface.
 */

import * as THREE from 'three';

// Base scale factor: markers use radius_factor as a fraction of half-cell-size
const BASE_SCALE = 0.4;

// Z offset above sticker surface (local coords) to avoid z-fighting.
// ExtrudeGeometry goes from z=0 (front cap, placed inward) to z=depth (back cap
// at cube surface). The VISIBLE outer cap is at z=depth = cellSize * 0.45.
// Markers must be placed just above that depth so they appear on top.
const STICKER_DEPTH_FACTOR = 0.45;  // must match CubeModel.js stickerDepth
const Z_LIFT = 0.02;   // offset above the outer sticker surface
const Z_STEP = 0.005;  // additional offset per z_order level

/**
 * Create a Three.js Group for a list of marker descriptors on one sticker.
 *
 * @param {Array<Object>} markers - Array of marker descriptor objects from server
 * @param {number} cellSize - Size of one cell in world units
 * @returns {THREE.Group} Group containing all marker meshes
 */
export function createMarkerGroup(markers, cellSize) {
    const group = new THREE.Group();
    const scale = cellSize * BASE_SCALE;
    // Sticker outer surface is at local z = stickerDepth
    const stickerDepth = cellSize * STICKER_DEPTH_FACTOR;
    const zBase = stickerDepth + Z_LIFT;

    for (const desc of markers) {
        const zOff = zBase + (desc.z_order || 0) * Z_STEP;
        const mesh = _createMarkerMesh(desc, scale, zOff);
        if (mesh) {
            group.add(mesh);
        }
    }

    return group;
}

/**
 * Create a material for markers — unlit, transparent, with polygon offset.
 */
function _markerMat(color, extraOffset = 0) {
    return new THREE.MeshBasicMaterial({
        color: new THREE.Color(color[0] / 255, color[1] / 255, color[2] / 255),
        side: THREE.DoubleSide,
        depthWrite: false,
        transparent: true,
        polygonOffset: true,
        polygonOffsetFactor: -1 - extraOffset,
        polygonOffsetUnits: -1,
    });
}

function _lineMat(color) {
    return new THREE.LineBasicMaterial({
        color: new THREE.Color(color[0] / 255, color[1] / 255, color[2] / 255),
        depthWrite: false,
        linewidth: 2,
    });
}

/**
 * Dispatch to the appropriate builder for each marker type.
 */
function _createMarkerMesh(desc, scale, zOff) {
    let mesh;
    switch (desc.type) {
        case 'filled_circle': mesh = _filledCircle(desc, scale, zOff); break;
        case 'ring':          mesh = _ring(desc, scale, zOff); break;
        case 'cross':         mesh = _cross(desc, scale, zOff); break;
        case 'bold_cross':    mesh = _boldCross(desc, scale, zOff); break;
        case 'checkmark':     mesh = _checkmark(desc, scale, zOff); break;
        case 'arrow':         mesh = _arrow(desc, scale, zOff); break;
        case 'character':     mesh = _character(desc, scale, zOff); break;
        case 'outlined_circle': mesh = _outlinedCircle(desc, scale, zOff); break;
        case 'bracket_corners': mesh = _bracketCorners(desc, scale, zOff); break;
        case 'crosshair':     mesh = _crosshair(desc, scale, zOff); break;
        default:              mesh = null;
    }
    // Tag marker meshes with animation metadata for the render loop
    if (mesh) {
        mesh.userData.markerType = desc.type;
        mesh.userData.moveable = desc.moveable !== false;
    }
    return mesh;
}

// ── Filled circle ──────────────────────────────────────────────────────

function _filledCircle(desc, scale, zOff) {
    const r = (desc.radius || 0.6) * scale;
    const geo = new THREE.CircleGeometry(r, 32);
    const mat = _markerMat(desc.color);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(0, 0, zOff);
    return mesh;
}

// ── Ring ────────────────────────────────────────────────────────────────

function _ring(desc, scale, zOff) {
    const inner = (desc.inner_radius || 0.5) * scale;
    const outer = (desc.outer_radius || 1.0) * scale;
    const geo = new THREE.RingGeometry(inner, outer, 32);
    const mat = _markerMat(desc.color);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(0, 0, zOff);
    return mesh;
}

// ── Cross (thin lines corner-to-corner) ────────────────────────────────

function _cross(desc, scale, zOff) {
    const s = scale * 1.0;  // extends to cell edges
    const points = [
        new THREE.Vector3(-s, -s, zOff),
        new THREE.Vector3( s,  s, zOff),
        new THREE.Vector3( s, -s, zOff),  // break
        new THREE.Vector3( s, -s, zOff),
        new THREE.Vector3(-s,  s, zOff),
    ];
    // Two separate line segments
    const geo1 = new THREE.BufferGeometry().setFromPoints([points[0], points[1]]);
    const geo2 = new THREE.BufferGeometry().setFromPoints([points[3], points[4]]);
    const mat = _lineMat(desc.color);
    const group = new THREE.Group();
    group.add(new THREE.Line(geo1, mat));
    group.add(new THREE.Line(geo2, mat));
    return group;
}

// ── Bold cross (thick rectangles forming an X) ─────────────────────────

function _boldCross(desc, scale, zOff) {
    const r = (desc.radius || 0.85) * scale;
    const t = (desc.thickness || 1.0) * scale * 0.12;  // thickness of each arm

    const group = new THREE.Group();
    const mat = _markerMat(desc.color);

    // Two rotated thin rectangles
    for (const angle of [Math.PI / 4, -Math.PI / 4]) {
        const geo = new THREE.PlaneGeometry(r * 2, t);
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = angle;
        mesh.position.set(0, 0, zOff);
        group.add(mesh);
    }
    return group;
}

// ── Checkmark (two line segments forming a tick/check) ──────────────────

function _checkmark(desc, scale, zOff) {
    const r = (desc.radius || 0.85) * scale;

    // Checkmark shape: short downstroke left, long upstroke right
    const points = [
        new THREE.Vector3(-r * 0.5,  0,      zOff),
        new THREE.Vector3(-r * 0.1, -r * 0.4, zOff),
        new THREE.Vector3( r * 0.6,  r * 0.5, zOff),
    ];

    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = _lineMat(desc.color);
    // Use Line (connected segments) for the checkmark
    const line = new THREE.Line(geo, mat);
    return line;
}

// ── Arrow (line shaft + triangle head) ──────────────────────────────────

function _arrow(desc, scale, zOff) {
    const r = (desc.radius || 0.8) * scale;
    const dir = (desc.direction || 0) * Math.PI / 180;  // degrees to radians

    const group = new THREE.Group();
    const mat = _lineMat(desc.color);
    const meshMat = _markerMat(desc.color);

    // Shaft: line from center toward direction
    const shaftLen = r * 0.8;
    const tipX = Math.cos(dir) * r;
    const tipY = Math.sin(dir) * r;
    const baseX = -Math.cos(dir) * shaftLen * 0.3;
    const baseY = -Math.sin(dir) * shaftLen * 0.3;

    const shaftGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(baseX, baseY, zOff),
        new THREE.Vector3(tipX, tipY, zOff),
    ]);
    group.add(new THREE.Line(shaftGeo, mat));

    // Arrowhead: triangle at tip
    const headSize = r * 0.3;
    const perpX = -Math.sin(dir) * headSize * 0.5;
    const perpY =  Math.cos(dir) * headSize * 0.5;
    const backX = tipX - Math.cos(dir) * headSize;
    const backY = tipY - Math.sin(dir) * headSize;

    const shape = new THREE.Shape();
    shape.moveTo(tipX, tipY);
    shape.lineTo(backX + perpX, backY + perpY);
    shape.lineTo(backX - perpX, backY - perpY);
    shape.closePath();
    const headGeo = new THREE.ShapeGeometry(shape);
    const headMesh = new THREE.Mesh(headGeo, meshMat);
    headMesh.position.z = zOff;
    group.add(headMesh);

    return group;
}

// ── Character (canvas texture on a plane) ───────────────────────────────

function _character(desc, scale, zOff) {
    const char = desc.char || '?';
    const r = (desc.radius || 0.8) * scale;

    // Render character to an offscreen canvas
    const size = 128;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    // Clear with transparent background
    ctx.clearRect(0, 0, size, size);

    // Draw character centered
    const c = desc.color || [0, 0, 0];
    ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
    ctx.font = `bold ${size * 0.7}px monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(char, size / 2, size / 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    const mat = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        polygonOffset: true,
        polygonOffsetFactor: -1,
        polygonOffsetUnits: -1,
    });

    const geo = new THREE.PlaneGeometry(r * 2, r * 2);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(0, 0, zOff);
    return mesh;
}

// ── Bracket corners (four L-shaped brackets framing the sticker) ─────

function _bracketCorners(desc, scale, zOff) {
    const r = (desc.radius || 0.85) * scale;
    const armLen = (desc.arm_length || 0.35) * scale;
    const armT = (desc.arm_thickness || 0.12) * scale;

    const group = new THREE.Group();
    const mat = _markerMat(desc.color);

    // Four corners: each is two PlaneGeometry arms forming an L
    const corners = [
        { x: -r, y: -r, dx: 1, dy: 1 },   // bottom-left
        { x:  r, y: -r, dx: -1, dy: 1 },   // bottom-right
        { x: -r, y:  r, dx: 1, dy: -1 },   // top-left
        { x:  r, y:  r, dx: -1, dy: -1 },   // top-right
    ];

    for (const c of corners) {
        // Horizontal arm
        const hGeo = new THREE.PlaneGeometry(armLen, armT);
        const hMesh = new THREE.Mesh(hGeo, mat);
        hMesh.position.set(c.x + c.dx * armLen / 2, c.y + c.dy * armT / 2, zOff);
        group.add(hMesh);

        // Vertical arm
        const vGeo = new THREE.PlaneGeometry(armT, armLen);
        const vMesh = new THREE.Mesh(vGeo, mat);
        vMesh.position.set(c.x + c.dx * armT / 2, c.y + c.dy * armLen / 2, zOff);
        group.add(vMesh);
    }

    return group;
}

// ── Crosshair / reticle (circle + 4 cross lines extending outward) ────

function _crosshair(desc, scale, zOff) {
    const r = (desc.radius || 0.55) * scale;
    const lineLen = (desc.line_length || 0.35) * scale;
    const lineT = (desc.line_thickness || 0.08) * scale;

    const group = new THREE.Group();
    const mat = _markerMat(desc.color);

    // Central circle (ring) — thin ring at radius r
    const ringThickness = lineT;
    const innerR = Math.max(r - ringThickness, r * 0.7);
    const ringGeo = new THREE.RingGeometry(innerR, r, 32);
    const ring = new THREE.Mesh(ringGeo, mat);
    ring.position.set(0, 0, zOff);
    group.add(ring);

    // Four cross lines extending outward from the circle edge
    // Each line starts at distance r from center and extends outward by lineLen
    const directions = [
        { x: 1, y: 0 },   // right
        { x: -1, y: 0 },  // left
        { x: 0, y: 1 },   // up
        { x: 0, y: -1 },  // down
    ];

    for (const dir of directions) {
        const geo = new THREE.PlaneGeometry(
            dir.x !== 0 ? lineLen : lineT,
            dir.y !== 0 ? lineLen : lineT
        );
        const mesh = new THREE.Mesh(geo, mat);
        // Position at midpoint of the line segment (from r to r+lineLen)
        const midDist = r + lineLen / 2;
        mesh.position.set(dir.x * midDist, dir.y * midDist, zOff);
        group.add(mesh);
    }

    return group;
}

// ── Outlined circle (ring + filled circle) ──────────────────────────────

function _outlinedCircle(desc, scale, zOff) {
    const r = (desc.radius || 0.4) * scale;
    const outlineW = (desc.outline_width || 0.15) * scale;
    const outerR = r + outlineW;

    const group = new THREE.Group();

    // Outline ring (underneath)
    const ringGeo = new THREE.RingGeometry(r, outerR, 32);
    const ringMat = _markerMat(desc.outline_color, 0);
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.position.set(0, 0, zOff);
    group.add(ring);

    // Filled circle (on top)
    const circGeo = new THREE.CircleGeometry(r, 32);
    const circMat = _markerMat(desc.fill_color, 1);
    const circ = new THREE.Mesh(circGeo, circMat);
    circ.position.set(0, 0, zOff + Z_STEP * 0.5);
    group.add(circ);

    return group;
}
