# Face Textures

This directory contains images for cube face textures.

## Directory Structure

```
resources/faces/
├── generate_images.py   # Script to create synthetic test images
├── README.md            # This file
├── set1/                # Simple face letters (F, B, R, L, U, D)
├── set2/                # Gradients with UV arrows
└── family/              # 3x3 numbered grid
```

## How to Create Images

### Option 1: Generate Synthetic Test Images

**Requires:** `pip install Pillow`

Run from this directory:
```bash
cd resources/faces
python generate_images.py <type> <output_dir>
```

**Parameters:**
- `type`: Image style to generate
  - `letters` - Simple face letters (F, B, R, L, U, D) with borders
  - `gradients` - Gradient patterns with UV direction arrows
  - `grid` - 3x3 numbered grid (1-9) for UV verification
- `output_dir`: Name of output directory (created under resources/faces/)

**Examples:**
```bash
python generate_images.py letters set1       # Creates set1/ with letter images
python generate_images.py gradients set2     # Creates set2/ with gradient images
python generate_images.py grid family        # Creates family/ with numbered grid
python generate_images.py letters demo       # Creates demo/ with letter images
```

Creates 6 PNG images (F.png, B.png, R.png, L.png, U.png, D.png) in the specified directory.

### Option 2: Use Your Own Images

1. Create a new directory under `resources/faces/` (e.g., `myphotos/`)

2. Add 6 square images named:
   - `F.png` - Front face (green on standard cube)
   - `B.png` - Back face (blue)
   - `R.png` - Right face (red)
   - `L.png` - Left face (orange)
   - `U.png` - Up face (white)
   - `D.png` - Down face (yellow)

3. Image requirements:
   - Format: PNG, JPG, or BMP
   - Size: Square recommended (e.g., 256x256, 512x512)
   - Non-square images will be stretched

## How to Use Textures

### Method 1: Launch Script
```bash
python run_with_textures.py set1      # Use set1
python run_with_textures.py family    # Use family
python run_with_textures.py myphotos  # Use custom directory
```

### Method 2: Keyboard Toggle
1. Run normal app: `python -m cube.main_pyglet`
2. Press `Ctrl+T` to toggle texture mode on/off

Note: Textures must be loaded first (via config or script).

### Method 3: Config File
Edit `src/cube/application/config.py`:
```python
TEXTURE_MODE_ENABLED = True
TEXTURE_SET_PATH = "resources/faces/set1"
```

## UV Mapping

Each face texture is mapped to a 3x3 grid (or NxN for larger cubes):
- Bottom-left cell = bottom-left of texture (UV 0,0)
- Top-right cell = top-right of texture (UV 1,1)

The `family` set shows numbered cells 1-9 to verify correct mapping.
