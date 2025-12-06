#!/usr/bin/env python3
"""
Generate synthetic face images for testing texture mapping.

Usage:
    python generate_images.py <type> <output_dir>

Types:
    letters   - Simple face letters (F, B, R, L, U, D) with borders
    gradients - Gradient patterns with UV direction arrows
    grid      - 3x3 numbered grid (1-9) for UV verification

Examples:
    python generate_images.py letters set1
    python generate_images.py gradients set2
    python generate_images.py grid family
    python generate_images.py letters demo

Output:
    Creates 6 PNG images (F.png, B.png, R.png, L.png, U.png, D.png)
    in the specified output directory.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Face colors (matching cube colors)
FACE_COLORS = {
    'F': (0, 255, 0),       # Green (Front)
    'B': (0, 69, 173),      # Blue (Back)
    'R': (184, 18, 51),     # Red (Right)
    'L': (255, 89, 0),      # Orange (Left)
    'U': (255, 255, 255),   # White (Up)
    'D': (255, 214, 0),     # Yellow (Down)
}

# Text colors for contrast
TEXT_COLORS = {
    'F': (0, 0, 0),
    'B': (255, 255, 255),
    'R': (255, 255, 255),
    'L': (0, 0, 0),
    'U': (0, 0, 0),
    'D': (0, 0, 0),
}


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a font, falling back to default if Arial not available."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def generate_letters(output_dir: Path, size: int = 256) -> None:
    """Letters: Simple face letter with border."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for face_name, color in FACE_COLORS.items():
        img = Image.new('RGB', (size, size), color)
        draw = ImageDraw.Draw(img)

        # Draw border
        border = 8
        draw.rectangle([border, border, size-border-1, size-border-1],
                      outline=(0, 0, 0), width=4)

        # Draw face letter
        font = get_font(size // 2)
        text_color = TEXT_COLORS[face_name]

        bbox = draw.textbbox((0, 0), face_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 10
        draw.text((x, y), face_name, fill=text_color, font=font)

        img.save(output_dir / f"{face_name}.png")

    print(f"Generated 6 images in {output_dir}/")


def generate_gradients(output_dir: Path, size: int = 256) -> None:
    """Gradients: Gradient pattern with arrows showing UV orientation."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for face_name, base_color in FACE_COLORS.items():
        img = Image.new('RGB', (size, size), (0, 0, 0))
        pixels = img.load()
        if pixels is None:
            raise RuntimeError(f"Failed to load pixels for {face_name}")

        # Create gradient (dark bottom-left to light top-right)
        for y in range(size):
            for x in range(size):
                factor = (x + (size - 1 - y)) / (2 * (size - 1))
                factor = 0.3 + 0.7 * factor

                r = int(base_color[0] * factor)
                g = int(base_color[1] * factor)
                b = int(base_color[2] * factor)
                pixels[x, y] = (r, g, b)

        draw = ImageDraw.Draw(img)
        text_color = TEXT_COLORS[face_name]
        font = get_font(size // 6)

        # Draw face letter in corner
        draw.text((10, 10), face_name, fill=text_color, font=font)

        # Draw UV direction arrows
        draw.line([(20, size-30), (size-40, size-30)], fill=text_color, width=2)
        draw.polygon([(size-40, size-30), (size-50, size-25), (size-50, size-35)],
                    fill=text_color)
        draw.text((size//2-10, size-50), "U", fill=text_color, font=font)

        draw.line([(30, size-20), (30, 40)], fill=text_color, width=2)
        draw.polygon([(30, 40), (25, 50), (35, 50)], fill=text_color)
        draw.text((10, size//2), "V", fill=text_color, font=font)

        img.save(output_dir / f"{face_name}.png")

    print(f"Generated 6 images in {output_dir}/")


def generate_grid(output_dir: Path, size: int = 256) -> None:
    """Grid: 3x3 grid with numbered cells for UV verification."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for face_name, base_color in FACE_COLORS.items():
        img = Image.new('RGB', (size, size), base_color)
        draw = ImageDraw.Draw(img)

        cell_size = size // 3
        text_color = TEXT_COLORS[face_name]

        font = get_font(cell_size // 3)
        small_font = get_font(cell_size // 6)

        # Draw 3x3 grid
        for i in range(4):
            draw.line([(i * cell_size, 0), (i * cell_size, size)], fill=(0, 0, 0), width=2)
            draw.line([(0, i * cell_size), (size, i * cell_size)], fill=(0, 0, 0), width=2)

        # Number each cell (1-9)
        cell_num = 1
        for row in range(3):
            for col in range(3):
                cx = col * cell_size + cell_size // 2
                cy = (2 - row) * cell_size + cell_size // 2

                text = str(cell_num)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                draw.text((cx - text_width // 2, cy - text_height // 2),
                         text, fill=text_color, font=font)
                cell_num += 1

        draw.text((5, 5), face_name, fill=text_color, font=small_font)
        img.save(output_dir / f"{face_name}.png")

    print(f"Generated 6 images in {output_dir}/")


GENERATORS = {
    'letters': generate_letters,
    'gradients': generate_gradients,
    'grid': generate_grid,
}


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        print(f"Available types: {', '.join(GENERATORS.keys())}")
        sys.exit(1)

    image_type = sys.argv[1].lower()
    output_name = sys.argv[2]

    if image_type not in GENERATORS:
        print(f"Unknown type: {image_type}")
        print(f"Available types: {', '.join(GENERATORS.keys())}")
        sys.exit(1)

    base_dir = Path(__file__).parent
    output_dir = base_dir / output_name

    GENERATORS[image_type](output_dir)


if __name__ == "__main__":
    main()
