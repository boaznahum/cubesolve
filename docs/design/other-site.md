# Mouse-Based Face Rotation - Analysis of rubikverse.com

**Source:** https://rubikverse.com/rubiks-cube-solver/
**Date:** 2026-02-27
**Purpose:** Learn how a production Rubik's cube web app implements mouse drag → face/slice rotation

---

## Table of Contents

1. [Tech Stack & Architecture](#tech-stack--architecture)
2. [Cubie Representation](#cubie-representation)
3. [Mouse Click Detection (Raycasting)](#mouse-click-detection-raycasting)
4. [Whole-Cube vs Face Rotation Toggle](#whole-cube-vs-face-rotation-toggle)
5. [Drag Direction Detection](#drag-direction-detection)
6. [Core Algorithm: calculateTurn](#core-algorithm-calculateturn)
7. [Face Index Mapping (Three.js → Logical)](#face-index-mapping)
8. [Per-Face Axis Mapping Table](#per-face-axis-mapping-table)
9. [Layer/Depth Calculation](#layerdepth-calculation)
10. [Rotation Execution (rotatePieces)](#rotation-execution-rotatepieces)
11. [Visual Feedback](#visual-feedback)
12. [Key Design Decisions & Takeaways](#key-design-decisions--takeaways)

---

## Tech Stack & Architecture

- **Three.js** (WebGL) - 3D rendering
- **React** - UI framework (buttons, panels)
- **OrbitControls** - built-in Three.js control for whole-cube orbit rotation
- **Raycaster** - built-in Three.js tool for detecting which 3D object the mouse hits

### Key Variables (from minified source, module 228)

| Variable | Three.js Class | Purpose |
|----------|---------------|---------|
| `u` | `Scene` | The 3D scene containing all cubies |
| `p` | `PerspectiveCamera` | Camera (fov=75, near=0.1, far=1000) |
| `d` | `WebGLRenderer` | Renderer (antialias, alpha) |
| `v` | `Raycaster` | For hit-testing mouse clicks against cubies |
| `b` | `Vector2` | Normalized device coordinates (NDC) for mouse |
| `L` | `OrbitControls` | Handles whole-cube orbit when not dragging a face |
| `a` | intersection | Saved first-click intersection result |
| `r` | number | Which material index (face) was clicked |
| `c` | boolean | Whether a cubie was clicked (face-drag mode active) |
| `S` | function ref | Reference to `this.calculateTurn` |
| `F` | function ref | Reference to `this.algorithm` (applies the move) |

---

## Cubie Representation

Each cubie is a **separate Three.js `Mesh`** with:
- **Geometry:** `BoxGeometry` (1x1x1 unit cube)
- **Materials:** Array of **6 materials** (one per face: `MeshBasicMaterial`)
  - Each material has a `.color` and `.opacity`
  - The array index corresponds to the face: `[right, left, top, bottom, front, back]` (Three.js standard)
- **Position:** Integer grid positions (e.g., for 3x3: positions 0,1,2 on each axis)

For a 3x3 cube, there are **27 cubies** (including the invisible center one), each placed at integer coordinates. The cube is centered around `(size/2 - 0.5, size/2 - 0.5, size/2 - 0.5)`.

---

## Mouse Click Detection (Raycasting)

### Step-by-step flow on `mousedown`:

```javascript
// 1. Convert mouse pixel coords to Normalized Device Coordinates (NDC)
//    NDC range: x = [-1, +1], y = [-1, +1]
//    (0,0) is center of screen, (-1,-1) is bottom-left, (+1,+1) is top-right
mouse.x = event.clientX / window.innerWidth * 2 - 1;
mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;  // Y is flipped!

// 2. Create a ray from camera through the mouse position
raycaster.setFromCamera(mouse, camera);

// 3. Test intersection against ALL cubies in the scene
var intersects = raycaster.intersectObjects(scene.children);

// 4. Check if we hit anything
if (intersects.length > 0) {
    // HIT - we clicked on a cubie
    // intersects[0] is the closest hit, containing:
    //   .point      - Vector3: exact 3D world coordinate where the ray hit the face
    //   .object     - Mesh: the cubie mesh that was hit
    //   .faceIndex  - number: which triangle was hit (0-11 for a box = 6 faces x 2 triangles)
    //   .object.position - Vector3: the cubie's grid position

    // Determine which face of the cubie was clicked
    // Three.js BoxGeometry has 2 triangles per face, so:
    //   faceIndex 0,1 → face 0 (right/+X)
    //   faceIndex 2,3 → face 1 (left/-X)
    //   faceIndex 4,5 → face 2 (top/+Y)
    //   faceIndex 6,7 → face 3 (bottom/-Y)
    //   faceIndex 8,9 → face 4 (front/+Z)
    //   faceIndex 10,11 → face 5 (back/-Z)
    var whichFace = Math.floor(intersects[0].faceIndex / 2);  // 0-5

    // Save intersection for later use in mousemove
    savedIntersection = intersects[0];  // stores .point, .object, .faceIndex
    savedFace = whichFace;

    // Visual feedback: dim the clicked face
    intersects[0].object.material[whichFace].opacity = 0.8;

    // DISABLE OrbitControls - we're doing face rotation now
    orbitControls.saveState();
    orbitControls.enabled = false;

} else {
    // MISS - clicked on background
    // ENABLE OrbitControls - we're doing whole-cube orbit
    orbitControls.enabled = true;
    savedIntersection = null;
}
```

### Critical detail: `intersects[0].point`

The `.point` is the **exact 3D world coordinate** where the ray hits the cubie surface. This is NOT the cubie position - it's the precise point on the face where the user clicked. This is used later to compute the 3D drag vector.

---

## Whole-Cube vs Face Rotation Toggle

The mechanism is simple and elegant:

| User Action | Raycaster Result | OrbitControls | Behavior |
|-------------|-----------------|---------------|----------|
| Click ON a cubie | `intersects.length > 0` | **Disabled** | Drag = face/slice rotation |
| Click on BACKGROUND | `intersects.length === 0` | **Enabled** | Drag = orbit whole cube |
| mouseup (always) | N/A | **Re-enabled** | Reset state |

```javascript
// mouseup handler:
function onMouseUp(e) {
    if (savedIntersection) {
        savedIntersection.object.material[savedFace].opacity = 1;  // restore
    }
    if (wasClicked) {
        orbitControls.reset();  // restore saved camera state
    }
    wasClicked = false;
    savedIntersection = null;
    orbitControls.enabled = true;
}
```

**Key insight:** OrbitControls is a standard Three.js addon. When `enabled = false`, mouse drags don't orbit the camera. When `enabled = true`, they do. By toggling this based on whether the raycaster hit a cubie, you get automatic switching between the two modes.

---

## Drag Direction Detection

### Step-by-step flow on `mousemove` (while mouse is held down):

```javascript
// Only process if we have a saved click intersection
if (!savedIntersection || !newIntersects.length) return;

// 1. Raycast again to get WHERE the mouse is now (in 3D world coords)
mouse.x = event.clientX / window.innerWidth * 2 - 1;
mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
raycaster.setFromCamera(mouse, camera);
var newIntersects = raycaster.intersectObjects(scene.children);

// 2. Get the current 3D point
var currentPoint = newIntersects[0].point;     // Vector3: where mouse is NOW in 3D
var startPoint = savedIntersection.point;       // Vector3: where mouse was on click
var cubiePosition = savedIntersection.object.position;  // Vector3: cubie grid pos
var faceIndex = Math.floor(savedIntersection.faceIndex / 2);

// 3. Map Three.js face index to logical face
//    Three.js faces: 0=+X, 1=-X, 2=+Y, 3=-Y, 4=+Z, 5=-Z
//    Logical faces:  0=U(top), 1=F(front), 2=R(right), 3=B(back), 4=L(left), 5=D(bottom)
var logicalFace = [2, 4, 3, 0, 1, 5][faceIndex];

// 4. Calculate which rotation to perform
var move = calculateTurn(currentPoint, startPoint, cubiePosition, logicalFace, cubeSize);

// 5. If we got a valid move, execute it
if (move !== null && !move.includes("null")) {
    algorithm(move, "Drag Turn");  // apply the rotation
    savedIntersection.object.material[savedFace].opacity = 1;  // restore opacity
    savedIntersection = null;  // clear - one drag = one rotation
}
```

**Critical design decision:** The drag is computed in **3D world coordinates**, not 2D screen space. This means:
- The drag vector components (dx, dy, dz) directly correspond to the cube's axes
- No need to project or unproject screen coordinates
- The face orientation naturally determines which axis components matter

---

## Core Algorithm: calculateTurn

This is the heart of the mouse interaction. It takes two 3D points (start and current), the clicked cubie's position, which face was clicked, and the cube size, and returns a move string like `"01R"` or `"02F'"`.

### Decompiled/reconstructed code:

```javascript
function calculateTurn(currentPoint, startPoint, cubiePosition, face, cubeSize) {
    var moveName = null;
    var depth = null;
    var result = null;

    // 1. Compute 3D drag vector
    var delta = {
        x: currentPoint.x - startPoint.x,
        y: currentPoint.y - startPoint.y,
        z: currentPoint.z - startPoint.z
    };

    // 2. If no movement, return null
    if (currentPoint.x === startPoint.x &&
        currentPoint.y === startPoint.y &&
        currentPoint.z === startPoint.z) {
        return null;
    }

    // 3. Helper: compare two axis components to decide rotation
    //    Parameters:
    //      primaryDelta    - the delta component for axis 1
    //      primaryPositive - whether positive delta = clockwise
    //      secondaryDelta  - the delta component for axis 2
    //      secondaryPositive - whether positive delta = clockwise
    //      primaryDepth    - layer depth if primary axis wins
    //      secondaryDepth  - layer depth if secondary axis wins
    //      primaryMove     - move name if primary axis wins (e.g., "R")
    //      secondaryMove   - move name if secondary axis wins (e.g., "U")
    function chooseDominantAxis(primaryDelta, primaryPositive,
                                 secondaryDelta, secondaryPositive,
                                 primaryDepth, secondaryDepth,
                                 primaryMoveName, secondaryMoveName) {
        if (Math.abs(primaryDelta) >= Math.abs(secondaryDelta) &&
            Math.abs(primaryDelta) > 0.05) {
            // Primary axis dominates
            return {
                calculated: primaryPositive ? primaryMoveName : primaryMoveName + "'",
                depth: primaryDepth
            };
        } else if (Math.abs(secondaryDelta) > Math.abs(primaryDelta) &&
                   Math.abs(secondaryDelta) > 0.05) {
            // Secondary axis dominates
            return {
                calculated: secondaryPositive ? secondaryMoveName : secondaryMoveName + "'",
                depth: secondaryDepth
            };
        } else {
            // Dead zone - drag too small
            return { calculated: null, depth: null };
        }
    }

    // 4. Switch on which face was clicked - each face has different axis mappings
    switch (face) {
        case 0:  // U (top) face - looking down at it
            // Dragging on top: Z-drag → R rotation, X-drag → U rotation
            result = chooseDominantAxis(
                delta.z, delta.z < 0,        // primary: Z axis
                delta.x, delta.x >= 0,       // secondary: X axis
                cubeSize - cubiePosition.z,   // depth: which R layer
                cubeSize - cubiePosition.x,   // depth: which U layer (but U on top?)
                "R", "U"
            );
            break;

        case 1:  // F (front) face - looking at it
            // Dragging on front: X-drag → F rotation, Y-drag → R rotation
            result = chooseDominantAxis(
                delta.x, delta.x <= 0,       // primary: X axis
                delta.y, delta.y < 0,        // secondary: Y axis
                cubeSize - cubiePosition.x,  // depth: which F layer
                cubiePosition.y + 1,         // depth: which R layer
                "F", "R"
            );
            break;

        case 2:  // R (right) face - looking at it from the right
            // Dragging on right: Z-drag → F rotation, Y-drag → U rotation
            result = chooseDominantAxis(
                delta.z, delta.z > 0,        // primary: Z axis
                delta.y, delta.y > 0,        // secondary: Y axis
                cubeSize - cubiePosition.z,  // depth: which F layer
                cubiePosition.y + 1,         // depth: which U layer
                "F", "U"
            );
            break;

        case 3:  // B (back) face
            result = chooseDominantAxis(
                delta.z, delta.z > 0,
                delta.x, delta.x <= 0,
                cubeSize - cubiePosition.z,
                cubeSize - cubiePosition.x,
                "R", "U"
            );
            break;

        case 4:  // L (left) face
            result = chooseDominantAxis(
                delta.z, delta.z < 0,
                delta.y, delta.y < 0,
                cubeSize - cubiePosition.z,
                cubiePosition.y + 1,
                "F", "U"
            );
            break;

        case 5:  // D (bottom) face
            result = chooseDominantAxis(
                delta.x, delta.x >= 0,
                delta.y, delta.y > 0,
                cubeSize - cubiePosition.x,
                cubiePosition.y + 1,
                "F", "R"
            );
            break;
    }

    moveName = result.calculated;
    depth = result.depth;

    // 5. Format: zero-padded depth + move name
    //    e.g., "01R" = layer 1, R clockwise
    //    e.g., "02F'" = layer 2, F counter-clockwise
    return (depth < 10 ? "0" : "") + depth + moveName;
}
```

### How the algorithm works conceptually:

1. **The 3D drag vector tells you everything.** When you drag on a face, only 2 of the 3 axes have meaningful movement (the face normal axis barely changes since you're dragging along the face).

2. **For each face, the two "in-plane" axes are pre-mapped** to two possible rotation types:
   - On the **top face (U)**: dragging along Z → "R" rotation, dragging along X → "U" rotation
   - On the **front face (F)**: dragging along X → "F" rotation, dragging along Y → "R" rotation

3. **The dominant axis wins.** If you drag more in Z than X on the top face, it's an "R" move. If more in X, it's a "U" move.

4. **The sign of the delta determines direction** (clockwise vs counter-clockwise, indicated by `'` suffix).

5. **The cubie position determines the depth** (which layer to rotate).

---

## Face Index Mapping

### Three.js BoxGeometry Face Order

Three.js assigns triangle indices to box faces in this standard order:

| faceIndex | Triangle | Three.js Face | Direction |
|-----------|----------|---------------|-----------|
| 0, 1 | 0 | Right | +X |
| 2, 3 | 1 | Left | -X |
| 4, 5 | 2 | Top | +Y |
| 6, 7 | 3 | Bottom | -Y |
| 8, 9 | 4 | Front | +Z |
| 10, 11 | 5 | Back | -Z |

### Three.js → Logical Face Mapping

The site uses this mapping array: `[2, 4, 3, 0, 1, 5]`

| Three.js Face Index | Three.js Direction | → Logical Face | Cube Notation |
|--------------------|--------------------|----------------|---------------|
| 0 | Right (+X) | 2 | R |
| 1 | Left (-X) | 4 | L |
| 2 | Top (+Y) | 3 | B (!) |
| 3 | Bottom (-Y) | 0 | U (!) |
| 4 | Front (+Z) | 1 | F |
| 5 | Back (-Z) | 5 | D |

**Note:** The mapping is non-obvious because the cube orientation in 3D space doesn't match the standard Rubik's notation. The camera looks at the cube from a specific angle, so what appears as "top" visually isn't necessarily the +Y axis.

---

## Per-Face Axis Mapping Table

This table summarizes what `calculateTurn` does for each face:

| Logical Face | Primary Axis | Primary Move | CW when | Secondary Axis | Secondary Move | CW when | Primary Depth | Secondary Depth |
|-------------|-------------|-------------|---------|---------------|---------------|---------|--------------|----------------|
| 0 (U) | delta.z | "R" | z < 0 | delta.x | "U" | x >= 0 | size - pos.z | size - pos.x |
| 1 (F) | delta.x | "F" | x <= 0 | delta.y | "R" | y < 0 | size - pos.x | pos.y + 1 |
| 2 (R) | delta.z | "F" | z > 0 | delta.y | "U" | y > 0 | size - pos.z | pos.y + 1 |
| 3 (B) | delta.z | "R" | z > 0 | delta.x | "U" | x <= 0 | size - pos.z | size - pos.x |
| 4 (L) | delta.z | "F" | z < 0 | delta.y | "U" | y < 0 | size - pos.z | pos.y + 1 |
| 5 (D) | delta.x | "F" | x >= 0 | delta.y | "R" | y > 0 | size - pos.x | pos.y + 1 |

### Pattern observations:
- Opposite faces (U/D, F/B, R/L) use the same axes but with **inverted signs**
- "R" (right) rotations always involve the **Z axis** as primary
- "F" (front) rotations appear on faces where the **Z or X axis** is the primary drag direction
- "U" (up) rotations appear as secondary on top/bottom/left/right faces
- Depth is always computed from the cubie's position relative to the cube size

---

## Layer/Depth Calculation

The **depth** determines which slice/layer to rotate. It's computed from the clicked cubie's grid position:

```
For faces using "size - pos.z":  depth = cubeSize - cubiePosition.z
For faces using "size - pos.x":  depth = cubeSize - cubiePosition.x
For faces using "pos.y + 1":    depth = cubiePosition.y + 1
```

For a 3x3 cube (size=3) with positions 0,1,2:
- `size - pos.z` when pos.z=2 → depth=1 (outer layer)
- `size - pos.z` when pos.z=1 → depth=2 (middle layer)
- `size - pos.z` when pos.z=0 → depth=3 (other outer layer)

The depth is zero-padded in the output string: `"01R"` means depth 1 (outer), R clockwise.

---

## Rotation Execution (rotatePieces)

Once `calculateTurn` returns a move string (e.g., `"01R"`), the `algorithm` function parses it and calls `rotatePieces` to animate the rotation:

### Parameters:
```javascript
rotatePieces(rotatePoint, cubes, {
    cubeDimension,   // cube size (3 for 3x3)
    cubes,           // array of all cubie meshes
    turnDirection,   // +1 or -1 (CW or CCW)
    speed,           // animation speed
    start,           // current rotation angle (animated from 0 to 90)
    face,            // 0=U, 1=F, 2=R
    cubeDepth,       // which layer
    isMulti,         // whether it's a wide move
    rubiksObject     // reference to all cube objects
})
```

### Per-face rotation:

```javascript
// Face 0 (U - top): rotate around Y axis, move X/Z
if (face === 0) {
    for each cubie:
        if cubie.position.y is in target layer range:
            // Animate rotation
            if (turnDirection < 0)
                cubie.rotation.y += 0.1745 * speed / 10;  // ~10 degrees per frame
            else
                cubie.rotation.y -= 0.1745 * speed / 10;

            // Move cubie position in a circle
            newPos = rotatePoint(center, center, direction, cubie.position.x, cubie.position.z, speed);

            // Snap to grid at 90-degree boundaries
            if (angle % 90 === 0) {
                newPos.p1 = Math.round(newPos.p1);
                newPos.p2 = Math.round(newPos.p2);
            }
            cubie.position.x = newPos.p1;
            cubie.position.z = newPos.p2;
}

// Face 1 (F - front): rotate around Z axis, move X/Y
if (face === 1) {
    // Select by position.z range
    // Rotate cubie.rotation.z
    // Update position.x and position.y
}

// Face 2 (R - right): rotate around X axis, move Y/Z
if (face === 2) {
    // Select by position.x range
    // Rotate cubie.rotation.x
    // Update position.y and position.z
}
```

### rotatePoint helper:
```javascript
// Rotates a point (o, s) around center (e, t) by a small angle
function rotatePoint(centerX, centerY, direction, pointX, pointY, speed) {
    var angle = (Math.PI / 180) * speed;  // Convert speed to radians
    if (direction < 0) angle *= -1;       // Reverse for CCW
    return {
        p1: Math.cos(angle) * (pointX - centerX) - Math.sin(angle) * (pointY - centerY) + centerX,
        p2: Math.sin(angle) * (pointX - centerX) + Math.cos(angle) * (pointY - centerY) + centerY
    };
}
```

---

## Visual Feedback

1. **On click:** Clicked face material opacity set to **0.8** (slightly transparent)
2. **On mouseup / after drag:** Opacity restored to **1.0**
3. **Move hints:** Arrow textures loaded and placed on face surfaces (visible=false by default), toggled on hover via `generateMoveHints`
4. **Animation:** Smooth 90-degree rotation at configurable speed with grid-snapping at completion

---

## Key Design Decisions & Takeaways

### 1. Raycasting is Non-Negotiable
You **must** know which cubie face was clicked in 3D space. Screen-space heuristics won't work reliably because the cube is viewed at an angle. The raycaster gives you:
- Which cubie was hit
- Which face of that cubie
- The exact 3D point on the surface

### 2. 3D Drag Vector > 2D Screen Drag
The drag is computed as `currentPoint3D - startPoint3D` in **world coordinates**. This is vastly simpler than trying to project 2D screen movement back into 3D, because:
- The face normal automatically constrains which axes matter
- No need for complex screen-to-world unprojection
- Opposite faces naturally get inverted sign behavior

### 3. Dominant Axis Wins (with Dead Zone)
- Compare `|primaryDelta|` vs `|secondaryDelta|`
- The larger one determines the rotation type
- **Dead zone: 0.05** world units - drags smaller than this are ignored
- This prevents accidental rotations from tiny mouse movements

### 4. One Drag = One Rotation
Once a valid move is detected during `mousemove`, the move is executed **immediately** and `savedIntersection` is cleared. The user can't chain rotations in a single drag - they must release and click again.

### 5. OrbitControls Toggle is the Simplest Approach
- Click on cube → disable orbit → face rotation mode
- Click on background → enable orbit → whole-cube rotation mode
- mouseup → always re-enable orbit
- No complex mode switching UI needed

### 6. Cubie Position = Layer Selection
The clicked cubie's grid position directly tells you which layer to rotate. No additional calculation needed - just read `position.x`, `.y`, or `.z` depending on the rotation axis.

### 7. Face-to-Axis Mapping is a Fixed Table
Each of the 6 faces has a hardcoded mapping of:
- Which two delta components to compare
- Which rotation names they correspond to
- How to compute depth from cubie position
- Which sign means clockwise

This table has **12 entries** (6 faces x 2 axes each) and doesn't change with cube size.

---

## Applying This to Our Codebase (cubesolve)

### What we need:
1. **Raycasting/hit detection** - Given a mouse click, determine which cell (cubie face) was clicked and get the 3D intersection point
2. **3D drag tracking** - Track mouse movement in 3D world coordinates (not screen space)
3. **Face-axis mapping table** - Map our face orientations to the correct axis pairs
4. **Dominant axis comparison** - Compare the two relevant delta components with a dead zone
5. **Layer depth from cell position** - Use the clicked cell's grid position to determine the slice
6. **OrbitControls equivalent** - Toggle between whole-cube rotation and face rotation based on whether the click hit a cubie

### What we already have:
- `screen_to_world()` in the renderer's ViewStateManager - can convert screen coords to 3D
- `_Board` / `_FaceBoard` / `_Cell` hierarchy - knows which face each cell belongs to
- Mouse event handling in `PygletAppWindow`
- Face rotation via the command system

### What we need to add:
- Raycast-like hit detection (find which `_Cell` was clicked)
- 3D drag vector computation
- The `calculateTurn`-equivalent function with our face mapping
- Toggle between orbit and face-rotation on mousedown
