/**
 * Marker animation — pulsing effects for bracket corners (target) and
 * filled circles (source), plus "meeting" flash when both land on the
 * same sticker.
 *
 * Called once per frame from the main render loop.
 */

export class MarkerAnimator {
    constructor(cubeModel) {
        this.cubeModel = cubeModel;
        this._time = 0;
        this._meetAnim = null;  // active meet animation state
    }

    /**
     * Update all marker animations.  Call once per frame.
     * @param {number} dt  seconds since last frame
     */
    update(dt) {
        this._time += dt;

        // If a meet animation is active, run it instead of normal pulses
        if (this._meetAnim) {
            this._updateMeetAnimation(dt);
            return;
        }

        // Animate fixed marker groups (bracket corners) — slow breathe
        for (const faceName of Object.keys(this.cubeModel.fixedMarkerGroups)) {
            const groups = this.cubeModel.fixedMarkerGroups[faceName];
            if (!groups) continue;
            for (const group of groups) {
                if (!group) continue;
                // Slow scale breathe: 0.92 – 1.0 over ~2.5 seconds
                const s = 0.96 + 0.04 * Math.sin(this._time * 2.5);
                group.scale.set(s, s, 1);
            }
        }

        // Moveable markers: static full opacity (animation only during meet)
    }

    /**
     * Play the "meeting" animation — a bright flash/pulse on stickers that
     * have both fixed AND moveable markers, then fade out.
     *
     * @param {CubeModel} cubeModel
     * @param {number} durationMs  total animation duration in milliseconds
     * @returns {Promise<void>} resolves when animation is complete
     */
    playMeetAnimation(cubeModel, durationMs) {
        // Find all marker groups that participate in the meet
        const targets = [];
        for (const faceName of Object.keys(cubeModel.fixedMarkerGroups)) {
            const fixedGroups = cubeModel.fixedMarkerGroups[faceName];
            const moveableGroups = cubeModel.markerGroups[faceName];
            if (!fixedGroups || !moveableGroups) continue;
            for (let i = 0; i < fixedGroups.length; i++) {
                const fixed = fixedGroups[i];
                const moveable = moveableGroups[i];
                // Only animate stickers where BOTH marker types are present (= they met)
                if (fixed && moveable) {
                    targets.push(fixed);
                    targets.push(moveable);
                }
            }
        }

        // If no markers found, resolve immediately
        if (targets.length === 0) {
            return Promise.resolve();
        }

        // Store initial opacities so we can restore/fade from them
        for (const group of targets) {
            group.traverse((child) => {
                if (child.material && child.material.transparent) {
                    child.material._savedOpacity = child.material.opacity;
                }
            });
        }

        return new Promise((resolve) => {
            this._meetAnim = {
                targets,
                elapsed: 0,
                duration: durationMs / 1000,  // convert to seconds
                resolve,
            };
        });
    }

    /**
     * Per-frame update for the meet animation.
     * Phase 1 (0–40%): scale up to 1.3x, brighten to full opacity
     * Phase 2 (40–100%): scale back to 1.0x, fade opacity to 0
     */
    _updateMeetAnimation(dt) {
        const anim = this._meetAnim;
        anim.elapsed += dt;
        const t = Math.min(anim.elapsed / anim.duration, 1.0);

        const flashPoint = 0.4;  // 40% of duration is the flash peak

        let scale, opacity;
        if (t < flashPoint) {
            // Phase 1: ramp up
            const p = t / flashPoint;  // 0 → 1
            scale = 1.0 + 0.3 * p;
            opacity = 0.8 + 0.2 * p;  // approach 1.0
        } else {
            // Phase 2: fade out
            const p = (t - flashPoint) / (1.0 - flashPoint);  // 0 → 1
            scale = 1.3 - 0.3 * p;  // back to 1.0
            opacity = 1.0 * (1.0 - p);  // fade to 0
        }

        for (const group of anim.targets) {
            group.scale.set(scale, scale, 1);
            group.traverse((child) => {
                if (child.material && child.material.transparent) {
                    child.material.opacity = opacity;
                }
            });
        }

        // Animation complete
        if (t >= 1.0) {
            // Restore original opacities (markers will be removed by next state update)
            for (const group of anim.targets) {
                group.traverse((child) => {
                    if (child.material && child.material.transparent) {
                        child.material.opacity = child.material._savedOpacity || 1.0;
                        delete child.material._savedOpacity;
                    }
                });
                group.scale.set(1, 1, 1);
            }
            const resolve = anim.resolve;
            this._meetAnim = null;
            resolve();
        }
    }
}
