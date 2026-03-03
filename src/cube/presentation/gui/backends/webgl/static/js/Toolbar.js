/**
 * Toolbar — DOM toolbar buttons, keyboard bindings, overlays, status bar.
 */

export class Toolbar {
    constructor(appState, sendFn, controls, animQueue) {
        this._state = appState;
        this._send = sendFn;
        this._controls = controls;
        this._animQueue = animQueue;
        this._animOverlay = document.getElementById('anim-overlay');
        this._statusOverlay = document.getElementById('status-overlay');
        this._statusEl = document.getElementById('status');
        this._assistDelayMs = 400;  // default, overridden by server config
    }

    bind() {
        this._bindToolbar();
        this._bindKeyboard();
    }

    /** Update all toolbar UI from the unified AppState snapshot. */
    updateFromState(appState) {
        // Stop button: controlled by server state machine
        const stopBtn = document.getElementById('btn-stop');
        if (stopBtn) {
            const a = appState.allowedActions || {};
            stopBtn.disabled = !a.stop;
        }

        // Text overlays
        this._updateTextOverlaysFromState(appState);

        // Status bar
        this._state.version = appState.version;
        this._state.clientCount = appState.clientCount;
        this._updateStatusBar();

        // Speed dropdown
        this._buildSpeedDropdown(appState.speedStep, appState.speedD0, appState.speedDn);
        document.getElementById('speed-select').value = appState.speedIndex;

        // Size dropdown
        document.getElementById('size-select').value = appState.cubeSize;

        // Toolbar toggles + solver list
        this._updateToolbarFromState(appState);
    }

    _updateTextOverlaysFromState(appState) {
        // Animation text
        if (this._animOverlay) {
            let html = '';
            for (const line of appState.animationText) {
                const style = `color:${line.color}; font-size:${line.size}px; font-weight:${line.bold ? 'bold' : 'normal'}`;
                html += `<div class="anim-line" style="${style}">${this._esc(line.text)}</div>`;
            }
            this._animOverlay.innerHTML = html;
        }

        // Status overlay
        if (this._statusOverlay) {
            let html = '';
            if (appState.solverText) {
                html += `<span class="seg seg-solver"><span class="seg-label">Solver</span><span class="seg-value">${this._esc(appState.solverText)}</span></span>`;
            }
            if (appState.statusText) {
                html += `<span class="seg seg-status"><span class="seg-label">Status</span><span class="seg-value">${this._esc(appState.statusText)}</span></span>`;
            }
            if (appState.moveCount !== undefined) {
                html += `<span class="seg seg-moves"><span class="seg-label">Moves</span><span class="seg-value">${appState.moveCount}</span></span>`;
            }
            this._statusOverlay.innerHTML = html;
        }
    }

    _updateToolbarFromState(appState) {
        // Debug toggle
        const btnDebug = document.getElementById('btn-debug');
        if (btnDebug) {
            btnDebug.textContent = appState.debug ? 'Dbg:ON' : 'Dbg:OFF';
            btnDebug.className = 'tb-btn ' + (appState.debug ? 'tb-on' : 'tb-off');
        }

        // Animation toggle
        const btnAnim = document.getElementById('btn-anim');
        if (btnAnim) {
            btnAnim.textContent = appState.animationEnabled ? 'Anim:ON' : 'Anim:OFF';
            btnAnim.className = 'tb-btn ' + (appState.animationEnabled ? 'tb-on' : 'tb-off');
        }

        // Solver list
        const sel = document.getElementById('solver-select');
        if (sel && appState.solverList.length > 0) {
            sel.innerHTML = '';
            for (const name of appState.solverList) {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = name;
                if (name === appState.solverName) opt.selected = true;
                sel.appendChild(opt);
            }
        }

        // Assist checkbox — only set from server if user hasn't locally overridden
        const chkAssist = document.getElementById('chk-assist');
        if (chkAssist && this._assistLocalOverride === undefined) {
            chkAssist.checked = appState.assistEnabled;
        }

        // Slice selection display
        this._updateSliceOverlay(appState.sliceStart, appState.sliceStop);
    }

