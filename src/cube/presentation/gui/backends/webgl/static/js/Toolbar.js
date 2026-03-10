/**
 * Toolbar — DOM toolbar buttons, keyboard bindings, overlays, status bar.
 */

export class Toolbar {
    constructor(appState, sendFn, controls, animQueue, soundManager) {
        this._state = appState;
        this._send = sendFn;
        this._controls = controls;
        this._animQueue = animQueue;
        this._sound = soundManager || null;
        this._animOverlay = document.getElementById('anim-overlay');
        this._statusOverlay = document.getElementById('status-overlay');
        this._statusEl = document.getElementById('status');
        this._errorBanner = this._createErrorBanner();
        this._assistDelayMs = 400;  // default, overridden by server config
        this._cubeModel = null;  // set by main.js for shadow toggle
    }

    bind() {
        this._bindToolbar();
        this._bindMoveButtons();
        this._bindKeyboard();
    }

    /** Update all toolbar UI from the unified AppState snapshot. */
    updateFromState(appState) {
        const a = appState.allowedActions || {};

        // Stop button: controlled by server state machine
        const stopBtn = document.getElementById('btn-stop');
        if (stopBtn) stopBtn.disabled = !a.stop;

        // Disable action buttons that aren't allowed in current state
        for (const btn of document.querySelectorAll('[data-cmd]')) {
            const cmd = btn.dataset.cmd;
            if (cmd === 'stop' || cmd === 'toggle_animation') continue;
            if (a[cmd] !== undefined) btn.disabled = !a[cmd];
        }

        // Paint button + size/solver selects: disable during solving/playing
        const canModify = !!a.scramble;  // proxy: scramble is allowed only in IDLE/READY
        const btnPaint = document.getElementById('btn-paint');
        if (btnPaint) btnPaint.disabled = !canModify;
        document.getElementById('size-select').disabled = !a.size_change;
        document.getElementById('solver-select').disabled = !canModify;
        document.getElementById('scramble-seed').disabled = !canModify;

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

        // Scramble seed dropdown + button label
        const ds = appState.defaultScramble || '0';
        document.getElementById('scramble-seed').value = ds;
        const scrambleBtn = document.querySelector('[data-cmd="scramble"]');
        if (scrambleBtn) scrambleBtn.textContent = `Scramble ${ds}`;

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

        // Error banner — separate element above status bar
        if (this._errorBanner) {
            if (appState.errorText) {
                this._errorBanner.textContent = '\u26A0 ' + appState.errorText;
                this._errorBanner.style.display = 'block';
            } else {
                this._errorBanner.style.display = 'none';
            }
        }
    }

