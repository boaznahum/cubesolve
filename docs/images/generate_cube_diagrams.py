"""
Generate professional cube notation diagrams for documentation.

Creates clear, user-friendly 3D cube images showing:
1. M, E, S slice indexing with clear labels
2. Standard Rw (2 layers) vs our Rw (all layers) difference
3. Face slice indexing (R[1], R[2], etc.)

Usage:
    python docs/images/generate_cube_diagrams.py
"""

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as mpatches
from typing import Tuple, List

# Standard Rubik's cube colors
COLORS = {
    'white': '#FFFFFF',
    'yellow': '#FFD500',
    'red': '#B71234',
    'orange': '#FF5800',
    'green': '#009B48',
    'blue': '#0046AD',
    'gray': '#808080',
    'light_gray': '#C0C0C0',
    'highlight': '#FFE135',  # Bright yellow for highlighting
}

# Face colors in standard orientation
FACE_COLORS = {
    'U': COLORS['white'],
    'D': COLORS['yellow'],
    'R': COLORS['red'],
    'L': COLORS['orange'],
    'F': COLORS['green'],
    'B': COLORS['blue'],
}


def create_cube_vertices(x: float, y: float, z: float, size: float = 1.0) -> np.ndarray:
    """Create vertices for a cube at position (x, y, z)."""
    return np.array([
        [x, y, z],
        [x + size, y, z],
        [x + size, y + size, z],
        [x, y + size, z],
        [x, y, z + size],
        [x + size, y, z + size],
        [x + size, y + size, z + size],
        [x, y + size, z + size],
    ])


def get_cube_faces(vertices: np.ndarray) -> List[List[np.ndarray]]:
    """Get the 6 faces of a cube from its vertices."""
    return [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom (D)
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top (U)
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front (F)
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back (B)
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # Left (L)
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right (R)
    ]


def draw_layer(ax: Axes3D, layer_index: int, n_layers: int, axis: str,
               color: str, alpha: float = 0.8, edge_color: str = 'black') -> None:
    """
    Draw a single layer of the cube.

    axis: 'x' (L-R), 'y' (D-U), 'z' (F-B)
    layer_index: 0-based index from the negative side
    """
    size = 1.0 / n_layers

    for i in range(n_layers):
        for j in range(n_layers):
            if axis == 'x':  # L-R layers
                x = layer_index * size
                y = i * size
                z = j * size
            elif axis == 'y':  # D-U layers
                x = i * size
                y = layer_index * size
                z = j * size
            else:  # F-B layers
                x = i * size
                y = j * size
                z = layer_index * size

            vertices = create_cube_vertices(x, y, z, size * 0.98)
            faces = get_cube_faces(vertices)

            collection = Poly3DCollection(faces, alpha=alpha)
            collection.set_facecolor(color)
            collection.set_edgecolor(edge_color)
            collection.set_linewidth(0.5)
            ax.add_collection3d(collection)


def setup_3d_axes(ax: Axes3D, title: str = "", elev: float = 25, azim: float = -60) -> None:
    """Configure 3D axes for cube visualization."""
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_zlim([0, 1])
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=10)


