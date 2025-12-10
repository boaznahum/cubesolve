"""
Create test textures with directional arrows for debugging texture rotation.

Each face gets an NxN grid where each cell shows:
- Face name (F, U, R, etc.)
- Cell position (row, col) - row 0 is BOTTOM, col 0 is LEFT
- Arrow pointing UP

This helps debug texture bugs by showing exactly which cell texture
ends up at which position after rotations.

Usage:
    python tools/create_arrow_textures.py [size]
    
    size: Cube size (default: 4 for 4x4 cube)

Creates: src/cube/resources/faces/arrows/F.png, U.png, R.png, etc.
"""
from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not found. Install with: pip install Pillow")
    exit(1)

# Output directory - directly to faces/arrows
OUTPUT_DIR = Path(__file__).parent.parent / "src" / "cube" / "resources" / "faces" / "arrows"
OUTPUT_DIR.mkdir(exist_ok=True)

# Face colors (matching user's cube colors)
FACE_COLORS = {
    "F": (0, 69, 173),      # Blue
    "B": (0, 155, 72),      # Green
    "R": (183, 18, 52),     # Red
    "L": (255, 89, 0),      # Orange
    "U": (255, 213, 0),     # Yellow
    "D": (255, 255, 255),   # White
}

# Text/arrow color (contrasting)
TEXT_COLORS = {
    "F": (255, 255, 255),   # White on blue
    "B": (255, 255, 255),   # White on green
    "R": (255, 255, 255),   # White on red
    "L": (0, 0, 0),         # Black on orange
    "U": (0, 0, 0),         # Black on yellow
    "D": (0, 0, 0),         # Black on white
}


def create_grid_texture(face_name: str, grid_size: int, cell_pixels: int = 64) -> Image.Image:
    """Create a texture with NxN grid, each cell labeled with position.

    Args:
        face_name: Name of the face (F, B, R, L, U, D)
        grid_size: Number of cells per side (e.g., 4 for 4x4)
        cell_pixels: Size of each cell in pixels
    
    Returns:
        PIL Image with the grid texture
    """
    img_size = grid_size * cell_pixels
    bg_color = FACE_COLORS[face_name]
    text_color = TEXT_COLORS[face_name]

    img = Image.new("RGB", (img_size, img_size), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    try:
        font_size = cell_pixels // 4
        font = ImageFont.truetype("arial.ttf", font_size)
        small_font = ImageFont.truetype("arial.ttf", font_size // 2)
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    # Draw each cell
    # NOTE: row 0 is BOTTOM in cube coordinates, but TOP in image coordinates
    # So we need to flip: image_row = (grid_size - 1 - cube_row)
    for cube_row in range(grid_size):
        for col in range(grid_size):
            # Convert cube row to image row (flip Y axis)
            img_row = grid_size - 1 - cube_row
            
            x = col * cell_pixels
            y = img_row * cell_pixels

            # Draw cell border
            draw.rectangle(
                [x + 1, y + 1, x + cell_pixels - 2, y + cell_pixels - 2],
                outline=text_color,
                width=2
            )

            # Draw arrow in upper portion of cell
            draw_arrow_in_cell(draw, x, y, cell_pixels, text_color)

            # Draw face name + position label in lower portion
            # Format: "F(r,c)" where r=row, c=col in CUBE coordinates
            label = f"{face_name}({cube_row},{col})"
            
            # Center the label horizontally
            bbox = draw.textbbox((0, 0), label, font=small_font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (cell_pixels - text_width) // 2
            text_y = y + cell_pixels - cell_pixels // 4
            
            draw.text((text_x, text_y), label, fill=text_color, font=small_font)

    return img


def draw_arrow_in_cell(draw: ImageDraw.Draw, x: int, y: int, size: int, color: tuple) -> None:
    """Draw an upward-pointing arrow in the upper portion of a cell."""
    # Arrow occupies upper 60% of cell
    arrow_height = int(size * 0.55)
    margin_x = size // 6
    margin_top = size // 10
    
    center_x = x + size // 2
    arrow_width = size // 5
    shaft_width = size // 10
    arrow_head_height = arrow_height // 2

    # Arrow shaft (rectangle)
    shaft_left = center_x - shaft_width // 2
    shaft_right = center_x + shaft_width // 2
    shaft_top = y + margin_top + arrow_head_height
    shaft_bottom = y + margin_top + arrow_height

    draw.rectangle([shaft_left, shaft_top, shaft_right, shaft_bottom], fill=color)

    # Arrow head (triangle pointing up)
    arrow_points = [
        (center_x, y + margin_top),                          # Top point
        (center_x - arrow_width, shaft_top),                 # Bottom left
        (center_x + arrow_width, shaft_top),                 # Bottom right
    ]
    draw.polygon(arrow_points, fill=color)


def main():
    # Get grid size from command line, default to 4
    grid_size = 4
    if len(sys.argv) > 1:
        try:
            grid_size = int(sys.argv[1])
        except ValueError:
            print(f"Invalid size: {sys.argv[1]}, using default 4")

    print(f"Creating {grid_size}x{grid_size} arrow textures in {OUTPUT_DIR}")
    print(f"Cell format: FACE(row,col) where row 0 = bottom, col 0 = left")

    for face_name in FACE_COLORS:
        img = create_grid_texture(face_name, grid_size)
        output_path = OUTPUT_DIR / f"{face_name}.png"
        img.save(output_path)
        print(f"  Created {output_path}")

    print("\nDone! Load these textures in the GUI to test rotation behavior.")
    print("\nExpected behavior after F rotation (clockwise):")
    print("  - All arrows ON face F should point RIGHT (texture rotated)")
    print("  - Cell labels should show original positions (e.g., F(0,0) moves to F(0,3))")
    print("  - Adjacent edge stickers move but arrows still point UP")


if __name__ == "__main__":
    main()
