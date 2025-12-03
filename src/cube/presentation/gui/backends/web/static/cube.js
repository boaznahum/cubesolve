/**
 * Cube Solver Web Client
 *
 * Connects to Python WebSocket server and renders commands on canvas.
 * Phase 1: Simple canvas with clear color support.
 */

class CubeClient {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.status = document.getElementById('status');
        this.ws = null;
        this.connected = false;

        // WebSocket port (Python server runs on 8765)
        this.wsPort = 8765;

        // Reconnect tracking
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;

        this.connect();
    }

    connect() {
        // Connect to /ws endpoint on same host
        const wsUrl = `ws://${window.location.host}/ws`;
        this.setStatus('Connecting...', '');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;  // Reset on successful connection
                this.setStatus('Connected', 'connected');

                // Send connected message
                this.send({ type: 'connected' });

                // Send initial resize
                this.send({
                    type: 'resize',
                    width: this.canvas.width,
                    height: this.canvas.height
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

                this.setStatus(`Disconnected - Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'error');
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

            this.setStatus(`Failed to connect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'error');
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
                    this.renderFrame(message.commands);
                    break;
                case 'clear':
                    this.clear(message.color);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    renderFrame(commands) {
        // Process each command in the frame
        for (const cmd of commands) {
            this.executeCommand(cmd);
        }
    }

    executeCommand(cmd) {
        switch (cmd.cmd) {
            case 'clear':
                this.clear(cmd.color);
                break;
            case 'quad':
                this.drawQuad(cmd.vertices, cmd.color);
                break;
            case 'quad_border':
                this.drawQuadWithBorder(cmd.vertices, cmd.face_color, cmd.line_width, cmd.line_color);
                break;
            case 'triangle':
                this.drawTriangle(cmd.vertices, cmd.color);
                break;
            case 'line':
                this.drawLine(cmd.p1, cmd.p2, cmd.width, cmd.color);
                break;
            case 'projection':
                // Store projection params for future use
                this.projection = cmd;
                break;
            case 'translate':
            case 'rotate':
            case 'scale':
            case 'push_matrix':
            case 'pop_matrix':
            case 'load_identity':
            case 'look_at':
                // Transform commands - will be implemented in Phase 3
                break;
            default:
                // Silently ignore unknown commands for now
                break;
        }
    }

    clear(color) {
        const [r, g, b, a] = color;
        this.ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a / 255})`;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    // Phase 2: Basic shape rendering (placeholder implementations)

    drawQuad(vertices, color) {
        // Simple 2D projection for testing
        const projected = vertices.map(v => this.project(v));

        this.ctx.beginPath();
        this.ctx.moveTo(projected[0][0], projected[0][1]);
        for (let i = 1; i < projected.length; i++) {
            this.ctx.lineTo(projected[i][0], projected[i][1]);
        }
        this.ctx.closePath();

        const [r, g, b] = color;
        this.ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        this.ctx.fill();
    }

    drawQuadWithBorder(vertices, faceColor, lineWidth, lineColor) {
        this.drawQuad(vertices, faceColor);

        const projected = vertices.map(v => this.project(v));

        this.ctx.beginPath();
        this.ctx.moveTo(projected[0][0], projected[0][1]);
        for (let i = 1; i < projected.length; i++) {
            this.ctx.lineTo(projected[i][0], projected[i][1]);
        }
        this.ctx.closePath();

        const [r, g, b] = lineColor;
        this.ctx.strokeStyle = `rgb(${r}, ${g}, ${b})`;
        this.ctx.lineWidth = lineWidth;
        this.ctx.stroke();
    }

    drawTriangle(vertices, color) {
        const projected = vertices.map(v => this.project(v));

        this.ctx.beginPath();
        this.ctx.moveTo(projected[0][0], projected[0][1]);
        this.ctx.lineTo(projected[1][0], projected[1][1]);
        this.ctx.lineTo(projected[2][0], projected[2][1]);
        this.ctx.closePath();

        const [r, g, b] = color;
        this.ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        this.ctx.fill();
    }

    drawLine(p1, p2, width, color) {
        const [x1, y1] = this.project(p1);
        const [x2, y2] = this.project(p2);

        const [r, g, b] = color;
        this.ctx.strokeStyle = `rgb(${r}, ${g}, ${b})`;
        this.ctx.lineWidth = width;

        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
    }

    // Simple isometric projection (same as Tkinter backend)
    project(point3d) {
        const [x, y, z] = point3d;

        // Center the cube (geometry spans 0-90)
        const cubeCenter = 45.0;
        const cx = x - cubeCenter;
        const cy = y - cubeCenter;
        const cz = z - cubeCenter;

        // Scale and offset
        const scale = this.canvas.width * 0.4 / 90;
        const offsetX = this.canvas.width / 2;
        const offsetY = this.canvas.height / 2;

        // Isometric projection
        const x2d = (cx - cz) * 0.866 * scale + offsetX;
        const y2d = offsetY - (cy * scale - (cx + cz) * 0.5 * scale);

        return [x2d, y2d];
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
            modifiers: (event.shiftKey ? 1 : 0) | (event.ctrlKey ? 2 : 0) | (event.altKey ? 4 : 0)
        });
    }
});

// Initialize on page load
window.addEventListener('load', () => {
    window.cubeClient = new CubeClient();
});
