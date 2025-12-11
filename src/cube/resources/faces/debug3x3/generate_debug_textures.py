"""Generate debug textures for 3x3 cube with clear directional information."""
from PIL import Image, ImageDraw, ImageFont
import os

# Configuration
CELL_SIZE = 100  # pixels per cell
SIZE = 3  # 3x3 cube
IMAGE_SIZE = CELL_SIZE * SIZE

# Colors for each face (background)
FACE_COLORS = {
    'F': (0, 100, 200),      # Blue
    'B': (0, 150, 50),       # Green
    'U': (255, 255, 255),    # White
    'D': (255, 200, 0),      # Yellow
    'L': (255, 100, 0),      # Orange
    'R': (200, 0, 0),        # Red
}

# Text colors (contrasting)
TEXT_COLORS = {
    'F': (255, 255, 255),    # White on blue
    'B': (255, 255, 255),    # White on green
    'U': (0, 0, 0),          # Black on white
    'D': (0, 0, 0),          # Black on yellow
    'L': (0, 0, 0),          # Black on orange
    'R': (255, 255, 255),    # White on red
}

def draw_arrow(draw, cx, cy, size, color, direction='up'):
    """Draw an arrow pointing in the specified direction."""
    arrow_len = size * 0.3
    arrow_head = size * 0.15

    if direction == 'up':
        # Shaft
        draw.line([(cx, cy + arrow_len), (cx, cy - arrow_len)], fill=color, width=3)
        # Head
        draw.polygon([
            (cx, cy - arrow_len - arrow_head),
            (cx - arrow_head, cy - arrow_len + 5),
            (cx + arrow_head, cy - arrow_len + 5)
        ], fill=color)

def create_face_image(face_name: str) -> Image.Image:
    """Create a debug image for one face."""
    bg_color = FACE_COLORS[face_name]
    text_color = TEXT_COLORS[face_name]

    img = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to get a font, fall back to default
    font_large: ImageFont.FreeTypeFont | ImageFont.ImageFont
    font_small: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    for row in range(SIZE):
        for col in range(SIZE):
            # Cell boundaries (row 0 = bottom in our coordinate system)
            # But PIL draws from top, so we need to flip
            pil_row = SIZE - 1 - row  # Flip for PIL
            x0 = col * CELL_SIZE
            y0 = pil_row * CELL_SIZE
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE
            cx = (x0 + x1) // 2
            cy = (y0 + y1) // 2

            # Draw cell border
            draw.rectangle([x0, y0, x1-1, y1-1], outline=text_color, width=2)

            # Draw arrow pointing UP (in cell's local coordinate system)
            draw_arrow(draw, cx, cy - 10, CELL_SIZE, text_color, 'up')

            # Draw face name at top of cell
            face_text = f"{face_name}"
            draw.text((cx, y0 + 5), face_text, fill=text_color, font=font_large, anchor='mt')

            # Draw coordinates at bottom of cell
            coord_text = f"({row},{col})"
            draw.text((cx, y1 - 5), coord_text, fill=text_color, font=font_small, anchor='mb')

    return img

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))

    for face_name in ['F', 'B', 'U', 'D', 'L', 'R']:
        img = create_face_image(face_name)
        filepath = os.path.join(output_dir, f"{face_name}.png")
        img.save(filepath)
        print(f"Created {filepath}")

    print(f"\nAll textures created in {output_dir}")

if __name__ == '__main__':
    main()