    _updateToolbarFromState(appState) {
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

        // Sound toggle — sync from server config on initial load
        const btnSound = document.getElementById('btn-sound');
        if (btnSound && this._sound && this._soundLocalOverride === undefined) {
            this._sound.enabled = appState.soundEnabled;
            btnSound.textContent = appState.soundEnabled ? '🔊' : '🔇';
            btnSound.className = 'tb-btn ' + (appState.soundEnabled ? 'tb-on' : 'tb-off');
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
        // Preserve the status dot if present
        const dot = this._statusEl.querySelector('.status-dot');
        this._statusEl.textContent = '';
        if (dot) this._statusEl.appendChild(dot);
        this._statusEl.appendChild(document.createTextNode('Connected'));
        if (this._state.version) {
            const vSpan = document.createElement('span');
            vSpan.className = 'status-version';
            vSpan.textContent = ` v${this._state.version}`;
            this._statusEl.appendChild(vSpan);
        }
        if (this._state.clientCount > 0) {
            this._statusEl.appendChild(document.createTextNode(` #${this._state.clientCount}`));
        }
        this._statusEl.className = 'connected';
    }

    _createErrorBanner() {
        const banner = document.createElement('div');
        banner.id = 'error-banner';
        banner.style.cssText = 'display:none;position:fixed;left:0;right:0;bottom:60px;z-index:9999;' +
            'background:#cc0000;color:#fff;font-weight:bold;font-size:14px;' +
            'padding:6px 16px;text-align:center;box-shadow:0 -2px 8px rgba(0,0,0,0.5)';
        document.body.appendChild(banner);
        return banner;
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

        // Sound toggle (client-side only — no server message)
        const btnSound = document.getElementById('btn-sound');
        if (btnSound && this._sound) {
            btnSound.addEventListener('click', () => {
                this._soundLocalOverride = true;
                this._sound.enabled = !this._sound.enabled;
                btnSound.textContent = this._sound.enabled ? '🔊' : '🔇';
                btnSound.className = 'tb-btn ' + (this._sound.enabled ? 'tb-on' : 'tb-off');
            });
        }

        // Scramble seed dropdown
        document.getElementById('scramble-seed').addEventListener('change', (e) => {
            this._send({ type: 'set_scramble_seed', seed: e.target.value });
        });

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

    _bindMoveButtons() {
        // Shift state machine: 'off' | 'once' | 'locked'
        this._shiftState = 'off';
        const shiftBtn = document.getElementById('btn-shift');
        let longPressTimer = null;
        let wasLongPress = false;

        const moveButtons = document.querySelectorAll('.mv-btn[data-key]');
        const updateShiftUI = () => {
            if (!shiftBtn) return;
            shiftBtn.classList.toggle('mv-shift-once', this._shiftState === 'once');
            shiftBtn.classList.toggle('mv-shift-locked', this._shiftState === 'locked');
            const prime = this._shiftState !== 'off';
            moveButtons.forEach(btn => {
                btn.textContent = btn.dataset.key.toUpperCase() + (prime ? '\u2032' : '');
            });
        };

        if (shiftBtn) {
            // Pointer down — start long-press timer
            shiftBtn.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                wasLongPress = false;
                longPressTimer = setTimeout(() => {
                    wasLongPress = true;
                    this._shiftState = 'locked';
                    updateShiftUI();
                }, 500);
            });

            // Pointer up — short tap logic
            shiftBtn.addEventListener('pointerup', (e) => {
                e.preventDefault();
                clearTimeout(longPressTimer);
                if (wasLongPress) return;  // already handled by timer
                // Cycle: off → once → off, locked → off
                if (this._shiftState === 'off') {
                    this._shiftState = 'once';
                } else {
                    this._shiftState = 'off';
                }
                updateShiftUI();
            });

            // Cancel on pointer leave
            shiftBtn.addEventListener('pointerleave', () => {
                clearTimeout(longPressTimer);
            });
        }

        // Move buttons — send key with shift modifier
        document.querySelectorAll('.mv-btn[data-key]').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.dataset.key;
                const modifiers = (this._shiftState !== 'off') ? 1 : 0;
                this._send({ type: 'key', code: key.toUpperCase().charCodeAt(0), modifiers, key });
                // Consume shift-once
                if (this._shiftState === 'once') {
                    this._shiftState = 'off';
                    updateShiftUI();
                }
            });
        });
    }

    _bindKeyboard() {
        window.addEventListener('keydown', (e) => {
            // Don't capture when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

            // F10 — toggle all shadow faces (client-side only)
            if (e.key === 'F10' && this._cubeModel) {
                e.preventDefault();
                const anyOn = ['L', 'D', 'B'].some(f => this._cubeModel.shadowVisible[f]);
                for (const f of ['L', 'D', 'B']) {
                    if (anyOn && this._cubeModel.shadowVisible[f]) {
                        this._cubeModel.toggleShadow(f);
                    } else if (!anyOn && !this._cubeModel.shadowVisible[f]) {
                        this._cubeModel.toggleShadow(f);
                    }
                }
                return;
            }

            // Space → single redo (play next move)
            if (e.key === ' ' || e.code === 'Space') {
                e.preventDefault();
                this._send({ type: 'command', name: 'redo' });
                return;
            }

            // Backspace → undo
            if (e.key === 'Backspace') {
                e.preventDefault();
                this._send({ type: 'command', name: 'undo' });
                return;
            }

            // ArrowRight → redo, Shift+ArrowRight → play all
            if (e.key === 'ArrowRight') {
                e.preventDefault();
                if (e.shiftKey) {
                    this._send({ type: 'play_next_redo' });
                } else {
                    this._send({ type: 'command', name: 'redo' });
                }
                return;
            }

            // ArrowLeft → undo, Shift+ArrowLeft → undo all
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                if (e.shiftKey) {
                    this._send({ type: 'play_next_undo' });
                } else {
                    this._send({ type: 'command', name: 'undo' });
                }
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
