/**
 * Cube Solver Web Client — Three.js 3D renderer
 *
 * Connects to Python WebSocket server, receives per-frame rendering commands,
 * and draws a 3D Rubik's cube using Three.js WebGL.
 */

class CubeClient {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.status = document.getElementById('status');
        this.speedSlider = document.getElementById('speed-slider');
        this.speedValue = document.getElementById('speed-value');
        this.sizeSlider = document.getElementById('size-slider');
        this.sizeValue = document.getElementById('size-value');
        this.solverSelect = document.getElementById('solver-select');
        this.animOverlay = document.getElementById('anim-overlay');
        this.statusOverlay = document.getElementById('status-overlay');
        this.ws = null;
        this.connected = false;

        // Reconnect tracking
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;

        // Three.js core
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
        });
        this.renderer.setSize(this.canvas.width, this.canvas.height, false);
        this.renderer.setClearColor(0xd9d9d9);

        this.scene = new THREE.Scene();

        this.camera = new THREE.PerspectiveCamera(
            50,
            this.canvas.width / this.canvas.height,
            0.1,
            1000
        );
        // Camera stays at origin; the server pushes the cube back via translate(0,0,-400)

        // Lighting (persistent — not disposed each frame)
        this.ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        this.directionalLight.position.set(1, 1, 1);
        this.scene.add(this.ambientLight, this.directionalLight);

        // Sticker inset factor (gap between stickers, exposing dark body)
        this.insetFactor = 0.08;

        // Matrix stack (OpenGL-style modelview)
        this.matrixStack = [new THREE.Matrix4()];

        // Track disposables for cleanup each frame
        this.disposables = [];

        // Render loop: rAF-driven, decoupled from WebSocket arrival.
        // WebSocket messages deposit frames into a queue; the rAF loop
        // pulls one frame per vsync and renders it — guaranteeing the
        // browser composites each frame to screen.
        this.frameQueue = [];
        this._startRenderLoop();

        // Wire sliders, dropdown, and toolbar buttons
        this._setupSpeedSlider();
        this._setupSizeSlider();
        this._setupSolverSelect();
        this._setupToolbarButtons();

        this.connect();
    }

    // ── Matrix stack helpers ─────────────────────────────────────────

    currentMatrix() {
        return this.matrixStack[this.matrixStack.length - 1];
    }

    pushMatrix() {
        this.matrixStack.push(this.currentMatrix().clone());
    }

    popMatrix() {
        if (this.matrixStack.length > 1) {
            this.matrixStack.pop();
        }
    }

    loadIdentity() {
        this.currentMatrix().identity();
    }

    applyTranslate(x, y, z) {
        const m = new THREE.Matrix4().makeTranslation(x, y, z);
        this.currentMatrix().multiply(m);
    }

    applyRotate(angleDeg, ax, ay, az) {
        const rad = THREE.MathUtils.degToRad(angleDeg);
        const axis = new THREE.Vector3(ax, ay, az).normalize();
        const m = new THREE.Matrix4().makeRotationAxis(axis, rad);
        this.currentMatrix().multiply(m);
    }

    applyScale(x, y, z) {
        const m = new THREE.Matrix4().makeScale(x, y, z);
        this.currentMatrix().multiply(m);
    }

    applyMultiplyMatrix(rawMatrix) {
        // rawMatrix is a 4×4 row-major array from Python (numpy .tolist())
        // THREE.Matrix4.set() takes row-major arguments
        const e = rawMatrix;
        const m = new THREE.Matrix4().set(
            e[0][0], e[0][1], e[0][2], e[0][3],
            e[1][0], e[1][1], e[1][2], e[1][3],
            e[2][0], e[2][1], e[2][2], e[2][3],
            e[3][0], e[3][1], e[3][2], e[3][3]
        );
        this.currentMatrix().multiply(m);
    }

    // ── Color helpers ────────────────────────────────────────────────

    toColor(rgb) {
        return new THREE.Color(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255);
    }

    // ── Shape helpers ────────────────────────────────────────────────

    _insetVertices(vertices, factor) {
        // Shrink vertices toward centroid by factor (0 = no change, 1 = collapse to center)
        let cx = 0, cy = 0, cz = 0;
        for (const v of vertices) { cx += v[0]; cy += v[1]; cz += v[2]; }
        cx /= vertices.length; cy /= vertices.length; cz /= vertices.length;
        return vertices.map(v => [
            v[0] + (cx - v[0]) * factor,
            v[1] + (cy - v[1]) * factor,
            v[2] + (cz - v[2]) * factor,
        ]);
    }

    _addQuadMesh(vertices, color, matOptions) {
        // Build a 2-triangle mesh from 4 vertices
        const positions = new Float32Array(18); // 6 verts × 3 coords
        const idx = [0, 1, 2, 0, 2, 3];
        for (let i = 0; i < 6; i++) {
            const v = vertices[idx[i]];
            positions[i * 3]     = v[0];
            positions[i * 3 + 1] = v[1];
            positions[i * 3 + 2] = v[2];
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
            color: this.toColor(color),
            side: THREE.DoubleSide,
            roughness: 0.4,
            metalness: 0.05,
            ...matOptions,
        });

        const mesh = new THREE.Mesh(geo, mat);
        mesh.matrixAutoUpdate = false;
        mesh.matrix.copy(this.currentMatrix());
        this.scene.add(mesh);
        this.disposables.push(geo, mat);
    }

    // ── Shape builders ───────────────────────────────────────────────

    addQuad(vertices, color, borderColor) {
        // Dark body quad at original vertices (pushed back via polygon offset)
        this._addQuadMesh(vertices, [30, 30, 30], {
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1,
            roughness: 0.8,
            metalness: 0.0,
        });

        // Colored sticker at inset vertices (gaps expose dark body behind)
        const inset = this._insetVertices(vertices, this.insetFactor);
        this._addQuadMesh(inset, color, {});
    }

    addQuadBorder(vertices, faceColor, lineWidth, lineColor) {
        // Face fill with inset + dark body
        this.addQuad(vertices, faceColor);

        // Border lines at inset vertices
        const inset = this._insetVertices(vertices, this.insetFactor);
        const positions = new Float32Array(24);
        const order = [0, 1, 1, 2, 2, 3, 3, 0];
        for (let i = 0; i < 8; i++) {
            const v = inset[order[i]];
            positions[i * 3]     = v[0];
            positions[i * 3 + 1] = v[1];
            positions[i * 3 + 2] = v[2];
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const mat = new THREE.LineBasicMaterial({
            color: this.toColor(lineColor),
            linewidth: lineWidth,
        });

        const lines = new THREE.LineSegments(geo, mat);
        lines.matrixAutoUpdate = false;
        lines.matrix.copy(this.currentMatrix());
        this.scene.add(lines);
        this.disposables.push(geo, mat);
    }

    addTriangle(vertices, color) {
        const positions = new Float32Array(9);
        for (let i = 0; i < 3; i++) {
            positions[i * 3]     = vertices[i][0];
            positions[i * 3 + 1] = vertices[i][1];
            positions[i * 3 + 2] = vertices[i][2];
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
            color: this.toColor(color),
            side: THREE.DoubleSide,
            roughness: 0.4,
            metalness: 0.05,
        });

        const mesh = new THREE.Mesh(geo, mat);
        mesh.matrixAutoUpdate = false;
        mesh.matrix.copy(this.currentMatrix());
        this.scene.add(mesh);
        this.disposables.push(geo, mat);
    }

    addLine(p1, p2, width, color) {
        const positions = new Float32Array([
            p1[0], p1[1], p1[2],
            p2[0], p2[1], p2[2],
        ]);

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const mat = new THREE.LineBasicMaterial({
            color: this.toColor(color),
            linewidth: width,
        });

        const line = new THREE.Line(geo, mat);
        line.matrixAutoUpdate = false;
        line.matrix.copy(this.currentMatrix());
        this.scene.add(line);
        this.disposables.push(geo, mat);
    }

    // ── Frame lifecycle ──────────────────────────────────────────────

    disposeScene() {
        for (const d of this.disposables) {
            d.dispose();
        }
        this.disposables.length = 0;
        this.scene.clear();
        // Re-add persistent lights (scene.clear() removes everything)
        this.scene.add(this.ambientLight, this.directionalLight);
    }

    _startRenderLoop() {
        const loop = () => {
            if (this.frameQueue.length > 0) {
                const commands = this.frameQueue.shift();
                this.renderFrame(commands);
            }
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    renderFrame(commands) {
        // 1. Dispose previous frame
        this.disposeScene();

        // 2. Reset matrix stack
        this.matrixStack = [new THREE.Matrix4()];

        // 3. Execute all commands
        for (const cmd of commands) {
            this.executeCommand(cmd);
        }

        // 4. Render to canvas buffer
        this.renderer.render(this.scene, this.camera);
    }

    executeCommand(cmd) {
        switch (cmd.cmd) {
            // Matrix stack
            case 'push_matrix':
                this.pushMatrix();
                break;
            case 'pop_matrix':
                this.popMatrix();
                break;
            case 'load_identity':
                this.loadIdentity();
                break;
            case 'translate':
                this.applyTranslate(cmd.x, cmd.y, cmd.z);
                break;
            case 'rotate':
                this.applyRotate(cmd.angle, cmd.x, cmd.y, cmd.z);
                break;
            case 'scale':
                this.applyScale(cmd.x, cmd.y, cmd.z);
                break;
            case 'multiply_matrix':
                this.applyMultiplyMatrix(cmd.matrix);
                break;

            // View
            case 'clear': {
                const [r, g, b] = cmd.color;
                this.renderer.setClearColor(new THREE.Color(r / 255, g / 255, b / 255));
                break;
            }
            case 'projection':
                this.camera.fov = cmd.fov_y;
                this.camera.aspect = cmd.width / cmd.height;
                this.camera.near = cmd.near;
                this.camera.far = Math.max(cmd.far, 1000);
                this.camera.updateProjectionMatrix();
                break;

            // Shapes
            case 'quad':
                this.addQuad(cmd.vertices, cmd.color);
                break;
            case 'quad_border':
                this.addQuadBorder(cmd.vertices, cmd.face_color, cmd.line_width, cmd.line_color);
                break;
            case 'triangle':
                this.addTriangle(cmd.vertices, cmd.color);
                break;
            case 'line':
                this.addLine(cmd.p1, cmd.p2, cmd.width, cmd.color);
                break;

            // Silently ignore unimplemented commands
            default:
                break;
        }
    }

    // ── Text overlays ─────────────────────────────────────────────────

    updateTextOverlays(data) {
        // Animation text (top-left overlay on canvas)
        if (this.animOverlay) {
            if (data.animation && data.animation.length > 0) {
                this.animOverlay.innerHTML = data.animation.map(line => {
                    const weight = line.bold ? 'bold' : 'normal';
                    return `<div class="anim-line" style="font-size:${line.size}px;color:${line.color};font-weight:${weight}">${this._escapeHtml(line.text)}</div>`;
                }).join('');
            } else {
                this.animOverlay.innerHTML = '';
            }
        }

        // Status text (bottom-left overlay on canvas)
        if (this.statusOverlay) {
            const parts = [];
            if (data.solver) parts.push(data.solver);
            if (data.status) parts.push(data.status);
            this.statusOverlay.textContent = parts.join(' | ');
        }
    }

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Speed slider ──────────────────────────────────────────────────

    _setupSizeSlider() {
        if (!this.sizeSlider) return;

        this.sizeSlider.addEventListener('input', () => {
            const value = parseInt(this.sizeSlider.value, 10);
            this.sizeValue.textContent = value;
            this.send({ type: 'set_size', value: value });
        });
    }

    updateSizeSlider(value) {
        if (this.sizeSlider) {
            this.sizeSlider.value = value;
        }
        if (this.sizeValue) {
            this.sizeValue.textContent = value;
        }
    }

    _setupSolverSelect() {
        if (!this.solverSelect) return;

        this.solverSelect.addEventListener('change', () => {
            this.send({ type: 'set_solver', name: this.solverSelect.value });
        });
    }

    updateSolverSelect(solverName, solverList) {
        if (!this.solverSelect) return;

        // Rebuild options if solver list is provided and differs
        if (solverList && solverList.length > 0) {
            const currentOptions = Array.from(this.solverSelect.options).map(o => o.value);
            const listsMatch = currentOptions.length === solverList.length &&
                currentOptions.every((v, i) => v === solverList[i]);

            if (!listsMatch) {
                this.solverSelect.innerHTML = '';
                for (const name of solverList) {
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    this.solverSelect.appendChild(opt);
                }
            }
        }

        // Sync selected value
        if (solverName) {
            this.solverSelect.value = solverName;
        }
    }

    _setupSpeedSlider() {
        if (!this.speedSlider) return;

        this.speedSlider.addEventListener('input', () => {
            const value = parseInt(this.speedSlider.value, 10);
            this.speedValue.textContent = value;
            this.send({ type: 'set_speed', value: value });
        });
    }

    _setupToolbarButtons() {
        document.querySelectorAll('.tb-btn[data-cmd]').forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.getAttribute('data-cmd');
                this.send({ type: 'command', name: cmd });
            });
        });
    }

    updateToolbarState(data) {
        const btnDebug = document.getElementById('btn-debug');
        if (btnDebug) {
            btnDebug.textContent = data.debug ? 'Dbg:ON' : 'Dbg:OFF';
            btnDebug.className = 'tb-btn ' + (data.debug ? 'tb-on' : 'tb-off');
        }
        const btnAnim = document.getElementById('btn-anim');
        if (btnAnim) {
            btnAnim.textContent = data.animation ? 'Anim:ON' : 'Anim:OFF';
            btnAnim.className = 'tb-btn ' + (data.animation ? 'tb-on' : 'tb-off');
        }
        // Sync solver dropdown
        if (data.solver_name !== undefined) {
            this.updateSolverSelect(data.solver_name, data.solver_list);
        }
    }

    updateSpeedSlider(value) {
        if (this.speedSlider) {
            this.speedSlider.value = value;
        }
        if (this.speedValue) {
            this.speedValue.textContent = value;
        }
    }

    // ── WebSocket ────────────────────────────────────────────────────

    connect() {
        const wsUrl = `ws://${window.location.host}/ws`;
        this.setStatus('Connecting...', '');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this.setStatus('Connected', 'connected');

                this.send({ type: 'connected' });
                this.send({
                    type: 'resize',
                    width: this.canvas.width,
                    height: this.canvas.height,
                });
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.ws.onclose = () => {
                this.connected = false;
                this.reconnectAttempts++;

                if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    this.setStatus('Server stopped - close this tab', 'error');
                    return;
                }

                this.setStatus(
                    `Disconnected - Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`,
                    'error'
                );
                setTimeout(() => this.connect(), 2000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.reconnectAttempts++;

            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.setStatus('Server stopped - close this tab', 'error');
                return;
            }

            this.setStatus(
                `Failed to connect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
                'error'
            );
            setTimeout(() => this.connect(), 2000);
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);

            switch (message.type) {
                case 'frame':
                    this.frameQueue.push(message.commands);
                    break;
                case 'speed_update':
                    this.updateSpeedSlider(message.value);
                    break;
                case 'text_update':
                    this.updateTextOverlays(message);
                    break;
                case 'toolbar_state':
                    this.updateToolbarState(message);
                    break;
                case 'size_update':
                    this.updateSizeSlider(message.value);
                    break;
                default:
                    break;
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    setStatus(text, className) {
        this.status.textContent = text;
        this.status.className = className;
    }
}

// Keyboard event handling
document.addEventListener('keydown', (event) => {
    if (window.cubeClient && window.cubeClient.connected) {
        window.cubeClient.send({
            type: 'key',
            key: event.key,
            code: event.keyCode,
            modifiers:
                (event.shiftKey ? 1 : 0) |
                (event.ctrlKey ? 2 : 0) |
                (event.altKey ? 4 : 0),
        });
    }
});

// Initialize on page load
window.addEventListener('load', () => {
    window.cubeClient = new CubeClient();
});
