/**
 * WebGL Cube Client — Entry point.
 *
 * Wires together all modules: scene, model, animation, controls,
 * WebSocket client, and toolbar.
 */

import * as THREE from 'three';
import { BACKGROUND_COLOR } from './constants.js';
import { AppState } from './AppState.js';
import { CubeModel } from './CubeModel.js';
import { AnimationQueue } from './AnimationQueue.js';
import { FaceTurnHandler } from './FaceTurnHandler.js';
import { OrbitControls } from './OrbitControls.js';
import { WsClient } from './WsClient.js';
import { Toolbar } from './Toolbar.js';

// ── Application state ──
const state = new AppState();

// ── Three.js setup ──
const canvas = document.getElementById('canvas');

const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(BACKGROUND_COLOR);
renderer.outputEncoding = THREE.sRGBEncoding;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);

// Lighting
const ambient = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambient);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(5, 8, 6);
scene.add(dirLight);

const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
dirLight2.position.set(-3, -2, 4);
scene.add(dirLight2);

// ── Cube model ──
const cubeModel = new CubeModel(scene);

// ── Animation queue ──
const animQueue = new AnimationQueue(cubeModel);

// ── WebSocket client ──
const wsClient = new WsClient(handleMessage);
const send = (msg) => wsClient.send(msg);

// ── Face turn handler ──
const faceTurnHandler = new FaceTurnHandler(
    cubeModel, camera, canvas, animQueue, send, scene,
);

// ── Orbit controls ──
const controls = new OrbitControls(camera, canvas, faceTurnHandler, send);

// ── Toolbar ──
const toolbar = new Toolbar(state, send, controls, animQueue);
toolbar.bind();

// Wire debug overlay callback from AnimationQueue → Toolbar
animQueue._onDebugUpdate = (alg, layers, count) => toolbar.updateDebug(alg, layers, count);

// ── Responsive sizing ──
function resize() {
    const wrapper = canvas.parentElement;
    const size = Math.min(wrapper.clientWidth, window.innerHeight - 120);
    renderer.setSize(size, size);
    camera.aspect = 1;
    camera.updateProjectionMatrix();
}
resize();
window.addEventListener('resize', resize);

// ── Message handler ──
function handleMessage(msg) {
    switch (msg.type) {
        case 'cube_state':
            state.latestState = msg;
            if (!animQueue.currentAnim && animQueue.queue.length === 0) {
                cubeModel.updateFromState(msg);
            } else {
                animQueue.pendingState = msg;
            }
            break;

        case 'animation_start': {
            const animState = msg.state || state.latestState;
            if (animState) {
                state.latestState = animState;
                animQueue.enqueue(msg, animState);
            }
            break;
        }

        case 'animation_stop':
            animQueue.stop();
            if (state.latestState) {
                cubeModel.updateFromState(state.latestState);
            }
            break;

        case 'flush_queue':
            animQueue.flush(state.latestState);
            break;

        case 'color_map':
            cubeModel.buildColorCorrections(msg.colors);
            break;

        default:
            // Toolbar handles: playing, text_update, version, client_count,
            // speed_update, size_update, toolbar_state, session_id
            toolbar.handleMessage(msg);
            break;
    }
}

// ── Render loop ──
function animate() {
    requestAnimationFrame(animate);
    animQueue.update();
    renderer.render(scene, camera);
}
animate();

// ── Connect ──
wsClient.connect();
