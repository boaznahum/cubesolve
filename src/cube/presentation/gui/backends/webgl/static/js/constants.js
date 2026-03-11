/**
 * Shared constants and geometry helpers for the WebGL cube client.
 */

import * as THREE from 'three';

export const BACKGROUND_COLOR = 0x2a2a2a;
export const BODY_COLOR = 0x1a1a1a;
export const STICKER_GAP = 0.10;        // fraction of cell size for gap
export const CORNER_RADIUS = 0.10;      // fraction of cell size for rounded corners
export const STICKER_DEPTH = 0.02;      // extrude depth relative to cell size

// PBR color palette — keyed by color name from server's color_map message.
// Overrides server RGB values that wash out under MeshStandardMaterial lighting.
// Only colors listed here are adjusted; unlisted colors use server values as-is.
export const PBR_COLOR_OVERRIDES = {
    'orange': [255, 100, 0],   // server sends (255,165,0) which looks too yellow under PBR
};

// Face definitions: normal direction, right/up axes for sticker placement
export const FACE_DEFS = {
    U: { axis: 'y', sign: +1, right: [1, 0, 0], up: [0, 0, -1] },
    D: { axis: 'y', sign: -1, right: [1, 0, 0], up: [0, 0,  1] },
    F: { axis: 'z', sign: +1, right: [1, 0, 0], up: [0, 1,  0] },
    B: { axis: 'z', sign: -1, right: [-1, 0, 0], up: [0, 1,  0] },
    R: { axis: 'x', sign: +1, right: [0, 0, -1], up: [0, 1,  0] },
    L: { axis: 'x', sign: -1, right: [0, 0,  1], up: [0, 1,  0] },
};

// Shadow face offsets — duplicate hidden faces (L, D, B) at offset positions
// so all 6 faces are visible without rotating the cube.
// Values are in cube units (total cube size = 3.0).
export const SHADOW_OFFSETS = {
    L: [-2.4, 0, 0],
    D: [0, -2.4, 0],
    B: [0, 0, -2.4],
};

// Shadow face opacity (slightly transparent to distinguish from real faces)
export const SHADOW_OPACITY = 0.88;

/**
 * Create a rounded rectangle shape for sticker faces.
 */
export function createRoundedRectShape(w, h, r) {
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
