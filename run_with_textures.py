#!/usr/bin/env python3
"""
Launch the Rubik's cube solver with face textures loaded.

Usage:
    python run_with_textures.py                    # Uses default set1
    python run_with_textures.py set2               # Uses set2 (gradients)
    python run_with_textures.py family             # Uses family (3x3 grid)
    python run_with_textures.py /path/to/textures  # Uses custom path

Creating Custom Textures:
    1. Create a directory with 6 images:
       - F.png (Front face - green)
       - B.png (Back face - blue)
       - R.png (Right face - red)
       - L.png (Left face - orange)
       - U.png (Up face - white)
       - D.png (Down face - yellow)

    2. Images should be square (256x256 recommended)

    3. Run: python run_with_textures.py /path/to/your/textures

Keyboard Controls:
    Ctrl+T  - Toggle texture mode on/off
    All other cube controls work normally (R, L, U, D, F, B for rotations)

Note: Texture mode only works with the pyglet2 backend.
"""
import sys
from pathlib import Path


def main() -> None:
    from cube.resources.faces import get_texture_set_path, list_texture_sets

    # Determine which texture set to use
    texture_arg = sys.argv[1] if len(sys.argv) > 1 else "set1"

    # Try as preset name first, then as path
    texture_path = get_texture_set_path(texture_arg)
    if texture_path is None:
        # Not a preset, try as direct path
        direct_path = Path(texture_arg)
        if direct_path.exists():
            texture_path = direct_path
        else:
            print(f"Error: Texture set not found: {texture_arg}")
            print(f"\nAvailable presets: {', '.join(list_texture_sets())}")
            print("Or specify a path to a directory with F.png, B.png, R.png, L.png, U.png, D.png")
            sys.exit(1)

    # Import after path check (in case of missing dependencies)
    from cube.application.AbstractApp import AbstractApp
    from cube.main_any_backend import create_app_window

    # Create the app and window (must use pyglet2 for texture support)
    app = AbstractApp.create_non_default(cube_size=3)
    window = create_app_window(app, backend_name="pyglet2", width=720, height=720)

    # Load textures
    loaded = window.load_texture_set(str(texture_path))
    print(f"Loaded {loaded}/6 textures from {texture_path}")

    # Enable texture mode (only if not already enabled from config)
    if not window._modern_viewer._texture_mode:
        window.toggle_texture_mode()
    print("Texture mode enabled. Press Ctrl+T to toggle off.")

    # Run the app
    window.run()


if __name__ == "__main__":
    main()
