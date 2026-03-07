/**
 * Color Picker — paint mode for manually setting sticker colors.
 *
 * User selects a color from the 6-face palette and taps stickers
 * to paint them.  Orbit / zoom still work; face turns are disabled.
 */

import * as THREE from 'three';

export class ColorPicker {
    constructor(cubeModel, camera, canvas) {
        this.cubeModel = cubeModel;
        this.camera = camera;
        this.canvas = canvas;

        this.active = false;
        this.selectedColorIndex = 0;
        this.palette = [];           // [{name, rgb:[r,g,b]}]
        this._originalColors = {};   // {face: [[r,g,b], ...]}  snapshot on enter
        this._paintedColors = {};    // {face: [[r,g,b], ...]}  current edits

        // Callbacks — wired by main.js
        this.onEnter = null;   // () => void
        this.onExit  = null;   // () => void
        this.onApply = null;   // (faces) => void
        this.onCheck = null;   // (faces) => void

        this._wireButtons();
        this._wireKeyboard();
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

        // Paint the Three.js material immediately
        const [r, g, b] = color.rgb;
        const mat = Array.isArray(meshes[gridIndex].material)
            ? meshes[gridIndex].material[0]
            : meshes[gridIndex].material;
        mat.color.setRGB(r / 255, g / 255, b / 255);

        // Track the change
        if (!this._paintedColors[face]) {
            this._paintedColors[face] = this._originalColors[face].map(c => [...c]);
        }
        this._paintedColors[face][gridIndex] = [r, g, b];
    }

    /* ── Palette ─────────────────────────────────────────── */

    _buildPalette() {
        this.palette = [];
        const size = this.cubeModel.size;
        const mid = Math.floor(size / 2);
        const centerIdx = mid * size + mid;

        for (const faceName of ['U', 'D', 'F', 'B', 'R', 'L']) {
            const meshes = this.cubeModel.stickers[faceName];
            if (!meshes || !meshes[centerIdx]) continue;

            const mat = Array.isArray(meshes[centerIdx].material)
                ? meshes[centerIdx].material[0]
                : meshes[centerIdx].material;
            const c = mat.color;
            this.palette.push({
                name: faceName,
                rgb: [Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255)],
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
            btn.style.backgroundColor = `rgb(${color.rgb[0]},${color.rgb[1]},${color.rgb[2]})`;
            btn.title = `${color.name}  (${idx + 1})`;
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

    /* ── Snapshot / Restore ───────────────────────────────── */

    _snapshotColors() {
        this._originalColors = {};
        this._paintedColors = {};

        for (const [face, meshes] of Object.entries(this.cubeModel.stickers)) {
            this._originalColors[face] = meshes.map(mesh => {
                const mat = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
                const c = mat.color;
                return [Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255)];
            });
        }
    }

    _restoreColors() {
        for (const [face, colors] of Object.entries(this._originalColors)) {
            const meshes = this.cubeModel.stickers[face];
            if (!meshes) continue;
            for (let i = 0; i < meshes.length && i < colors.length; i++) {
                const [r, g, b] = colors[i];
                const mat = Array.isArray(meshes[i].material) ? meshes[i].material[0] : meshes[i].material;
                mat.color.setRGB(r / 255, g / 255, b / 255);
            }
        }
    }

    /** Merge original + painted into a full {face: [[r,g,b],...]} map. */
    _getFullState() {
        const result = {};
        for (const face of Object.keys(this.cubeModel.stickers)) {
            result[face] = this._paintedColors[face]
                ? this._paintedColors[face].map(c => [...c])
                : this._originalColors[face].map(c => [...c]);
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
