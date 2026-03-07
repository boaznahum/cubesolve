/**
 * Color Picker — paint mode for manually setting sticker colors.
 *
 * User selects a color from the 6-face palette and taps stickers
 * to paint them.  Orbit / zoom still work; face turns are disabled.
 *
 * Colors are tracked by COLOR NAME (e.g., "blue", "yellow"), not RGB.
 * The server's color_map provides the name→RGB mapping. This avoids
 * any PBR color correction mismatch between client and server.
 *
 * Apply button 3 states:
 *   - red:    sanity check failed (disabled)
 *   - orange: sanity check passed but not solve-verified (disabled)
 *   - green:  full solve check passed (enabled)
 */

import * as THREE from 'three';

export class ColorPicker {
    constructor(cubeModel, camera, canvas) {
        this.cubeModel = cubeModel;
        this.camera = camera;
        this.canvas = canvas;

        this.active = false;
        this.selectedColorIndex = 0;
        this.palette = [];            // [{faceName, colorName, rgb:[r,g,b]}]
        this._originalNames = {};     // {face: [colorName, ...]}  snapshot on enter
        this._paintedNames = {};      // {face: [colorName, ...]}  current edits
        this._colorMap = {};          // {colorName: [r,g,b]}  from server color_map

        // Apply button state: 'red' | 'orange' | 'green'
        this._applyState = 'red';

        // Callbacks — wired by main.js
        this.onEnter = null;      // () => void
        this.onExit  = null;      // () => void
        this.onApply = null;      // (faces) => void   — faces = {face: [colorName,...]}
        this.onQuickCheck = null; // (faces) => void
        this.onCheck = null;      // (faces) => void

        this._wireButtons();
        this._wireKeyboard();
    }

    /** Set the server color map (called from main.js on color_map message). */
    setColorMap(colorMap) {
        this._colorMap = colorMap;  // {colorName: [r,g,b]}
        // Build reverse lookup: "r,g,b" → colorName
        this._rgbToName = {};
        for (const [name, rgb] of Object.entries(colorMap)) {
            const key = `${rgb[0]},${rgb[1]},${rgb[2]}`;
            this._rgbToName[key] = name;
        }
    }

    /* ── Public API ──────────────────────────────────────── */

    enter() {
        if (this.active) return;
        this.active = true;

        this._buildPalette();
        this._renderPalette();
        this.selectedColorIndex = 0;
        this._highlightSelected();
        this._snapshotColors();
        this._setApplyState('red');

        document.getElementById('paint-toolbar').style.display = '';
        document.getElementById('toolbar').style.display = 'none';
        document.getElementById('history-panel').classList.add('hp-hidden');
        document.body.classList.add('paint-mode');

        if (this.onEnter) this.onEnter();
    }

    exit(cancelled = true) {
        if (!this.active) return;
        this.active = false;

        if (cancelled) this._restoreColors();

        document.getElementById('paint-toolbar').style.display = 'none';
        document.getElementById('toolbar').style.display = '';
        document.getElementById('history-panel').classList.remove('hp-hidden');
        document.body.classList.remove('paint-mode');

        if (this.onExit) this.onExit();
    }

    /** Called from OrbitControls when a sticker is tapped in paint mode. */
    handleStickerClick(hit) {
        if (!this.active) return;
        const { face, gridIndex } = hit;
        const color = this.palette[this.selectedColorIndex];
        if (!color) return;

        const meshes = this.cubeModel.stickers[face];
        if (!meshes || !meshes[gridIndex]) return;

        // Paint the Three.js material immediately (using PBR-corrected color for display)
        const displayRgb = this._toDisplayRgb(color.rgb);
        const mat = Array.isArray(meshes[gridIndex].material)
            ? meshes[gridIndex].material[0]
            : meshes[gridIndex].material;
        mat.color.setRGB(displayRgb[0] / 255, displayRgb[1] / 255, displayRgb[2] / 255);

        // Track the change by COLOR NAME
        if (!this._paintedNames[face]) {
            this._paintedNames[face] = [...this._originalNames[face]];
        }
        this._paintedNames[face][gridIndex] = color.colorName;

        // Reset to red until quick check passes, then send quick check
        this._setApplyState('red');
        if (this.onQuickCheck) this.onQuickCheck(this._getFullState());
    }

    /** Handle quick check result from server. */
    onQuickCheckResult(valid) {
        if (!this.active) return;
        this._setApplyState(valid ? 'orange' : 'red');
    }

    /** Handle full check result from server. */
    onFullCheckResult(valid, error) {
        if (!this.active) return;
        this._setApplyState(valid ? 'green' : 'red');
    }

    /* ── PBR color correction ────────────────────────────── */

    _toDisplayRgb(rgb) {
        const key = `${rgb[0]},${rgb[1]},${rgb[2]}`;
        if (this.cubeModel.colorCorrections[key]) {
            return this.cubeModel.colorCorrections[key];
        }
        return rgb;
    }

    /* ── Palette ─────────────────────────────────────────── */

