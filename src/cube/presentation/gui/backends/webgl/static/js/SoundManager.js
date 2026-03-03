/**
 * SoundManager — procedural cube rotation sounds via Web Audio API.
 *
 * Generates a satisfying mechanical click + subtle tonal sweep on each move.
 * No external audio files needed — entirely synthesized.
 *
 * Usage:
 *   const sound = new SoundManager();
 *   sound.play();           // play click sound
 *   sound.enabled = false;  // mute
 */

export class SoundManager {
    constructor() {
        this._ctx = null;       // AudioContext (lazy init on first user gesture)
        this._enabled = true;
        this._masterGain = null;
        this._initialized = false;
    }

    get enabled() { return this._enabled; }

    set enabled(val) {
        this._enabled = !!val;
        if (this._masterGain) {
            this._masterGain.gain.value = this._enabled ? 1.0 : 0.0;
        }
    }

    /**
     * Initialize AudioContext lazily (must happen after user gesture).
     */
    _init() {
        if (this._initialized) return;
        try {
            this._ctx = new (window.AudioContext || window.webkitAudioContext)();
            this._masterGain = this._ctx.createGain();
            this._masterGain.gain.value = this._enabled ? 1.0 : 0.0;
            this._masterGain.connect(this._ctx.destination);
            this._initialized = true;
        } catch (e) {
            console.warn('SoundManager: Web Audio API not available', e);
        }
    }

    /**
     * Play a cube rotation sound.
     * @param {number} [volume=0.35] - Volume 0..1
     */
    play(volume = 0.35) {
        if (!this._enabled) return;
        this._init();
        if (!this._ctx) return;

        // Resume context if suspended (autoplay policy)
        if (this._ctx.state === 'suspended') {
            this._ctx.resume();
        }

        const now = this._ctx.currentTime;
        const vol = Math.max(0, Math.min(1, volume));

        // ── Layer 1: Mechanical click (filtered noise burst) ──
        this._playClick(now, vol);

        // ── Layer 2: Subtle tonal snap (short oscillator) ──
        this._playTone(now, vol * 0.4);
    }

    /**
     * Short percussive click — band-pass filtered noise burst.
     */
    _playClick(time, vol) {
        const ctx = this._ctx;
        const duration = 0.04;

        // Create noise buffer
        const bufferSize = Math.ceil(ctx.sampleRate * duration);
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1);
        }

        const source = ctx.createBufferSource();
        source.buffer = buffer;

        // Band-pass filter for "plasticky" click character
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 3500;
        filter.Q.value = 1.2;

        // Envelope
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(vol * 0.8, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration);

        source.connect(filter);
        filter.connect(gain);
        gain.connect(this._masterGain);

        source.start(time);
        source.stop(time + duration + 0.01);
    }

    /**
     * Short tonal snap — oscillator that sweeps down.
     */
    _playTone(time, vol) {
        const ctx = this._ctx;
        const duration = 0.065;

        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, time);
        osc.frequency.exponentialRampToValueAtTime(200, time + duration);

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(vol, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration);

        osc.connect(gain);
        gain.connect(this._masterGain);

        osc.start(time);
        osc.stop(time + duration + 0.01);
    }
}
