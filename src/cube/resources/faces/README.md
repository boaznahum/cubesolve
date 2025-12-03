# Face Textures

This directory contains images for cube face textures.

## Directory Structure

```
resources/faces/
├── README.md            # This file
├── set1/                # Default texture set
├── numbers/             # Numbered faces (was "boaz")
├── letters/             # Letter faces F,B,R,L,U,D (was "demo")
└── family/              # Your family photos (create this!)
```

## How to Toggle Textures

**Keyboard:** Press `Ctrl+Shift+T` to cycle through texture sets.

The cycle follows `TEXTURE_SETS` in `config.py`:
```python
TEXTURE_SETS: list[str | None] = ["set1", "numbers", "family", None]
```
- `None` = solid colors (no textures)

## How to Create Your Own Textures

### Option 1: From Family Photos (Automatic Face Detection)

```bash
# Install dependencies
.venv_pyglet2/Scripts/pip.exe install opencv-python pillow

# Extract all faces from your photos
.venv_pyglet2/Scripts/python.exe make_face_textures.py extract "C:/Photos/Family" src/cube/resources/faces/family

# Review faces in src/cube/resources/faces/family/all_faces/
# Note which numbers (001, 002, ...) you want

# Select 6 faces for the cube
.venv_pyglet2/Scripts/python.exe make_face_textures.py select src/cube/resources/faces/family 1 3 5 7 9 11

# Add "family" to TEXTURE_SETS in config.py
```

### Option 2: Manual Image Creation

1. Create a new directory (e.g., `myphotos/`)

2. Add 6 square images named:
   - `F.png` - Front face (green on standard cube)
   - `B.png` - Back face (blue)
   - `R.png` - Right face (red)
   - `L.png` - Left face (orange)
   - `U.png` - Up face (white)
   - `D.png` - Down face (yellow)

3. Image requirements:
   - Format: PNG, JPG, or BMP
   - Size: Square recommended (e.g., 512x512)
   - Non-square images will be cropped to square

4. Add your folder name to `TEXTURE_SETS` in `config.py`

### Option 3: Generate Synthetic Test Images

```bash
cd src/cube/resources/faces
python generate_images.py letters mytest    # Creates letter images
python generate_images.py gradients mytest  # Creates gradient images
python generate_images.py grid mytest       # Creates numbered grid
```

## UV Mapping

Each face texture is mapped to a 3x3 grid (or NxN for larger cubes):
- Bottom-left cell = bottom-left of texture (UV 0,0)
- Top-right cell = top-right of texture (UV 1,1)

The `numbers` set shows numbered cells to verify correct mapping.