    /** Update debug overlay (called from AnimationQueue via callback). */
    updateDebug(alg, layers, count) {
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
                <span class="seg-value">${count}</span>
            </span>
        `;
    }

    _buildSpeedDropdown(step, d0, dn) {
        const sel = document.getElementById('speed-select');
        const cur = sel.value;
        sel.innerHTML = '';
        // I goes from 0 to 7 in increments of step
        // D(I) = d0 * (dn/d0)^(I/7)
        const ratio = dn / d0;
        for (let v = 0; v <= 7; v = Math.round((v + step) * 1e6) / 1e6) {
            const opt = document.createElement('option');
            opt.value = v;
            const dur = d0 * Math.pow(ratio, v / 7.0);
            opt.textContent = `${v}`;
            sel.appendChild(opt);
        }
        if (cur) sel.value = cur;
    }

    _updateStatusBar() {
        const parts = ['Connected'];
        if (this._state.version) parts[0] += ` v${this._state.version}`;
        if (this._state.clientCount > 0) parts[0] += ` #${this._state.clientCount}`;
        this._statusEl.textContent = parts[0];
        this._statusEl.className = 'connected';
    }

    _esc(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
                const cmd = btn.dataset.cmd;

                if (cmd === 'fast_play') {
                    // Client-initiated playback: start forward mode, request first move
                    this._animQueue.startPlayback('forward');
                    this._send({ type: 'play_next_redo' });
                    return;
                }

                if (cmd === 'fast_rewind') {
                    // Client-initiated rewind: start backward mode, request first move
                    this._animQueue.startPlayback('backward');
                    this._send({ type: 'play_next_undo' });
                    return;
                }

                if (cmd === 'solve_and_play') {
                    // Server FSM handles SOLVE_AND_PLAY → SOLVING → PLAYING transition
                    document.body.style.cursor = 'progress';
                    this._send({ type: 'command', name: 'solve_and_play' });
                    return;
                }

                if (cmd === 'stop') {
                    // Graceful stop: let current animation finish, stop requesting more
                    this._animQueue.stopPlayback();
                    this._animQueue.requestStop();
                    this._send({ type: 'command', name: 'stop' });
                    return;
                }

                // Show wait cursor for long operations
                if (cmd === 'scramble' || cmd === 'solve') {
                    document.body.style.cursor = 'progress';
                }
                this._send({ type: 'command', name: cmd });
            });
        });

        // View reset button (client-side only — resets OrbitControls camera)
        const btnViewReset = document.getElementById('btn-view-reset');
        if (btnViewReset) {
            btnViewReset.addEventListener('click', () => {
                this._controls.reset();
            });
        }

        // Assist checkbox (controls AnimationQueue preview delay)
        const chkAssist = document.getElementById('chk-assist');
        if (chkAssist) {
            chkAssist.addEventListener('change', () => {
                this._assistLocalOverride = chkAssist.checked;
                this._animQueue.assistDelayMs = chkAssist.checked ? (this._assistDelayMs || 400) : 0;
                chkAssist.blur();  // Release focus so keyboard handler works
            });
        }

        // Solver dropdown
        document.getElementById('solver-select').addEventListener('change', (e) => {
            this._send({ type: 'set_solver', name: e.target.value });
        });

        // Speed dropdown — built dynamically from server config
        this._buildSpeedDropdown(0.5, 500, 50);
        document.getElementById('speed-select').addEventListener('change', (e) => {
            this._send({ type: 'set_speed', value: parseFloat(e.target.value) });
        });

        // Size dropdown — populate options 3..20
        const sizeSelect = document.getElementById('size-select');
        for (let n = 2; n <= 20; n++) {
            const opt = document.createElement('option');
            opt.value = n;
            opt.textContent = `${n}×${n}`;
            sizeSelect.appendChild(opt);
        }
        sizeSelect.addEventListener('change', (e) => {
            this._send({ type: 'set_size', value: parseInt(e.target.value) });
        });
    }

    _bindKeyboard() {
        window.addEventListener('keydown', (e) => {
            // Don't capture when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

            // Space → single redo (play next move)
            if (e.key === ' ' || e.code === 'Space') {
                e.preventDefault();
                this._send({ type: 'command', name: 'redo' });
                return;
            }

            // Camera reset: Alt+C (view reset) or Ctrl+C (cube + view reset)
            // Camera is client-side (OrbitControls), so handle here
            if (e.key.toLowerCase() === 'c' && (e.altKey || e.ctrlKey)) {
                this._controls.reset();
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