    /**
     * Build palette from server state. Each face's center sticker gives
     * us both the color name (via reverse RGB→name lookup) and display RGB.
     */
    _buildPalette() {
        this.palette = [];
        const size = this.cubeModel.size;
        const mid = Math.floor(size / 2);
        const centerIdx = mid * size + mid;

        // Need serverState to read original server RGB
        if (!this.serverState) return;

        for (const faceName of ['U', 'D', 'F', 'B', 'R', 'L']) {
            const faceState = this.serverState.faces[faceName];
            if (!faceState || !faceState.colors || !faceState.colors[centerIdx]) continue;

            const serverRgb = faceState.colors[centerIdx];
            const key = `${serverRgb[0]},${serverRgb[1]},${serverRgb[2]}`;
            const colorName = this._rgbToName[key] || 'unknown';

            this.palette.push({
                faceName,
                colorName,          // e.g., "blue", "yellow"
                rgb: [...serverRgb], // original server RGB (for display + PBR lookup)
            });
        }
    }

    _renderPalette() {
        const el = document.getElementById('paint-palette');
        el.innerHTML = '';

        this.palette.forEach((color, idx) => {
            const btn = document.createElement('button');
            btn.className = 'pt-swatch';
            btn.dataset.index = idx;
            const display = this._toDisplayRgb(color.rgb);
            btn.style.backgroundColor = `rgb(${display[0]},${display[1]},${display[2]})`;
            btn.title = `${color.faceName} — ${color.colorName} (${idx + 1})`;
            btn.addEventListener('click', () => {
                this.selectedColorIndex = idx;
                this._highlightSelected();
            });
            el.appendChild(btn);
        });
    }

    _highlightSelected() {
        document.querySelectorAll('.pt-swatch').forEach((s, i) => {
            s.classList.toggle('pt-selected', i === this.selectedColorIndex);
        });
    }

    /* ── Apply button 3-state ────────────────────────────── */

    _setApplyState(state) {
        this._applyState = state;
        const btn = document.getElementById('pt-apply');
        if (!btn) return;

        btn.classList.remove('pt-apply-red', 'pt-apply-orange', 'pt-apply-green');
        btn.classList.add(`pt-apply-${state}`);
        btn.disabled = state !== 'green';
    }

    /* ── Snapshot / Restore ───────────────────────────────── */

    /**
     * Snapshot current sticker color NAMES from server state.
     */
    _snapshotColors() {
        this._originalNames = {};
        this._paintedNames = {};

        if (!this.serverState) return;

        for (const faceName of Object.keys(this.cubeModel.stickers)) {
            const faceState = this.serverState.faces[faceName];
            if (!faceState || !faceState.colors) continue;

            // Convert each server RGB → color name
            this._originalNames[faceName] = faceState.colors.map(rgb => {
                const key = `${rgb[0]},${rgb[1]},${rgb[2]}`;
                return this._rgbToName[key] || 'unknown';
            });
        }
    }

    /**
     * Restore original colors to Three.js materials.
     */
    _restoreColors() {
        if (!this.serverState) return;
        for (const [face, names] of Object.entries(this._originalNames)) {
            const meshes = this.cubeModel.stickers[face];
            if (!meshes) continue;
            for (let i = 0; i < meshes.length && i < names.length; i++) {
                const serverRgb = this._colorMap[names[i]];
                if (!serverRgb) continue;
                const display = this._toDisplayRgb(serverRgb);
                const mat = Array.isArray(meshes[i].material) ? meshes[i].material[0] : meshes[i].material;
                mat.color.setRGB(display[0] / 255, display[1] / 255, display[2] / 255);
            }
        }
    }

    /**
     * Merge original + painted into a full {face: [colorName,...]} map.
     * This is what gets sent to the server — color names, not RGB.
     */
    _getFullState() {
        const result = {};
        for (const face of Object.keys(this._originalNames)) {
            result[face] = this._paintedNames[face]
                ? [...this._paintedNames[face]]
                : [...this._originalNames[face]];
        }
        return result;
    }

    /* ── DOM wiring ──────────────────────────────────────── */

    _wireButtons() {
        document.getElementById('pt-cancel')?.addEventListener('click', () => this.exit(true));

        document.getElementById('pt-check')?.addEventListener('click', () => {
            if (this.onCheck) this.onCheck(this._getFullState());
        });

        document.getElementById('pt-apply')?.addEventListener('click', () => {
            if (this._applyState !== 'green') return;
            if (this.onApply) this.onApply(this._getFullState());
            this.exit(false);
        });
    }

    _wireKeyboard() {
        window.addEventListener('keydown', (e) => {
            if (!this.active) return;
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

            // 1–6 → select palette color
            const num = parseInt(e.key);
            if (num >= 1 && num <= 6 && num <= this.palette.length) {
                e.preventDefault();
                this.selectedColorIndex = num - 1;
                this._highlightSelected();
                return;
            }

            // Escape → cancel
            if (e.key === 'Escape') {
                e.preventDefault();
                this.exit(true);
            }
        });
    }
}
