"""
Create test textures with directional arrows for debugging texture rotation.

Each face gets a different colored arrow pointing UP, so we can easily see
if textures rotate correctly during face rotations.

Usage:
    python tools/create_arrow_textures.py

Creates: tools/arrow_textures/F.png, U.png, R.png, etc.
"""
from pathlib import Path

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

# Arrow color (contrasting)
ARROW_COLORS = {
    "F": (255, 255, 255),   # White arrow on blue
    "B": (255, 255, 255),   # White arrow on green
    "R": (255, 255, 255),   # White arrow on red
    "L": (0, 0, 0),         # Black arrow on orange
    "U": (0, 0, 0),         # Black arrow on yellow
    "D": (0, 0, 0),         # Black arrow on white
}

def create_arrow_texture(face_name: str, img_size: int = 128) -> Image.Image:
    """Create a texture with a SINGLE upward-pointing arrow.

    Each cell has its own texture (per-cell texturing mode), so each image
    should contain just ONE arrow that fills the entire image.

    Args:
        face_name: Name of the face (F, B, R, L, U, D)
        img_size: Total image size in pixels
    """
    bg_color = FACE_COLORS[face_name]
    arrow_color = ARROW_COLORS[face_name]

    img = Image.new("RGB", (img_size, img_size), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw border (for debugging alignment)
    draw.rectangle(
        [2, 2, img_size - 3, img_size - 3],
        outline=arrow_color,
        width=2
    )

    # Draw single arrow filling the image
    draw_arrow_in_cell(draw, 0, 0, img_size, arrow_color)

    return img


def draw_arrow_in_cell(draw: ImageDraw.Draw, x: int, y: int, size: int, color: tuple) -> None:
    """Draw an upward-pointing arrow within a cell."""
    margin = size // 8
    arrow_width = size // 4
    arrow_head_height = size // 3
    shaft_width = size // 8

    center_x = x + size // 2

    # Arrow shaft (rectangle)
    shaft_left = center_x - shaft_width // 2
    shaft_right = center_x + shaft_width // 2
    shaft_top = y + margin + arrow_head_height
    shaft_bottom = y + size - margin

    draw.rectangle([shaft_left, shaft_top, shaft_right, shaft_bottom], fill=color)

    # Arrow head (triangle pointing up)
    arrow_points = [
        (center_x, y + margin),                              # Top point
        (center_x - arrow_width, shaft_top),                 # Bottom left
        (center_x + arrow_width, shaft_top),                 # Bottom right
    ]
    draw.polygon(arrow_points, fill=color)


def main():
    print(f"Creating arrow textures in {OUTPUT_DIR}")

    for face_name in FACE_COLORS:
        img = create_arrow_texture(face_name)
        output_path = OUTPUT_DIR / f"{face_name}.png"
        img.save(output_path)
        print(f"  Created {output_path}")

    print("\nDone! Load these textures in the GUI to test rotation behavior.")
    print("All arrows should point UP initially.")
    print("After F rotation, arrows ON face F should point RIGHT.")
    print("Arrows on adjacent edges should still point UP (relative to their new face).")


if __name__ == "__main__":
    main()