def create_m_slice_diagram() -> plt.Figure:
    """Create diagram showing M slice indexing on a 5x5 cube."""
    fig = plt.figure(figsize=(14, 8))

    # Left subplot: Full cube view with M slices highlighted
    ax1 = fig.add_subplot(121, projection='3d')
    n = 5

    colors_by_layer = [
        FACE_COLORS['L'],      # Layer 0: L face (orange)
        COLORS['highlight'],    # Layer 1: M[1] - highlighted
        COLORS['highlight'],    # Layer 2: M[2] - highlighted
        COLORS['highlight'],    # Layer 3: M[3] - highlighted
        FACE_COLORS['R'],      # Layer 4: R face (red)
    ]

    alphas = [0.4, 0.9, 0.9, 0.9, 0.4]  # Highlight middle slices

    for layer in range(n):
        draw_layer(ax1, layer, n, 'x', colors_by_layer[layer], alphas[layer])

    setup_3d_axes(ax1, "M Slice Indexing (5x5 Cube)", elev=20, azim=-55)

    # Add labels with arrows
    ax1.text(-0.15, 0.5, 0.5, "L\nface", fontsize=14, ha='center', va='center', fontweight='bold')
    ax1.text(1.15, 0.5, 0.5, "R\nface", fontsize=14, ha='center', va='center', fontweight='bold')

    # Labels for M slices
    ax1.text(0.2, -0.15, 0.5, "M[1]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.4, -0.15, 0.5, "M[2]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.6, -0.15, 0.5, "M[3]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')

    # Right subplot: Explanation
    ax2 = fig.add_subplot(122)
    ax2.axis('off')

    explanation = """
    M Slice (Middle) - Rotates like L

    On a 5x5 cube, there are 3 inner slices
    between the L and R faces.

    Numbering starts from L (the reference face):

        M[1]  =  closest to L face
        M[2]  =  center slice
        M[3]  =  closest to R face

    Standard notation:
        M      =  center slice only (M[2])

    Our notation:
        M      =  ALL inner slices (M[1:3])
        M[2]   =  center slice only

    Key: M rotates in the SAME direction as L
    (front pieces go UP)
    """

    ax2.text(0.1, 0.9, explanation, fontsize=13, va='top', ha='left',
             family='monospace', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


def create_e_slice_diagram() -> plt.Figure:
    """Create diagram showing E slice indexing on a 5x5 cube."""
    fig = plt.figure(figsize=(14, 8))

    # Left subplot: Full cube view with E slices highlighted
    ax1 = fig.add_subplot(121, projection='3d')
    n = 5

    colors_by_layer = [
        FACE_COLORS['D'],      # Layer 0: D face (yellow)
        COLORS['highlight'],    # Layer 1: E[1] - highlighted
        COLORS['highlight'],    # Layer 2: E[2] - highlighted
        COLORS['highlight'],    # Layer 3: E[3] - highlighted
        FACE_COLORS['U'],      # Layer 4: U face (white)
    ]

    alphas = [0.4, 0.9, 0.9, 0.9, 0.4]

    for layer in range(n):
        draw_layer(ax1, layer, n, 'y', colors_by_layer[layer], alphas[layer])

    setup_3d_axes(ax1, "E Slice Indexing (5x5 Cube)", elev=20, azim=-55)

    # Add labels
    ax1.text(0.5, -0.15, 0.5, "D\nface", fontsize=14, ha='center', va='center', fontweight='bold')
    ax1.text(0.5, 1.15, 0.5, "U\nface", fontsize=14, ha='center', va='center', fontweight='bold')

    # Labels for E slices
    ax1.text(0.5, 0.2, -0.15, "E[1]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.5, 0.4, -0.15, "E[2]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.5, 0.6, -0.15, "E[3]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')

    # Right subplot: Explanation
    ax2 = fig.add_subplot(122)
    ax2.axis('off')

    explanation = """
    E Slice (Equator) - Rotates like D

    On a 5x5 cube, there are 3 inner slices
    between the U and D faces.

    Numbering starts from D (the reference face):

        E[1]  =  closest to D face (bottom)
        E[2]  =  center slice (equator)
        E[3]  =  closest to U face (top)

    Standard notation:
        E      =  center slice only (E[2])

    Our notation:
        E      =  ALL inner slices (E[1:3])
        E[2]   =  center slice only

    Key: E rotates in the SAME direction as D
    (front pieces go RIGHT)
    """

    ax2.text(0.1, 0.9, explanation, fontsize=13, va='top', ha='left',
             family='monospace', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


def create_s_slice_diagram() -> plt.Figure:
    """Create diagram showing S slice indexing on a 5x5 cube."""
    fig = plt.figure(figsize=(14, 8))

    # Left subplot: Full cube view with S slices highlighted
    ax1 = fig.add_subplot(121, projection='3d')
    n = 5

    colors_by_layer = [
        FACE_COLORS['F'],      # Layer 0: F face (green)
        COLORS['highlight'],    # Layer 1: S[1] - highlighted
        COLORS['highlight'],    # Layer 2: S[2] - highlighted
        COLORS['highlight'],    # Layer 3: S[3] - highlighted
        FACE_COLORS['B'],      # Layer 4: B face (blue)
    ]

    alphas = [0.4, 0.9, 0.9, 0.9, 0.4]

    for layer in range(n):
        draw_layer(ax1, layer, n, 'z', colors_by_layer[layer], alphas[layer])

    setup_3d_axes(ax1, "S Slice Indexing (5x5 Cube)", elev=20, azim=-55)

    # Add labels
    ax1.text(0.5, 0.5, -0.15, "F\nface", fontsize=14, ha='center', va='center', fontweight='bold')
    ax1.text(0.5, 0.5, 1.15, "B\nface", fontsize=14, ha='center', va='center', fontweight='bold')

    # Labels for S slices
    ax1.text(0.5, -0.15, 0.2, "S[1]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.5, -0.15, 0.4, "S[2]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')
    ax1.text(0.5, -0.15, 0.6, "S[3]", fontsize=13, ha='center', va='center', fontweight='bold', color='#B8860B')

    # Right subplot: Explanation
    ax2 = fig.add_subplot(122)
    ax2.axis('off')

    explanation = """
    S Slice (Standing) - Rotates like F

    On a 5x5 cube, there are 3 inner slices
    between the F and B faces.

    Numbering starts from F (the reference face):

        S[1]  =  closest to F face (front)
        S[2]  =  center slice (standing)
        S[3]  =  closest to B face (back)

    Standard notation:
        S      =  center slice only (S[2])

    Our notation:
        S      =  ALL inner slices (S[1:3])
        S[2]   =  center slice only

    Key: S rotates in the SAME direction as F
    (top pieces go RIGHT)
    """

    ax2.text(0.1, 0.9, explanation, fontsize=13, va='top', ha='left',
             family='monospace', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


def create_rw_comparison_diagram() -> plt.Figure:
    """Create diagram comparing standard Rw vs our Rw."""
    fig = plt.figure(figsize=(16, 8))

    # Left subplot: Standard Rw (2 layers)
    ax1 = fig.add_subplot(121, projection='3d')
    n = 5

    # Standard Rw: only R face + 1 inner layer
    for layer in range(n):
        if layer >= n - 2:  # R face and first inner (layers 3, 4)
            color = COLORS['highlight']
            alpha = 0.9
        else:
            color = COLORS['light_gray']
            alpha = 0.3
        draw_layer(ax1, layer, n, 'x', color, alpha)

    setup_3d_axes(ax1, "Standard Rw (2 layers)", elev=20, azim=-55)

    ax1.text(-0.15, 0.5, 0.5, "L", fontsize=14, ha='center', va='center', fontweight='bold')
    ax1.text(1.15, 0.5, 0.5, "R", fontsize=14, ha='center', va='center', fontweight='bold')

    # Add bracket showing 2 layers
    ax1.text(0.9, -0.2, 0.5, "R[1:2]", fontsize=14, ha='center', fontweight='bold', color='#B8860B')

    # Right subplot: Our Rw (4 layers on 5x5)
    ax2 = fig.add_subplot(122, projection='3d')

    # Our Rw: R face + ALL inner layers (only L stays)
    for layer in range(n):
        if layer >= 1:  # Everything except L face (layers 1,2,3,4)
            color = COLORS['highlight']
            alpha = 0.9
        else:
            color = FACE_COLORS['L']
            alpha = 0.3
        draw_layer(ax2, layer, n, 'x', color, alpha)

    setup_3d_axes(ax2, "Our Rw (4 layers on 5x5)", elev=20, azim=-55)

    ax2.text(-0.15, 0.5, 0.5, "L", fontsize=14, ha='center', va='center', fontweight='bold')
    ax2.text(1.15, 0.5, 0.5, "R", fontsize=14, ha='center', va='center', fontweight='bold')

    # Add bracket showing 4 layers
    ax2.text(0.7, -0.2, 0.5, "R[1:4]", fontsize=14, ha='center', fontweight='bold', color='#B8860B')

    # Add explanation at bottom
    fig.text(0.5, 0.02,
             "Standard: Rw = R + 1 inner layer (always 2 layers)  |  "
             "Ours: Rw = R + ALL inner layers (N-1 layers on NxN cube)",
             ha='center', fontsize=13, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    return fig


def create_r_slice_indexing_diagram() -> plt.Figure:
    """Create diagram showing R face slice indexing."""
    fig = plt.figure(figsize=(14, 8))

    # Left subplot: Full cube view with R slices labeled
    ax1 = fig.add_subplot(121, projection='3d')
    n = 5

    colors_by_layer = [
        FACE_COLORS['L'],      # Layer 0: L face
        '#FFB6C1',             # Layer 1: R[4] - light pink
        '#FFA07A',             # Layer 2: R[3] - light salmon
        '#FF7F50',             # Layer 3: R[2] - coral
        FACE_COLORS['R'],      # Layer 4: R[1] = R face
    ]

    alphas = [0.4, 0.7, 0.7, 0.7, 0.9]

    for layer in range(n):
        draw_layer(ax1, layer, n, 'x', colors_by_layer[layer], alphas[layer])

    setup_3d_axes(ax1, "R Face Slice Indexing (5x5 Cube)", elev=20, azim=-55)

    # Add labels
    ax1.text(-0.15, 0.5, 0.5, "L\nface", fontsize=14, ha='center', va='center', fontweight='bold')
    ax1.text(1.15, 0.5, 0.5, "R\nface", fontsize=14, ha='center', va='center', fontweight='bold')

    # Labels for R slices (numbering from R face)
    ax1.text(0.9, -0.15, 0.5, "R[1]", fontsize=12, ha='center', va='center', fontweight='bold')
    ax1.text(0.7, -0.15, 0.5, "R[2]", fontsize=12, ha='center', va='center', fontweight='bold')
    ax1.text(0.5, -0.15, 0.5, "R[3]", fontsize=12, ha='center', va='center', fontweight='bold')
    ax1.text(0.3, -0.15, 0.5, "R[4]", fontsize=12, ha='center', va='center', fontweight='bold')

    # Right subplot: Explanation
    ax2 = fig.add_subplot(122)
    ax2.axis('off')

    explanation = """
    R Face Slice Indexing (5x5 Cube)

    Face moves are numbered from the face itself:

        R[1]  =  R face (the outer layer)
        R[2]  =  first inner layer from R
        R[3]  =  second inner layer from R
        R[4]  =  third inner layer from R

    Combining slices:

        R       =  same as R[1]
        R[1:2]  =  Standard Rw (2 layers)
        R[1:4]  =  Our Rw (4 layers)
        R[2:4]  =  Inner 3 layers only

    Note: The L face is never included in R moves.
    Use X (cube rotation) to rotate everything.
    """

    ax2.text(0.1, 0.9, explanation, fontsize=13, va='top', ha='left',
             family='monospace', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


def create_slice_overview() -> plt.Figure:
    """Create a comprehensive overview of all slice types."""
    fig = plt.figure(figsize=(18, 12))

    # Create 2x3 grid of 3D plots
    positions = [
        (231, "M Slice (like L)", 'x', 'M'),
        (232, "E Slice (like D)", 'y', 'E'),
        (233, "S Slice (like F)", 'z', 'S'),
        (234, "Standard Rw", 'x', 'Rw_std'),
        (235, "Our Rw", 'x', 'Rw_our'),
        (236, "R[1:3] Example", 'x', 'R_range'),
    ]

    n = 5

    for pos, title, axis, move_type in positions:
        ax = fig.add_subplot(pos, projection='3d')

        for layer in range(n):
            # Determine color based on move type
            if move_type in ['M', 'E', 'S']:
                # Slice moves: highlight inner layers
                if layer == 0 or layer == n - 1:
                    color = COLORS['light_gray']
                    alpha = 0.3
                else:
                    color = COLORS['highlight']
                    alpha = 0.9
            elif move_type == 'Rw_std':
                # Standard Rw: 2 layers from R
                if layer >= n - 2:
                    color = COLORS['highlight']
                    alpha = 0.9
                else:
                    color = COLORS['light_gray']
                    alpha = 0.3
            elif move_type == 'Rw_our':
                # Our Rw: all but L
                if layer >= 1:
                    color = COLORS['highlight']
                    alpha = 0.9
                else:
                    color = COLORS['light_gray']
                    alpha = 0.3
            else:  # R_range
                # R[1:3]: 3 layers from R
                if layer >= n - 3:
                    color = COLORS['highlight']
                    alpha = 0.9
                else:
                    color = COLORS['light_gray']
                    alpha = 0.3

            draw_layer(ax, layer, n, axis, color, alpha)

        setup_3d_axes(ax, title, elev=20, azim=-55)

    # Add legend at bottom
    fig.text(0.5, 0.02,
             "Yellow = layers that move  |  Gray = layers that stay fixed  |  "
             "All examples shown on 5x5 cube",
             ha='center', fontsize=12,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    return fig


def create_simple_overview() -> plt.Figure:
    """Create a simple 2x2 overview matching the original layout but with better readability."""
    fig = plt.figure(figsize=(16, 16))

    n = 5  # 5x5 cube

    # Top-left: M Slice Indexing
    ax1 = fig.add_subplot(221, projection='3d')
    colors = [FACE_COLORS['L']] + [COLORS['highlight']] * 3 + [FACE_COLORS['R']]
    alphas = [0.5, 0.95, 0.95, 0.95, 0.5]
    for layer in range(n):
        draw_layer(ax1, layer, n, 'x', colors[layer], alphas[layer])
    setup_3d_axes(ax1, "", elev=25, azim=-60)

    # Top-right: R Face Slice Indexing
    ax2 = fig.add_subplot(222, projection='3d')
    r_colors = [FACE_COLORS['L'], '#FFCCCC', '#FF9999', '#FF6666', FACE_COLORS['R']]
    r_alphas = [0.4, 0.7, 0.8, 0.9, 0.95]
    for layer in range(n):
        draw_layer(ax2, layer, n, 'x', r_colors[layer], r_alphas[layer])
    setup_3d_axes(ax2, "", elev=25, azim=-60)

    # Bottom-left: Standard Rw (2 layers)
    ax3 = fig.add_subplot(223, projection='3d')
    for layer in range(n):
        if layer >= n - 2:  # R and R[2]
            color = COLORS['highlight']
            alpha = 0.95
        else:
            color = COLORS['light_gray']
            alpha = 0.3
        draw_layer(ax3, layer, n, 'x', color, alpha)
    setup_3d_axes(ax3, "", elev=25, azim=-60)

    # Bottom-right: Our Rw (4 layers on 5x5)
    ax4 = fig.add_subplot(224, projection='3d')
    for layer in range(n):
        if layer >= 1:  # Everything except L
            color = COLORS['highlight']
            alpha = 0.95
        else:
            color = FACE_COLORS['L']
            alpha = 0.4
        draw_layer(ax4, layer, n, 'x', color, alpha)
    setup_3d_axes(ax4, "", elev=25, azim=-60)

    # Add 2D text annotations using figure coordinates
    # Top-left labels
    fig.text(0.25, 0.92, "M Slice Indexing (rotates like L)", ha='center', fontsize=16, fontweight='bold')
    fig.text(0.25, 0.88, "M[1]  M[2]  M[3]  numbered from L face", ha='center', fontsize=13, color='#996600')
    fig.text(0.08, 0.72, "L\nface", ha='center', va='center', fontsize=14, fontweight='bold')
    fig.text(0.42, 0.72, "R\nface", ha='center', va='center', fontsize=14, fontweight='bold')

    # Top-right labels
    fig.text(0.75, 0.92, "R Face Slice Indexing", ha='center', fontsize=16, fontweight='bold')
    fig.text(0.75, 0.88, "R[1]=R face  R[2]  R[3]  R[4]  from R", ha='center', fontsize=13, color='#993333')
    fig.text(0.58, 0.72, "L\nface", ha='center', va='center', fontsize=14, fontweight='bold')
    fig.text(0.92, 0.72, "R\nface", ha='center', va='center', fontsize=14, fontweight='bold')

    # Bottom-left labels
    fig.text(0.25, 0.46, "Standard Rw = R[1:2]", ha='center', fontsize=16, fontweight='bold')
    fig.text(0.25, 0.42, "Always 2 layers (R face + 1 inner)", ha='center', fontsize=13, color='#996600')
    fig.text(0.08, 0.26, "L\nstays", ha='center', va='center', fontsize=14, fontweight='bold', color='gray')
    fig.text(0.42, 0.26, "R\nmoves", ha='center', va='center', fontsize=14, fontweight='bold', color='#996600')

    # Bottom-right labels
    fig.text(0.75, 0.46, "Our Rw = R[1:4] on 5x5", ha='center', fontsize=16, fontweight='bold')
    fig.text(0.75, 0.42, "N-1 layers (all but opposite face)", ha='center', fontsize=13, color='#996600')
    fig.text(0.58, 0.26, "L\nstays", ha='center', va='center', fontsize=14, fontweight='bold', color='gray')
    fig.text(0.92, 0.26, "R\nmoves", ha='center', va='center', fontsize=14, fontweight='bold', color='#996600')

    # Add overall legend at bottom
    fig.text(0.5, 0.02,
             "Yellow = layers that move  |  Gray/colored = layers that stay fixed  |  "
             "All examples on 5x5 cube",
             ha='center', fontsize=14, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='#996600', linewidth=2))

    plt.tight_layout(rect=[0.05, 0.06, 0.95, 0.86])
    return fig


def main() -> None:
    """Generate all cube notation diagrams."""
    import os

    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating cube notation diagrams...")

    # Generate individual diagrams
    diagrams = [
        ("m_slice_indexing.png", create_m_slice_diagram),
        ("e_slice_indexing.png", create_e_slice_diagram),
        ("s_slice_indexing.png", create_s_slice_diagram),
        ("rw_comparison.png", create_rw_comparison_diagram),
        ("r_slice_indexing.png", create_r_slice_indexing_diagram),
        ("slice_overview_6panel.png", create_slice_overview),
        ("cube_slice_overview_3d.png", create_simple_overview),  # Replace the original
    ]

    for filename, create_func in diagrams:
        filepath = os.path.join(output_dir, filename)
        print(f"  Creating {filename}...")
        fig = create_func()
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"    Saved: {filepath}")

    print("\nAll diagrams generated successfully!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
