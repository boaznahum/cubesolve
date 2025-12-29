#!/usr/bin/env python3
"""
Generate graphical diagrams for the edge-face coordinate system documentation.

Creates:
1. Face rotation diagram - showing ltr coordinate system and rotation pattern
2. Slice rotation diagram - showing physical alignment and axis exchange
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np
from pathlib import Path


def create_face_rotation_diagram():
    """Create diagram showing face rotation with ltr coordinates."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 10.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Face Rotation: LTR Coordinate System\n(Clockwise Rotation)', fontsize=16, fontweight='bold')

    # Draw the face (center square)
    face_rect = patches.FancyBboxPatch((3, 3), 4, 4, boxstyle="round,pad=0.05",
                                        facecolor='lightblue', edgecolor='black', linewidth=2)
    ax.add_patch(face_rect)
    ax.text(5, 5, 'Face F', fontsize=14, ha='center', va='center', fontweight='bold')

    # Colors for edges
    colors = {'top': '#FF6B6B', 'bottom': '#4ECDC4', 'left': '#45B7D1', 'right': '#96CEB4'}

    # Draw TOP edge with ltr labels
    for i in range(3):
        x = 3.5 + i * 1.2
        rect = patches.Rectangle((x, 7.2), 1, 0.6, facecolor=colors['top'], edgecolor='black')
        ax.add_patch(rect)
        ax.text(x + 0.5, 7.5, str(i), fontsize=12, ha='center', va='center', fontweight='bold')
    ax.text(5, 8.2, 'TOP (horizontal)', fontsize=11, ha='center', va='center')
    ax.annotate('', xy=(6.5, 7.9), xytext=(3.5, 7.9),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(5, 8.5, 'ltr: 0 → 1 → 2', fontsize=10, ha='center', va='center', style='italic')

    # Draw BOTTOM edge with ltr labels
    for i in range(3):
        x = 3.5 + i * 1.2
        rect = patches.Rectangle((x, 2.2), 1, 0.6, facecolor=colors['bottom'], edgecolor='black')
        ax.add_patch(rect)
        ax.text(x + 0.5, 2.5, str(i), fontsize=12, ha='center', va='center', fontweight='bold')
    ax.text(5, 1.5, 'BOTTOM (horizontal)', fontsize=11, ha='center', va='center')
    ax.annotate('', xy=(6.5, 2.1), xytext=(3.5, 2.1),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(5, 1.2, 'ltr: 0 → 1 → 2', fontsize=10, ha='center', va='center', style='italic')

    # Draw LEFT edge with ltr labels (vertical)
    for i in range(3):
        y = 3.5 + i * 1.2
        rect = patches.Rectangle((2.2, y), 0.6, 1, facecolor=colors['left'], edgecolor='black')
        ax.add_patch(rect)
        ax.text(2.5, y + 0.5, str(i), fontsize=12, ha='center', va='center', fontweight='bold')
    ax.text(1.3, 5, 'LEFT\n(vertical)', fontsize=11, ha='center', va='center')
    ax.annotate('', xy=(2.1, 6.5), xytext=(2.1, 3.5),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(0.8, 5, 'ltr:\n0→1→2', fontsize=9, ha='center', va='center', style='italic')

    # Draw RIGHT edge with ltr labels (vertical)
    for i in range(3):
        y = 3.5 + i * 1.2
        rect = patches.Rectangle((7.2, y), 0.6, 1, facecolor=colors['right'], edgecolor='black')
        ax.add_patch(rect)
        ax.text(7.5, y + 0.5, str(i), fontsize=12, ha='center', va='center', fontweight='bold')
    ax.text(8.7, 5, 'RIGHT\n(vertical)', fontsize=11, ha='center', va='center')
    ax.annotate('', xy=(7.9, 6.5), xytext=(7.9, 3.5),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(9.2, 5, 'ltr:\n0→1→2', fontsize=9, ha='center', va='center', style='italic')

    # Draw rotation arrows
    rotation_style = dict(arrowstyle='->', color='#E74C3C', lw=3, mutation_scale=20)

    # LEFT → TOP
    ax.annotate('', xy=(3.2, 7.5), xytext=(2.8, 6.2),
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2,
                               connectionstyle='arc3,rad=0.3'))

    # TOP → RIGHT
    ax.annotate('', xy=(7.2, 6.2), xytext=(6.8, 7.5),
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2,
                               connectionstyle='arc3,rad=0.3'))

    # RIGHT → BOTTOM
    ax.annotate('', xy=(6.8, 2.5), xytext=(7.2, 3.8),
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2,
                               connectionstyle='arc3,rad=0.3'))

    # BOTTOM → LEFT
    ax.annotate('', xy=(2.8, 3.8), xytext=(3.2, 2.5),
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2,
                               connectionstyle='arc3,rad=0.3'))

    # Add rotation pattern text
    pattern_text = """Clockwise Rotation Pattern:

LEFT[ltr] → TOP[ltr]
TOP[ltr] → RIGHT[inv(ltr)]
RIGHT[inv(ltr)] → BOTTOM[inv(ltr)]
BOTTOM[inv(ltr)] → LEFT[ltr]

Key insight: inv() handles the geometry,
edge translation handles f1/f2 differences!"""

    ax.text(5, -0.2, pattern_text, fontsize=10, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            family='monospace')

    plt.tight_layout()
    return fig


