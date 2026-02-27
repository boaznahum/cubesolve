#!/usr/bin/env python3
"""
Create cube face textures from photos by detecting and cropping faces.

Usage:
    # Step 1: Extract all faces from photos
    python make_face_textures.py extract "C:/Photos/Family" output_folder

    # Step 2: Review the faces in output_folder/all_faces/
    #         Delete the ones you don't want

    # Step 3: Select 6 faces for the cube (by number)
    python make_face_textures.py select output_folder 1 3 5 7 9 11
    # This assigns: face_001.png→F, face_003.png→B, face_005.png→R, etc.

    # Or just copy the best 6 to output_folder as F.png, B.png, R.png, L.png, U.png, D.png

Requirements:
    pip install opencv-python pillow

"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple
import shutil

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: .venv_pyglet2/Scripts/pip.exe install opencv-python pillow")
    sys.exit(1)


# Face names for cube faces
FACE_NAMES = ['F', 'B', 'R', 'L', 'U', 'D']

# Output size (square)
OUTPUT_SIZE = 512

# Padding around detected face (as fraction of face size)
FACE_PADDING = 0.5


def find_faces(image_path: Path) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """Detect faces in an image.

    Args:
        image_path: Path to image file

    Returns:
        List of (cropped_face_image, (x, y, w, h)) tuples
    """
    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"  Could not load: {image_path}")
        return []

    # Convert to grayscale for detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load face detector (Haar cascade - comes with OpenCV)
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(50, 50)
    )

    results = []
    for (x, y, w, h) in faces:
        # Add padding around face
        pad_w = int(w * FACE_PADDING)
        pad_h = int(h * FACE_PADDING)

        # Calculate padded bounds (clamp to image bounds)
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(img.shape[1], x + w + pad_w)
        y2 = min(img.shape[0], y + h + pad_h)

        # Crop face region
        face_img = img[y1:y2, x1:x2]
        results.append((face_img, (x, y, w, h)))

    return results


def make_square(img: np.ndarray) -> np.ndarray:
    """Crop/pad image to square, centered on content."""
    h, w = img.shape[:2]

    if h == w:
        return img

    # Crop to square (center crop)
    if h > w:
        # Taller than wide - crop top/bottom
        diff = h - w
        top = diff // 2
        return img[top:top + w, :]
    else:
        # Wider than tall - crop left/right
        diff = w - h
        left = diff // 2
        return img[:, left:left + h]


def process_face(face_img: np.ndarray, output_path: Path) -> bool:
    """Process a face image and save as texture.

    Args:
        face_img: OpenCV image (BGR)
        output_path: Where to save the result

    Returns:
        True if successful
    """
    try:
        # Make square
        square = make_square(face_img)

        # Resize to output size
        resized = cv2.resize(square, (OUTPUT_SIZE, OUTPUT_SIZE), interpolation=cv2.INTER_LANCZOS4)

        # Convert BGR to RGB for PIL
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Save with PIL (better PNG compression)
        pil_img = Image.fromarray(rgb)
        pil_img.save(output_path, 'PNG')

        return True
    except Exception as e:
        print(f"  Error processing face: {e}")
        return False


def extract_faces(input_dir: Path, output_dir: Path) -> None:
    """Extract all faces from photos and save them numbered."""

    # Create output directories
    all_faces_dir = output_dir / "all_faces"
    all_faces_dir.mkdir(parents=True, exist_ok=True)

    # Find all images
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    image_files = [f for f in input_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"No images found in {input_dir}")
        sys.exit(1)

    print(f"Found {len(image_files)} images in {input_dir}")

    # Collect all faces
    face_count = 0

    for img_path in sorted(image_files):
        print(f"Processing: {img_path.name}")
        faces = find_faces(img_path)
        print(f"  Found {len(faces)} face(s)")

        for face_img, bbox in faces:
            face_count += 1
            output_path = all_faces_dir / f"face_{face_count:03d}.png"
            if process_face(face_img, output_path):
                print(f"  Saved: {output_path.name}")

    print(f"\n{'='*50}")
    print(f"Extracted {face_count} faces to: {all_faces_dir}")
    print(f"\nNext steps:")
    print(f"  1. Open {all_faces_dir} and review the faces")
    print(f"  2. Delete any that aren't actual faces")
    print(f"  3. Run: python make_face_textures.py select {output_dir} <6 numbers>")
    print(f"     Example: python make_face_textures.py select {output_dir} 1 2 3 4 5 6")
    print(f"     This assigns face_001→F, face_002→B, face_003→R, face_004→L, face_005→U, face_006→D")
    print(f"\n  Or manually copy 6 faces to {output_dir} as F.png, B.png, R.png, L.png, U.png, D.png")


def select_faces(output_dir: Path, face_numbers: List[int]) -> None:
    """Select specific faces for the cube."""

    all_faces_dir = output_dir / "all_faces"

    if not all_faces_dir.exists():
        print(f"Error: {all_faces_dir} not found. Run 'extract' first.")
        sys.exit(1)

    if len(face_numbers) != 6:
        print(f"Error: Need exactly 6 face numbers, got {len(face_numbers)}")
        print(f"Usage: python make_face_textures.py select {output_dir} 1 2 3 4 5 6")
        sys.exit(1)

    print(f"Selecting faces: {face_numbers}")
    print(f"Mapping: F={face_numbers[0]}, B={face_numbers[1]}, R={face_numbers[2]}, L={face_numbers[3]}, U={face_numbers[4]}, D={face_numbers[5]}")

    for i, (face_name, num) in enumerate(zip(FACE_NAMES, face_numbers)):
        src_path = all_faces_dir / f"face_{num:03d}.png"
        dst_path = output_dir / f"{face_name}.png"

        if not src_path.exists():
            print(f"  Warning: {src_path.name} not found, skipping {face_name}")
            continue

        shutil.copy(src_path, dst_path)
        print(f"  {face_name}.png <- face_{num:03d}.png")

    print(f"\nTextures saved to: {output_dir}")
    print(f"\nTo use these textures:")
    print(f'  1. Add "{output_dir.name}" to TEXTURE_SETS in config.py')
    print("  2. Run the cube and press Ctrl+Shift+T to cycle textures")


def show_help():
    print(__doc__)
    print("\nCommands:")
    print("  extract <input_folder> <output_folder>  - Extract all faces from photos")
    print("  select <output_folder> N1 N2 N3 N4 N5 N6 - Select 6 faces for cube")
    print("\nExamples:")
    print('  python make_face_textures.py extract "C:/Photos" ./family_faces')
    print('  python make_face_textures.py select ./family_faces 1 3 5 7 9 11')


def main() -> None:
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "extract":
        if len(sys.argv) < 4:
            print("Usage: python make_face_textures.py extract <input_folder> <output_folder>")
            sys.exit(1)
        input_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3])

        if not input_dir.exists():
            print(f"Error: Input folder not found: {input_dir}")
            sys.exit(1)

        extract_faces(input_dir, output_dir)

    elif command == "select":
        if len(sys.argv) < 9:
            print("Usage: python make_face_textures.py select <output_folder> N1 N2 N3 N4 N5 N6")
            print("Example: python make_face_textures.py select ./faces 1 2 3 4 5 6")
            sys.exit(1)
        output_dir = Path(sys.argv[2])
        try:
            face_numbers = [int(x) for x in sys.argv[3:9]]
        except ValueError:
            print("Error: Face numbers must be integers")
            sys.exit(1)
        select_faces(output_dir, face_numbers)

    elif command in ("help", "-h", "--help"):
        show_help()

    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
