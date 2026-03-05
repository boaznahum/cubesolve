/**
 * Camera orbit controls — drag to orbit, scroll to zoom, Alt+drag to pan.
 *
 * Integrates with FaceTurnHandler: if pointer-down hits a sticker,
 * the face turn handler takes over; otherwise orbit begins.
 */

import * as THREE from 'three';

export class OrbitControls {
    constructor(camera, domElement, faceTurnHandler, sendFn) {
        this.camera = camera;
        this.domElement = domElement;
        this._faceTurn = faceTurnHandler;
        this._sendFn = sendFn;

        // Default camera angles
        this._defaultPhi = Math.PI / 4;
        this._defaultTheta = Math.PI / 6;
        this._defaultRadius = 8; // updated dynamically by fitToView()

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
        this.spherical.radius = this._defaultRadius;
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
     * Compute camera distance so the cube fits the viewport.
     *
     * Math: at distance d with vertical FOV, visible half-height = d * tan(fov/2).
     * For aspect < 1 (portrait), horizontal becomes the constraint, so we scale
     * distance by 1/aspect.  BASE_RADIUS=8 is calibrated for aspect=1, FOV=40°,
     * cube world-size=3.0.
     *
     * Only changes the live radius if user hasn't manually zoomed away from default.
     */
    fitToView(aspect) {
        const BASE_RADIUS = 8;   // correct for aspect=1, FOV=40°, cubeSize=3.0
        const PADDING = 1.05;    // 5% breathing room
        const newRadius = (BASE_RADIUS * PADDING) / Math.min(aspect, 1);

        const wasAtDefault = Math.abs(this.spherical.radius - this._defaultRadius) < 0.5;
        this._defaultRadius = newRadius;
        if (wasAtDefault) {
            this.spherical.radius = newRadius;
            this.update();
        }
    }

    /**
     * Adjust camera distance for different cube sizes.
     */
    setForCubeSize(size) {
        this._defaultRadius = size * 2.5;
        this.spherical.radius = this._defaultRadius;
        this.update();
    }
}