def create_slice_rotation_diagram():
    """Create diagram showing S slice rotation with axis exchange.

    S slice alternates between ROW and COLUMN as it moves around faces:
    - U: ROW (uses vertical edge_left L-U)
    - R: COLUMN (uses horizontal edge_top U-R)
    - D: ROW (uses vertical edge_right D-R)
    - L: COLUMN (uses horizontal edge_bottom L-D)

    Note: M slice does NOT have axis exchange - it stays as COLUMN on all faces.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    # Left side: Face U (looking down)
    ax1 = axes[0]
    ax1.set_xlim(-0.5, 5.5)
    ax1.set_ylim(-0.5, 5.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('Face U (looking down)\nS slice is a ROW', fontsize=14, fontweight='bold')

    # Draw 3x3 grid for Face U
    for i in range(3):
        for j in range(3):
            color = '#FFD93D' if i == 1 else 'lightgray'  # Middle row is S slice
            rect = patches.Rectangle((1 + j * 1.2, 1 + i * 1.2), 1.1, 1.1,
                                     facecolor=color, edgecolor='black', linewidth=2)
            ax1.add_patch(rect)
            if i == 1:
                ax1.text(1.55 + j * 1.2, 1.55 + i * 1.2, 'S', fontsize=14,
                        ha='center', va='center', fontweight='bold')

    # Labels for Face U
    ax1.text(2.8, 0.3, 'S slice (ROW)', fontsize=11, ha='center', va='center',
            color='#E67E22', fontweight='bold')

    # Draw vertical ltr arrow on left (edge_left L-U)
    ax1.annotate('', xy=(0.5, 4), xytext=(0.5, 1.5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax1.text(0.2, 2.8, 'ltr\n0→2', fontsize=10, ha='center', va='center', color='blue')

    # Label edges
    ax1.text(2.8, 4.8, 'edge_top (U-B)', fontsize=9, ha='center', va='center', style='italic')
    ax1.text(2.8, 0.6, 'edge_bottom (F-U)', fontsize=9, ha='center', va='center', style='italic')
    ax1.text(0.3, 2.2, 'edge_left\n(L-U)\nVERTICAL', fontsize=9, ha='center', va='center',
             style='italic', color='blue', fontweight='bold')

    # Right side: Face R (looking from right side)
    ax2 = axes[1]
    ax2.set_xlim(-0.5, 5.5)
    ax2.set_ylim(-0.5, 5.5)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('Face R (looking from right)\nS slice is a COLUMN', fontsize=14, fontweight='bold')

    # Draw 3x3 grid for Face R
    for i in range(3):
        for j in range(3):
            color = '#FFD93D' if j == 1 else 'lightgray'  # Middle column is S slice
            rect = patches.Rectangle((1 + j * 1.2, 1 + i * 1.2), 1.1, 1.1,
                                     facecolor=color, edgecolor='black', linewidth=2)
            ax2.add_patch(rect)
            if j == 1:
                ax2.text(1.55 + j * 1.2, 1.55 + i * 1.2, 'S', fontsize=14,
                        ha='center', va='center', fontweight='bold')

    # Labels for Face R
    ax2.text(2.8, 0.3, 'S slice (COLUMN)', fontsize=11, ha='center', va='center',
            color='#E67E22', fontweight='bold')

    # Draw horizontal ltr arrow on top (edge_top U-R)
    ax2.annotate('', xy=(4, 4.7), xytext=(1.5, 4.7),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax2.text(2.8, 5.0, 'ltr 0 → 1 → 2', fontsize=10, ha='center', va='center', color='blue')

    # Label edges
    ax2.text(2.8, 4.4, 'edge_top (U-R)\nHORIZONTAL', fontsize=9, ha='center', va='center',
             style='italic', color='blue', fontweight='bold')
    ax2.text(2.8, 0.6, 'edge_bottom (D-R)', fontsize=9, ha='center', va='center', style='italic')
    ax2.text(0.5, 2.8, 'edge_left\n(F-R)', fontsize=9, ha='center', va='center', style='italic')

    # Add connection arrow between the two faces
    fig.text(0.5, 0.15,
             'S SLICE AXIS EXCHANGE: ROW on U → COLUMN on R\n'
             'U uses VERTICAL edge (L-U) → ltr selects ROW\n'
             'R uses HORIZONTAL edge (U-R) → ltr selects COLUMN\n'
             'Physical alignment preserved via edge translation!',
             fontsize=12, ha='center', va='center',
             bbox=dict(boxstyle='round', facecolor='#E8F6F3', alpha=0.9, edgecolor='#1ABC9C'),
             fontweight='bold')

    plt.tight_layout(rect=[0, 0.2, 1, 1])
    return fig


def create_physical_alignment_diagram():
    """Create diagram showing physical alignment across 4 faces."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 11)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Slice Rotation: Physical Alignment Across 4 Faces\n(M Slice Path: F → U → B → D → F)',
                fontsize=14, fontweight='bold')

    # Draw 4 faces in a cross pattern
    face_positions = {
        'U': (4, 7),
        'L': (1, 4),
        'F': (4, 4),
        'R': (7, 4),
        'D': (4, 1)
    }

    face_colors = {
        'U': '#FFFACD',  # Light yellow
        'L': '#FFE4C4',  # Bisque
        'F': '#E0FFFF',  # Light cyan
        'R': '#E6E6FA',  # Lavender
        'D': '#F0FFF0'   # Honeydew
    }

    for face_name, (x, y) in face_positions.items():
        # Draw face
        rect = patches.FancyBboxPatch((x, y), 2, 2, boxstyle="round,pad=0.02",
                                       facecolor=face_colors[face_name],
                                       edgecolor='black', linewidth=2)
        ax.add_patch(rect)

        # Draw M slice highlight (middle column or row)
        if face_name in ['F', 'B']:
            # Vertical slice (column)
            m_rect = patches.Rectangle((x + 0.7, y + 0.1), 0.6, 1.8,
                                       facecolor='#FFD93D', edgecolor='orange', linewidth=2)
            ax.add_patch(m_rect)
        elif face_name in ['U', 'D']:
            # Horizontal slice (row) - at bottom for U, top for D
            m_y = y + 0.1 if face_name == 'U' else y + 1.1
            m_rect = patches.Rectangle((x + 0.1, m_y), 1.8, 0.6,
                                       facecolor='#FFD93D', edgecolor='orange', linewidth=2)
            ax.add_patch(m_rect)

        # Face label
        ax.text(x + 1, y + 1, face_name, fontsize=16, ha='center', va='center', fontweight='bold')

    # Draw arrows showing slice path
    arrow_style = dict(arrowstyle='->', color='#E74C3C', lw=3, mutation_scale=15)

    # F → U
    ax.annotate('', xy=(5, 7), xytext=(5, 6.2), arrowprops=arrow_style)
    ax.text(5.3, 6.6, '1', fontsize=12, color='#E74C3C', fontweight='bold')

    # U → B (wraps around - represented going off-screen)
    ax.annotate('', xy=(5, 9.5), xytext=(5, 9), arrowprops=arrow_style)
    ax.text(5, 9.8, 'to B', fontsize=10, ha='center', color='#E74C3C')
    ax.text(5.3, 9.3, '2', fontsize=12, color='#E74C3C', fontweight='bold')

    # B → D (from off-screen)
    ax.annotate('', xy=(5, 3), xytext=(5, 3.5), arrowprops=arrow_style)
    ax.text(5, 3.7, 'from B', fontsize=10, ha='center', color='#E74C3C')
    ax.text(5.3, 3.3, '3', fontsize=12, color='#E74C3C', fontweight='bold')

    # D → F
    ax.annotate('', xy=(5, 4), xytext=(5, 3), arrowprops=arrow_style)
    ax.text(5.3, 3.5, '4', fontsize=12, color='#E74C3C', fontweight='bold')

    # Add explanation
    explanation = """Physical Alignment Problem:

• Slice 2 on Face F must align with the correct slice on U, B, D
• Each face has different internal storage order
• The edge translation layer ensures physical alignment

Solution: Edge as Bridge
• current_face ltr → edge index → next_face ltr
• Same ltr value at connection point = same physical position"""

    ax.text(9, 5, explanation, fontsize=10, ha='left', va='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
            family='monospace')

    plt.tight_layout()
    return fig


def main():
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'docs' / 'design2' / 'images'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate and save diagrams
    print("Generating face rotation diagram...")
    fig1 = create_face_rotation_diagram()
    fig1.savefig(output_dir / 'face-rotation-ltr.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    plt.close(fig1)
    print(f"  Saved: {output_dir / 'face-rotation-ltr.png'}")

    print("Generating slice rotation diagram...")
    fig2 = create_slice_rotation_diagram()
    fig2.savefig(output_dir / 'slice-rotation-axis-exchange.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    plt.close(fig2)
    print(f"  Saved: {output_dir / 'slice-rotation-axis-exchange.png'}")

    print("Generating physical alignment diagram...")
    fig3 = create_physical_alignment_diagram()
    fig3.savefig(output_dir / 'slice-physical-alignment.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    plt.close(fig3)
    print(f"  Saved: {output_dir / 'slice-physical-alignment.png'}")

    print("\nAll diagrams generated successfully!")


if __name__ == "__main__":
    main()
